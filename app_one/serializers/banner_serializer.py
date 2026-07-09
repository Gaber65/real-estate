from odoo.http import request


class BannerSerializer:
    @staticmethod
    def serialize(banner):
        base_url = request.httprequest.host_url.rstrip('/')
        return {
            'id': banner.id,
            'name': banner.name,
            'sequence': banner.sequence,
            'active': banner.active,
            'start_date': str(banner.start_date) if banner.start_date else None,
            'end_date': str(banner.end_date) if banner.end_date else None,
            'image_url': f"{base_url}/web/image/property.banner/{banner.id}/image" if banner.image else None,
            'property': {
                'id': banner.property_id.id,
                'name': banner.property_id.name,
            } if banner.property_id else None,
            'tag': {
                'id': banner.tag_id.id,
                'name': banner.tag_id.name,
            } if banner.tag_id else None,
            'action_type': banner.action_type,
            'external_url': banner.external_url,
        }

    @staticmethod
    def serialize_list(banners):
        return [BannerSerializer.serialize(b) for b in banners]