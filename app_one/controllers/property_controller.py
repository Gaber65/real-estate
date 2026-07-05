from odoo.fields import Date

from odoo import http
from odoo.http import request
from ..helpers.auth_guard import require_auth
from ..helpers.exception_handler import handle_exceptions
from ..helpers.global_response import GlobalResponse

from ..utils.api_exception_handler import api_exception_handler

from ..services.property_service import PropertyService
from ..serializers.property_serializer import PropertySerializer
from ..mappers.property_mapper import PropertyMapper

import json
import math


class PropertyController(http.Controller):

    @http.route(
        ['/api/properties', '/api/properties/<int:property_id>'],
        methods=['GET'],
        type='http',
        auth='public',
        csrf=False
    )
    @api_exception_handler
    @handle_exceptions
    @require_auth
    def get_properties(self, property_id=None, **kwargs):

        # GET BY ID
        if property_id:

            property_record = PropertyService.get_by_id(
                property_id
            )

            if not property_record:
                return GlobalResponse.error(
                    message='Property not found',
                    status=404
                )

            return GlobalResponse.success(
                message='Property retrieved successfully',
                data=PropertySerializer.serialize(
                    property_record
                ),
                status=200
            )

        # GET ALL WITH PAGINATION
        page = int(kwargs.get('page', 1))
        limit = int(kwargs.get('limit', 10))

        page = max(page, 1)
        limit = max(min(limit, 100), 1)

        offset = (page - 1) * limit

        properties = PropertyService.get_all(
            limit=limit,
            offset=offset
        )

        total = PropertyService.count()

        pages = math.ceil(total / limit) if total else 0

        properties = properties.filtered(
            lambda p: p.state in ("closed", "sold")
        )

        return GlobalResponse.success(
            message='Properties retrieved successfully',
            data={
                'items': PropertySerializer.serialize_many(
                    properties
                ),
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
        '/api/properties',
        methods=['POST'],
        type='http',
        auth='public',
        csrf=False
    )
    @api_exception_handler
    def create_property(self):

        data = json.loads(
            request.httprequest.data.decode('utf-8')
        )

        data = PropertyMapper.prepare_data(data)

        property_record = PropertyService.create(data)

        return GlobalResponse.success(
            message='Property created successfully',
            data=PropertySerializer.serialize(
                property_record
            ),
            status=201
        )

    @http.route(
        '/api/properties/<int:property_id>',
        methods=['PUT'],
        type='http',
        auth='public',
        csrf=False
    )
    @api_exception_handler
    def update_property(self, property_id):

        data = json.loads(
            request.httprequest.data.decode('utf-8')
        )

        data = PropertyMapper.prepare_data(data)

        property_record = PropertyService.update(
            property_id,
            data
        )

        if not property_record:
            return GlobalResponse.error(
                message='Property not found',
                status=404
            )

        return GlobalResponse.success(
            message='Property updated successfully',
            data=PropertySerializer.serialize(
                property_record
            ),
            status=200
        )

    @http.route(
        '/api/properties/<int:property_id>',
        methods=['DELETE'],
        type='http',
        auth='public',
        csrf=False
    )
    @api_exception_handler
    def delete_property(self, property_id):

        deleted = PropertyService.delete(
            property_id
        )

        if not deleted:
            return GlobalResponse.error(
                message='Property not found',
                status=404
            )

        return GlobalResponse.success(
            message='Property deleted successfully',
            status=200
        )
