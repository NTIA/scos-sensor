from collections import OrderedDict

from scos_actions.actions.interfaces.signals import register_action

registered_actions = OrderedDict()


def add_action_handler(sender, **kwargs):
    action = kwargs["action"]
    registered_actions[action.name] = action


register_action.connect(add_action_handler)
