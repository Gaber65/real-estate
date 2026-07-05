# -*- coding: utf-8 -*-
import json

from odoo.http import Response


def get_json_body(request) -> dict:
    """Parses the raw request body as plain JSON. Used instead of Odoo's
    type='json' routes (which require a JSON-RPC envelope:
    {"jsonrpc": "2.0", "method": "call", "params": {...}}) — public REST
    clients (Postman, curl, mobile apps) expect to send plain JSON, so
    every controller in this module uses type='http' + this helper
    instead.
    """
    raw = request.httprequest.get_data()
    if not raw:
        return {}
    try:
        return json.loads(raw.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return {}


def json_response(payload: dict) -> Response:
    """Wraps a GlobalResponse dict into a real HTTP response with the
    matching status code and Content-Type — so an API client (or
    Postman) sees an actual 401/403/429/500, not always 200 with a
    'status' field buried in the body.
    """
    status = payload.get('status', 200)
    return Response(
        json.dumps(payload),
        status=status,
        headers=[('Content-Type', 'application/json')],
    )
