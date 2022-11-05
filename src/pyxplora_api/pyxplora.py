from __future__ import annotations

from datetime import datetime, timedelta
from time import time
from typing import Any

from .exception_classes import ChildNoError, XTypeError


class PyXplora:
    def __init__(
        self,
        countrycode: str,
        phoneNumber: str,
        password: str,
        userLang: str,
        timeZone: str,
        childPhoneNumber: list[str] = [],
        wuid: str | list | None = None,
        email: str | None = None,
    ) -> None:
        self._countrycode = countrycode
        self._phoneNumber = phoneNumber
        self._email = email
        self._password = password
        self._userLang = userLang
        self._timeZone = timeZone

        self.error_message = ""

        self._childPhoneNumber = childPhoneNumber

        self._wuid = wuid

        self.tokenExpiresAfter = 240
        self.maxRetries = 3
        self.retryDelay = 2

        self.dtIssueToken = int(time()) - (self.tokenExpiresAfter * 1000)

        self.device: dict[str, Any] = {}

        self.watchs: list[Any] = []
        self._logoff()

    def _isConnected(self) -> bool:
        return bool(self._gqlHandler and self._issueToken)

    def _logoff(self) -> None:
        self.user: dict[Any, Any] = {}
        self._gqlHandler = None
        self._issueToken: dict[Any, Any] = {}

    def _hasTokenExpired(self) -> bool:
        return (int(time()) - self.dtIssueToken) > (self.tokenExpiresAfter * 1000)

    def delay(self, duration_in_seconds):
        current_time = datetime.now()
        end_time = current_time + timedelta(0, duration_in_seconds)
        while current_time < end_time:
            current_time = datetime.now()

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
        extra: dict[str, str] = self.user.get("extra", {})
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
    def getWatchUserIDs(self, watchuserphonenumbers: list[str] = []) -> list[str]:
        if isinstance(self._wuid, list):
            if self._wuid:
                return self._wuid
        if isinstance(self._wuid, str):
            if self._wuid != "":
                return [self._wuid]
        watch_IDs: list[str] = []
        for watch in self.watchs:
            if watchuserphonenumbers:
                if watch["ward"]["phoneNumber"] in watchuserphonenumbers:
                    watch_IDs.append(watch["ward"]["id"])
            else:
                watch_IDs.append(watch["ward"]["id"])
        return watch_IDs

    def getWatchUserPhoneNumbers(self, wuid: str | list[str] | None = None, ignoreError: bool = False) -> str | list[str]:
        watchuserphonenumbers: list[str] = []
        i = 1
        if wuid is None:
            wuid = self.getWatchUserIDs()
        if not wuid and not ignoreError:
            raise ChildNoError(["Watch ID"])
        for watch in self.watchs:
            if str(watch["ward"]["phoneNumber"]) == "" and not ignoreError:
                if i == len(self.watchs):
                    raise ChildNoError()
                i += 1
                continue
            if isinstance(wuid, list):
                if watch["ward"]["id"] in wuid:
                    watchuserphonenumbers.append(str(watch["ward"]["phoneNumber"]))
            elif isinstance(wuid, str):
                if watch["ward"]["id"] == wuid:
                    return str(watch["ward"]["phoneNumber"])
            else:
                raise XTypeError("str | list[str]", type(wuid))
        if not watchuserphonenumbers and not ignoreError:
            raise ChildNoError(["Child phonenumber"])
        return watchuserphonenumbers

    def getWatchUserNames(self, wuid: str | list[str] | None = None) -> str | list[str]:
        watchusernames: list[str] = []
        if wuid is None:
            wuid = self.getWatchUserIDs()
        if not wuid:
            raise ChildNoError(["Watch ID"])
        for watch in self.watchs:
            if isinstance(wuid, list):
                if watch["ward"]["id"] in wuid:
                    watchusernames.append(str(watch["ward"]["name"]))
            elif isinstance(wuid, str):
                if watch["ward"]["id"] == wuid:
                    return str(watch["ward"]["name"])
            else:
                raise XTypeError("str | list[str]", type(wuid))
        if not watchusernames:
            raise ChildNoError(["Watch Username"])
        return watchusernames

    def getWatchUserIcons(self, wuid: str | list[str] | None = None) -> str | list[str]:
        watchusericons: list[str] = []
        if wuid is None:
            wuid = self.getWatchUserIDs()
        if not wuid:
            raise ChildNoError(["Watch ID"])
        for watch in self.watchs:
            if isinstance(wuid, list):
                if watch["ward"]["id"] in wuid:
                    watchusericons.append(f"https://api.myxplora.com/file?id={watch['ward']['file']['id']}")
            elif isinstance(wuid, str):
                if watch["ward"]["id"] == wuid:
                    return f"https://api.myxplora.com/file?id={watch['ward']['file']['id']}"
            else:
                raise XTypeError("str | list[str]", type(wuid))
        if not watchusericons:
            raise ChildNoError(["Watch User Icon"])
        return watchusericons

    def getWatchUserXcoins(self, wuid: str | list[str] | None = None) -> int | list[int]:
        watchuserxcoins: list[int] = []
        if wuid is None:
            wuid = self.getWatchUserIDs()
        if not wuid:
            raise ChildNoError(["Watch ID"])
        for watch in self.watchs:
            if isinstance(wuid, list):
                if watch["ward"]["id"] in wuid:
                    watchuserxcoins.append(int(watch["ward"]["xcoin"]))
            elif isinstance(wuid, str):
                if watch["ward"]["id"] == wuid:
                    return int(watch["ward"]["xcoin"])
            else:
                raise XTypeError("str | list[str]", type(wuid))
        if not watchuserxcoins:
            raise ChildNoError(["Watch User XCoins"])
        return watchuserxcoins

    def getWatchUserCurrentStep(self, wuid: str | list[str] | None = None) -> int | list[int]:
        watchusercurrentstep: list[int] = []
        if wuid is None:
            wuid = self.getWatchUserIDs()
        if not wuid:
            raise ChildNoError(["Watch ID"])
        for watch in self.watchs:
            if isinstance(wuid, list):
                if watch["ward"]["id"] in wuid:
                    watchusercurrentstep.append(int(watch["ward"]["currentStep"]))
            elif isinstance(wuid, str):
                if watch["ward"]["id"] == wuid:
                    return int(watch["ward"]["currentStep"])
            else:
                raise XTypeError("str | list[str]", type(wuid))
        if not watchusercurrentstep:
            raise ChildNoError(["Watch User Currentsteps"])
        return watchusercurrentstep

    def getWatchUserTotalStep(self, wuid: str | list[str] | None = None) -> int | list[int]:
        watchusertotalstep: list[int] = []
        if wuid is None:
            wuid = self.getWatchUserIDs()
        if not wuid:
            raise ChildNoError(["Watch ID"])
        for watch in self.watchs:
            if isinstance(wuid, list):
                if watch["ward"]["id"] in wuid:
                    watchusertotalstep.append(int(watch["ward"]["totalStep"]))
            elif isinstance(wuid, str):
                if watch["ward"]["id"] == wuid:
                    return int(watch["ward"]["totalStep"])
            else:
                raise XTypeError("str | list[str]", type(wuid))
        if not watchusertotalstep:
            raise ChildNoError(["Watch User totalsteps"])
        return watchusertotalstep

    ##### - #####
    def _helperTime(self, t: str) -> str:
        h = str(int(t) / 60).split(".")
        h2 = str(int(h[1]) * 60).zfill(2)[:2]
        return h[0].zfill(2) + ":" + str(h2).zfill(2)
