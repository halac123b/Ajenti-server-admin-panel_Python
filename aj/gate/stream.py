import json
import logging
import os
import gevent
from gevent.lock import RLock

MSG_CONTINUATION_MARKER = '\x00\x00\x00continued\x00\x00\x00'

def _seq_is_continued(part):
    '''Check signal end of gipc message'''
    return part.endswith(MSG_CONTINUATION_MARKER)

def _seq_combine(parts):
    '''Combine parts of gipc message'''
    full_object = ''
    for part in parts[:-1]:
        # Trừ đi phần signal thông báo tiếp tục
        full_object += part[len(MSG_CONTINUATION_MARKER):]
    full_object += parts[-1]    # Msg cuối k có phần đó
    return full_object

class GateStreamServerEndpoint():
    def __init__(self, pipe):
        self.pipe = pipe
        self.buffer = {}
        self.buffer_lock = RLock()
        self.log = False

    def buffer_single_response(self, timeout):
        try:
            with self.buffer_lock:
                data = self.recv_single(timeout)
                if not data:
                    return
                
    def recv_single(self, timeout):
        try:
            if timeout:
                with gevent.Timeout(timeout) as t:
                    data = self.pipe.get(t)
            else:
                data = self.pipe.get()

        except gevent.Timeout:
            return None
        except EOFError:
            return None

class GateStreamWorkerEndpoint():
    def __init__(self, pipe):
        self.pipe = pipe
        self.log = False

    def reply(self, request, obj):
        resp = GateStreamResponse(request.id if request else None, obj)
        self.pipe.put(resp.serialize())
        if self.log:
            logging.debug(f'{self}: >> {resp.id}')
    
    def recv(self):
        parts = [self.pipe.get()]
        # Liên tục nhận msg từ pipe sender đến khi gặp signal end
        while _seq_is_continued(parts[-1]):
            parts.append(self.pipe.get())
        rq = GateStreamRequest.deserialize(json.loads(_seq_combine(parts)))
        if self.log:
            logging.debug(f'{self}: << {rq.id}')
        return rq


class GateStreamResponse():
    def __init__(self, _id, obj):
        self.id = _id
        self.object = obj

    def serialize(self):
        return {
            'id': self.id,
            'object': self.object,
        }

class GateStreamRequest():
    def __init__(self, obj, endpoint):
        self.id = os.urandom(32).hex()
        self.object = obj
        self.endpoint = endpoint
    
    @classmethod
    def deserialize(cls, data):
        self = cls(data['object'], None)
        self.id = data['id']
        return self