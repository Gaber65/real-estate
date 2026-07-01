{
    'name': 'Real Estate Management',
    'version': '1.0',
    'category': 'Real Estate',
    'summary': 'Real Estate Property Management System',
    'description': """
        Complete Real Estate Management System with:
        - Property Management
        - Owner Management
        - Customer Management
        - User Management with Roles
        - Authentication Tokens
        - OTP Verification
        - Role-based Access Control
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'mail', 'contacts', 'web'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/property_sequence.xml',
        'data/security_data.xml',

        # Views - NO MENUITEMS in these
        'views/property_view.xml',
        'views/property_image_view.xml',
        'views/property_line_view.xml',
        'views/owner_view.xml',
        'views/customer_view.xml',
        'views/building_view.xml',
        'views/tag_view.xml',
        'views/user_view.xml',
        'views/estate_auth_token_view.xml',
        'views/otp_verifie_view.xml',

        # Wizards
        'wizards/change_state_wizard.xml',

        # MENU MUST BE LOADED LAST
        'views/base_menu.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}