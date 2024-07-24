import subprocess
import traceback

import aj


def platform_select(**kwargs):
    """
    Selects a value from **kwargs** depending on runtime platform
    ::

        service = platform_select(
            debian='samba',
            ubuntu='smbd',
            centos='smbd',
            default='samba',
        )
    """
    if aj.platform_unmapped in kwargs:
        return kwargs[aj.platform_unmapped]
    if aj.platform in kwargs:
        return kwargs[aj.platform]
    return kwargs.get("default", None)
