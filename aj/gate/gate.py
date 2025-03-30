import hashlib
import logging
import pickle
import gevent
import gipc
import greenlet

import aj
from aj.security.totp import TOTP
from aj.util.broadcast_queue import BroadcastQueue
from aj.gate.stream import GateStreamServerEndpoint, GateStreamWorkerEndpoint
from aj.gate.worker import Worker

class WorkerGate:
    def __init__(self, session, gateway_middleware, name=None, log_tag=None, restricted=False,
                 initial_identity=None):
        self.session = session
        self.process = None
        self.stream = None
        self.stream_reader = None
        self.worker = None
        self.name = name
        self.log_tag = log_tag
        self.restricted = restricted
        self.gateway_middleware = gateway_middleware
        self.initial_identity = initial_identity
        self.q_http_replies = BroadcastQueue()
        self.q_socket_messages = BroadcastQueue()

    def start(self):
        pipe_parent, pipe_child = gipc.pipe(
            duplex=True,
            encoder=lambda x: pickle.dumps(x, 2),
        )

        self.stream = GateStreamServerEndpoint(pipe_parent)
        stream_child = GateStreamWorkerEndpoint(pipe_child)

        # Start a new process
        self.process = gipc.start_process(
            target=self._target,
            kwargs={
                'stream': stream_child,
                '_pipe': pipe_child,
            }
        )

        logging.debug(f'Started child process {self.process.pid}')
        self.stream_reader = gevent.spawn(self._stream_reader)

    def _target(self, stream=None, _pipe=None):
        self.worker = Worker(stream, self)
        self.worker.run()

    def _stream_reader(self):
        try:
            while True:
                resp = self.stream.buffer_single_response(None)
                if not resp:
                    return
                self.stream.ack_response(resp.id)
                if resp.object['type'] == 'socket':
                    self.q_socket_messages.broadcast(resp)
                if resp.object['type'] == 'http':
                    self.q_http_replies.broadcast(resp)

                if resp.object['type'] == 'terminate':
                    if self.session != self.gateway_middleware:
                        # Not the restricted session, we can disable it
                        self.session.deactivate()

                if resp.object['type'] == 'restart-master':
                    aj.restart()

                if resp.object['type'] == 'update-session-list':
                    self.gateway_middleware.broadcast_session_list()

                if resp.object['type'] == 'verify-totp':
                    self.gateway_middleware.verify_totp(
                        resp.object['userid'],
                        resp.object['code'],
                        self.session.key
                    )

                if resp.object['type'] == 'change-totp':
                    self.gateway_middleware.change_totp(
                        resp.object['data'],
                        self.session.key
                    )

                if resp.object['type'] == 'reload-config':
                    aj.config.load()
                    aj.users.load()
                    aj.config.ensure_structure()
                    self.gateway_middleware.broadcast_config_data()

                if resp.object['type'] == 'log':
                    method = {
                        'info': logging.info,
                        'warn': logging.warning,
                        'warning': logging.warning,
                        'debug': logging.debug,
                        'error': logging.error,
                        'critical': logging.critical,
                    }.get(resp.object['method'], None)
                    if method:
                        method(f"{resp.object['message']}", extra=resp.object['kwargs'])
        except greenlet.GreenletExit:
            pass

    def send_session_list(self):
        logging.debug(f'Sending a session list update to {self.name}')
        self.stream.send({
            'type': 'session-list',
            'data': {hashlib.sha3_256(key.encode()).hexdigest(): session.serialize()
                     for key, session in self.gateway_middleware.sessions.items()},
        })

    def send_config_data(self):
        logging.debug(f'Sending a config update to {self.name}')
        self.stream.send({
            'type': 'config-data',
            'data': {'config': aj.config.data, 'users': aj.users.data, 'tfa': aj.tfa_config.data}
        })

    def verify_totp(self, userid, code):
        secrets = aj.tfa_config.get_user_totp_secrets(userid)
        user = userid.split('@')[0]
        for secret in secrets:
            if TOTP(user, secret).verify(code):
                self.stream.send({
                    'type': 'verify-totp',
                    'data': {'result': True, 'userid': userid}
                })
                return
        self.stream.send({
            'type': 'verify-totp',
            'data': {'result': False, 'userid': userid}
        })

    def change_totp(self, data):
        if data['type'] == 'delete':
            aj.tfa_config.delete_user_totp({
                'userid': data['userid'],
                'timestamp': data['timestamp']
            })
        elif data['type'] == 'append':
            aj.tfa_config.append_user_totp({
                'userid': data['userid'],
                'secret_details': data['secret_details']
            })
        gevent.sleep(0.3)
        self.gateway_middleware.broadcast_config_data()