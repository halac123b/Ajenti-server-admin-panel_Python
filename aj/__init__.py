import platform as pyplatform

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
    """Version of package"""
    return __version__


def detect_python():
    """Version of Python"""
    return pyplatform.python_version()


def detect_platform():
    """Platform đang chạy package"""
    base_mapping = {
        "gentoo base system": "gentoo",
        "centos linux": "centos",
        "mandriva linux": "mandriva",
        "elementary os": "ubuntu",
        "trisquel": "ubuntu",
        "linaro": "ubuntu",
        "linuxmint": "ubuntu",
        "amazon": "ubuntu",
        "redhat enterprise linux": "rhel",
        "red hat enterprise linux server": "rhel",
        "oracle linux server": "rhel",
        "fedora": "rhel",
        "olpc": "rhel",
        "xo-system": "rhel",
        "kali linux": "debian",
    }

    platform_mapping = {
        "ubuntu": "debian",
        "rhel": "centos",
    }

    # MacOS
    if hasattr(pyplatform, "mac_ver") and pyplatform.mac_ver()[0] != "":
        return "osx", "osx"

    # Nếu không phải Linux, return luôn
    if pyplatform.system() != "Linux":
        res = pyplatform.system().lower()
        return res, res

    dist = ""
    (major, minor, _) = pyplatform.python_version_tuple()
    major = int(major)
    minor = int(minor)
    if (major * 10 + minor) >= 36:
        import distro

        dist = distro.id()
