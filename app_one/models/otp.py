# -*- coding: utf-8 -*-
import hashlib
import secrets
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RealEstateOTP(models.Model):
    _name = 'real_estate.otp'
    _description = 'One-Time Password'
    _order = 'create_date desc'
    _rec_name = 'phone'

    # ------------------------------------------------------------------
    # Fields
    # ------------------------------------------------------------------
    user_id = fields.Many2one(
        'res.users', string='User', index=True,
        help='Left empty for pre-registration OTPs (user does not exist yet).'
    )
    phone = fields.Char(string='Phone Number', required=True, index=True)

    code_hash = fields.Char(string='Code Hash', required=True)

    purpose = fields.Selection(
        selection=[
            ('register', 'Register'),
            ('login', 'Login'),
            ('reset_password', 'Reset Password'),
            ('change_phone', 'Change Phone'),
        ],
        string='Purpose', required=True, index=True,
    )

    attempts = fields.Integer(string='Attempts', default=0)
    max_attempts = fields.Integer(string='Max Attempts', default=5)

    expires_at = fields.Datetime(string='Expires At', required=True, index=True)
    consumed_at = fields.Datetime(string='Consumed At')

    resend_count = fields.Integer(string='Resend Count', default=0)
    last_sent_at = fields.Datetime(string='Last Sent At')

    provider = fields.Selection(
        selection=[
            ('twilio', 'Twilio Verify'),
            ('vonage', 'Vonage'),
            ('sms_misr', 'SMSMisr'),
        ],
        string='SMS Provider',
    )
    provider_message_id = fields.Char(string='Provider Message ID')

    ip_address = fields.Char(string='IP Address')

    # ------------------------------------------------------------------
    # Constraints / Indexes
    # ------------------------------------------------------------------
    _sql_constraints = [
        # Cheap DB-level guard: an index Postgres can use for the
        # "latest active OTP for phone+purpose" lookup that OTPService
        # performs on every verify() / generate_and_send() call.
    ]

    def init(self):
        # Composite index for the hot lookup path (phone, purpose, consumed_at)
        self.env.cr.execute("""
            SELECT indexname FROM pg_indexes
            WHERE indexname = 'real_estate_otp_phone_purpose_consumed_idx'
        """)
        if not self.env.cr.fetchone():
            self.env.cr.execute("""
                CREATE INDEX real_estate_otp_phone_purpose_consumed_idx
                ON real_estate_otp (phone, purpose, consumed_at)
            """)

    # ------------------------------------------------------------------
    # Helpers (pure data-layer only — orchestration lives in OTPService)
    # ------------------------------------------------------------------
    @staticmethod
    def hash_code(raw_code: str) -> str:
        """One-way hash for storage. OTPs are short-lived and low-entropy,
        so a fast hash (sha256) is acceptable here — unlike passwords,
        there is no need for bcrypt's deliberate slowness."""
        return hashlib.sha256(raw_code.encode('utf-8')).hexdigest()

    @staticmethod
    def generate_raw_code(length: int = 6) -> str:
        """Cryptographically secure numeric code, not random.randint."""
        return ''.join(secrets.choice('0123456789') for _ in range(length))

    def is_expired(self) -> bool:
        self.ensure_one()
        return bool(self.expires_at) and self.expires_at < fields.Datetime.now()

    def is_consumed(self) -> bool:
        self.ensure_one()
        return bool(self.consumed_at)

    def mark_consumed(self):
        self.ensure_one()
        self.write({'consumed_at': fields.Datetime.now()})

    def register_failed_attempt(self):
        self.ensure_one()
        self.write({'attempts': self.attempts + 1})

    @api.model
    def find_active(self, phone, purpose):
        """Latest OTP for phone+purpose that is neither consumed nor expired."""
        return self.search([
            ('phone', '=', phone),
            ('purpose', '=', purpose),
            ('consumed_at', '=', False),
            ('expires_at', '>', fields.Datetime.now()),
        ], order='create_date desc', limit=1)

    @api.model
    def find_latest(self, phone, purpose):
        """Latest OTP regardless of state — used for cooldown/rate-limit checks."""
        return self.search([
            ('phone', '=', phone),
            ('purpose', '=', purpose),
        ], order='create_date desc', limit=1)

    @api.model
    def cleanup_expired(self, older_than_days=1):
        """Cron target: purge old rows so the table stays small and the
        (phone, purpose, consumed_at) index stays cheap to scan."""
        cutoff = fields.Datetime.now() - timedelta(days=older_than_days)
        stale = self.search([('expires_at', '<', cutoff)])
        count = len(stale)
        stale.unlink()
        return count

    @api.constrains('attempts', 'max_attempts')
    def _check_attempts_bounds(self):
        for rec in self:
            if rec.attempts < 0 or rec.max_attempts <= 0:
                raise ValidationError('Invalid OTP attempt configuration.')
