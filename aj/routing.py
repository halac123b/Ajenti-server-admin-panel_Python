import jadi
from aj.api.http import BaseHttpHandler

@jadi.service
class CentralDispatcher(BaseHttpHandler):
    def __init__(self, context):
        self.context = context
        self.invalid = InvalidRouteHandler(context)
        self.denied = DeniedRouteHandler(context)

class InvalidRouteHandler(BaseHttpHandler):
    def __init__(self, context):
        pass

class DeniedRouteHandler(BaseHttpHandler):
    """If client authentication is forced, and the client certificate is not valid."""
    def __init__(self, context):
        pass