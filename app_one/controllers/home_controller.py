from odoo import http
from odoo.http import request
from ..helpers.exception_handler import handle_exceptions
from ..helpers.global_response import GlobalResponse
from ..serializers.banner_serializer import BannerSerializer
from ..serializers.tag_serializer import TagSerializer
from ..serializers.property_serializer import PropertySerializer
from ..services.property_service import PropertyService


class HomeController(http.Controller):

    @http.route(
        '/api/v1/home',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False
    )
    @handle_exceptions
    def get_home(self, **kwargs):
        # Banners
        Banner = request.env['property.banner'].sudo()
        banner_domain = [('active', '=', True)]
        banners = Banner.search(banner_domain, order='sequence, id')

        # Tags
        Tag = request.env['tag'].sudo()
        tag_domain = [('active', '=', True)]
        tags = Tag.search(tag_domain, order='sequence, id')

        # Featured properties
        featured = PropertyService.get_featured(limit=10)

        # Latest properties
        latest = PropertyService.get_all(limit=10)

        return GlobalResponse.success(
            message='Home data retrieved successfully.',
            data={
                'banners': BannerSerializer.serialize_list(banners),
                'tags': TagSerializer.serialize_list(tags),
                'featured_properties': PropertySerializer.serialize_many(featured),
                'latest_properties': PropertySerializer.serialize_many(latest),
            },
            status=200
        )