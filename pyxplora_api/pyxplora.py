from __future__ import annotations

from datetime import datetime
from time import time
from typing import Any, Dict, List


class PyXplora:
    def __init__(
        self,
        countrycode: str,
        phoneNumber: str,
        password: str,
        userLang: str,
        timeZone: str,
        childPhoneNumber=[],
    ) -> None:
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

        self.watchs: List[str] = []

        self.user = None
        self._gqlHandler = None
        self._issueToken: Dict[Any, Any] = {}

    def _isConnected(self) -> bool:
        return bool(self._gqlHandler and self._issueToken)

    def _logoff(self) -> None:
        self._gqlHandler = None
        self._issueToken = {}

    def _hasTokenExpired(self) -> bool:
        return (int(time()) - self.dtIssueToken) > (self.tokenExpiresAfter * 1000)

    ##### User Info #####
    def getUserID(self) -> str:
        return self.user["id"]

    def getUserName(self) -> str:
        return self.user["name"]

    def getUserIcon(self) -> str:
        return self.user["extra"]["profileIcon"]

    def getUserXcoin(self) -> int:
        return self.user["xcoin"]

    def getUserCurrentStep(self) -> int:
        return self.user["currentStep"]

    def getUserTotalStep(self) -> int:
        return self.user["totalStep"]

    def getUserCreate(self) -> str:
        return datetime.fromtimestamp(self.user["create"]).strftime("%Y-%m-%d %H:%M:%S")

    def getUserUpdate(self) -> str:
        return datetime.fromtimestamp(self.user["update"]).strftime("%Y-%m-%d %H:%M:%S")

    ##### Watch Info #####
    def getWatchUserID(self, child_no: list = []) -> List[str]:
        watch_IDs: List[str] = []
        for watch in self.watchs:
            if child_no:
                if watch["ward"]["phoneNumber"] in child_no:
                    watch_IDs.append(watch["ward"]["id"])
            else:
                watch_IDs.append(watch["ward"]["id"])
        return watch_IDs

    def getWatchUserPhoneNumber(self) -> List[str]:
        watch_IDs: List[str] = []
        for watch in self.watchs:
            watch_IDs.append(watch["ward"]["phoneNumber"])
        return watch_IDs

    def getWatchUserName(self, watchID) -> str:
        for watch in self.watchs:
            if watch["ward"]["id"] == watchID:
                return watch["ward"]["name"]
        raise Exception("Child phonenumber not found!")

    def getWatchUserIcon(self, watchID) -> str:
        for watch in self.watchs:
            if watch["ward"]["id"] == watchID:
                return f"https://api.myxplora.com/file?id={watch['ward']['file']['id']}"
        raise Exception("Child phonenumber not found!")

    def getWatchXcoin(self, watchID) -> str:
        for watch in self.watchs:
            if watch["ward"]["id"] == watchID:
                return watch["ward"]["xcoin"]
        raise Exception("Child phonenumber not found!")

    def getWatchCurrentStep(self, watchID) -> str:
        for watch in self.watchs:
            if watch["ward"]["id"] == watchID:
                return watch["ward"]["currentStep"]
        raise Exception("Child phonenumber not found!")

    def getWatchTotalStep(self, watchID) -> str:
        for watch in self.watchs:
            if watch["ward"]["id"] == watchID:
                return watch["ward"]["totalStep"]
        raise Exception("Child phonenumber not found!")

    ##### - #####
    def _helperTime(self, t) -> str:
        h = str(int(t) / 60).split(".")
        h2 = str(int(h[1]) * 60).zfill(2)[:2]
        return h[0].zfill(2) + ":" + str(h2).zfill(2)
