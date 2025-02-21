import logging
import os
import sys
import aj
import setproctitle
import aj.log
import jadi
from aj.htttp import HttpMiddlewareAggregator
from aj.auth import AuthenticationMiddleware
from aj.routing import CentralDispatcher

class Worker():
    def __init__(self, stream, gate):
        aj.worker = self
        self.stream = stream
        self.gate = gate
        aj.master = False
        # Detach this process
        os.setpgrp()
        # Đổi tên process
        setproctitle.setproctitle(f'{sys.argv[0]} worker [{self.gate.name}]')
        aj.log.set_log_params(tag=self.gate.log_tag)
        aj.log.init_log_forwarding(self.send_log_event)

        logging.info(
            f'New worker "{self.gate.name}" PID {os.getpid()}, '
            f'EUID {os.geteuid()}, EGID {os.getegid()}'
        )

        self.context = jadi.Context(parent=aj.context)
        self.context.session = self.gate.session
        self.context.worker = self
        self.handler = HttpMiddlewareAggregator([
            AuthenticationMiddleware.get(self.context),
            CentralDispatcher.get(self.context),
        ])

    def send_log_event(self, method, message, *args, **kwargs):
        self.send_to_upstream({
            'type': 'log',
            'method': method,
            'message': message % args,
            'kwargs': kwargs,
        })

    def send_to_upstream(self, obj):
        self.stream.reply(None, obj)