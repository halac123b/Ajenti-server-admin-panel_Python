import jadi

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
        
