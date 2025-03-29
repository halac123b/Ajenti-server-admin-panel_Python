import hashlib
import random
import jadi

from aj.gate.gate import WorkerGate


@jadi.service
class GateMiddleware():
    def __init__(self, context):
        self.context = context
        self.sessions = {}
        self.key = self.generate_session_key({
            'REMOTE_ADDR': 'localhost',
            'HTTP_USER_AGENT': '',
            'HTTP_HOST': 'localhost',
        })
        self.restricted_gate = WorkerGate(
            self,
            gateway_middleware=self,
            restricted=True,
            name='restricted session',
            log_tag='restricted'
        )

    def generate_session_key(self, env):
        h = str(random.random())
        h += env.get('REMOTE_ADDR', '')
        h += env.get('HTTP_USER_AGENT', '')
        h += env.get('HTTP_HOST', '')
        return hashlib.sha256(h.encode('utf-8')).hexdigest()

    def broadcast_session_list(self):
        self.restricted_gate.send_session_list()
        for session in self.sessions.values():
            if not session.is_dead():
                session.gate.send_session_list()
