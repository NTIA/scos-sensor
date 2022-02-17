from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def get_test_public_private_key():
    """Creates public/private key pair for testing
    https://stackoverflow.com/a/39126754
    """
    key = rsa.generate_private_key(
        backend=default_backend(), public_exponent=65537, key_size=4096
    )
    private_key = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_key = key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return private_key, public_key
