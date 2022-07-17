import json
from flask import request, _request_ctx_stack, abort
from functools import wraps
from jose import jwt
from urllib.request import urlopen
from .settings import AUTH0_DOMAIN, ALGORITHMS, API_AUDIENCE

AUTH0_DOMAIN = AUTH0_DOMAIN
ALGORITHMS = ALGORITHMS
API_AUDIENCE = API_AUDIENCE

# AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# Auth Header

def get_token_auth_header():
    if "Authorization" not in request.headers:
        abort(401)

    auth_header = request.headers['Authorization']
    header_parts = auth_header.split(' ')
    if len(header_parts) != 2:
        abort(401)
    if header_parts[0].upper() != 'BEARER':
        abort(401)

    return header_parts[1]


def check_permissions(permission, payload):
    if 'permissions' not in payload:
        abort(401)
    if permission not in payload['permissions']:
        abort(403)
    return True


def verify_decode_jwt(token):
    url = urlopen('https://{}/.well-known/jwks.json'.format(AUTH0_DOMAIN))
    j_keys = json.loads(url.read())
    bad_header = jwt.get_unverified_header(token)

    rsa_key = {}
    if 'kid' not in bad_header:
        raise AuthError(
            {
                'code': 'invalid_header',
                'description': 'Malformed authorization'
            }, 401
        )
    for key in j_keys['keys']:
        if key['kid'] == bad_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }

    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer=f'https://{AUTH0_DOMAIN}/')
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthError(
                {
                    'code': 'token_expired',
                    'description': 'Expired token'
                }, 401
            )
        except jwt.JWTClaimsError:
            raise AuthError(
                {
                    'code': 'invalid_claims',
                    'description': 'incorrect claims'
                }, 401
            )
        except Exception:
            raise AuthError(
                {
                    'code': 'invalid_header',
                    'description': "can't parse authentication token"
                }, 400
            )

    raise AuthError(
        {
            'code': 'invalid_header',
            'description': "can't find appropriate key"
        }, 400
    )


def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            jwt = get_token_auth_header()
            try:
                payload = verify_decode_jwt(jwt)
            except BaseException:
                abort(401)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator
