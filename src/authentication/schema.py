from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.openapi import AutoSchema

from authentication.auth import oauth_jwt_authentication_enabled, token_auth_enabled

if token_auth_enabled:

    class KnoxTokenAuthenticationScheme(OpenApiAuthenticationExtension):
        target_class = "knox.auth.TokenAuthentication"
        name = "token"

        def get_security_definition(self, auto_schema: AutoSchema) -> dict:
            return {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": (
                    "Tokens are automatically generated for all users. You can "
                    "view yours by going to your User Details view in the "
                    "browsable API at `/api/v1/users/me` and looking for the "
                    "`auth_token` key. New user accounts do not initially "
                    "have a password and so can not log in to the browsable API. "
                    "To set a password for a user (for testing purposes), an "
                    "admin can do that in the Sensor Configuration Portal, but "
                    "only the account's token should be stored and used for "
                    "general purpose API access. "
                    'Example cURL call: `curl -kLsS -H "Authorization: Token'
                    ' 529c30e6e04b3b546f2e073e879b75fdfa147c15" '
                    "https://localhost/api/v1`"
                ),
            }


if oauth_jwt_authentication_enabled:

    class OAuth2JWTAuthenticationScheme(OpenApiAuthenticationExtension):
        target_class = "authentication.auth.OAuthJWTAuthentication"
        name = "oAuth2JWT"

        def get_security_definition(self, auto_schema: AutoSchema) -> dict:
            return {
                "type": "oauth2",
                "description": (
                    "OAuth2 authentication using resource owner password flow."
                    "This is done by verifing JWT bearer tokens signed with RS256 algorithm."
                    "The JWT_PUBLIC_KEY_FILE setting controls the public key used for signature verification."
                    "Only authorizes users who have an authority matching the REQUIRED_ROLE setting."
                    "For more information, see https://tools.ietf.org/html/rfc6749#section-4.3."
                ),
                "flows": {"password": {"scopes": {}}},  # scopes are not used
            }
