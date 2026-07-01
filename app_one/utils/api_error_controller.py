from odoo import http
from .global_response import GlobalResponse


class ApiErrorController(http.Controller):

    @http.route(
        '/api/<path:path>',
        auth='public',
        type='http',
        methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
        csrf=False
    )
    def api_not_found(self, path):

        return GlobalResponse.api_response(
            
                success= False,
                status= 404,
                message= 'Endpoint not found',
                errors= [
                    f'/api/${path} does not exist'
                ],
                data= None
        
        )