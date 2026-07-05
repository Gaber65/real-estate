# -*- coding: utf-8 -*-
from odoo import api, fields, models
from passlib.context import CryptContext

_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)


def _truncate_bcrypt_password(password):
    """bcrypt accepts at most 72 bytes."""
    if not password:
        return password

    return password.encode("utf-8")[:72].decode("utf-8", errors="ignore")


try:
    from passlib.context import CryptContext

    _pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto', bcrypt__rounds=12)
except ImportError:
    _pwd_context = None


class ResUsersExtension(models.Model):
    """Adds the fields the JWT-based API auth flow needs, kept separate
    from Odoo's own web-login password so the two auth systems never
    collide (the API never touches `res.users.password`)."""
    _inherit = 'res.users'

    phone = fields.Char(string='Phone Number', index=True, copy=False)
    phone_verified = fields.Boolean(string='Phone Verified', default=False)

    api_password_hash = fields.Char(string='API Password Hash', copy=False)

    role_key = fields.Selection(
        selection=[
            ('super_admin', 'Super Admin'),
            ('admin', 'Admin'),
            ('agent', 'Agent'),
            ('property_owner', 'Property Owner'),
            ('customer', 'Customer'),
        ],
        string='Business Role', default='customer', index=True,
    )

    is_active_account = fields.Boolean(string='Active Account', default=True)
    last_login = fields.Datetime(string='Last Login')
    failed_login_count = fields.Integer(string='Failed Login Count', default=0)
    locked_until = fields.Datetime(string='Locked Until')

    _sql_constraints = [
        ('phone_unique', 'unique(phone)', 'This phone number is already registered.'),
    ]

    # ------------------------------------------------------------------
    # Password helpers — bcrypt via passlib, never plaintext, never
    # Odoo's default hashing (which is tuned for web-login, not a
    # standalone JWT API).
    # ------------------------------------------------------------------
    def set_api_password(self, raw_password):
        self.ensure_one()

        if _pwd_context is None:
            raise RuntimeError(
                "passlib is not installed. Run: pip install passlib bcrypt"
            )

        safe_password = _truncate_bcrypt_password(raw_password)

        self.sudo().write({
            "api_password_hash": _pwd_context.hash(safe_password)
        })

    def verify_api_password(self, raw_password):
        self.ensure_one()

        if _pwd_context is None:
            return False

        if not self.api_password_hash:
            return False

        safe_password = _truncate_bcrypt_password(raw_password)

        return _pwd_context.verify(
            safe_password,
            self.api_password_hash
        )

    def is_locked(self) -> bool:
        self.ensure_one()
        return bool(self.locked_until) and self.locked_until > fields.Datetime.now()

    def register_failed_login(self, max_attempts=5, lockout_minutes=15):
        self.ensure_one()
        from datetime import timedelta
        new_count = self.failed_login_count + 1
        vals = {'failed_login_count': new_count}
        if new_count >= max_attempts:
            vals['locked_until'] = fields.Datetime.now() + timedelta(minutes=lockout_minutes)
        self.sudo().write(vals)

    def reset_failed_logins(self):
        self.ensure_one()
        self.sudo().write({'failed_login_count': 0, 'locked_until': False, 'last_login': fields.Datetime.now()})

    @api.model
    def find_by_phone_or_email(self, identifier):
        return self.sudo().search([
            '|', ('phone', '=', identifier), ('login', '=', identifier),
        ], limit=1)
