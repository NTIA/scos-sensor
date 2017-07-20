"""Provides custom exception classes."""


from requests.status_codes import codes


class CommsensorError(Exception):
    def __init__(self, *args):
        super().__init__(*args)
        self.code = codes.internal_server_error


class NoSuchActionError(CommsensorError):
    def __init__(self, *args):
        super().__init__(*args)
        self.code = codes.unprocessable_entity


class ValidationError(CommsensorError):
    def __init__(self, *args, messages=None):
        super().__init__(*args)
        self.code = codes.unprocessable_entity
        self.messages = messages
