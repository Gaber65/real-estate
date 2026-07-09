from odoo import http
from odoo.http import request
from .property_serializer import PropertySerializer

class TagSerializer:
    @staticmethod
    def serialize(tag):
        base_url = request.httprequest.host_url.rstrip('/')
        return {
            'id': tag.id,
            'name': tag.name,
            'sequence': tag.sequence,
            'active': tag.active,
            'image_url': f"{base_url}/web/image/tag/{tag.id}/image" if tag.image else None,
            # Keep properties minimal to avoid heavy payloads in list endpoints
            'properties': [PropertySerializer.serialize(prop) for prop in tag.property_ids],
        }

    @staticmethod
    def serialize_list(tags):
        return [TagSerializer.serialize(tag) for tag in tags]
