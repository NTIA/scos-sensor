from django.conf import settings
from django.test import Client
from django.test.client import MULTIPART_CONTENT

UID = "test_uid"


class SCOSTestClient(Client):
    def get(self, path, data=None, follow=False, secure=False, **extra):
        if settings.AUTHENTICATION == "OAUTH":
            extra[
                "HTTP_X_SSL_CLIENT_DN"
            ] = f"UID={UID},CN=Test,OU=Test,O=Test,L=Test,ST=Test,C=Test"
        return super().get(path, data, follow, secure, **extra)

    def post(
        self,
        path,
        data=None,
        content_type=MULTIPART_CONTENT,
        follow=False,
        secure=False,
        **extra,
    ):
        if settings.AUTHENTICATION == "OAUTH":
            extra[
                "HTTP_X_SSL_CLIENT_DN"
            ] = f"UID={UID},CN=Test,OU=Test,O=Test,L=Test,ST=Test,C=Test"
        return super().post(path, data, content_type, follow, secure, **extra)

    def delete(
        self,
        path,
        data="",
        content_type="application/octet-stream",
        follow=False,
        secure=False,
        **extra,
    ):
        if settings.AUTHENTICATION == "OAUTH":
            extra[
                "HTTP_X_SSL_CLIENT_DN"
            ] = f"UID={UID},CN=Test,OU=Test,O=Test,L=Test,ST=Test,C=Test"
        return super().delete(path, data, content_type, follow, secure, **extra)

    def put(
        self,
        path,
        data="",
        content_type="application/octet-stream",
        follow=False,
        secure=False,
        **extra,
    ):
        if settings.AUTHENTICATION == "OAUTH":
            extra[
                "HTTP_X_SSL_CLIENT_DN"
            ] = f"UID={UID},CN=Test,OU=Test,O=Test,L=Test,ST=Test,C=Test"
        return super().put(path, data, content_type, follow, secure, **extra)

    def patch(
        self,
        path,
        data="",
        content_type="application/octet-stream",
        follow=False,
        secure=False,
        **extra,
    ):
        if settings.AUTHENTICATION == "OAUTH":
            extra[
                "HTTP_X_SSL_CLIENT_DN"
            ] = f"UID={UID},CN=Test,OU=Test,O=Test,L=Test,ST=Test,C=Test"
        return super().patch(path, data, content_type, follow, secure, **extra)
