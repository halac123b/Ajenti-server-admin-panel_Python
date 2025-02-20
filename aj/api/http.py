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