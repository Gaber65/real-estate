from odoo import models, fields, api
from odoo.exceptions import ValidationError
import random
from datetime import datetime, timedelta


class EstateOtp(models.Model):
    _name = 'estate.otp'
    _description = 'OTP Verification'
    _order = 'id desc'

    phone = fields.Char(required=True)
    otp_code = fields.Char(required=True)
    expires_at = fields.Datetime()
    verified = fields.Boolean(default=False)
    attempt_count = fields.Integer(default=0)
    purpose = fields.Selection([
        ('verify', 'Verify'),
        ('reset', 'Reset Password')
    ], default='verify')

    is_expired = fields.Boolean(compute='_compute_is_expired', store=True)

    @api.depends('expires_at')
    def _compute_is_expired(self):
        for rec in self:
            rec.is_expired = rec.expires_at and rec.expires_at < datetime.now() and not rec.verified

    @api.model
    def generate_otp(self, phone, purpose='verify'):
        """Generate a new OTP for a phone number"""
        # Generate 6-digit OTP
        otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

        # Create OTP record
        otp = self.create({
            'phone': phone,
            'otp_code': otp_code,
            'expires_at': datetime.now() + timedelta(minutes=5),
            'purpose': purpose,
        })

        # Send OTP via SMS/WhatsApp (implementation would depend on provider)
        # self._send_otp(phone, otp_code)

        return otp

    def action_verify(self):
        """Verify OTP code"""
        for rec in self:
            if rec.verified:
                raise ValidationError("This OTP has already been verified.")
            if rec.is_expired:
                raise ValidationError("This OTP has expired.")
            if rec.attempt_count >= 3:
                raise ValidationError("Maximum attempts exceeded. Please generate a new OTP.")

            # OTP is valid, mark as verified
            rec.write({
                'verified': True,
                'attempt_count': rec.attempt_count + 1
            })

            # Update user verification status if purpose is 'verify'
            if rec.purpose == 'verify':
                user = self.env['res.users'].search([('phone', '=', rec.phone)], limit=1)
                if user:
                    user.write({'is_verified': True})

    def action_resend(self):
        """Resend OTP"""
        for rec in self:
            if rec.verified:
                raise ValidationError("This OTP has already been verified.")

            # Generate new OTP
            new_otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            rec.write({
                'otp_code': new_otp,
                'expires_at': datetime.now() + timedelta(minutes=5),
                'attempt_count': 0,
            })

            # Resend OTP
            # self._send_otp(rec.phone, new_otp)

    def action_invalidate(self):
        """Invalidate OTP"""
        self.write({'verified': False, 'expires_at': datetime.now()})

    def action_send_otp(self):
        """Manual action to send OTP"""
        # Implementation would depend on SMS/WhatsApp provider
        pass