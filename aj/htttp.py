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