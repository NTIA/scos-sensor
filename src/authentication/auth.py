import logging
import jwt
from django.contrib.auth import get_user_model
from jwt import ExpiredSignatureError, InvalidSignatureError
from rest_framework import authentication
from rest_framework import exceptions
from django.conf import settings
from rest_framework.authentication import get_authorization_header

logger = logging.getLogger(__name__)

token_auth_enabled = "rest_framework.authentication.TokenAuthentication" in settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]
oauth_jwt_authentication_enabled = "authentication.auth.OAuthJWTAuthentication" in settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]

def jwt_request_has_required_role(request):
    if request.auth:
        if "authorities" in request.auth:
            if request.auth["authorities"]:
                authorities = request.auth["authorities"]
                return settings.REQUIRED_ROLE.upper() in authorities
    return False

class OAuthJWTAuthentication(authentication.BaseAuthentication):

    def authenticate(self, request):
        auth_header = get_authorization_header(request)
        if not auth_header:
            return None
        
        auth_header = auth_header.split()
        if auth_header[0].decode().lower() != "bearer":
            return None # attempt other configured authentication methods
        token = auth_header[1]

        # get JWT public key
        public_key = ""
        with open(settings.JWT_PUBLIC_KEY_FILE) as public_key_file:
            public_key = public_key_file.read()
        if not public_key:
            raise exceptions.AuthenticationFailed("Unable to get public key to decode jwt")

        try:
            # decode JWT token
            # verifies jwt signature using RS256 algorithm and public key
            # requires exp claim to verify token is not expired
            # decodes and returns base64 encoded payload
            decoded_key = jwt.decode(token, public_key, verify=True, algorithms='RS256', options={
                'require': ['exp'],
                'verify_exp': True
                })
        except ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token is expired!")
        except InvalidSignatureError:
            raise exceptions.AuthenticationFailed("Unable to verify token!")
        except:
            raise exceptions.AuthenticationFailed("Unable to decode token!")
        jwt_username = decoded_key["user_name"]
        user_model =  get_user_model()
        user = None
        try:
            user = user_model.objects.get(username=jwt_username)
        except user_model.DoesNotExist:
            user = user_model.objects.create_user(username=jwt_username)
            user.save()
        return (user, decoded_key)