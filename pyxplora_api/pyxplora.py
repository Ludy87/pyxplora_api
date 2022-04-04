from __future__ import annotations

from time import time


class PyXplora:
    def __init__(self, countrycode: str, phoneNumber: str, password: str, userLang: str, timeZone: str, childPhoneNumber=[]) -> None:
        self._countrycode = countrycode
        self._phoneNumber = phoneNumber
        self._password = password
        self._userLang = userLang
        self._timeZone = timeZone

        self._childPhoneNumber = childPhoneNumber

        self.tokenExpiresAfter = 240
        self.maxRetries = 3
        self.retryDelay = 2

        self.dtIssueToken = int(time()) - (self.tokenExpiresAfter * 1000)

        self.watchs = []

        self.user = None
