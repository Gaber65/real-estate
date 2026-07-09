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

    # ---------------------- New search helpers ----------------------
    @staticmethod
    def search(domain=None, limit=None, offset=None, order='id desc'):
        domain = domain or []
        return request.env['property'].sudo().search(domain, limit=limit, offset=offset, order=order)

    @staticmethod
    def count_with_domain(domain=None):
        domain = domain or []
        return request.env['property'].sudo().search_count(domain)

    @staticmethod
    def get_featured(limit=None, offset=None):
        domain = [('active', '=', True), ('state', '!=', 'draft'), ('is_featured', '=', True)]
        return request.env['property'].sudo().search(domain, limit=limit, offset=offset, order='id desc')

    @staticmethod
    def similar_properties(property_id, limit=10):
        prop = PropertyService.get_by_id(property_id)
        if not prop:
            return request.env['property'].sudo().browse([])

        Property = request.env['property'].sudo()
        domain_base = [('active', '=', True), ('state', '!=', 'draft'), ('id', '!=', prop.id)]

        results = Property.search(domain_base + (('tag_ids', 'in', prop.tag_ids.ids),), limit=limit, order='id desc') if prop.tag_ids else request.env['property'].sudo().browse([])

        # Fill with same state
        if len(results) < limit and prop.state:
            needed = limit - len(results)
            same_state = Property.search(domain_base + (('state', '=', prop.state),), limit=needed)
            results = results | same_state

        # Fill with similar price (+-20%)
        if len(results) < limit and prop.selling_price:
            needed = limit - len(results)
            low = prop.selling_price * 0.8
            high = prop.selling_price * 1.2
            price_matches = Property.search(domain_base + (('selling_price', '>=', low), ('selling_price', '<=', high)), limit=needed)
            results = results | price_matches

        # Ensure unique and limit
        results = results.sorted(lambda r: r.id, reverse=True)[:limit]
        return results