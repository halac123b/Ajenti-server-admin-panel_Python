import logging
import os


LOG_PARAMS = {
    'master_pid': None,
    'tag': 'master',
}

def set_log_params(**kwargs):
    LOG_PARAMS.update(kwargs)

def init_log_forwarding(fx):
    methods = ['info', 'warn', 'debug', 'error', 'critical']
    for method in methods:
        # Override lại các method của package logging
        setattr(
            logging,
            method,
            # immediately invoked lambda expression (IIFE) để tránh bị late binding
            (lambda method: lambda message, *args: fx(
                method,
                message,
                tag=LOG_PARAMS['tag'],
                pid=os.getpid(),
                *args
            ))(method)
        )