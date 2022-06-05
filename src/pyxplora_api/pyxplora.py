from __future__ import annotations

from datetime import datetime
from time import time
from typing import Any, Dict, List

from .exception_classes import ChildNoError


class PyXplora:
    def __init__(
        self,
        countrycode: str,
        phoneNumber: str,
        password: str,
        userLang: str,
        timeZone: str,
        childPhoneNumber: List[str] = [],
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

        self.device: Dict[str, Any] = {}

        self.watchs: List[Any] = []
        self._logoff()

    def _isConnected(self) -> bool:
        return bool(self._gqlHandler and self._issueToken)

    def _logoff(self) -> None:
        self.user: Dict[Any, Any] = {}
        self._gqlHandler = None
        self._issueToken: Dict[Any, Any] = {}

    def _hasTokenExpired(self) -> bool:
        return (int(time()) - self.dtIssueToken) > (self.tokenExpiresAfter * 1000)

    def delay(self, duration_in_seconds):
        current_time = datetime.datetime.now()
        end_time = current_time + datetime.timedelta(0, duration_in_seconds)
        while current_time < end_time:
            current_time = datetime.datetime.now()

    def getDevice(self, wuid: str):
        try:
            return self.device[wuid]
        except KeyError:
            return {}

    ##### User Info #####
    def getUserID(self) -> str:
        return self.user.get("id", "")

    def getUserName(self) -> str:
        return self.user.get("name", "")

    def getUserIcon(self) -> str:
        extra: Dict[str, str] = self.user.get("extra", {})
        return extra.get("profileIcon", "https://s3.eu-central-1.amazonaws.com/kids360uc/default_icon.png")

    def getUserXcoin(self) -> int:
        return self.user.get("xcoin", -1)

    def getUserCurrentStep(self) -> int:
        return self.user.get("currentStep", -1)

    def getUserTotalStep(self) -> int:
        return self.user.get("totalStep", -1)

    def getUserCreate(self) -> str:
        return datetime.fromtimestamp(self.user.get("create", 0.0)).strftime("%Y-%m-%d %H:%M:%S")

    def getUserUpdate(self) -> str:
        return datetime.fromtimestamp(self.user.get("update", 0.0)).strftime("%Y-%m-%d %H:%M:%S")

    ##### Watch Info #####
    def getWatchUserIDs(self, watchuserphonenumbers: List[str] = []) -> List[str]:
        watch_IDs: List[str] = []
        for watch in self.watchs:
            if watchuserphonenumbers:
                if watch["ward"]["phoneNumber"] in watchuserphonenumbers:
                    watch_IDs.append(watch["ward"]["id"])
            else:
                watch_IDs.append(watch["ward"]["id"])
        return watch_IDs

    def getWatchUserPhoneNumbers(self, wuid: str | List[str], ignoreError: bool = False) -> str | List[str]:
        watchuserphonenumbers: List[str] = []
        for watch in self.watchs:
            if str(watch["ward"]["phoneNumber"]) != "" and ignoreError:
                raise ChildNoError()
            if isinstance(wuid, list):
                if watch["ward"]["id"] in wuid:
                    watchuserphonenumbers.append(str(watch["ward"]["phoneNumber"]))
            elif isinstance(wuid, str):
                if watch["ward"]["id"] == wuid:
                    return str(watch["ward"]["phoneNumber"])
        if not watchuserphonenumbers:
            raise ChildNoError()
        return watchuserphonenumbers

    def getWatchUserNames(self, wuid: str | List[str]) -> str | List[str]:
        watchusernames: List[str] = []
        for watch in self.watchs:
            if isinstance(wuid, list):
                if watch["ward"]["id"] in wuid:
                    watchusernames.append(str(watch["ward"]["name"]))
            elif isinstance(wuid, str):
                if watch["ward"]["id"] == wuid:
                    return str(watch["ward"]["name"])
        if not watchusernames:
            raise ChildNoError()
        return watchusernames

    def getWatchUserIcons(self, wuid: str | List[str]) -> str | List[str]:
        watchusericons: List[str] = []
        for watch in self.watchs:
            if isinstance(wuid, list):
                if watch["ward"]["id"] in wuid:
                    watchusericons.append(f"https://api.myxplora.com/file?id={watch['ward']['file']['id']}")
            elif isinstance(wuid, str):
                if watch["ward"]["id"] == wuid:
                    return f"https://api.myxplora.com/file?id={watch['ward']['file']['id']}"
        if not watchusericons:
            raise ChildNoError()
        return watchusericons

    def getWatchUserXcoins(self, wuid: str | List[str]) -> int | List[int]:
        watchuserxcoins: List[int] = []
        for watch in self.watchs:
            if isinstance(wuid, list):
                if watch["ward"]["id"] in wuid:
                    watchuserxcoins.append(int(watch["ward"]["xcoin"]))
            elif isinstance(wuid, str):
                if watch["ward"]["id"] == wuid:
                    return int(watch["ward"]["xcoin"])
        if not watchuserxcoins:
            raise ChildNoError()
        return watchuserxcoins

    def getWatchUserCurrentStep(self, wuid: str | List[str]) -> int | List[int]:
        watchusercurrentstep: List[int] = []
        for watch in self.watchs:
            if isinstance(wuid, list):
                if watch["ward"]["id"] in wuid:
                    watchusercurrentstep.append(int(watch["ward"]["currentStep"]))
            elif isinstance(wuid, str):
                if watch["ward"]["id"] == wuid:
                    return int(watch["ward"]["currentStep"])
        if not watchusercurrentstep:
            raise ChildNoError()
        return watchusercurrentstep

    def getWatchUserTotalStep(self, wuid: str | List[str]) -> int | List[int]:
        watchusertotalstep: List[int] = []
        for watch in self.watchs:
            if isinstance(wuid, list):
                if watch["ward"]["id"] in wuid:
                    watchusertotalstep.append(int(watch["ward"]["totalStep"]))
            elif isinstance(wuid, str):
                if watch["ward"]["id"] == wuid:
                    return int(watch["ward"]["totalStep"])
        if not watchusertotalstep:
            raise ChildNoError()
        return watchusertotalstep

    ##### - #####
    def _helperTime(self, t: str) -> str:
        h = str(int(t) / 60).split(".")
        h2 = str(int(h[1]) * 60).zfill(2)[:2]
        return h[0].zfill(2) + ":" + str(h2).zfill(2)
