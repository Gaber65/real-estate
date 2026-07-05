from odoo import http
from ..helpers.global_response import GlobalResponse


class ApiErrorController(http.Controller):

    @http.route(
        '/api/<path:path>',
        auth='public',
        type='http',
        methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
        csrf=False
    )
    def api_not_found(self, path):

        return GlobalResponse.error(
            
                status= 404,
                message= 'Endpoint not found',

                data= None
        
        )