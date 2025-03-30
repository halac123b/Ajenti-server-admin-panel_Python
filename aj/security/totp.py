import pyotp

class TOTP:
    def __init__(self, user, secret):
        self.user = user
        self.totp = pyotp.TOTP(secret)

    def verify(self, code):
        return self.totp.verify(code)