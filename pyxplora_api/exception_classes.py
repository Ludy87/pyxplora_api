from __future__ import annotations


class Error(Exception):
    pass


class LoginError(Error):
    def __init__(self, message, res=1):
        self.message = message
        self.res = res
        super().__init__(self.message, self.res)

    def __str__(self):
        return f'{self.message} - {self.res}'
