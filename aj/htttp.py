import base64
import pickle
from aj.api.http import BaseHttpHandler

class HttpMiddlewareAggregator(BaseHttpHandler):
    """
    Stacks multiple HTTP handlers together in a middleware fashion.

    :param stack: handler list
    :type  stack: list(:class:`aj.api.http.BaseHttpHandler`)
    """
    def __init__(self, stack):
        self.stack = stack
    
    def handle(self, http_context):
        for middleware in self.stack:
            output = middleware.handle(http_context)
            if output is not None:
                return output

class HttpContext():
    """
    Instance of :class:`HttpContext` is passed to all HTTP handler methods

    .. attribute:: env

        WSGI environment dict

    .. attribute:: path

        Path segment of the URL

    .. attribute:: method

        Request method

    .. attribute:: headers

        List of HTTP response headers

    .. attribute:: body

        Request body

    .. attribute:: response_ready

        Indicates whether a HTTP response has already been submitted in this context

    .. attribute:: query

        HTTP query parameters
    """
    def __init__(self, env, start_response=None):
        self.start_response = start_response
        self.env = env
        self.path = env['PATH_INFO']
        self.headers = []
        self.response_ready = False
        self.status = None
        self.body = None
        self.query = None
        self.form_cgi_query = None
        self.url_cgi_query = None
        self.prefix = None
        self.method = self.env['REQUEST_METHOD'].upper()
    
    @classmethod
    def deserialize(cls, data):
        data = pickle.loads(base64.b64decode(data))
        self = cls(data['env'])
        self.path = data['path']
        self.headers = data['headers']
        self.body = base64.b64decode(data['body']) if data['body'] else None
        self.query = data['query']
        self.prefix = data['prefix']
        self.method = data['method']
        return self
    
    def add_header(self, key, value):
        """
        Adds a given HTTP header to the response

        :param key: header name
        :type  key: str
        :param value: header value
        :type  value: str
        """
        self.headers += [(key, value)]