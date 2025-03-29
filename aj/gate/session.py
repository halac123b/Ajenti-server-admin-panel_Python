import logging
import time

from aj.gate.gate import WorkerGate


class Session:
    """Holds the HTTP session data"""
    last_id = 0

    def __init__(self, key, gateway_middleware=None, client_info=None, auth_info=None, session_max_time=3600, **kwargs):
        self.id = Session.last_id
        self.key = key
        self.client_info = client_info or {}
        self.data = {}
        self.identity = kwargs.get('initial_identity', None)
        self.auth_info = auth_info
        self.touch()
        self.active = True
        logging.info(
            f"Opening a new worker gate for session {self.id}, "
            f"client {self.client_info['address']}"
        )
        self.gate = WorkerGate(
            self,
            gateway_middleware=gateway_middleware,
            name=f'session {self.id:d}',
            log_tag='worker',
            **kwargs
        )
        self.session_max_time = session_max_time
        self.gate.start()
        logging.debug(f'New session {self.id}')

    def touch(self):
        """
        Updates the "last used" timestamp
        """
        self.timestamp = time.time()

    def deactivate(self):
        """
        Marks this session as dead
        """
        self.active = False

