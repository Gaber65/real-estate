from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request
from ..serializers.property_serializer import PropertySerializer
from ..helpers.exception_handler import handle_exceptions
from ..helpers.global_response import GlobalResponse

from ..serializers.tag_serializer import TagSerializer
from ..helpers.auth_guard import require_auth


class TagController(http.Controller):
    @http.route(
        '/api/v1/tags',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False
    )
    @handle_exceptions
    @require_auth
    def get_tags(self, **kwargs):
        page = int(kwargs.get('page', 1))
        limit = int(kwargs.get('limit', 20))
        page = max(page, 1)
        limit = max(min(limit, 100), 1)

        Tag = request.env['tag'].sudo()
        domain = [('active', '=', True)]
        total = Tag.search_count(domain)
        tags = Tag.search(domain, offset=(page - 1) * limit, limit=limit, order='sequence, id')
        data = TagSerializer.serialize_list(tags)
        pages = (total + limit - 1) // limit if total else 0
        return GlobalResponse.success(
            data={
                'items': data,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'pages': pages,
                    'has_next': page < pages,
                    'has_previous': page > 1,
                }
            },
            message='Tags retrieved successfully.',
            status=200
        )

    @http.route(
        '/api/v1/tags/<int:tag_id>/properties',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False
    )
    @handle_exceptions
    @require_auth
    def get_tag_properties(self, tag_id, **kwargs):
        page = int(kwargs.get('page', 1))
        limit = int(kwargs.get('limit', 10))
        sort = kwargs.get('sort', 'latest')

        page = max(page, 1)
        limit = max(min(limit, 100), 1)

        Tag = request.env['tag'].sudo()
        tag = Tag.browse(tag_id)
        if not tag.exists() or not tag.active:
            return GlobalResponse.error(message='Tag not found', status=404)

        # Build domain for properties
        domain = [('tag_ids', 'in', tag.id), ('active', '=', True), ('state', '!=', 'draft')]

        order = 'id desc'
        if sort == 'latest':
            order = 'id desc'
        elif sort == 'oldest':
            order = 'id asc'
        elif sort == 'price_low':
            order = 'selling_price asc'
        elif sort == 'price_high':
            order = 'selling_price desc'

        Property = request.env['property'].sudo()
        total = Property.search_count(domain)
        offset = (page - 1) * limit
        properties = Property.search(domain, offset=offset, limit=limit, order=order)

        items = [PropertySerializer.serialize(p) for p in properties]
        pages = (total + limit - 1) // limit if total else 0

        return GlobalResponse.success(
            data={
                'items': items,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'pages': pages,
                    'has_next': page < pages,
                    'has_previous': page > 1,
                }
            },
            message='Properties retrieved for tag.',
            status=200
        )
