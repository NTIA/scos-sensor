from django.test.client import Client, MULTIPART_CONTENT
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

from sensor.tests.utils import get_http_request_ssl_dn_header

cert_auth_enabled = settings.AUTHENTICATION == "CERT"

class CertificateAuthClient(Client):
    """Adds SSL DN header if certificate authentication is being used"""

    def __init__(self, enforce_csrf_checks=False, json_encoder=DjangoJSONEncoder, **defaults) -> None:
        super().__init__(enforce_csrf_checks, json_encoder=json_encoder, **defaults)
        self.username = ""

    def get_kwargs(self, extra):
        kwargs = {}
        kwargs.update(extra)
        if cert_auth_enabled:
            kwargs.update(get_http_request_ssl_dn_header(self.username))
        return kwargs

    def get(self, path, data=None, follow=False, secure=False, **extra):
        return super().get(path, data, follow, secure, **self.get_kwargs(extra))

    def post(self, path, data=None, content_type=MULTIPART_CONTENT, follow=False, secure=False, **extra):
        return super().post(path, data, content_type, follow, secure, **self.get_kwargs(extra))

    def head(self, path, data=None, follow=False, secure=False, **extra):
        pass

    def options(self, path, data='', content_type='application/octet-stream', follow=False, secure=False, **extra):
        pass

    def put(self, path, data='', content_type='application/octet-stream', follow=False, secure=False, **extra):
        return super().put(path, data, content_type, follow, secure, **self.get_kwargs(extra))

    def patch(self, path, data='', content_type='application/octet-stream', follow=False, secure=False, **extra):
        pass

    def delete(self, path, data='', content_type='application/octet-stream', follow=False, secure=False, **extra):
        return super().delete(path, data, content_type, follow, secure, **self.get_kwargs(extra))

    def trace(self, path, follow=False, secure=False, **extra):
        pass

    def login(self, **credentials):
        if cert_auth_enabled:
            assert "username" in credentials
            self.username = credentials["username"]
        else:
            super().login(**credentials)
