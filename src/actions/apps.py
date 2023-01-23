import importlib
import logging
import pkgutil

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class ActionsConfig(AppConfig):

    name = "actions"
