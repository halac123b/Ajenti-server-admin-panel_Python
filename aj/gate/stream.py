import logging
from gevent.lock import RLock

class GateStreamServerEndpoint():
    def __init__(self, pipe):
        self.pipe = pipe
        self.buffer = {}
        self.buffer_lock = RLock()
        self.log = False

class GateStreamWorkerEndpoint():
    def __init__(self, pipe):
        self.pipe = pipe
        self.log = False

    def reply(self, request, obj):
        resp = GateStreamResponse(request.id if request else None, obj)
        self.pipe.put(resp.serialize())
        if self.log:
            logging.debug(f'{self}: >> {resp.id}')

class GateStreamResponse():
    def __init__(self, _id, obj):
        self.id = _id
        self.object = obj

    def serialize(self):
        return {
            'id': self.id,
            'object': self.object,
        }
