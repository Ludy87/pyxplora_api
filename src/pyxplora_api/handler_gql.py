from __future__ import annotations

import hashlib
import logging
import math
from datetime import datetime, timezone
from time import time
from typing import Any

from .const import API_KEY, API_SECRET
from .status import ClientType
_LOGGER = logging.getLogger(__name__)


class HandlerGQL:
    accessToken: Any = None

    def __init__(
        self,
        countryPhoneNumber: str,
        phoneNumber: str,
        password: str,
        userLang: str,
        timeZone: str,
        email: str = None,
        signup: bool = True,
    ) -> None:
        # init vars
        self.sessionId = None
        # self.accessToken = None
        self.accessTokenExpire = 0
        self.userLocale = userLang
        self.timeZone = timeZone
        self.countryPhoneNumber = countryPhoneNumber
        self.phoneNumber = phoneNumber
        self.email = email
        self.passwordMD5 = hashlib.md5(password.encode()).hexdigest()
        self._API_KEY = API_KEY
        self._API_SECRET = API_SECRET
        # self.issueDate = 0
        # self.expireDate = 0
        self.userId = None
        self.variables = {
            "countryPhoneNumber": self.countryPhoneNumber,
            "phoneNumber": self.phoneNumber,
            "password": self.passwordMD5,
            "userLang": self.userLocale,
            "timeZone": self.timeZone,
            "emailAddress": self.email,
            "client": ClientType.WEB.value,
        }
        self.issueToken: dict[str, Any] = None

        self.errors: list[Any] = []

        self.signup = signup

    def getRequestHeaders(self, acceptedContentType: str) -> dict[str, Any]:
        if acceptedContentType == "" or acceptedContentType is None:
            raise Exception("acceptedContentType MUST NOT be empty!")
        if self._API_KEY is None:
            raise Exception("Xplorao2o API_KEY MUST NOT be empty!")
        if self._API_SECRET is None:
            raise Exception("Xplorao2o API_SECRET MUST NOT be empty!")
        requestHeaders = {}

        if self.accessToken is None or not self.issueToken:
            # OPEN authorization
            authorizationHeader = f"Open {self._API_KEY}:{self._API_SECRET}"
        else:
            # BEARER authorization
            if self.issueToken:
                w360: dict = self.issueToken.get("w360", None)
                if w360:
                    if w360.get("token") and w360.get("secret"):
                        authorizationHeader = (
                            f'Bearer {w360.get("token", self.accessToken)}:{w360.get("secret", self._API_SECRET)}'
                        )
                else:
                    authorizationHeader = f"Bearer {self.accessToken}:{self._API_SECRET}"
            else:
                authorizationHeader = f"Bearer {self.key}:{self.secret_key}"
        _LOGGER.debug(authorizationHeader)
        rfc1123DateString = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S") + " GMT"
        requestHeaders["H-Date"] = rfc1123DateString
        requestHeaders["H-Tid"] = str(math.floor(time()))
        requestHeaders["Content-Type"] = acceptedContentType
        requestHeaders["H-BackDoor-Authorization"] = authorizationHeader
        return requestHeaders
