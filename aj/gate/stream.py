import json
import logging
import os
import gevent
from gevent.lock import RLock

MSG_CONTINUATION_MARKER = '\x00\x00\x00continued\x00\x00\x00'
MSG_SIZE_LIMIT = 1024 * 1024 * 128  # 128 MB

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

def _seq_split(to_split):
    while to_split:
        yield to_split[:MSG_SIZE_LIMIT] + (MSG_CONTINUATION_MARKER if len(to_split) > MSG_SIZE_LIMIT else '')
        to_split = to_split[MSG_SIZE_LIMIT:]

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
                # Đọc data sau đó convert sang Response obj
                resp = GateStreamResponse.deserialize(data)
                if self.log:
                    logging.debug(f'{self}: << {resp.id}')
                    # Lưu response vào buffer
                    self.buffer[resp.id] = resp
                    return resp
        except IOError:
            return None
                
    def recv_single(self, timeout):
        """Đọc data từ pipe sender"""
        try:
            if timeout:
                with gevent.Timeout(timeout) as t:
                    data = self.pipe.get(t)
            else:
                data = self.pipe.get()
            return data

        except gevent.Timeout:
            return None
        except EOFError:
            return None

    def ack_response(self, _id):
        """Xử lí xog request trong buffer thì xoá trong buffer"""
        with self.buffer_lock:
            return self.buffer.pop(_id)

    def send(self, obj):
        rq = GateStreamRequest(obj, self)
        if not self.pipe._reader._closed:
            for part in _seq_split(json.dumps(rq.serialize())):
                self.pipe.put(part)
        if self.log:
            logging.debug(f'{self}: >> {rq.id}')
        return rq

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

    @classmethod
    def deserialize(cls, data):
        self = cls(data['object'], None)
        self.id = data['id']
        return self

class GateStreamRequest:
    def __init__(self, obj, endpoint):
        self.id = os.urandom(32).hex()
        self.object = obj
        self.endpoint = endpoint

    @classmethod
    def deserialize(cls, data):
        self = cls(data['object'], None)
        self.id = data['id']
        return self

    def serialize(self):
        object_tmp = {k: (v.decode() if isinstance(v, bytes) else v) for k, v in self.object.items()}
        return {
            'id': self.id,
            'object': object_tmp,
        }