from odoo.http import request


class PropertySerializer:

    @staticmethod
    def serialize(record):
        base_url = request.httprequest.host_url.rstrip('/')

        return {
            "id": record.id,
            "sequence": record.sequence,
            "name": record.name,
            "description": record.description,

            # Location & Availability
            "postcode": record.postcode,
            "state": record.state,

            # Building
            "building": {
                "id": record.building_id.id,
                "name": record.building_id.name,
                "description": record.building_id.description,
                "code": record.building_id.code,
            } if record.building_id else None,

            # Owner
            "owner": {
                "id": record.owner_id.id,
                "name": record.owner_id.name,
                "address": record.owner_id.address,
                "phone": record.owner_id.phone,
                "image_url": (
                    f"{base_url}/web/image/owner/{record.owner_id.id}/owner_image"
                    if record.owner_id.owner_image else None
                ),
            } if record.owner_id else None,

            # Characteristics
            "bedrooms": record.bedrooms,
            "living_area": record.living_area,
            "facades": record.facades,
            "garage": record.garage,
            "garden": record.garden,
            "garden_area": record.garden_area,
            "garden_orientation": record.garden_orientation,

            # Pricing
            "selling_price": record.selling_price,

            # Photos
            "photos": [
                {
                    "id": photo.id,
                    "url": f"{base_url}/web/image/property.image/{photo.id}/image"
                }
                for photo in record.property_image_ids
            ],
        }

    @staticmethod
    def serialize_many(records):
        return [
            PropertySerializer.serialize(record)
            for record in records
        ]