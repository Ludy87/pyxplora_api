from __future__ import annotations

import hashlib
import math
from time import time
from datetime import datetime, timezone

from .const import API_KEY, API_SECRET
from .status import ClientType


class HandlerGQL:
    def __init__(
        self,
        countryPhoneNumber: str,
        phoneNumber: str,
        password: str,
        userLang: str,
        timeZone: str,
        email: str = None,
    ) -> None:
        # init vars
        self.sessionId = None
        self.accessToken = None
        self.accessTokenExpire = 0
        self.userLocale = userLang
        self.timeZone = timeZone
        self.countryPhoneNumber = countryPhoneNumber
        self.phoneNumber = phoneNumber
        self.email = email
        self.passwordMD5 = hashlib.md5(password.encode()).hexdigest()
        self._API_KEY = API_KEY
        self._API_SECRET = API_SECRET
        self.issueDate = 0
        self.expireDate = 0
        self.userId = None
        self.variables = {
            "countryPhoneNumber": self.countryPhoneNumber,
            "phoneNumber": self.phoneNumber,
            "password": self.passwordMD5,
            "userLang": self.userLocale,
            "timeZone": self.timeZone,
            "emailAddress": self.email,
            "client": ClientType.APP.value,
        }
        self.issueToken: dict[str, any]

        self.errors: list[any] = []

    def c(self) -> HandlerGQL:
        return self

    def getRequestHeaders(self, acceptedContentType: str) -> dict[str, any]:
        if acceptedContentType == "" or acceptedContentType is None:
            raise Exception("acceptedContentType MUST NOT be empty!")
        if self._API_KEY is None:
            raise Exception("Xplorao2o API_KEY MUST NOT be empty!")
        if self._API_SECRET is None:
            raise Exception("Xplorao2o API_SECRET MUST NOT be empty!")
        requestHeaders = {}
        if self.accessToken is None:
            # OPEN authorization
            authorizationHeader = f"Open {self._API_KEY}:{self._API_SECRET}"
        else:
            # BEARER authorization
            authorizationHeader = f"Bearer {self.accessToken}:{self._API_SECRET}"
            rfc1123DateString = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S") + " GMT"
            requestHeaders["H-Date"] = rfc1123DateString
            requestHeaders["H-Authorization"] = authorizationHeader
        requestHeaders["H-BackDoor-Authorization"] = authorizationHeader
        requestHeaders["Accept"] = acceptedContentType
        requestHeaders["Content-Type"] = acceptedContentType
        requestHeaders["H-Tid"] = str(math.floor(time()))
        return requestHeaders
