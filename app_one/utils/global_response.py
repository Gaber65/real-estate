from odoo.http import request


class GlobalResponse:

    @staticmethod
    def api_response(
        success=True,
        message="Success",
        data=None,
        errors=None,
        status=200
    ):
        return request.make_json_response(
            {
                "success": success,
                "status_code": status,
                "message": message,
                "errors": errors or [],
                "data": data
            },
            status=status
        )