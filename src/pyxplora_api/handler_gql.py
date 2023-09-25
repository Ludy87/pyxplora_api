from __future__ import annotations

import sys

if sys.version_info >= (3, 11):
    from datetime import UTC, datetime
else:
    from datetime import datetime, timezone
import hashlib
import math
from time import time

from .const import API_KEY, API_SECRET
from .status import ClientType


class HandlerGQL:
    """A class to handle GraphQL API requests for PyXplora.

    Attributes:
        accessToken (any): The access token used for authentication.
        sessionId (None): The session ID.
        userId (None): The user ID.
        _API_KEY (str): The API key.
        _API_SECRET (str): The API secret.
        issueToken (dict[str, any]): The issue token.
        errors (list[any]): A list of errors.

    """

    accessToken: any = None  # noqa: N815
    sessionId = None  # noqa: N815
    userId = None  # noqa: N815
    issueToken: dict[str, any] = None  # noqa: N815
    errors: list[any] = []

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
        """Initializes the class with the given parameters.

        Args:
            countryPhoneNumber (str): The country phone number.
            phoneNumber (str): The phone number.
            password (str): The password.
            userLang (str): The user language.
            timeZone (str): The time zone.
            email (str, optional): The email address. Defaults to None.
            signup (bool, optional): Indicates if the user is signing up. Defaults to True.

        """
        # init vars
        self.userLocale = userLang
        self.timeZone = timeZone
        self.countryPhoneNumber = countryPhoneNumber
        self.phoneNumber = phoneNumber
        self.email = email
        self.passwordMD5 = hashlib.md5(password.encode()).hexdigest()
        self._API_KEY = API_KEY
        self._API_SECRET = API_SECRET
        self.variables = {
            "countryPhoneNumber": self.countryPhoneNumber,
            "phoneNumber": self.phoneNumber,
            "password": self.passwordMD5,
            "userLang": self.userLocale,
            "timeZone": self.timeZone,
            "emailAddress": self.email,
            "client": ClientType.APP.value,
        }
        self.signup = signup

    def getApiKey(self):
        """Returns the API key.

        Returns:
            str: The API key.

        """
        return self._API_KEY

    def getSecret(self):
        """Returns the API secret.

        Returns:
            str: The API secret.

        """
        return self._API_SECRET

    def getRequestHeaders(self, acceptedContentType: str) -> dict[str, any]:
        """Returns the request headers with the specified content type.

        Args:
            acceptedContentType (str): The accepted content type.

        Returns:
            dict[str, any]: The request headers.

        Raises:
            Exception: If `acceptedContentType` is empty or if `API_KEY` or `API_SECRET` is not set.

        """
        if acceptedContentType == "" or acceptedContentType is None:
            raise Exception("acceptedContentType MUST NOT be empty!")
        if self._API_KEY is None:
            raise Exception("Xplorao2o API_KEY MUST NOT be empty!")
        if self._API_SECRET is None:
            raise Exception("Xplorao2o API_SECRET MUST NOT be empty!")

        authorizationHeader = ""

        if (self.accessToken is None or not self.issueToken) and self._API_KEY == API_KEY:
            # OPEN authorization
            authorizationHeader = f"Open {self._API_KEY}:{self._API_SECRET}"
        # else:
        # BEARER authorization
        elif self.issueToken:
            w360: dict = self.issueToken.get("w360", None)
            if w360:
                if w360.get("token") and w360.get("secret"):
                    authorizationHeader = (
                        f'Bearer {w360.get("token", self.accessToken)}:{w360.get("secret", self._API_SECRET)}'
                    )
                    self._API_KEY = w360.get("token", API_KEY)
                    self._API_SECRET = w360.get("secret", API_SECRET)
            else:
                authorizationHeader = f"Bearer {self.accessToken}:{self._API_SECRET}"
        else:
            authorizationHeader = f"Bearer {self._API_KEY}:{self._API_SECRET}"
        if sys.version_info >= (3, 11):
            utc = UTC
        else:
            utc = timezone.utc
        requestHeaders = {
            "H-Date": datetime.now(utc).strftime("%a, %d %b %Y %H:%M:%S") + " GMT",
            "H-Tid": str(math.floor(time())),
            "Content-Type": acceptedContentType,
            "H-BackDoor-Authorization": authorizationHeader,
        }
        return requestHeaders
