"""
Backward-compatibility wrapper.

This file used to contain a legacy, ad-hoc AuthService implementation
that created hardcoded JWTs and stored them in `estate.auth.token`.
The project now has a unified service at
`app_one.services.auth.auth_service.AuthService` which owns the full
auth flows (OTP, login, token rotation, blacklist, etc.).

To avoid breaking any code that imports
`app_one.services.auth_service.AuthService`, we re-export the
modern implementation from the new location.
"""

from .auth.auth_service import AuthService  # re-export

