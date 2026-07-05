# -*- coding: utf-8 -*-
"""Service for managing customer profile completion."""

from ..helpers.exceptions import NotFoundError, ValidationError


class CustomerProfileService:
    """Handles customer profile validation and completion checks."""

    def __init__(self, env):
        self.env = env

    def get_user_profile(self, user_id):
        """Get or create the customer profile for a user."""
        profile = self.env['estate.customer'].sudo().search(
            [('user_id', '=', user_id)],
            limit=1
        )
        
        # If profile doesn't exist, create it
        if not profile:
            user = self.env['res.users'].sudo().browse(user_id)
            if not user.exists():
                raise NotFoundError(f'User {user_id} not found')
            
            # Auto-create profile for new users
            profile = self.env['estate.customer'].sudo().create({
                'user_id': user_id,
            })
        
        return profile

    def check_profile_completion(self, user_id):
        """Check if a user's profile is complete.
        
        Returns:
            dict: {
                'is_complete': bool,
                'missing_fields': list of field names,
                'profile': profile data if complete
            }
        """
        profile = self.get_user_profile(user_id)

        # Define required fields for profile completion
        required_fields = {
            'phone': 'Phone',
            'email': 'Email', 
            'address': 'Address',
            'preferred_contact': 'Preferred Contact Method',
            'min_price': 'Minimum Budget',
            'max_price': 'Maximum Budget',
        }

        missing_fields = []

        # Check each required field
        for field_name, field_label in required_fields.items():
            field_value = getattr(profile, field_name, None)
            
            # Check for empty/null values
            if not field_value or (isinstance(field_value, (int, float)) and field_value == 0):
                missing_fields.append({
                    'field': field_name,
                    'label': field_label
                })

        is_complete = len(missing_fields) == 0

        return {
            'is_complete': is_complete,
            'missing_fields': missing_fields,
            'profile_id': profile.id,
        }

    def get_profile_data(self, user_id):
        """Get complete profile data for a user."""
        profile = self.get_user_profile(user_id)

        return {
            'id': profile.id,
            'owner_id': user_id,
            'full_name': profile.full_name or '',
            'phone': profile.phone or '',
            'email': profile.email or '',
            'address': profile.address or '',
            'preferred_contact': profile.preferred_contact or '',
            'min_price': profile.min_price or 0,
            'max_price': profile.max_price or 0,
            'notes': profile.notes or '',
            'date_joined': str(profile.date_joined) if profile.date_joined else None,
        }

    def update_profile(self, user_id, data):
        """Update user profile with provided data.
        
        Args:
            user_id: The user ID
            data: Dictionary of fields to update
            
        Returns:
            Updated profile data
        """
        profile = self.get_user_profile(user_id)

        # Validate that user is updating their own profile
        if profile.user_id.id != user_id:
            raise ValidationError('You can only update your own profile.')

        # Only allow specific fields to be updated
        allowed_fields = {
            'phone', 'address', 'preferred_contact', 'notes',
            'min_price', 'max_price', 'preferred_area'
        }

        update_data = {}
        for key, value in data.items():
            if key in allowed_fields:
                update_data[key] = value

        if update_data:
            profile.write(update_data)

        return self.get_profile_data(user_id)

    def add_interested_property(self, user_id, property_id):
        """Add a property to user's interested properties.
        
        Args:
            user_id: The user ID
            property_id: The property ID to add
            
        Returns:
            Updated list of interested properties
        """
        profile = self.get_user_profile(user_id)

        # Verify property exists
        prop = self.env['property'].sudo().browse(property_id)
        if not prop.exists():
            raise NotFoundError(f'Property {property_id} not found')

        # Check if already added
        if property_id in profile.interested_property_ids.ids:
            raise ValidationError('This property is already in your interested list.')

        # Add property
        profile.write({
            'interested_property_ids': [(4, property_id)]
        })

        return self.get_interested_properties(user_id)

    def remove_interested_property(self, user_id, property_id):
        """Remove a property from user's interested properties.
        
        Args:
            user_id: The user ID
            property_id: The property ID to remove
            
        Returns:
            Updated list of interested properties
        """
        profile = self.get_user_profile(user_id)

        # Verify property exists in interested list
        if property_id not in profile.interested_property_ids.ids:
            raise NotFoundError('This property is not in your interested list.')

        # Remove property
        profile.write({
            'interested_property_ids': [(3, property_id)]
        })

        return self.get_interested_properties(user_id)

    def get_interested_properties(self, user_id):
        """Get list of user's interested properties.
        
        Returns:
            List of interested properties with details
        """
        profile = self.get_user_profile(user_id)
        
        properties = profile.interested_property_ids

        return {
            'total': len(properties),
            'properties': [
                {
                    'id': prop.id,
                    'name': prop.name,
                    'description': prop.description,
                    'postcode': prop.postcode,
                    'expected_price': prop.expected_price,
                    'bedrooms': prop.bedrooms,
                    'living_area': prop.living_area,
                    'garage': prop.garage,
                    'garden': prop.garden,
                }
                for prop in properties
            ]
        }
