import logging
import syslog
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
    
    def handle(self, http_context):
        if http_context.env['SSL_CLIENT_VALID']:
            if not self.context.identity:
                username = http_context.env['SSL_CLIENT_USER']
                logging.info(
                    f'SSL client certificate {http_context.env["SSL_CLIENT_DIGEST"]}'
                    f' verified as {username}'
                )

@aj.util.public
@jadi.service
class AuthenticationService():
    def __init__(self, context):
        self.context = context

    def login(self, username, demote=True):
        logging.info(f'Authenticating session as {username}')

        syslog.openlog(facility=syslog.LOG_AUTH)
        syslog.syslog(
            syslog.LOG_NOTICE,
            f'{username} has logged in from {self.context.session.client_info["address"]}'
        )

        # Allow worker to perform operations as root before demoting
        self.get_provider().prepare_environment(username)

        if demote:
            uid = self.get_provider().get_isolation_uid(username)
            gid = self.get_provider().get_isolation_gid(username)
            logging.debug(
                f'Authentication provider "{self.get_provider().name}" maps "{username}" -> {uid:d}'
            )
            self.context.worker.demote(uid, gid)
        self.context.identity = username

    def get_provider(self):
        provider_id = aj.config.data['auth'].get('provider', 'os')
        for provider in AuthenticationProvider.all(self.context):
            if provider.id == provider_id:
                return provider
        raise AuthenticationError(f'Authentication provider {provider_id} is unavailable')

@jadi.interface
class AuthenticationProvider():
    id = None
    name = None
    allows_sudo_elevation = False

    def __init__(self, context):
        self.context = context
    
    def get_isolation_uid(self, username):
        raise NotImplementedError
    
    def get_isolation_gid(self, username):
        return None

class AuthenticationError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message