from django.core.files.storage import FileSystemStorage
import gpg
import io
import logging
from django.core.files.base import ContentFile
logger = logging.getLogger(__name__)

PASSPHRASE = "changeme"


class EncryptedStorage(FileSystemStorage):
    """Encrypts files before saving to the file system and decrypts when opening from the file system

    See https://docs.djangoproject.com/en/3.1/howto/custom-file-storage/#writing-a-custom-storage-system
    """

    def _open(self, name, mode='rb'):
        unencrypted_bytes = io.BytesIO()
        unencrypted = None
        with FileSystemStorage._open(self, name, mode=mode) as encrypted:
            try:
                unencrypted, result, verify_result = gpg.Context().decrypt(encrypted, passphrase=PASSPHRASE)
            except gpg.errors.GPGMEError as e:
                unencrypted = None
                logger.error(e)
        unencrypted_bytes.write(unencrypted)
        unencrypted_bytes.seek(0)
        return unencrypted_bytes

    def _save(self, name, content):
        context = gpg.Context()
        encrypted_content, result, sign_result = context.encrypt(content.read(), passphrase=PASSPHRASE, compress=True, sign=False)
        return FileSystemStorage._save(self, name, ContentFile(encrypted_content))