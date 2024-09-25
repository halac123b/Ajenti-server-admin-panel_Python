import gevent
import threading
import logging
import sys
import os
import subprocess
import socketio
import importlib
import aj
import aj.log
import jadi

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
    # Catch error, uninstall wrong package and install the right one
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

def run(config=None, plugin_providers=None, product_name='ajenti', dev_mode=False,
        debug_mode=False, autologin=False):
    """
    A global entry point for Ajenti.

    :param config: config file implementation instance to use
    :type  config: :class:`aj.config.BaseConfig`
    :param plugin_providers: list of plugin providers to load plugins from
    :type  plugin_providers: list(:class:`aj.plugins.PluginProvider`)
    :param str product_name: a product name to use
    :param bool dev_mode: enables dev mode (automatic resource recompilation)
    :param bool debug_mode: enables debug mode (verbose and extra logging)
    :param bool autologin: disables authentication and logs everyone in as the user running the panel. This is EXTREMELY INSECURE.
    """
    if config is None:
        raise TypeError('`config` can\'t be None')

    aj.product = product_name
    aj.debug = debug_mode
    aj.dev = dev_mode
    aj.dev_autologin = autologin

    aj.init()
    aj.log.set_log_params(tag='master', master_pid=os.getpid())
    aj.context = jadi.Context()
    aj.config = config
    aj.plugin_providers = plugin_providers or []
    logging.info(f'Loading config from {aj.config}')

    aj.config.load()
    aj.config.ensure_structure()