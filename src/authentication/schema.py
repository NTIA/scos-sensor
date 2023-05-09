from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.openapi import AutoSchema


class KnoxTokenAuthenticationSchema(OpenApiAuthenticationExtension):
    target_class = "knox.auth.TokenAuthentication"
    name = "knoxTokenAuth"

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
