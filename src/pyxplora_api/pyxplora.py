from __future__ import annotations

from datetime import datetime, timedelta
from time import time
from typing import Any, List, Optional, Union

from .exception_classes import ChildNoError, XTypeError


class PyXplora:
    def __init__(
        self,
        countrycode: str,
        phoneNumber: str,
        password: str,
        userLang: str,
        timeZone: str,
        childPhoneNumber: list[str] = None,
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
        return bool(self._gql_handler and self._issueToken and self._gql_handler.accessToken)

    def _logoff(self) -> None:
        self.user: dict[Any, Any] = {}
        self._issueToken: dict[Any, Any] = {}

    def _hasTokenExpired(self) -> bool:
        return (int(time()) - self.dtIssueToken) > (self.tokenExpiresAfter * 1000)

    def delay(self, duration_in_seconds):
        end_time = datetime.now() + timedelta(seconds=duration_in_seconds)
        while datetime.now() < end_time:
            pass

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
        extra = self.user.get("extra", {})
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
    def getWatchUserIDs(self, watch_user_phone_numbers: list[str] = None) -> list[str]:
        if isinstance(self._wuid, list) and self._wuid:
            return self._wuid
        if isinstance(self._wuid, str) and self._wuid:
            return [self._wuid]
        watch_ids = []
        for watch in self.watchs:
            if watch_user_phone_numbers:
                if watch["ward"]["phoneNumber"] in watch_user_phone_numbers:
                    watch_ids.append(watch["ward"]["id"])
            else:
                watch_ids.append(watch["ward"]["id"])
        return watch_ids

    def getWatchUserPhoneNumbers(self, wuid: Union[str, List[str]] = None, ignoreError: bool = False) -> Union[str, List[str]]:
        watchuserphonenumbers = []
        if wuid is None:
            wuid = self.getWatchUserIDs()
        if not wuid and not ignoreError:
            raise ChildNoError(["Watch ID"])
        for watch in self.watchs:
            phone_number = str(watch["ward"]["phoneNumber"])
            if not phone_number and not ignoreError:
                continue
            if isinstance(wuid, list):
                if watch["ward"]["id"] in wuid:
                    watchuserphonenumbers.append(phone_number)
            elif isinstance(wuid, str):
                if watch["ward"]["id"] == wuid:
                    return phone_number
            else:
                raise XTypeError("str | list[str]", type(wuid))
        if not watchuserphonenumbers and not ignoreError:
            raise ChildNoError(["Child phonenumber"])
        return watchuserphonenumbers

    def getWatchUserNames(self, wuid: Optional[Union[str, List[str]]] = None) -> Union[str, List[str]]:
        watchusernames = []
        if wuid is None:
            wuid = self.getWatchUserIDs()
        if not wuid:
            raise ChildNoError(["Watch ID"])
        for watch in self.watchs:
            if isinstance(wuid, list):
                if watch["ward"]["id"] in wuid:
                    watchusernames.append(watch["ward"]["name"])
            elif isinstance(wuid, str):
                if watch["ward"]["id"] == wuid:
                    return watch["ward"]["name"]
            else:
                raise XTypeError("str | list[str]", type(wuid))
        if not watchusernames:
            raise ChildNoError(["Watch username"])
        return watchusernames

    def getWatchUserIcons(self, wuid: Union[str, List[str], None] = None) -> Union[str, List[str]]:
        watch_user_icons = []
        if wuid is None:
            wuid = self.getWatchUserIDs()
        if not wuid:
            raise ChildNoError(["Watch ID"])
        for watch in self.watchs:
            if isinstance(wuid, list):
                if watch["ward"]["id"] in wuid:
                    watch_user_icons.append(f"https://api.myxplora.com/file?id={watch['ward']['file']['id']}")
            elif isinstance(wuid, str):
                if watch["ward"]["id"] == wuid:
                    return f"https://api.myxplora.com/file?id={watch['ward']['file']['id']}"
            else:
                raise XTypeError("str | list[str]", type(wuid))
        if not watch_user_icons:
            raise ChildNoError(["Watch User Icon"])
        return watch_user_icons

    def getWatchUserXCoins(self, wuid: Optional[Union[str, List[str]]] = None) -> Union[int, List[int]]:
        watchuserxcoins = []
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

    def getWatchUserCurrentStep(self, wuid: Union[str, List[str], None] = None) -> Union[int, List[int]]:
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

    def getWatchUserTotalStep(self, wuid: Union[str, List[str], None] = None) -> Union[int, List[int]]:
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
        hours = str(int(t) // 60).zfill(2)
        minutes = str(int(t) % 60).zfill(2)
        return f"{hours}:{minutes}"
