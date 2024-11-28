import locale
import gevent
import threading
import logging
import sys
import os
import subprocess
import gevent.monkey
import socketio
import importlib
import aj
import aj.log
import aj.config
import jadi

import aj.log

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

    logging.info("Loading users from /etc/ajenti/users.yml")
    aj.users = aj.config.AjentiUsers(aj.config.data['auth']['users_file'])
    aj.users.load()

    logging.info('Loading smtp config from /etc/ajenti/smtp.yml')
    aj.smtp_config = aj.config.SmtpConfig()
    aj.smtp_config.load()
    aj.smtp_config.ensure_structure()

    logging.info('Loading tfa config from /etc/ajenti/tfa.yml')
    aj.tfa_config = aj.config.TFAConfig()
    aj.tfa_config.load()
    aj.tfa_config.ensure_structure()

    if aj.debug:
        logging.warning('Debug mode')
    if aj.dev:
        logging.warning('Dev mode')
    
    # Set locale format to default
    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error:
        logging.warning('Couldn\'t set default locale')

    # Trong package gettext, _() thường sẽ tự động dịch text, nhưng ta có tool khác xử lí nên k dùng
    # Override lại hàm này để vô hiệu hoá gettext
    __builtins__['_'] = lambda x: x

    # Logging info about this Ajenti version
    logging.info(f'Ajenti Core {aj.version}')
    logging.info(f'Master PID - {os.getpid()}')
    logging.info(f'Detected platform: {aj.platform} / {aj.platform_string}')
    logging.info(f'Python version: {aj.python_version}')

    # Load plugins
    aj.plugins.PluginManager.get(aj.context).load_all_from(aj.plugin_providers)
    if len(aj.plugins.PluginManager.get(aj.context)) == 0:
        logging.warning('No plugins were loaded!')

    if aj.config.data['bind']['mode'] == 'unix':
        path = aj.config.data['bind']['socket']
        if os.path.exists(path):
            os.unlink(path)