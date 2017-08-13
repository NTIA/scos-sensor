# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals

from os import path

from rest_framework.decorators import api_view
from rest_framework.response import Response

import actions


def get_actions():
    serialized_actions = []
    for action in actions.by_name:
        serialized_actions.append({
            'name': action,
            'summary': actions.get_summary(actions.by_name[action]),
            'description': actions.by_name[action].description
        })

    return serialized_actions


def get_capabilities():
    capabilities = {}
    fname = 'capabilities.py'
    fpath = path.join(path.dirname(__file__), fname)
    exec(compile(open(fpath, 'r').read(), fpath, 'exec'), {}, capabilities)
    return capabilities


@api_view()
def capabilities_view(request, format=None):
    capabilities = get_capabilities()
    capabilities['actions'] = get_actions()
    return Response(capabilities)
