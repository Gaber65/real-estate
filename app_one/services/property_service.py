from odoo.http import request


class PropertyService:

    @staticmethod
    def get_all(limit=None, offset=None):
        return request.env['property'].sudo().search(
            [],
            limit=limit,
            offset=offset,
            order='id desc'
        )

    @staticmethod
    def count():
        return request.env['property'].sudo().search_count([])

    @staticmethod
    def get_by_id(property_id):
        return (
            request.env['property']
            .sudo()
            .browse(property_id)
            .exists()
        )

    @staticmethod
    def create(data):
        return request.env['property'].sudo().create(data)

    @staticmethod
    def update(property_id, data):
        property_record = PropertyService.get_by_id(property_id)

        if not property_record:
            return None

        property_record.write(data)
        return property_record

    @staticmethod
    def delete(property_id):
        property_record = PropertyService.get_by_id(property_id)

        if not property_record:
            return False

        property_record.unlink()
        return True