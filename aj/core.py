import gevent

gevent.monkey.patch_all(select=True, thread=True, aggressive=False, subprocess=True)
