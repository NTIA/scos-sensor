from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

server_url_help = "URL of server if account belongs to a sensor manager"


class User(AbstractUser):
    """A user of the sensor."""
    email = models.EmailField(null=True)
    server_url = models.URLField(
        null=True,
        blank=True,
        verbose_name="Server URL",
        help_text=server_url_help,
    )


@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
