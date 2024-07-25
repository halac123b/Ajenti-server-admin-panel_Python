__version__ = "2.2.10"

# Global state (Các biến metadata cho 1 package Python)
product = "River Ajenti Learn"

config = None
""" Configuration dict"""

users = None
""" Users list for auth plugin """

version = None
""" Ajenti version """

platform = None
""" Current platform """

platform_unmapped = None
""" Current platform without "Ubuntu is Debian-like mapping"""

platform_string = None
""" Human-friendly platform name """

server = None
""" Web server """

debug = False
""" Debug mode """

dev = False
""" Dev mode """

context = None

edition = "vanilla"

master = True

plugin_providers = []

sessions = {}

python_version = None

# Tên của các field có thể import trong package này
__all__ = [
    "config",
    "platform",
    "platform_string",
    "platform_unmapped",
    "version",
    "server",
    "debug",
    "init",
    "exit",
    "restart",
    "python_version",
]


def detect_version():
    return __version__


def detect_python():
    return pyplatform.python_version()
