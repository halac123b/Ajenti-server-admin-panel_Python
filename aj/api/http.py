import jadi

class BaseHttpHandler():
    """
    Base class for everything that can process HTTP requests
    """

    def handle(self, http_context):
        """
        Should create a HTTP response in the given ``http_context`` and return
        the plain output

        :param http_context: HTTP context
        :type  http_context: :class:`aj.http.HttpContext`
        """

@jadi.interface
class HttpMiddleware(BaseHttpHandler):
    def __init__(self, context):
        self.context = context

    def handle(self, http_context):
        pass

@jadi.interface
class SocketEndpoint():
    """
    Base interface for Socket.IO endpoints.
    """

    plugin = None
    """arbitrary plugin ID for socket message routing"""

    def __init__(self, context):
        self.context = context
        self.greenlets = []
    
    