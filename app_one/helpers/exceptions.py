# -*- coding: utf-8 -*-
"""Single exception hierarchy for the whole module.

Every service raises one of these (never a bare Exception, never an
Odoo UserError/ValidationError directly) so the global exception
handler can map exception type -> HTTP status -> GlobalResponse in
exactly one place. See helpers/exception_handler.py.
"""


class AppError(Exception):
    """Base class for all intentional, expected application errors."""
    default_message = 'An error occurred.'

    def __init__(self, message=None, **context):
        self.message = message or self.default_message
        self.context = context  # extra machine-readable detail if needed
        super().__init__(self.message)


class ValidationError(AppError):
    default_message = 'Invalid input.'


class NotFoundError(AppError):
    default_message = 'Resource not found.'


class ConflictError(AppError):
    default_message = 'Conflict with current state.'


class PermissionDeniedError(AppError):
    default_message = 'You do not have permission to perform this action.'


class InvalidCredentialsError(AppError):
    default_message = 'Invalid credentials.'


class AccountLockedError(AppError):
    default_message = 'Account temporarily locked due to repeated failed attempts.'


class InvalidStatusTransitionError(AppError):
    default_message = 'Invalid status transition.'


class AlreadyFavoritedError(ConflictError):
    default_message = 'Property already in favorites.'


# ---------------------------------------------------------------------
# OTP-specific
# ---------------------------------------------------------------------
class OTPError(AppError):
    default_message = 'OTP error.'


class OTPCooldownError(OTPError):
    default_message = 'Please wait before requesting another code.'

    def __init__(self, seconds_remaining, **context):
        super().__init__(
            message=f'Please wait {seconds_remaining}s before requesting another code.',
            seconds_remaining=seconds_remaining,
            **context,
        )


class OTPRateLimitExceeded(OTPError):
    default_message = 'Too many OTP requests. Please try again later.'


class OTPExpiredError(OTPError):
    default_message = 'This code has expired. Please request a new one.'


class OTPInvalidError(OTPError):
    default_message = 'Incorrect code.'


class OTPMaxAttemptsExceeded(OTPError):
    default_message = 'Too many incorrect attempts. Please request a new code.'


class OTPSendFailedError(OTPError):
    default_message = 'Failed to send verification code. Please try again.'


# ---------------------------------------------------------------------
# Token-specific
# ---------------------------------------------------------------------
class TokenError(AppError):
    default_message = 'Token error.'


class TokenExpiredError(TokenError):
    default_message = 'Session expired. Please log in again.'


class TokenRevokedError(TokenError):
    default_message = 'Session has been revoked.'


class TokenReuseDetectedError(TokenError):
    default_message = 'Security alert: token reuse detected. All sessions have been revoked.'


class RateLimitExceeded(AppError):
    default_message = 'Too many requests. Please slow down.'
