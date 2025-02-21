import logging
import aj.util
import jadi
from aj.api.http import BaseHttpHandler

@aj.util.public
@jadi.service
class AuthenticationMiddleware(BaseHttpHandler):
    def __init__(self, context):
        self.context = context
        self.auth = AuthenticationService.get(self.context)
        if not hasattr(context, 'identity'):
            context.identity = None

@aj.util.public
@jadi.service
class AuthenticationService():
    def __init__(self, context):
        self.context = context

    def handle(self, http_context):
        if http_context.env['SSL_CLIENT_VALID']:
            if not self.context.identity:
                username = http_context.env['SSL_CLIENT_USER']
                logging.info(
                    f'SSL client certificate {http_context.env["SSL_CLIENT_DIGEST"]}'
                    f' verified as {username}'
                )