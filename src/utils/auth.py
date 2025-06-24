from datetime import timedelta, datetime
import jwt
from fastapi import Cookie

class UserAuth:

    def __init__(self, private_key_path, public_key_path):
        with open(private_key_path) as f:
            key = f.read()
            self.private_key = key
        with open(public_key_path) as f:
            key = f.read()
            self.public_key = key

    def create_tokens(self, user_id: int, login: str,
                      access_layer: int, access_ttl: int = 15,
                      refresh_ttl: int = 14 * 24 * 60):
        access_token = self.create_jwt(user_id, login, access_layer, access_ttl)
        refresh_token = self.create_jwt(user_id, login, access_layer, refresh_ttl)
        return access_token, refresh_token


    def create_jwt(self, user_id: int, login: str, access_layer: int, ttl: int = 15):
        now = datetime.now()
        delta = timedelta(minutes=ttl)
        exp = now + delta
        payload = {
            'login': login,
            'id': user_id,
            'access_layer_id': access_layer,
            'exp': exp,

        }
        token = jwt.encode(payload=payload, algorithm="RS256", key=self.private_key)
        return token

    def check_access_jwt(self, access_token: str = Cookie(None)):
        try:
            if type(access_token) is str:
                decoded = jwt.decode(jwt=access_token.encode(), key=self.public_key, algorithms=['RS256'])
                if access_token != jwt.encode(payload=decoded, algorithm="RS256", key=self.private_key):
                    return None
                else:
                    return decoded
        except:
            return None

    def check_refresh_jwt(self, refresh_token: str = Cookie(None)):
        try:
            if type(refresh_token) is str:
                decoded = jwt.decode(jwt=refresh_token.encode(), key=self.public_key, algorithms=['RS256'])
                if refresh_token != jwt.encode(payload=decoded, algorithm="RS256", key=self.private_key):
                    return None
                else:
                    return decoded
        except:
            return None