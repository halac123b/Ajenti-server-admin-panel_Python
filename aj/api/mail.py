import os

import aj

DEFAULT_TEMPLATES = {
    "reset_email": os.path.dirname(__file__) + "/../static/emails/reset_email.html",
}


class Mail:
    def __init__(self):
        self.enabled = aj.config.data["email"].get("enable", False)
