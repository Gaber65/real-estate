from odoo import Command


class PropertyMapper:

    @staticmethod
    def prepare_data(data):

        data = data.copy()

        if data.get('tag_ids'):
            data['tag_ids'] = [
                Command.set(data['tag_ids'])
            ]

        if data.get('property_line_ids'):
            data['property_line_ids'] = [
                Command.create(line)
                for line in data['property_line_ids']
            ]

        return data