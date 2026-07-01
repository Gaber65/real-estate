from odoo.http import request


class PropertySerializer:

    @staticmethod
    def serialize(property_record):
        base_url = request.httprequest.host_url.rstrip('/')

        return {
            'id': property_record.id,
            'sequence': property_record.sequence,
            'name': property_record.name,
            'description': property_record.description,
            'postcode': property_record.postcode,
            'expected_price': property_record.expected_price,
            'selling_price': property_record.selling_price,
            'state': property_record.state,
            'owner': {
                'id': property_record.owner_id.id,
                'name': property_record.owner_id.name,
                'address': property_record.owner_id.address,
                'phone': property_record.owner_id.phone,
                'image_url': (
                    f'{base_url}/web/image/owner/{property_record.owner_id.id}/owner_image'
                    if property_record.owner_id.owner_image
                    else None
                ),
            } if property_record.owner_id else None,
        }

    @staticmethod
    def serialize_many(records):
        return [
            PropertySerializer.serialize(record)
            for record in records
        ]