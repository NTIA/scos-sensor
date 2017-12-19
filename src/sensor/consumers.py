from channels import Group
from channels.auth import channel_session_user, channel_session_user_from_http
from channels.security.websockets import allowed_hosts_only


@allowed_hosts_only
@channel_session_user_from_http
def ws_add(message):
    """Connected to websocket.connect."""
    if message.user.is_authenticated:
        # Accept the incoming connection
        message.reply_channel.send({'accept': True})
        # Add them to the logs group
        Group('logs').add(message.reply_channel)
    else:
        # Deny the incoming connection
        message.reply_channel.send({'accept': False})


@channel_session_user
def ws_message(message):
    """Connected to websocket.receive."""
    pass


@channel_session_user
def ws_disconnect(message):
    """Connected to websocket.disconnect."""
    Group('logs').discard(message.reply_channel)
