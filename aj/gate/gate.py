import hashlib
import logging
import pickle
import gevent
import gipc

import aj
from aj.util.broadcast_queue import BroadcastQueue
from aj.gate.stream import GateStreamServerEndpoint, GateStreamWorkerEndpoint
from aj.gate.worker import Worker

class WorkerGate():
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

                if resp.object['type'] == 'update-sessionlist':
                    self.gateway_middleware.broadcast_session_list()

    def send_session_list(self):
        logging.debug(f'Sending a session list update to {self.name}')
        self.stream.send({
            'type': 'session-list',
            'data': {hashlib.sha3_256(key.encode()).hexdigest(): session.serialize()
                     for key, session in self.gateway_middleware.sessions.items()},
        })
                