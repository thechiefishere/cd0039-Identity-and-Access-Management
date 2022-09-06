import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen
import os
from dotenv import load_dotenv

load_dotenv()

AUTH0_DOMAIN = os.getenv("DOMAIN_NAME")
ALGORITHMS = os.getenv("ALGORITHM")
API_AUDIENCE = os.getenv("AUDIENCE")

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

'''
it should attempt to get the header from the request
    it should raise an AuthError if no header is present
it should attempt to split bearer and the token
    it should raise an AuthError if the header is malformed
return the token part of the header
'''
def get_token_auth_header():
    try:
        auth_header = request.headers["Authorization"]
    except:
        raise AuthError({
                'code': 'bad_request',
                'description': 'Provide a valid token.'
            }, 400)
    # if not auth_header:
    #     raise AuthError({
    #             'code': 'invalid_token',
    #             'description': 'The provided token is invalid.'
    #         }, 401)
    if not(auth_header.startswith("Bearer ")):
        raise AuthError({
                'code': 'invalid_token',
                'description': 'The provided token is invalid.'
            }, 401)
    token = auth_header.split(" ")[1]
    
    return token

'''
@INPUTS
    permission: string permission (i.e. 'post:drink')
    payload: decoded jwt payload

it should raise an AuthError if permissions are not included in the payload
    !!NOTE check your RBAC settings in Auth0
it should raise an AuthError if the requested permission string is not in the payload permissions array
return true otherwise
'''
def check_permissions(payload, permission):
    print("am in check permissions")
    print("payload", payload)
    if 'permissions' not in payload:
        print("in first if")
        raise AuthError({
                'code': 'unauthorized',
                'description': 'You can not access this resource or page.'
            }, 403)
    if permission not in payload['permissions']:
        print("in second if")
        raise AuthError({
                'code': 'unauthorized',
                'description': 'You can not access this resource or page.'
            }, 403)
    print("am returning true")
    return True

'''
@INPUTS
    token: a json web token (string)

it should be an Auth0 token with key id (kid)
it should verify the token using Auth0 /.well-known/jwks.json
it should decode the payload from the token
it should validate the claims
return the decoded payload

!!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
'''
def verify_decode_jwt(token):
    # GET THE PUBLIC KEY FROM AUTH0
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    # print("jwks", jwks)
    
    # GET THE DATA IN THE HEADER
    unverified_header = jwt.get_unverified_header(token)
    # print("unverified header", unverified_header)
    
    # CHOOSE OUR KEY
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    
    # Finally, verify!!!
    if rsa_key:
        try:
            # USE THE KEY TO VALIDATE THE JWT
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
    raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to find the appropriate key.'
            }, 400)

'''
@INPUTS
    permission: string permission (i.e. 'post:drink')

it should use the get_token_auth_header method to get the token
it should use the verify_decode_jwt method to decode the jwt
it should use the check_permissions method validate claims and check the requested permission
return the decorator which passes the decoded payload to the decorated method
'''
def requires_auth(permission):
    def requires_auth_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            try:
                payload = verify_decode_jwt(token)
                # print("payload", payload)
            except:
                raise AuthError({
                'code': 'invalid_token',
                'description': 'The provided token is invalid.'
            }, 401)
                
            check_permissions(payload, permission)
            
            return func(*args, **kwargs)
        return wrapper
    return requires_auth_decorator