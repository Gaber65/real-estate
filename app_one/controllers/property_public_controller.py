from odoo import http
from odoo.http import request
from ..helpers.exception_handler import handle_exceptions
from ..helpers.global_response import GlobalResponse
from ..utils.api_exception_handler import api_exception_handler
from ..services.property_service import PropertyService
from ..serializers.property_serializer import PropertySerializer

import math


class PropertyPublicController(http.Controller):

    @http.route(
        '/api/v1/properties/search',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False
    )
    @api_exception_handler
    @handle_exceptions
    def search_properties(self, **kwargs):
        # Params
        keyword = kwargs.get('keyword')
        tag_id = kwargs.get('tag_id')
        city = kwargs.get('city')
        try:
            min_price = float(kwargs.get('min_price')) if kwargs.get('min_price') is not None else None
            max_price = float(kwargs.get('max_price')) if kwargs.get('max_price') is not None else None
        except ValueError:
            return GlobalResponse.error(message='min_price and max_price must be numbers', status=400)

        page = int(kwargs.get('page', 1))
        limit = int(kwargs.get('limit', 10))
        sort = kwargs.get('sort', 'latest')

        page = max(page, 1)
        limit = max(min(limit, 100), 1)
        offset = (page - 1) * limit

        domain = [('active', '=', True), ('state', '!=', 'draft')]

        if keyword:
            domain += ['|', ('name', 'ilike', keyword), ('description', 'ilike', keyword)]

        if tag_id:
            try:
                tag_id_int = int(tag_id)
                domain += [('tag_ids', 'in', tag_id_int)]
            except Exception:
                return GlobalResponse.error(message='tag_id must be an integer', status=400)

        if city:
            domain += [('state', 'ilike', city)]

        if min_price is not None:
            domain += [('selling_price', '>=', min_price)]
        if max_price is not None:
            domain += [('selling_price', '<=', max_price)]

        order = 'id desc'
        if sort == 'latest':
            order = 'id desc'
        elif sort == 'oldest':
            order = 'id asc'
        elif sort == 'price_low':
            order = 'selling_price asc'
        elif sort == 'price_high':
            order = 'selling_price desc'

        total = PropertyService.count_with_domain(domain)
        props = PropertyService.search(domain=domain, limit=limit, offset=offset, order=order)

        pages = math.ceil(total / limit) if total else 0

        return GlobalResponse.success(
            message='Properties search results',
            data={
                'items': PropertySerializer.serialize_many(props),
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'pages': pages,
                    'has_next': page < pages,
                    'has_previous': page > 1,
                }
            },
            status=200
        )

    @http.route(
        '/api/v1/properties/featured',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False
    )
    @api_exception_handler
    @handle_exceptions
    def get_featured(self, **kwargs):
        page = int(kwargs.get('page', 1))
        limit = int(kwargs.get('limit', 10))
        page = max(page, 1)
        limit = max(min(limit, 100), 1)
        offset = (page - 1) * limit

        featured = PropertyService.get_featured(limit=limit, offset=offset)
        total = PropertyService.count_with_domain([('active', '=', True), ('state', '!=', 'draft'), ('is_featured', '=', True)])
        pages = math.ceil(total / limit) if total else 0

        return GlobalResponse.success(
            message='Featured properties retrieved successfully',
            data={
                'items': PropertySerializer.serialize_many(featured),
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'pages': pages,
                    'has_next': page < pages,
                    'has_previous': page > 1,
                }
            },
            status=200
        )

    @http.route(
        '/api/v1/properties/<int:property_id>/similar',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False
    )
    @api_exception_handler
    @handle_exceptions
    def get_similar(self, property_id, **kwargs):
        prop = PropertyService.get_by_id(property_id)
        if not prop:
            return GlobalResponse.error(message='Property not found', status=404)

        similar = PropertyService.similar_properties(property_id, limit=10)

        return GlobalResponse.success(
            message='Similar properties retrieved',
            data={'items': PropertySerializer.serialize_many(similar)},
            status=200
        )