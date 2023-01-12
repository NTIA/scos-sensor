#!/usr/bin/env python3


import os
import sys

import django

from utils.action_registrar import registered_actions

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")

sys.path.append(PATH)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensor.settings")
django.setup()


action_names = sorted(registered_actions.keys())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action", choices=action_names, help="Name of action to get docstring for"
    ),

    args = parser.parse_args()
    print(registered_actions[args.action].description)
