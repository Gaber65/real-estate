import jwt

from datetime import datetime, timedelta


SECRET_KEY = "CHANGE_ME_SECRET_KEY"


class JwtHelper:

    @staticmethod
    def generate_access_token(user_id):

        payload = {
            "user_id": user_id,
            "type": "access",
            "exp": datetime.utcnow() + timedelta(days=1)
        }

        return jwt.encode(
            payload,
            SECRET_KEY,
            algorithm="HS256"
        )

    @staticmethod
    def generate_refresh_token(user_id):

        payload = {
            "user_id": user_id,
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=30)
        }

        return jwt.encode(
            payload,
            SECRET_KEY,
            algorithm="HS256"
        )

    @staticmethod
    def decode(token):

        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )