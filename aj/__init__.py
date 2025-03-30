import logging
import platform as pyplatform
import signal
import subprocess
import distro
import os

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

tfa_config = None

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

worker = None


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

    dist = distro.name()
    # Kiểm tra distribution trên các OS python k tự detect đc
    if dist == "":
        if os.path.exists("/etc/os-release"):
            release = open("/etc/os-release").read()
            if "Arch Linux" in release:
                dist = "arch"
    if dist == "":
        if os.path.exists("/etc/system-release"):
            release = open("/etc/system-release").read()
            if "Amazon Linux AMI" in release:
                dist = "centos"
    if dist == "":
        try:
            # Nếu tìm trong file vẫn k có, tức có vấn đề với OS, check file OS và log lỗi
            dist = (
                subprocess.check_output(["strings", "-4", "/etc/issue"])
                .split()[0]
                .strip()
                .decode()
            )
        except subprocess.CalledProcessError as e:
            dist = "unknown"

    # Xử lý string kết quả
    res = dist.strip(" '\"\t\n\r").lower()
    if res in base_mapping:
        res = base_mapping[res]

    res_mapped = res
    if res in platform_mapping:
        res_mapped = platform_mapping[res]
    return res, res_mapped


def detect_platform_string():
    try:
        return subprocess.check_output(["lsb_release", "-sd"]).strip().decode()
    except subprocess.CalledProcessError as e:
        return subprocess.check_output(["uname", "-mrs"]).strip().decode()
    except FileNotFoundError:
        logging.warning("Please install lsb_release to detect the platform!")
        return subprocess.check_output(["uname", "-mrs"]).strip().decode()


def init():
    import aj

    aj.version = detect_version()
    if aj.platform is None:
        aj.platform_unmapped, aj.platform = detect_platform()
    else:
        logging.warning("Platform ID was enforced by commandline!")
        aj.platform_unmapped = aj.platform

    aj.platform_string = detect_platform_string()
    aj.python_version = detect_python()


def exit():
    os.kill(os.getpid(), signal.SIGQUIT)


def restart():
    server.restart_marker = True
    server.stop()
