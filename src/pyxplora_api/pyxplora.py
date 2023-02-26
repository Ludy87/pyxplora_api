from __future__ import annotations

from datetime import datetime, timedelta
from time import time
from typing import Any, List, Optional, Union

from .exception_classes import ChildNoError, XTypeError


class PyXplora:
    """
    This class represents the PyXplora client. It has class level attributes and methods to interact with the Xplora API.

    Attributes:
    _gql_handler (Any): The GQL handler to interact with the Xplora API.
    error_message (str): A string representing the error message, if any.
    tokenExpiresAfter (int): An integer representing the time in seconds after which the token will expire.
    maxRetries (int): The maximum number of retries in case of API failure.
    retryDelay (int): The time in seconds to wait between retries.
    device (dict[str, Any]): A dictionary representing the device details, if any.
    watchs (list[Any]): A list of dictionaries representing the watch details, if any.
    """

    _gql_handler: Any = None
    error_message = ""
    tokenExpiresAfter = 240
    maxRetries = 3
    retryDelay = 2
    device: dict[str, Any] = {}
    watchs: list[Any] = []

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
        """
        Initialize the instance with the user's account information.

        Args:
            countrycode (str): The country code of the user's phone number.
            phoneNumber (str): The phone number of the user.
            password (str): The password of the user's account.
            userLang (str): The language setting of the user.
            timeZone (str): The time zone of the user.
            childPhoneNumber (list[str], optional): A list of phone numbers for the children of the user.
            wuid (str | list | None, optional): The ID of the watch or a list of IDs for the watches.
            email (str | None, optional): The email address of the user.

        Returns:
            None
        """
        self._countrycode = countrycode
        self._phoneNumber = phoneNumber
        self._email = email
        self._password = password
        self._userLang = userLang
        self._timeZone = timeZone

        self._childPhoneNumber = childPhoneNumber

        self._wuid = wuid

        self.dtIssueToken = int(time()) - (self.tokenExpiresAfter * 1000)

        self._logoff()

    def _isConnected(self) -> bool:
        """
        Check if the instance is connected to the server.

        Returns:
            bool: True if the instance is connected, False otherwise.
        """
        return bool(self._gql_handler and self._issueToken and self._gql_handler.accessToken)

    def _logoff(self) -> None:
        """
        Log off the user by clearing the stored information.

        Returns:
            None
        """
        self.user: dict[Any, Any] = {}
        self._issueToken: dict[Any, Any] = {}

    def _hasTokenExpired(self) -> bool:
        """
        Check if the token has expired.

        Returns:
            bool: True if the token has expired, False otherwise.
        """
        return (int(time()) - self.dtIssueToken) > (self.tokenExpiresAfter * 1000)

    def delay(self, duration_in_seconds):
        """
        Delay the execution for a specified duration.

        Args:
            duration_in_seconds (int): The duration to delay in seconds.

        Returns:
            None
        """
        end_time = datetime.now() + timedelta(seconds=duration_in_seconds)
        while datetime.now() < end_time:
            pass

    def getDevice(self, wuid: str):
        """
        Get the information for a specific watch.

        Args:
            wuid (str): The ID of the watch.

        Returns:
            dict: A dictionary containing the information of the watch.
        """
        try:
            return self.device[wuid]
        except KeyError:
            return {}

    ##### User Info #####
    def getUserID(self) -> str:
        """
        This function returns the id of the user.

        Returns:
        str: The id of the user.
        """
        return self.user.get("id", "")

    def getUserName(self) -> str:
        """
        This function returns the name of the user.

        Returns:
        str: The name of the user.
        """
        return self.user.get("name", "")

    def getUserIcon(self) -> str:
        """
        This function returns the profile icon of the user.

        Returns:
        str: The profile icon of the user.
        """
        extra = self.user.get("extra", {})
        return extra.get("profileIcon", "https://s3.eu-central-1.amazonaws.com/kids360uc/default_icon.png")

    def getUserXcoin(self) -> int:
        """
        This function returns the xcoin amount of the user.

        Returns:
        int: The xcoin amount of the user.
        """
        return self.user.get("xcoin", -1)

    def getUserCurrentStep(self) -> int:
        """
        This function returns the current step count of the user.

        Returns:
        int: The current step count of the user.
        """
        return self.user.get("currentStep", -1)

    def getUserTotalStep(self) -> int:
        """
        This function returns the total step count of the user.

        Returns:
        int: The total step count of the user.
        """
        return self.user.get("totalStep", -1)

    def getUserCreate(self) -> str:
        """
        This function returns the creation date and time of the user.

        Returns:
        str: The creation date and time of the user in the format "YYYY-MM-DD HH:MM:SS".
        """
        return datetime.fromtimestamp(self.user.get("create", 0.0)).strftime("%Y-%m-%d %H:%M:%S")

    def getUserUpdate(self) -> str:
        """
        This function returns the user update time in a string format.

        Returns:
        str: The user update time in the format 'YYYY-MM-DD HH:MM:SS'.

        """
        return datetime.fromtimestamp(self.user.get("update", 0.0)).strftime("%Y-%m-%d %H:%M:%S")

    ##### Watch Info #####
    def getWatchUserIDs(self, watch_user_phone_numbers: Optional[List[str]] = None) -> List[str]:
        """
        This function returns the unique identifiers of the watch users.

        Parameters:
        watch_user_phone_numbers (List[str], optional): A list of watch user phone numbers to filter the watch users. If not provided, all watch user ids will be returned.

        Returns:
        List[str]: A list of unique identifiers of the watch users.

        """
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

    def getWatchUserPhoneNumbers(
        self, wuid: Optional[Union[str, List[str]]] = None, ignoreError: bool = False
    ) -> Union[str, List[str]]:
        """
        This function returns the phone number of the watch users.

        Parameters:
        wuid (Union[str, List[str]], optional): The unique identifier of the watch user. If not provided, the function will retrieve all watch user ids using `self.getWatchUserIDs()`.
        ignoreError (bool, optional): If True, the function will not raise error in case of missing information. Default value is False.

        Returns:
        Union[str, List[str]]: The phone number(s) of the watch user(s).

        Raises:
        ChildNoError: If no `wuid` provided or watch user ids are not found.
        XTypeError: If the `wuid` is not of type `str` or `list[str]`.

        """
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
        """
        This function returns the name of one or multiple users specified by their user ID. If no user ID is specified,
        the names of all watched users are returned.

        Parameters:
        wuid (str, list[str], optional): A string or a list of strings representing the user IDs of the watched users. Defaults to None.

        Returns:
        Union[str, List[str]]: A string representing the name of a single user or a list of strings representing the names of multiple users.

        Raises:
        ChildNoError: If the user IDs are not found.
        XTypeError: If the `wuid` parameter is not a string or a list of strings.

        """
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
        # if not watchusernames:
        #     raise ChildNoError(["Watch username"])
        return watchusernames

    def getWatchUserIcons(self, wuid: Optional[Union[str, List[str], None]] = None) -> Union[str, List[str]]:
        """
        Get the icon URL for watch users.

        Parameters:
        wuid (str or list[str] or None, optional): Watch User ID. Defaults to None.
        If None, all watch user IDs will be retrieved using `getWatchUserIDs()`.

        Returns:
        str or list[str]: The URL of the icon for the specified watch user(s).

        Raises:
        ChildNoError: If no watch user ID is found.
        XTypeError: If the input argument is not of type 'str' or 'list[str]'.

        """
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
        # if not watch_user_icons:
        #     raise ChildNoError(["Watch User Icon"])
        return watch_user_icons

    def getWatchUserXCoins(self, wuid: Optional[Union[str, List[str]]] = None) -> Union[int, List[int]]:
        """
        Get the XCoins earned by the watch user.

        Args:
        wuid (str or list of str or None, optional): Watch User ID or a list of Watch User IDs. If None, returns XCoins for all Watch Users.

        Returns:
        int or list of int: XCoins earned by the specified Watch User or a list of XCoins earned by specified Watch Users.

        Raises:
        ChildNoError: If the specified Watch User ID(s) is not found.
        XTypeError: If the specified `wuid` is not of type str or list of str.
        """
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
        # if not watchuserxcoins:
        #     raise ChildNoError(["Watch User XCoins"])
        return watchuserxcoins

    def getWatchUserCurrentStep(self, wuid: Union[str, List[str], None] = None) -> Union[int, List[int]]:
        """
        Get the current step count of a watch user.

        Args:
        wuid (str | list[str] | None): ID(s) of watch user(s). If None, all IDs are used. (default None)

        Returns:
        int | list[int]: current step count of the watch user(s).

        Raises:
        ChildNoError: if the specified `wuid` does not exist.
        XTypeError: if the type of `wuid` is not `str` or `list[str]`.
        """
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
        # if not watchusercurrentstep:
        #     raise ChildNoError(["Watch User Currentsteps"])
        return watchusercurrentstep

    def getWatchUserTotalStep(self, wuid: Optional[Union[str, List[str], None]] = None) -> Union[int, List[int]]:
        """
        Get the total steps taken by a user or a list of users from the watch.

        Args:
        wuid (str | list[str] | None, optional): the watch user id or a list of watch user ids. If None, get total steps for all users. Default is None.

        Returns:
        int | list[int]: the total steps taken by the user(s) or a list of total steps taken by each user in the list.

        Raises:
        ChildNoError: if wuid is an empty list.
        XTypeError: if wuid is not a string or a list of strings.
        """
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
        # if not watchusertotalstep:
        #     raise ChildNoError(["Watch User totalsteps"])
        return watchusertotalstep

    ##### - #####
    def _helperTime(self, t: str) -> str:
        """
        Convert time in minutes to hours and minutes.

        Args:
        t (str): time in minutes as string

        Returns:
        str: time in hours and minutes format (hh:mm)
        """
        hours = str(int(t) // 60).zfill(2)
        minutes = str(int(t) % 60).zfill(2)
        return f"{hours}:{minutes}"
