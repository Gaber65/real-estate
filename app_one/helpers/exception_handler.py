# -*- coding: utf-8 -*-
import logging
from functools import wraps

from .exceptions import (
    AppError,
    ValidationError,
    NotFoundError,
    ConflictError,
    PermissionDeniedError,
    InvalidCredentialsError,
    AccountLockedError,
    InvalidStatusTransitionError,
    OTPCooldownError,
    OTPRateLimitExceeded,
    OTPExpiredError,
    OTPInvalidError,
    OTPMaxAttemptsExceeded,
    OTPSendFailedError,
    TokenExpiredError,
    TokenRevokedError,
    TokenReuseDetectedError,
    RateLimitExceeded,
)
from .global_response import GlobalResponse
from .http_utils import json_response

_logger = logging.getLogger(__name__)

# Every AppError subclass maps to exactly one HTTP status here.
# Anything not listed falls through to 400 (AppError) or 500 (unknown).
STATUS_MAP = {
    ValidationError: 400,
    NotFoundError: 404,
    ConflictError: 409,
    PermissionDeniedError: 403,
    InvalidCredentialsError: 401,
    AccountLockedError: 423,
    InvalidStatusTransitionError: 409,
    OTPCooldownError: 429,
    OTPRateLimitExceeded: 429,
    OTPExpiredError: 400,
    OTPInvalidError: 400,
    OTPMaxAttemptsExceeded: 429,
    OTPSendFailedError: 502,
    TokenExpiredError: 401,
    TokenRevokedError: 401,
    TokenReuseDetectedError: 401,
    RateLimitExceeded: 429,
}


def resolve_status(exc: Exception) -> int:
    for exc_type, status in STATUS_MAP.items():
        if isinstance(exc, exc_type):
            return status
    return 400 if isinstance(exc, AppError) else 500


def to_response(exc: Exception) -> dict:
    status = resolve_status(exc)
    if status == 500:
        _logger.exception('Unhandled exception in request')
        return GlobalResponse.error(message='Internal server error', status=500)
    return GlobalResponse.error(message=str(exc), status=status)


def handle_exceptions(func):
    """Decorator for controller route methods — apply this once per
    route instead of repeating try/except in every controller.

    Also converts whatever the controller returns (a plain
    GlobalResponse dict) into a real HTTP Response with the matching
    status code, since these routes use type='http' rather than
    type='json' (see helpers/http_utils.py for why).
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception as exc:
            result = to_response(exc)
        return json_response(result)
    return wrapper
