import gevent
import threading
import logging
import sys
import os
import subprocess

# Init Monkey-patching
gevent.monkey.patch_all(select=True, thread=True, aggressive=False, subprocess=True)

# Set module event của thread gốc thành của gevent
threading.Event = gevent.event.Event


def restart():
    logging.warning("Will restart the process now")
    if "-d" in sys.argv:
        sys.argv.remove("-d")
    os.execv(sys.argv[0], sys.argv)


try:
    # If Namespace is not provided, then the wrong socketio library is installed
    from socketio import Namespace
except ImportError:
    logging.warning("Replacing gevent-socketio with python-socketio")
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "uninstall",
            "-y",
            "gevent-socketio-hartwork",
            "python-socketio",
        ]
    )
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-socketio"])
    restart()
