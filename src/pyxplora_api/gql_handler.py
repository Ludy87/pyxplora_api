from __future__ import annotations

import logging
from typing import Any, Dict

from . import gql_mutations as gm
from . import gql_queries as gq
from .const import ENDPOINT
from .exception_classes import LoginError, NoAdminError
from .graphql_client import GraphqlClient
from .handler_gql import HandlerGQL
from .model import Chats
from .status import EmailAndPhoneVerificationTypeV2, NormalStatus, UserContactType

_LOGGER = logging.getLogger(__name__)


class GQLHandler(HandlerGQL):
    """This class represents the GQLHandler that interacts with the Xplora® API.

    It inherits the `HandlerGQL` class and implements the `runGqlQuery` method to execute GraphQL queries and mutations.

    Args:
        countryPhoneNumber (str): The country phone number of the user.
        phoneNumber (str): The phone number of the user.
        password (str): The password of the user.
        userLang (str): The language preference of the user.
        timeZone (str): The time zone of the user.
        email (str, optional): The email of the user. Defaults to None.
        signup (bool, optional): Indicates if the user is signing up. Defaults to True.
    """

    def __init__(
        self,
        countryPhoneNumber: str,
        phoneNumber: str,
        password: str,
        userLang: str,
        timeZone: str,
        email: str | None = None,
        signup: bool = True,
    ) -> None:
        super().__init__(countryPhoneNumber, phoneNumber, password, userLang, timeZone, email, signup)

    def runGqlQuery(
        self, query: str, variables: dict[str, Any] | None = None, operation_name: str | None = None
    ) -> Dict[str, Any]:
        """Execute a GraphQL query or mutation.

        Args:
            query (str): The GraphQL query string to be executed.
            variables (dict, optional): The variables to be passed to the query. Defaults to None.
            operation_name (str, optional): The name of the operation to be executed. Defaults to None.

        Returns:
            dict: The result of the executed query.

        Raises:
            Exception: If the query string is empty.
        """
        if query is None:
            raise Exception("GraphQL guery string MUST NOT be empty!")
        # Add Xplora® API headers
        requestHeaders = self.getRequestHeaders("application/json; charset=UTF-8")
        # create GQLClient
        gqlClient = GraphqlClient(endpoint=ENDPOINT, headers=requestHeaders)
        # execute QUERY|MUTATION
        data: dict[str, Any] = gqlClient.execute(query=query, variables=variables, operation_name=operation_name)
        return data

    def runAuthorizedGqlQuery(
        self, query: str, variables: dict[str, Any] | None = None, operation_name: str | None = None
    ) -> Dict[str, Any]:
        """
        This function executes a GraphQL query that requires authorization.

        Args:
            query (str): The GraphQL query string to be executed.
            variables (dict[str, Any], optional): Variables to be passed along with the GraphQL query. Defaults to None.
            operation_name (str, optional): Name of the operation being executed. Defaults to None.

        Returns:
            dict[str, Any]: A dictionary representing the response from the executed GraphQL query.

        Raises:
            Exception: If the accessToken is None and signup flag is not set.

        """
        if self.accessToken is None and self.signup:
            self.login()
        # Run GraphQL query and return
        return self.runGqlQuery(query, variables, operation_name)

    def login(self) -> Dict[str, Any]:
        """
        This method logs the user into the Xplora API by executing a GraphQL mutation `signInWithEmailOrPhone`.
        The user is identified by the `variables` property of the `Client` instance, which should contain the
        email or phone number and the password for the user.

        Returns:
            dict[str, Any]: A dictionary representing the JSON response from the Xplora API. The relevant data for
            the user is stored in the `Client` instance's `issueToken`, `sessionId`, `userId`, and `accessToken`
            properties.
        """
        dataAll = self.runGqlQuery(gm.SIGN_M.get("signInWithEmailOrPhoneM", ""), self.variables, "signInWithEmailOrPhone")
        if dataAll is None:
            return
        errors = dataAll.get("errors", None)
        if errors:
            self.errors.append({"function": "login", "errors": errors})
        data = dataAll.get("data", {})
        signIn = data.get("signInWithEmailOrPhone", None)
        if signIn is None:
            error_message = dataAll.get("errors", [{"message": ""}])[0].get("message", "")
            raise LoginError(f"Login error: {error_message}")

        self.issueToken = signIn
        self.sessionId = self.issueToken["id"]
        self.userId = self.issueToken["user"]["id"]
        self.accessToken = self.issueToken["token"]

        return self.issueToken

    def isAdmin(self, wuid: str, query: str, variables: dict[str, Any], key: str) -> bool:
        """
        This method determines whether the currently logged-in user is an admin for the specified watch user.

        Args:
            wuid (str): The id of the watch user for which the admin status of the current user should be determined.
            query (str): The GraphQL query that should be executed to determine the admin status of the current user.
            variables (dict[str, Any]): The variables for the GraphQL query.
            key (str): The key in the JSON response from the Xplora API that represents the admin status of the
            current user.

        Returns:
            bool: `True` if the current user is an admin for the specified watch user, `False` otherwise.

        Raises:
            NoAdminError: If the current user is not an admin for the specified watch user.
        """
        contacts: dict[str, Any] = self.getWatchUserContacts(wuid)
        for contact in contacts["contacts"]["contacts"]:
            try:
                id = contact["contactUser"]["id"]
            except KeyError and TypeError:
                id = None
            if self.userId == id:
                if contact["guardianType"] == "FIRST":
                    data: dict[str, Any] = self.runAuthorizedGqlQuery(query, variables, key).get("data", {})
                    for k in data.keys():
                        if k.upper() == key.upper():
                            return data.get(k, False)
        raise NoAdminError()

    ########## SECTION QUERY start ##########

    def askWatchLocate(self, wuid: str) -> Dict[str, Any]:
        """
        Ask the watch for its location.

        Args:
            wuid (str): The watch identifier.

        Returns:
            dict[str, Any]: A dictionary containing the response of the query, with a key "askWatchLocate".
        """
        data: dict[str, Any] = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("askLocateQ", ""), {"uid": wuid}, "AskWatchLocate")
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "askWatchLocate", "errors": errors})
        res: dict[str, Any] = data.get("data", {})
        if res["askWatchLocate"] is not None:
            return res
        return {"askWatchLocate": False}

    def getWatchUserContacts(self, wuid: str) -> Dict[str, Any]:
        """
        Get the user contacts associated with the watch.

        Args:
            wuid (str): The watch identifier.

        Returns:
            dict[str, Any]: A dictionary containing the response of the query.
        """
        data: dict[str, Any] = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("contactsQ", ""), {"uid": wuid}, "Contacts")
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchUserContacts", "errors": errors})
        return data.get("data", {})

    def getWatches(self, wuid: str) -> Dict[str, Any]:
        """
        Get the watches associated with the user.

        Args:
            wuid (str): The watch identifier.

        Returns:
            dict[str, Any]: A dictionary containing the response of the query.
        """
        data: dict[str, Any] = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("watchesQ", ""), {"uid": wuid}, "Watches")
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatches", "errors": errors})
        return data.get("data", {})

    def getSWInfo(self, qrCode: str) -> Dict[str, Any]:
        """
        Get software information for a watch using its QR code.

        Args:
            qrCode (str): The QR code of the watch.

        Returns:
            dict[str, Any]: A dictionary containing the response of the query.
        """
        data: dict[str, Any] = self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("checkByQrCodeQ", ""), {"qrCode": qrCode}, "CheckWatchByQrCode"
        )
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getSWInfo", "errors": errors})
        return data.get("data", {})

    def getWatchState(self, qrCode: str, qrt: str = "", qrc: str = "") -> Dict[str, Any]:
        """
        Get the state of a watch using its QR code.

        Args:
            qrCode (str): The QR code of the watch.
            qrt (str, optional): The QR type. Defaults to "".
            qrc (str, optional): The QR code. Defaults to "".

        Returns:
            dict[str, Any]: A dictionary containing the response of the query.
        """
        variables = {}
        if qrCode:
            variables["qrCode"] = qrCode
        if qrt:
            variables["qrt"] = qrt
        if qrc:
            variables["qrc"] = qrc
        data: dict[str, Any] = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("stateQ", ""), variables, "WatchState")
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchState", "errors": errors})
        return data.get("data", {})

    def getWatchLastLocation(self, wuid: str) -> Dict[str, Any]:
        """
        Get the last location of a watch.

        Args:
            wuid (str): The unique identifier of the watch.

        Returns:
            dict[str, Any]: A dictionary containing the response of the query.
        """
        data: dict[str, Any] = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("locateQ", ""), {"uid": wuid}, "WatchLastLocate")
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchLastLocation", "errors": errors})
        return data.get("data", {})

    def trackWatch(self, wuid: str) -> Dict[str, Any]:
        """
        Track a watch.

        Args:
            wuid (str): The unique identifier of the watch.

        Returns:
            dict[str, Any]: A dictionary containing the response of the query.
        """
        data: dict[str, Any] = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("trackQ", ""), {"uid": wuid}, "TrackWatch")
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "trackWatch", "errors": errors})
        res = data.get("data", {})
        if res.get("trackWatch", {"trackWatch": -1}):
            return res
        return {"trackWatch": -1}

    def getAlarmTime(self, wuid: str) -> Dict[str, Any]:
        """Get the alarm time of a watch.

        Args:
            wuid (str): The unique identifier of the watch.

        Returns:
            dict: A dictionary containing the response of the query.
        """
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("alarmsQ", ""), {"uid": wuid}, "Alarms").get("data", {})

    def getWifi(self, wuid: str) -> Dict[str, Any]:
        """Get the Wi-Fi information of a watch.

        Args:
            wuid (str): The unique identifier of the watch.

        Returns:
            dict: A dictionary containing the response of the query.
        """
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("getWifisQ", ""), {"uid": wuid}, "GetWifis").get("data", {})

    def unReadChatMsgCount(self, wuid: str) -> Dict[str, Any]:
        """
        Get the count of unread chat messages for a watch.

        Args:
            wuid (str): The unique identifier of the watch.

        Returns:
            dict: A dictionary containing the response of the query.
        """
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("unReadChatMsgCountQ", ""), {"uid": wuid}, "UnReadChatMsgCount").get(
            "data", {}
        )

    def safeZones(self, wuid: str) -> Dict[str, Any]:
        """
        Get the safe zones for a watch.

        Args:
            wuid (str): The unique identifier of the watch.

        Returns:
            dict: A dictionary containing the response of the query.
        """
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("safeZonesQ", ""), {"uid": wuid}, "SafeZones").get("data", {})

    def safeZoneGroups(self) -> Dict[str, Any]:
        """
        Get the safe zone groups.

        Returns:
            dict: A dictionary containing the response of the query.
        """
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("safeZoneGroupsQ", ""), {}, "SafeZoneGroups").get("data", {})

    def silentTimes(self, wuid: str) -> Dict[str, Any]:
        """
        Get the silent times for a watch.

        Args:
            wuid (str): The unique identifier of the watch.

        Returns:
            dict: A dictionary containing the response of the query.
        """
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("silentTimesQ", ""), {"uid": wuid}, "SlientTimes").get("data", {})

    def chats(self, wuid: str, offset: int = 0, limit: int = 0, msgId: str = "", asObject=False) -> Dict[str, Any]:
        """
        Get the chat messages for a watch.

        Args:
            wuid (str): The unique identifier of the watch.
            offset (int, optional): The number of messages to skip.
            limit (int, optional): The maximum number of messages to return.
            msgId (str, optional): The message identifier to start from.
            asObject (bool, optional): Return the data as a Chats object if True.

        Returns:
            Union[dict, Chats]: A dictionary containing the response of the query or a Chats object if asObject is True.
        """
        res: dict = self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("chatsQ", ""), {"uid": wuid, "offset": offset, "limit": limit, "msgId": msgId}, "Chats"
        )
        if res.get("errors", None) or res.get("data", None) is None:
            if asObject:
                _LOGGER.error(res.get("errors", {}))
                return Chats.from_dict(res.get("data", {}))
            return {}
        if asObject:
            return Chats.from_dict(res.get("data", {}))
        return res.get("data", {})

    def fetchChatImage(self, wuid: str, msgId: str) -> Dict[str, Any]:
        """
        Fetches a chat image.

        Args:
            wuid (str): The ID of the watch.
            msgId (str): The ID of the message.

        Returns:
            Dict[str, Any]: The data of the image.
        """
        return self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("fetchChatImageQ", ""), {"uid": wuid, "msgId": msgId}, "FetchChatImage"
        ).get("data", {})

    def fetchChatMp3(self, wuid: str, msgId: str) -> Dict[str, Any]:
        """
        Fetches a chat mp3.

        Args:
            wuid (str): The ID of the watch.
            msgId (str): The ID of the message.

        Returns:
            Dict[str, Any]: The data of the mp3.
        """
        return self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("fetchChatMp3Q", ""), {"uid": wuid, "msgId": msgId}, "FetchChatMp3"
        ).get("data", {})

    def fetchChatShortVideo(self, wuid: str, msgId: str) -> Dict[str, Any]:
        """
        Fetches a chat short video.

        Args:
            wuid (str): The ID of the watch.
            msgId (str): The ID of the message.

        Returns:
            Dict[str, Any]: The data of the short video.
        """
        return self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("fetchChatShortVideoQ", ""), {"uid": wuid, "msgId": msgId}, "FetchChatShortVideo"
        ).get("data", {})

    def fetchChatShortVideoCover(self, wuid: str, msgId: str) -> Dict[str, Any]:
        """
        Fetches a chat short video cover.

        Args:
            wuid (str): The ID of the watch.
            msgId (str): The ID of the message.

        Returns:
            Dict[str, Any]: The data of the short video cover.
        """
        return self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("fetchChatShortVideoCoverQ", ""), {"uid": wuid, "msgId": msgId}, "FetchChatShortVideoCover"
        ).get("data", {})

    def fetchChatVoice(self, wuid: str, msgId: str) -> Dict[str, Any]:
        """
        Fetches a chat voice.

        Args:
            wuid (str): The ID of the watch.
            msgId (str): The ID of the message.

        Returns:
            Dict[str, Any]: The data of the voice.
        """
        return self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("fetchChatVoiceQ", ""), {"uid": wuid, "msgId": msgId}, "FetchChatVoice"
        ).get("data", {})

    def watchImei(self, imei: str, qrCode: str, deviceKey: str) -> Dict[str, Any]:
        """
        Retrieve data for a watch with a given IMEI.

        Args:
            imei (str): IMEI of the watch to retrieve data for.
            qrCode (str): QR code associated with the watch.
            deviceKey (str): Key associated with the device.

        Returns:
            Dict[str, Any]: Data for the watch with the given IMEI.
        """
        return self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("imeiQ", ""), {"imei": imei, "qrCode": qrCode, "deviceKey": deviceKey}, "WatchImei"
        ).get("data", {})

    def getWatchLocHistory(self, wuid: str, date: int, tz: str, limit: int) -> Dict[str, Any]:
        """
        Retrieve the location history for a watch with a given WUID.

        Args:
            wuid (str): WUID of the watch to retrieve location history for.
            date (int): Date for the location history (in UNIX timestamp format).
            tz (str): Time zone for the location history.
            limit (int): Maximum number of locations to retrieve.

        Returns:
            Dict[str, Any]: Location history for the watch with the given WUID.
        """
        return self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("locHistoryQ", ""), {"uid": wuid, "date": date, "tz": tz, "limit": limit}, "LocHistory"
        ).get("data", {})

    def watchesDynamic(self) -> Dict[str, Any]:
        """
        Retrieve dynamic data for all watches.

        Returns:
            Dict[str, Any]: Dynamic data for all watches.
        """
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("watchesDynamicQ", ""), {}, "WatchesDynamic").get("data", {})

    def coinHistory(self, wuid: str, start: int, end: int, type: str, offset: int, limit: int) -> Dict[str, Any]:
        """
        Retrieve coin history for a watch with a given WUID.

        Args:
            wuid (str): WUID of the watch to retrieve coin history for.
            start (int): Start of the time range for the coin history (in UNIX timestamp format).
            end (int): End of the time range for the coin history (in UNIX timestamp format).
            type (str): Type of coin history to retrieve.
            offset (int): Offset for the coin history.
            limit (int): Maximum number of coins to retrieve.

        Returns:
            Dict[str, Any]: Coin history for the watch with the given WUID.
        """
        return self.runAuthorizedGqlQuery(
            gq.XCOIN_Q.get("historyQ", ""),
            {"uid": wuid, "start": start, "end": end, "type": type, "offset": offset, "limit": limit},
            "CoinHistory",
        ).get("data", {})

    def reminders(self, wuid: str) -> Dict[str, Any]:
        """
        Get reminder data for a given user.

        Args:
            wuid (str): The user id for which the reminder data is to be retrieved.

        Returns:
            Dict[str, Any]: The reminder data for the given user.
        """
        return self.runAuthorizedGqlQuery(gq.XMOVE_Q.get("remindersQ", ""), {"uid": wuid}, "Reminders").get("data", {})

    def groups(self, isCampaign: bool) -> Dict[str, Any]:
        """
        Get card group data.

        Args:
            isCampaign (bool): Whether to retrieve card group data for campaigns or not.

        Returns:
            Dict[str, Any]: The card group data.
        """
        return self.runAuthorizedGqlQuery(gq.CARD_Q.get("groupsQ", ""), {"isCampaign": isCampaign}, "CardGroups").get(
            "data", {}
        )

    def dynamic(self) -> Dict[str, Any]:
        """
        Get dynamic card data.

        Returns:
            Dict[str, Any]: The dynamic card data.
        """
        return self.runAuthorizedGqlQuery(gq.CARD_Q.get("dynamicQ", ""), {}, "DynamicCards").get("data", {})

    def staticCard(self) -> Dict[str, Any]:
        """
        Get dynamic card data.

        Returns:
            Dict[str, Any]: The dynamic card data.
        """
        return self.runAuthorizedGqlQuery(gq.CARD_Q.get("staticQ", ""), {}, "StaticCard").get("data", {})

    def familyInfo(self, wuid: str, watchId: str, tz: str, date: int) -> Dict[str, Any]:
        """
        Get family information for a given user.

        Args:
            wuid (str): The user id for which the family information is to be retrieved.
            watchId (str): The watch id associated with the user.
            tz (str): The timezone of the user.
            date (int): The date for which the family information is to be retrieved.

        Returns:
            Dict[str, Any]: The family information for the given user.
        """
        return self.runAuthorizedGqlQuery(
            gq.FAMILY_Q.get("infoQ", ""), {"uid": wuid, "watchId": watchId, "tz": tz, "date": date}, "FamilyInfo"
        ).get("data", {})

    def getMyTotalInfo(
        self, wuid: str, tz: str, date: int, start: int, end: int, type: str, offset: int, limit: int
    ) -> Dict[str, Any]:
        """
        Retrieve total information for the given user.

        Args:
            wuid (str): The user's unique identifier.
            tz (str): Timezone identifier.
            date (int): Date as an integer.
            start (int): Start time as an integer.
            end (int): End time as an integer.
            type (str): Type of information to retrieve.
            offset (int): Offset for the information to retrieve.
            limit (int): Limit for the information to retrieve.

        Returns:
            dict: Information retrieved for the given user, including the data field.
        """
        return self.runAuthorizedGqlQuery(
            gq.MYINFO_Q.get("getMyTotalInfoQ", ""),
            {"uid": wuid, "tz": tz, "date": date, "start": start, "end": end, "type": type, "offset": offset, "limit": limit},
            "GetMyTotalInfo",
        ).get("data", {})

    def myInfoWithCoinHistory(
        self, wuid: str, start: int, end: int, tz: str, type: str, offset: int, limit: int
    ) -> Dict[str, Any]:
        """
        Retrieve information for the given user with coin history.

        Args:
            wuid (str): The user's unique identifier.
            start (int): Start time as an integer.
            end (int): End time as an integer.
            tz (str): Timezone identifier.
            type (str): Type of information to retrieve.
            offset (int): Offset for the information to retrieve.
            limit (int): Limit for the information to retrieve.

        Returns:
            dict: Information retrieved for the given user with coin history, including the data field.
        """
        return self.runAuthorizedGqlQuery(
            gq.MYINFO_Q.get("coinHistoryQ", ""),
            {"uid": wuid, "start": start, "end": end, "tz": tz, "type": type, "offset": offset, "limit": limit},
            "MyInfoWithCoinHistory",
        ).get("data", {})

    def getMyInfo(self) -> Dict[str, Any]:
        """
        Retrieve information for the logged in user.

        Returns:
            dict: Information retrieved for the logged in user, including the data field.
        """
        # Profil from login Account
        return self.runAuthorizedGqlQuery(gq.MYINFO_Q.get("readQ", ""), {}, "ReadMyInfo").get("data", {})

    def readCampaignProfile(self, wuid: str) -> Dict[str, Any]:
        """
        Retrieve campaign profile for the given user.

        Args:
            wuid (str): The user's unique identifier.

        Returns:
            dict: Campaign profile information retrieved for the given user, including the data field.
        """
        return self.runAuthorizedGqlQuery(
            gq.MYINFO_Q.get("readCampaignProfileQ", ""),
            {"uid": wuid},
        ).get("data", {})

    def getReviewStatus(self, wuid: str) -> Dict[str, Any]:
        """
        Get the review status for a given user id.

        Args:
            wuid (str): The user id for which the review status is to be retrieved.

        Returns:
            Dict[str, Any]: The review status data in dictionary format.
        """
        return self.runAuthorizedGqlQuery(gq.REVIEW_Q.get("getStatusQ", ""), {"uid": wuid}, "GetReviewStatus").get("data", {})

    def getWatchUserSteps(self, wuid: str, tz: str, date: int) -> Dict[str, Any]:
        """
        Get the step count data for a given user id.

        Args:
            wuid (str): The user id for which the step count data is to be retrieved.
            tz (str): The time zone of the user.
            date (int): The date for which the step count data is to be retrieved.

        Returns:
            Dict[str, Any]: The step count data in dictionary format.
        """
        data: dict[str, Any] = self.runAuthorizedGqlQuery(
            gq.STEP_Q.get("userQ", ""), {"uid": wuid, "tz": tz, "date": date}, "UserSteps"
        )
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchUserSteps", "errors": errors})
        return data.get("data", {})

    def countries(self) -> Dict[str, Any]:
        """
        Get the list of countries supported by the service.

        Returns:
            Dict[str, Any]: The list of countries in dictionary format.
        """
        return self.runAuthorizedGqlQuery(gq.UTILS_Q.get("countriesQ", ""), {}, "Countries").get("data", {})

    def avatars(self, id: str) -> Dict[str, Any]:
        """
        Get the avatar data for a given id.

        Args:
            id (str): The id for which the avatar data is to be retrieved.

        Returns:
            Dict[str, Any]: The avatar data in dictionary format.
        """
        return self.runAuthorizedGqlQuery(gq.CAMPAIGN_Q.get("avatarsQ", ""), {"id": id}, "Avatars").get("data", {})

    def getFollowRequestWatchCount(self) -> Dict[str, Any]:
        """
        Get the follow request and watch count data.

        Returns:
            Dict[str, Any]: The follow request and watch count data in dictionary format.
        """
        return self.runAuthorizedGqlQuery(
            gq.CAMPAIGN_Q.get("followRequestWatchCountQ", ""), {}, "FollowRequestWatchCount"
        ).get("data", {})

    def campaigns(self, id: str, categoryId: str) -> Dict[str, Any]:
        """
        Get the campaigns for the given id and category id.

        Args:
            id (str): The id of the campaign.
            categoryId (str): The id of the category.

        Returns:
            Dict[str, Any]: The data returned by the query, in the form of a dictionary.
        """
        return self.runAuthorizedGqlQuery(
            gq.CAMPAIGN_Q.get("campaignsQ", ""), {"id": id, "categoryId": categoryId}, "Campaigns"
        ).get("data", {})

    def isSubscribed(self, id: str, wuid: str) -> Dict[str, Any]:
        """
        Check if the user with the given wuid is subscribed to the campaign with the given id.

        Args:
            id (str): The id of the campaign.
            wuid (str): The wuid of the user.

        Returns:
            Dict[str, Any]: The data returned by the query, in the form of a dictionary.
        """
        return self.runAuthorizedGqlQuery(
            gq.CAMPAIGN_Q.get("isSubscribedQ", ""), {"id": id, "uid": wuid}, "IsSubscribedCampaign"
        ).get("data", {})

    def subscribed(self, wuid: str, needDetail: bool) -> Dict[str, Any]:
        """
        Get the campaigns that the user with the given wuid is subscribed to.

        Args:
            wuid (str): The wuid of the user.
            needDetail (bool): Indicates whether detailed information is needed.

        Returns:
            Dict[str, Any]: The data returned by the query, in the form of a dictionary.
        """
        return self.runAuthorizedGqlQuery(
            gq.CAMPAIGN_Q.get("subscribedQ", ""), {"uid": wuid, "needDetail": needDetail}, "SubscribedCampaign"
        ).get("data", {})

    def ranks(self, campaignId: str) -> Dict[str, Any]:
        """
        Get the ranks for the campaign with the given id.

        Args:
            campaignId (str): The id of the campaign.

        Returns:
            Dict[str, Any]: The data returned by the query, in the form of a dictionary.
        """
        return self.runAuthorizedGqlQuery(gq.CAMPAIGN_Q.get("ranksQ", ""), {"campaignId": campaignId}, "Ranks").get("data", {})

    def conv360IDToO2OID(self, qid: str, deviceId: str) -> Dict[str, Any]:
        """
        Convert the 360 ID to the O2O ID.

        Args:
            qid (str): The 360 ID.
            deviceId (str): The device ID.

        Returns:
            Dict[str, Any]: The data returned by the query, in the form of a dictionary.
        """
        return self.runAuthorizedGqlQuery(
            gq.QUERY.get("conv360IDToO2OIDQ", ""), {"qid": qid, "deviceId": deviceId}, "Conv360IDToO2OID"
        ).get("data", {})

    def getAppVersion(self) -> Dict[str, Any]:
        """
        Returns the data for the GetAppVersion query.

        Returns:
            Dict[str, Any]: The data for the GetAppVersion query.
        """
        return self.runAuthorizedGqlQuery(gq.QUERY.get("getAppVersionQ", ""), {}, "GetAppVersion").get("data", {})

    def watchGroups(self, id: str = "") -> Dict[str, Any]:
        """
        Returns the data for the WatchGroups query.

        Args:
            id (str, optional): The id of the watch group. Defaults to "".

        Returns:
            Dict[str, Any]: The data for the WatchGroups query.
        """
        return self.runAuthorizedGqlQuery(gq.WATCHGROUP_Q.get("watchGroupsQ", ""), {"id": id}, "WatchGroups").get("data", {})

    def getStartTrackingWatch(self, wuid: str) -> Dict[str, Any]:
        """
        Returns the data for the StartTrackingWatch query.

        Args:
            wuid (str): The wuid of the user.

        Returns:
            Dict[str, Any]: The data for the StartTrackingWatch query.
        """
        data = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("startTrackingWatchQ", ""), {"uid": wuid}, "StartTrackingWatch")
        errors: list[dict[str, str]] = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getStartTrackingWatch", "error": errors})
        return data.get("data", {})

    def getEndTrackingWatch(self, wuid: str) -> Dict[str, Any]:
        """
        Returns the data for the EndTrackingWatch query.

        Args:
            wuid (str): The wuid of the user.

        Returns:
            Dict[str, Any]: The data for the EndTrackingWatch query.
        """
        data = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("endTrackingWatchQ", ""), {"uid": wuid}, "EndTrackingWatch")
        errors: list[dict[str, str]] = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getEndTrackingWatch", "error": errors})
        return data.get("data", {})

    def checkEmailOrPhoneExist(
        self, type: UserContactType, email: str = "", countryCode: str = "", phoneNumber: str = ""
    ) -> Dict[str, bool]:
        """
        Check if email or phone number exist.

        Args:
            type (UserContactType): The type of contact to check (email or phone number).
            email (str, optional): The email to check.
            countryCode (str, optional): The country code for the phone number.
            phoneNumber (str, optional): The phone number to check.

        Returns:
            Dict[str, bool]: A dictionary containing the result of the existence check.
        """
        data = self.runAuthorizedGqlQuery(
            gq.UTILS_Q.get("checkEmailOrPhoneExistQ", ""),
            {"type": type.value, "email": email, "countryCode": countryCode, "phoneNumber": phoneNumber},
            "CheckEmailOrPhoneExist",
        )
        return data.get("data", {})

    ########## SECTION QUERY end ##########

    ########## SECTION MUTATION start ##########

    def sendText(self, wuid: str, text: str) -> bool:
        """
        Sends a chat text to a specified user.

        Args:
            wuid (str): The ID of the user.
            text (str): The text to send.

        Returns:
            bool: Whether the text was sent successfully.
        """
        if (
            self.runAuthorizedGqlQuery(gm.WATCH_M.get("sendChatTextM", ""), {"uid": wuid, "text": text}, "SendChatText").get(
                "data", {}
            )["sendChatText"]
            is not None
        ):
            return True
        return False

    def addStep(self, stepCount: int) -> Dict[str, Any]:
        """
        Adds a specified number of steps.

        Args:
            stepCount (int): The number of steps to add.

        Returns:
            dict: A dictionary containing the data from the response.
        """
        return self.runAuthorizedGqlQuery(gm.STEP_M.get("addM", ""), {"stepCount": stepCount}, "AddStep").get("data", {})

    def shutdown(self, wuid: str) -> bool:
        """
        Shuts down the system for a specified user.

        Args:
            wuid (str): The ID of the user.

        Returns:
            bool: Whether the system was shut down successfully.
        """
        return self.isAdmin(wuid, gm.WATCH_M.get("shutdownM", ""), {"uid": wuid}, "ShutDown")

    def reboot(self, wuid: str) -> bool:
        """
        Reboots the system for a specified user.

        Args:
            wuid (str): The ID of the user.

        Returns:
            bool: Whether the system was rebooted successfully.
        """
        return self.isAdmin(wuid, gm.WATCH_M.get("rebootM", ""), {"uid": wuid}, "reboot")

    def modifyAlert(self, id: str, yesOrNo: str) -> Dict[str, Any]:
        """
        Modifies an alert.

        Args:
            id (str): The ID of the alert.
            yesOrNo (str): The value to set for the alert.

        Returns:
            dict: A dictionary containing the data from the response.
        """
        return self.runAuthorizedGqlQuery(gm.WATCH_M.get("modifyAlertM", ""), {"uid": id, "remind": yesOrNo}, "modifyAlert")

    def setEnableSilentTime(self, silent_id: str, status: str = NormalStatus.ENABLE.value) -> Dict[str, Any]:
        """
        Sets the silent time for a specified user.

        Args:
            silent_id (str): The ID of the silent time.
            status (str, optional): The status to set for the silent time. Defaults to `NormalStatus.ENABLE.value`.

        Returns:
            dict: A dictionary containing the data from the response.
        """
        return self.runAuthorizedGqlQuery(
            gm.WATCH_M.get("setEnableSlientTimeM", ""), {"silentId": silent_id, "status": status}, "SetEnableSlientTime"
        ).get("data", {})

    def setEnableAlarmTime(self, alarm_id: str, status: str = NormalStatus.ENABLE.value) -> Dict[str, Any]:
        """
        Enable or disable alarm time.

        Args:
            alarm_id (str): ID of the alarm to modify.
            status (str, optional): New status for the alarm, either `NormalStatus.ENABLE.value` or `NormalStatus.DISABLE.value`. Defaults to `NormalStatus.ENABLE.value`.

        Returns:
            Dict[str, Any]: Dictionary containing the response data.
        """
        return self.runAuthorizedGqlQuery(
            gm.WATCH_M.get("modifyAlarmM", ""), {"alarmId": alarm_id, "status": status}, "ModifyAlarm"
        ).get("data", {})

    def setReadChatMsg(self, wuid: str, msgId: str, id: str) -> Dict[str, Any]:
        """
        Mark a chat message as read.

        Args:
            wuid (str): ID of the user who sent the chat message.
            msgId (str): ID of the chat message to mark as read.
            id (str): ID of the message in the chat history.

        Returns:
            Dict[str, Any]: Dictionary containing the response data.
        """
        return self.runAuthorizedGqlQuery(
            gm.WATCH_M.get("setReadChatMsgM", ""), {"uid": wuid, "msgId": msgId, "id": id}, "setReadChatMsg"
        ).get("data", {})

    def submitIncorrectLocationData(self, wuid: str, lat: str, lng: str, timestamp: str) -> Dict[str, Any]:
        """
        Submit incorrect location data.

        Args:
            wuid (str): ID of the user.
            lat (str): Latitude of the location.
            lng (str): Longitude of the location.
            timestamp (str): Timestamp of the location.

        Returns:
            Dict[str, Any]: Dictionary containing the response data.
        """
        return self.runAuthorizedGqlQuery(
            gm.WATCH_M.get("submitIncorrectLocationDataM", ""),
            {"uid": wuid, "lat": lat, "lng": lng, "timestamp": timestamp},
            "SubmitIncorrectLocationData",
        ).get("data", {})

    def modifyContact(self, contactId: str, isAdmin: bool, contactName: str = "", fileId: str = "") -> Dict[str, Any]:
        """
        Modify a contact.

        Args:
            contactId (str): ID of the contact to modify.
            isAdmin (bool): Whether the contact should be an admin or not.
            contactName (str, optional): New name for the contact. Defaults to "".
            fileId (str, optional): New profile picture for the contact. Defaults to "".

        Returns:
            Dict[str, Any]: Dictionary containing the response data.
        """
        return self.runAuthorizedGqlQuery(
            gm.WATCH_M.get("modifyContactM", ""),
            {"contactId": contactId, "contactName": contactName, "fileId": fileId, "isAdmin": isAdmin},
        )

    def issueEmailOrPhoneCode(
        self,
        purpose: EmailAndPhoneVerificationTypeV2 = EmailAndPhoneVerificationTypeV2.UNKNOWN__,
        type: UserContactType = UserContactType.UNKNOWN__,
        email: str = "",
        phoneNumber: str = "",
        countryCode: str = "",
        previousToken: str = "",
        lang: str = "",
    ) -> Dict[str, Any]:
        """Issue a code for email or phone verification.

        Args:
            purpose (EmailAndPhoneVerificationTypeV2, optional): Purpose of the code. Default is EmailAndPhoneVerificationTypeV2.UNKNOWN__.
            type (UserContactType, optional): Type of user contact. Default is UserContactType.UNKNOWN__.
            email (str, optional): Email address. Default is an empty string.
            phoneNumber (str, optional): Phone number. Default is an empty string.
            countryCode (str, optional): Country code. Default is an empty string.
            previousToken (str, optional): Previous token. Default is an empty string.
            lang (str, optional): Language. Default is an empty string.

        Returns:
            Dict[str, Any]: Result of the query.
        """
        return self.runAuthorizedGqlQuery(
            gm.SIGN_M.get("issueEmailOrPhoneCodeM", ""),
            {
                "purpose": purpose.value,
                "type": type.value,
                "email": email,
                "phoneNumber": phoneNumber,
                "countryCode": countryCode,
                "previousToken": previousToken,
                "lang": lang,
            },
            "IssueEmailOrPhoneCode",
        )

    def signUpWithEmailAndPhoneV2(
        self,
        countryPhoneCode: str = "",
        phoneNumber: str = "",
        password: str = "",
        name: str = "",
        emailAddress: str = "",
        emailConsent: int = -1,
    ) -> Dict[str, Any]:
        """Sign up with email and phone, version 2.

        Args:
            countryPhoneCode (str, optional): Country phone code. Default is an empty string.
            phoneNumber (str, optional): Phone number. Default is an empty string.
            password (str, optional): Password. Default is an empty string.
            name (str, optional): Name. Default is an empty string.
            emailAddress (str, optional): Email address. Default is an empty string.
            emailConsent (int, optional): Email consent. Default is -1.

        Returns:
            Dict[str, Any]: Result of the query.
        """
        return self.runAuthorizedGqlQuery(
            gm.SIGN_M.get("signUpWithEmailAndPhoneV2M", ""),
            {
                "countryPhoneCode": countryPhoneCode,
                "phoneNumber": phoneNumber,
                "password": password,
                "name": name,
                "emailAddress": emailAddress,
                "emailConsent": emailConsent,
            },
            "SignUpWithEmailAndPhoneV2",
        )

    def verifyCaptcha(self, captchaString: str = "", type: str = "") -> Dict[str, Any]:
        """
        Verify a given captcha string.

        Args:
            captchaString (str, optional): The captcha string to verify.
            type (str, optional): The type of the captcha to verify.

        Returns:
            Dict[str, Any]: The result of the `verifyCaptcha` query.
        """
        return self.runAuthorizedGqlQuery(
            gm.SIGN_M.get("verifyCaptchaM", ""), {"captchaString": captchaString, "type": type}, "verifyCaptcha"
        )

    def verifyEmailOrPhoneCode(
        self,
        type: UserContactType = UserContactType.UNKNOWN__,
        email: str = "",
        phoneNumber: str = "",
        countryCode: str = "",
        verifyCode: str = "",
        verificationToken: str = "",
    ) -> Dict[str, Any]:
        """
        Verify a given email or phone code.

        Args:
            type (UserContactType, optional): The type of the email or phone to verify.
            email (str, optional): The email to verify.
            phoneNumber (str, optional): The phone number to verify.
            countryCode (str, optional): The country code of the phone number to verify.
            verifyCode (str, optional): The code to verify.
            verificationToken (str, optional): The verification token to use.

        Returns:
            Dict[str, Any]: The result of the `verifyEmailOrPhoneCode` query.
        """
        return self.runAuthorizedGqlQuery(
            gm.SIGN_M.get("verifyEmailOrPhoneCodeM", ""),
            {
                "type": type.value,
                "email": email,
                "phoneNumber": phoneNumber,
                "countryCode": countryCode,
                "verifyCode": verifyCode,
                "verificationToken": verificationToken,
            },
            "verifyEmailOrPhoneCode",
        )

    async def deleteMessageFromApp(self, wuid: str, msgId: str) -> Dict[str, Any]:
        """
        Delete a message from the app.

        Args:
            wuid (str): The WUID of the message to delete.
            msgId (str): The ID of the message to delete.

        Returns:
            Dict[str, Any]: The result of the `deleteChatMessage` query.
        """
        return self.runAuthorizedGqlQuery(
            gm.WATCH_M.get("deleteChatMessageM", ""), {"uid": wuid, "msgId": msgId}, "DeleteChatMessage"
        ).get("data", {})

    ########## SECTION MUTATION end ##########
