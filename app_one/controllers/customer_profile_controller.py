# -*- coding: utf-8 -*-
from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request

from ..helpers.exception_handler import handle_exceptions
from ..helpers.global_response import GlobalResponse
from ..helpers.auth_guard import require_auth
from ..helpers.http_utils import get_json_body
from ..services.customer_profile_service import CustomerProfileService


class CustomerProfileController(http.Controller):
    """API endpoints for customer profile management.
    
    Supports:
    - Viewing profile and checking completion status
    - Updating profile information
    - Warning when profile is incomplete before adding customers
    """

    @http.route(
        '/api/customer/profile',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False
    )
    @handle_exceptions
    @require_auth
    def get_profile(self, **kwargs):
        """Get user's customer profile and check completion status.
        
        Returns warning if profile is incomplete with list of missing fields.
        Auto-creates profile if it doesn't exist.
        """
        user_id = request.jwt_user_id
        service = CustomerProfileService(request.env)
        
        # Get or create profile
        profile = service.get_user_profile(user_id)
        
        # Check profile completion
        completion_check = service.check_profile_completion(user_id)
        profile_data = service.get_profile_data(user_id)

        # If profile is incomplete, return warning with missing fields
        if not completion_check['is_complete']:
            missing_count = len(completion_check['missing_fields'])
            return GlobalResponse.success(
                data={
                    'profile': profile_data,
                    'completion_status': completion_check,
                    'warning': f'Your profile is incomplete. Please complete {missing_count} required field(s) to add customers.',
                },
                message='Profile retrieved. Incomplete fields detected.',
                status=200
            )

        # Profile is complete
        return GlobalResponse.success(
            data={
                'profile': profile_data,
                'completion_status': completion_check,
            },
            message='Profile retrieved. Profile is complete. You can now add customers.',
            status=200
        )

    @http.route(
        '/api/customer/profile',
        type='http',
        auth='public',
        methods=['PUT'],
        csrf=False
    )
    @handle_exceptions
    @require_auth
    def update_profile(self, **kwargs):
        """Update user's customer profile.
        
        Allowed fields: phone, address, preferred_contact, notes,
                       min_price, max_price, preferred_area
        """
        user_id = request.jwt_user_id
        payload = get_json_body(request)
        
        service = CustomerProfileService(request.env)
        updated_profile = service.update_profile(user_id, payload)

        # Check if profile is now complete
        completion_check = service.check_profile_completion(user_id)

        if completion_check['is_complete']:
            message = 'Profile updated successfully. Profile is now complete!'
        else:
            message = f"Profile updated. {len(completion_check['missing_fields'])} fields still need to be completed."

        return GlobalResponse.success(
            data={
                'profile': updated_profile,
                'completion_status': completion_check,
            },
            message=message,
            status=200
        )

    @http.route(
        '/api/customer/profile/completion-check',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False
    )
    @handle_exceptions
    @require_auth
    def check_profile_completion(self, **kwargs):
        """Check if user's profile is complete.
        
        Useful before allowing customer creation operations.
        
        Returns:
            {
                'is_complete': bool,
                'missing_fields': [ { 'field': '', 'label': '' }, ... ]
            }
        """
        user_id = request.jwt_user_id
        service = CustomerProfileService(request.env)
        completion_check = service.check_profile_completion(user_id)

        if completion_check['is_complete']:
            message = 'Profile is complete. You can proceed to add customers.'
            status = 200
        else:
            message = f"Profile is incomplete. {len(completion_check['missing_fields'])} field(s) need to be completed."
            status = 200

        return GlobalResponse.success(
            data=completion_check,
            message=message,
            status=status
        )

    # ========================================================================
    # Interested Properties Endpoints
    # ========================================================================

    @http.route(
        '/api/customer/interested-properties',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False
    )
    @handle_exceptions
    @require_auth
    def get_interested_properties(self, **kwargs):
        """Get list of user's interested properties."""
        user_id = request.jwt_user_id
        service = CustomerProfileService(request.env)
        
        interested_props = service.get_interested_properties(user_id)

        return GlobalResponse.success(
            data=interested_props,
            message=f"Found {interested_props['total']} interested properties.",
            status=200
        )

    @http.route(
        '/api/customer/interested-properties/add',
        type='http',
        auth='public',
        methods=['POST'],
        csrf=False
    )
    @handle_exceptions
    @require_auth
    def add_interested_property(self, **kwargs):
        """Add a property to user's interested properties.
        
        Request body:
            {
                "property_id": 123
            }
        """
        user_id = request.jwt_user_id
        payload = get_json_body(request)
        property_id = payload.get('property_id')

        if not property_id:
            raise ValidationError('property_id is required.')

        service = CustomerProfileService(request.env)
        interested_props = service.add_interested_property(user_id, property_id)

        return GlobalResponse.success(
            data=interested_props,
            message='Property added to interested properties.',
            status=201
        )

    @http.route(
        '/api/customer/interested-properties/remove',
        type='http',
        auth='public',
        methods=['POST'],
        csrf=False
    )
    @handle_exceptions
    @require_auth
    def remove_interested_property(self, **kwargs):
        """Remove a property from user's interested properties.
        
        Request body:
            {
                "property_id": 123
            }
        """
        user_id = request.jwt_user_id
        payload = get_json_body(request)
        property_id = payload.get('property_id')

        if not property_id:
            raise ValidationError('property_id is required.')

        service = CustomerProfileService(request.env)
        interested_props = service.remove_interested_property(user_id, property_id)

        return GlobalResponse.success(
            data=interested_props,
            message='Property removed from interested properties.',
            status=200
        )
