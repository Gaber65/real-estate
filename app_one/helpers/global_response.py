# -*- coding: utf-8 -*-


class GlobalResponse:
    """Matches the existing unified response envelope:
    {success, message, data, status}
    """

    @staticmethod
    def success(data=None, message='Operation completed successfully', status=200):
        return {
            'success': True,
            'message': message,
            'data': data if data is not None else {},
            'status': status,
        }

    @staticmethod
    def error(message='An error occurred', status=400, data=None , errors=None):
        return {
            'success': False,
            'message': message,
            'data': data,
            'status': status,
            'errors':errors ,
        }
