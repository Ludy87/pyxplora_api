"""GQL Handler."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from . import gql_mutations as gm, gql_queries as gq
from .const import API_KEY, API_SECRET, ENDPOINT
from .exception_classes import ErrorMSG, HandlerException, LoginError, NoAdminError
from .graphql_client import GraphqlClient
from .handler_gql import HandlerGQL
from .model import Chats, ChatsNew
from .status import EmailAndPhoneVerificationTypeV2, NormalStatus, UserContactType

_LOGGER = logging.getLogger(__name__)


class GQLHandler(HandlerGQL):
    def __init__(
        self,
        countryPhoneNumber: str,
        phoneNumber: str,
        password: str,
        userLang: str,
        timeZone: str,
        email: str | None = None,
        signup: bool = True,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._session = session
        self.refreshToken = None
        super().__init__(countryPhoneNumber, phoneNumber, password, userLang, timeZone, email, signup)

    async def runGqlQuery_a(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        operation_name: str | None = None,
    ) -> dict[str, Any]:
        if query is None:
            raise HandlerException("GraphQL guery string MUST NOT be empty!")
        # Add Xplora® API headers
        requestHeaders = self.getRequestHeaders("application/json; charset=UTF-8")
        # create GQLClient
        gqlClient = GraphqlClient(endpoint=ENDPOINT, headers=requestHeaders)
        # execute QUERY|MUTATION
        if self._session:
            data: dict[str, Any] = await gqlClient.ha_execute_async(
                query=query, variables=variables, operation_name=operation_name, session=self._session
            )
        else:
            data: dict[str, Any] = await gqlClient.execute_async(
                query=query, variables=variables, operation_name=operation_name
            )
        return data

    async def runAuthorizedGqlQuery_a(
        self, query: str, variables: dict[str, Any] | None = None, operation_name: str | None = None
    ) -> dict[str, Any]:
        # Run GraphQL query and return
        return await self.runGqlQuery_a(query, variables, operation_name)

    async def login_a(self, key, sec) -> tuple[dict[str, Any], Any]:
        if key and sec:
            self._API_KEY = key
            self._API_SECRET = sec
        dataAll = await self.runGqlQuery_a(
            gm.SIGN_M.get("signInWithEmailOrPhoneM", ""), self.variables, "signInWithEmailOrPhone"
        )
        if dataAll is None:
            return
        errors = dataAll.get("errors", None)
        if errors:
            self.errors.append({"function": "login", "errors": errors})
        data = dataAll.get("data", {})
        signIn: dict[str, Any] | None = data.get("signInWithEmailOrPhone", None)
        if signIn is None:
            error_message = dataAll.get("errors", [{"message": ""}])[0].get("message", "")
            if error_message:
                raise LoginError(f"Login error: {error_message}")
            raise LoginError("The server is not responding, please wait a moment and try again.")

        self.issueToken = signIn
        self.refreshToken = self.issueToken.get("refreshToken", None)
        self.sessionId = self.issueToken.get("id")
        self.userId = self.issueToken.get("user", {"id": None}).get("id", None)
        self.accessToken = self.issueToken.get("token", None)
        w360: dict = self.issueToken.get("w360", None)
        if w360:
            if w360.get("token") and w360.get("secret"):
                self._API_KEY = w360.get("token", API_KEY)
                self._API_SECRET = w360.get("secret", API_SECRET)

        return self.issueToken, self.refreshToken

    async def isAdmin_a(self, wuid: str, query: str, variables: dict[str, Any], key: str) -> bool:
        contacts: dict[str, Any] = await self.getWatchUserContacts_a(wuid)
        for contact in contacts["contacts"]["contacts"]:
            try:
                id = contact["contactUser"]["id"]
            except (KeyError, TypeError):
                id = None
            if self.userId == id:
                if contact["guardianType"] == "FIRST":
                    data: dict[str, Any] = (await self.runGqlQuery_a(query, variables, key)).get("data", {})
                    for k in data:
                        if k.upper() == key.upper():
                            return data.get(k, False)
        raise NoAdminError()

    ########## SECTION QUERY start ##########

    async def askWatchLocate_a(self, wuid: str) -> dict[str, Any]:
        data: dict[str, Any] = await self.runGqlQuery_a(gq.WATCH_Q.get("askLocateQ", ""), {"uid": wuid}, "AskWatchLocate")
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "askWatchLocate", "errors": errors})
        res: dict[str, Any] = data.get("data", {})
        if res.get("askWatchLocate", None) is not None:
            return res
        return {"askWatchLocate": False}

    async def getWatchUserContacts_a(self, wuid: str) -> dict[str, Any]:
        # Contacts from ownUser
        data: dict[str, Any] = await self.runGqlQuery_a(gq.WATCH_Q.get("contactsQ", ""), {"uid": wuid}, "Contacts")
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchUserContacts", "errors": errors})
        return data.get("data", {})

    async def getWatches_a(self, wuid: str) -> dict[str, Any]:
        data: dict[str, Any] = await self.runGqlQuery_a(gq.WATCH_Q.get("watchesQ", ""), {"uid": wuid}, "Watches")
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatches", "errors": errors})
        return data.get("data", {})

    async def getSWInfo_a(self, qrCode: str) -> dict[str, Any]:
        data: dict[str, Any] = await self.runGqlQuery_a(
            gq.WATCH_Q.get("checkByQrCodeQ", ""), {"qrCode": qrCode}, "CheckWatchByQrCode"
        )
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getSWInfo", "errors": errors})
        return data.get("data", {})

    async def getWatchState_a(self, qrCode: str, qrt: str = "", qrc: str = "") -> dict[str, Any]:
        variables = {}
        if qrCode:
            variables["qrCode"] = qrCode
        if qrt:
            variables["qrt"] = qrt
        if qrc:
            variables["qrc"] = qrc
        data: dict[str, Any] = await self.runGqlQuery_a(gq.WATCH_Q.get("stateQ", ""), variables, "WatchState")
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchState", "errors": errors})
        return data.get("data", {})

    async def getWatchLastLocation_a(self, wuid: str) -> dict[str, Any]:
        data: dict[str, Any] = await self.runGqlQuery_a(gq.WATCH_Q.get("locateQ", ""), {"uid": wuid}, "WatchLastLocate")
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchLastLocation", "errors": errors})
            error_msg = data.get("errors", [{"code": "E", "message": "E"}])[0].get("message", "E")
            if error_msg == ErrorMSG.AUTH_FAIL.value:
                _LOGGER.error(error_msg)
                return errors[0]
        return data.get("data", {})

    async def trackWatch_a(self, wuid: str) -> dict[str, Any]:
        # tracking time - seconds
        data: dict[str, Any] = await self.runGqlQuery_a(gq.WATCH_Q.get("trackQ", ""), {"uid": wuid}, "TrackWatch")
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "trackWatch", "errors": errors})
        res = data.get("data", {})
        if res.get("trackWatch", {"trackWatch": -1}):
            return res
        return {"trackWatch": -1}

    async def getAlarmTime_a(self, wuid: str) -> dict[str, Any]:
        return (await self.runGqlQuery_a(gq.WATCH_Q.get("alarmsQ", ""), {"uid": wuid}, "Alarms")).get("data", {})

    async def getWifi_a(self, wuid: str) -> dict[str, Any]:
        # without function?
        return (await self.runGqlQuery_a(gq.WATCH_Q.get("getWifisQ", ""), {"uid": wuid}, "GetWifis")).get("data", {})

    async def unReadChatMsgCount_a(self, wuid: str) -> dict[str, Any]:
        return (await self.runGqlQuery_a(gq.WATCH_Q.get("unReadChatMsgCountQ", ""), {"uid": wuid}, "UnReadChatMsgCount")).get(
            "data", {}
        )

    async def safeZones_a(self, wuid: str) -> dict[str, Any]:
        return (await self.runGqlQuery_a(gq.WATCH_Q.get("safeZonesQ", ""), {"uid": wuid}, "SafeZones")).get("data", {})

    async def safeZoneGroups_a(self) -> dict[str, Any]:
        return (await self.runGqlQuery_a(gq.WATCH_Q.get("safeZoneGroupsQ", ""), {}, "SafeZoneGroups")).get("data", {})

    async def silentTimes_a(self, wuid: str) -> dict[str, Any]:
        return (await self.runGqlQuery_a(gq.WATCH_Q.get("silentTimesQ", ""), {"uid": wuid}, "SlientTimes")).get("data", {})

    async def chats_a(
        self, wuid: str, offset: int = 0, limit: int = 0, msgId: str = "", asObject=False
    ) -> dict[str, Any] | Chats | ChatsNew | str | None:
        # ownUser id
        res: dict = await self.runGqlQuery_a(
            gq.WATCH_Q.get("chatsQ", ""), {"uid": wuid, "offset": offset, "limit": limit, "msgId": msgId}, "Chats"
        )
        if res.get("errors", None) or res.get("data", None) is None:
            if asObject:
                _LOGGER.error(res.get("errors", None))
                return Chats.from_dict(res.get("data", {}))
            return {}
        if asObject:
            return Chats.from_dict(res.get("data", {}))
        return res.get("data", {})

    async def fetchChatImage_a(self, wuid: str, msgId: str) -> dict[str, Any]:
        return (
            await self.runGqlQuery_a(gq.WATCH_Q.get("fetchChatImageQ", ""), {"uid": wuid, "msgId": msgId}, "FetchChatImage")
        ).get("data", {})

    async def fetchChatMp3_a(self, wuid: str, msgId: str) -> dict[str, Any]:
        return (
            await self.runGqlQuery_a(gq.WATCH_Q.get("fetchChatMp3Q", ""), {"uid": wuid, "msgId": msgId}, "FetchChatMp3")
        ).get("data", {})

    async def fetchChatShortVideo_a(self, wuid: str, msgId: str) -> dict[str, Any]:
        return (
            await self.runGqlQuery_a(
                gq.WATCH_Q.get("fetchChatShortVideoQ", ""), {"uid": wuid, "msgId": msgId}, "FetchChatShortVideo"
            )
        ).get("data", {})

    async def fetchChatShortVideoCover_a(self, wuid: str, msgId: str) -> dict[str, Any]:
        return (
            await self.runGqlQuery_a(
                gq.WATCH_Q.get("fetchChatShortVideoCoverQ", ""), {"uid": wuid, "msgId": msgId}, "FetchChatShortVideoCover"
            )
        ).get("data", {})

    async def fetchChatVoice_a(self, wuid: str, msgId: str) -> dict[str, Any]:
        return (
            await self.runGqlQuery_a(gq.WATCH_Q.get("fetchChatVoiceQ", ""), {"uid": wuid, "msgId": msgId}, "FetchChatVoice")
        ).get("data", {})

    async def watchImei_a(self, imei: str, qrCode: str, deviceKey: str) -> dict[str, Any]:
        return (
            await self.runGqlQuery_a(
                gq.WATCH_Q.get("imeiQ", ""), {"imei": imei, "qrCode": qrCode, "deviceKey": deviceKey}, "WatchImei"
            )
        ).get("data", {})

    async def getWatchLocHistory_a(
        self, wuid: str, date: int | None = None, tz: str | None = None, limit: int = 1
    ) -> dict[str, Any]:
        return (
            await self.runGqlQuery_a(
                gq.WATCH_Q.get("locHistoryQ", ""), {"uid": wuid, "date": date, "tz": tz, "limit": limit}, "LocHistory"
            )
        ).get("data", {})

    async def watchesDynamic_a(self) -> dict[str, Any]:
        return (await self.runGqlQuery_a(gq.WATCH_Q.get("watchesDynamicQ", ""), {}, "WatchesDynamic")).get("data", {})

    async def coinHistory_a(self, wuid: str, start: int, end: int, _type: str, offset: int, limit: int) -> dict[str, Any]:
        return (
            await self.runGqlQuery_a(
                gq.XCOIN_Q.get("historyQ", ""),
                {"uid": wuid, "start": start, "end": end, "type": _type, "offset": offset, "limit": limit},
                "CoinHistory",
            )
        ).get("data", {})

    async def reminders_a(self, wuid: str) -> dict[str, Any]:
        return (await self.runGqlQuery_a(gq.XMOVE_Q.get("remindersQ", ""), {"uid": wuid}, "Reminders")).get("data", {})

    async def groups_a(self, isCampaign: bool) -> dict[str, Any]:
        return (await self.runGqlQuery_a(gq.CARD_Q.get("groupsQ", ""), {"isCampaign": isCampaign}, "CardGroups")).get(
            "data", {}
        )

    async def dynamic_a(self) -> dict[str, Any]:
        return (await self.runGqlQuery_a(gq.CARD_Q.get("dynamicQ", ""), {}, "DynamicCards")).get("data", {})

    async def staticCard_a(self) -> dict[str, Any]:
        return (await self.runGqlQuery_a(gq.CARD_Q.get("staticQ", ""), {}, "StaticCard")).get("data", {})

    async def familyInfo_a(self, wuid: str, watchId: str, tz: str, date: int) -> dict[str, Any]:
        return (
            await self.runGqlQuery_a(
                gq.FAMILY_Q.get("infoQ", ""), {"uid": wuid, "watchId": watchId, "tz": tz, "date": date}, "FamilyInfo"
            )
        ).get("data", {})

    async def getMyTotalInfo_a(
        self, wuid: str, tz: str, date: int, start: int, end: int, _type: str, offset: int, limit: int
    ) -> dict[str, Any]:
        return (
            await self.runGqlQuery_a(
                gq.MYINFO_Q.get("getMyTotalInfoQ", ""),
                {
                    "uid": wuid,
                    "tz": tz,
                    "date": date,
                    "start": start,
                    "end": end,
                    "type": _type,
                    "offset": offset,
                    "limit": limit,
                },
                "GetMyTotalInfo",
            )
        ).get("data", {})

    async def myInfoWithCoinHistory_a(
        self, wuid: str, start: int, end: int, tz: str, _type: str, offset: int, limit: int
    ) -> dict[str, Any]:
        return (
            await self.runGqlQuery_a(
                gq.MYINFO_Q.get("myInfoWithCoinHistoryQ", ""),
                {"uid": wuid, "start": start, "end": end, "tz": tz, "type": _type, "offset": offset, "limit": limit},
                "MyInfoWithCoinHistory",
            )
        ).get("data", {})

    async def getMyInfo_a(self) -> dict[str, Any]:
        # Profil from login Account
        return (await self.runGqlQuery_a(gq.MYINFO_Q.get("readQ", ""), {}, "ReadMyInfo")).get("data", {})

    async def readCampaignProfile_a(self, wuid: str) -> dict[str, Any]:
        return (
            await self.runGqlQuery_a(
                gq.MYINFO_Q.get("readCampaignProfileQ", ""),
                {"uid": wuid},
            )
        ).get("data", {})

    async def getReviewStatus_a(self, wuid: str) -> dict[str, Any]:
        return (await self.runGqlQuery_a(gq.REVIEW_Q.get("getStatusQ", ""), {"uid": wuid}, "GetReviewStatus")).get("data", {})

    async def getWatchUserSteps_a(self, wuid: str, tz: str, date: int) -> dict[str, Any]:
        data: dict[str, Any] = await self.runGqlQuery_a(
            gq.STEP_Q.get("userQ", ""), {"uid": wuid, "tz": tz, "date": date}, "UserSteps"
        )
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchUserSteps", "errors": errors})
        return data.get("data", {})

    async def countries_a(self) -> dict[str, Any]:
        # Country Support
        return (await self.runGqlQuery_a(gq.UTILS_Q.get("countriesQ", ""), {}, "Countries")).get("data", {})

    async def avatars_a(self, _id: str) -> dict[str, Any]:
        return (await self.runGqlQuery_a(gq.CAMPAIGN_Q.get("avatarsQ", ""), {"id": _id}, "Avatars")).get("data", {})

    async def getFollowRequestWatchCount_a(self) -> dict[str, Any]:
        return (
            await self.runGqlQuery_a(gq.CAMPAIGN_Q.get("followRequestWatchCountQ", ""), {}, "FollowRequestWatchCount")
        ).get("data", {})

    async def campaigns_a(self, _id: str, categoryId: str) -> dict[str, Any]:
        return (
            await self.runGqlQuery_a(gq.CAMPAIGN_Q.get("campaignsQ", ""), {"id": _id, "categoryId": categoryId}, "Campaigns")
        ).get("data", {})

    async def isSubscribed_a(self, _id: str, wuid: str) -> dict[str, Any]:
        return (
            await self.runGqlQuery_a(gq.CAMPAIGN_Q.get("isSubscribedQ", ""), {"id": _id, "uid": wuid}, "IsSubscribedCampaign")
        ).get("data", {})

    async def subscribed_a(self, wuid: str, needDetail: bool) -> dict[str, Any]:
        return (
            await self.runGqlQuery_a(
                gq.CAMPAIGN_Q.get("subscribedQ", ""), {"uid": wuid, "needDetail": needDetail}, "SubscribedCampaign"
            )
        ).get("data", {})

    async def ranks_a(self, campaignId: str) -> dict[str, Any]:
        return (await self.runGqlQuery_a(gq.CAMPAIGN_Q.get("ranksQ", ""), {"campaignId": campaignId}, "Ranks")).get("data", {})

    async def conv360IDToO2OID_a(self, qid: str, deviceId: str) -> dict[str, Any]:
        return (
            await self.runGqlQuery_a(
                gq.QUERY.get("conv360IDToO2OIDQ", ""), {"qid": qid, "deviceId": deviceId}, "Conv360IDToO2OID"
            )
        ).get("data", {})

    async def getAppVersion_a(self) -> dict[str, Any]:
        return (await self.runGqlQuery_a(gq.QUERY.get("getAppVersionQ", ""), {}, "GetAppVersion")).get("data", {})

    async def watchGroups_a(self, _id: str = "") -> dict[str, Any]:
        return (await self.runGqlQuery_a(gq.WATCHGROUP_Q.get("watchGroupsQ", ""), {"id": _id}, "WatchGroups")).get("data", {})

    async def getStartTrackingWatch_a(self, wuid: str) -> dict[str, Any]:
        data = await self.runGqlQuery_a(gq.WATCH_Q.get("startTrackingWatchQ", ""), {"uid": wuid}, "StartTrackingWatch")
        errors: list[dict[str, str]] = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getStartTrackingWatch", "error": errors})
        return data.get("data", {})

    async def getEndTrackingWatch_a(self, wuid: str) -> dict[str, Any]:
        data = await self.runGqlQuery_a(gq.WATCH_Q.get("endTrackingWatchQ", ""), {"uid": wuid}, "EndTrackingWatch")
        errors: list[dict[str, str]] = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getEndTrackingWatch", "error": errors})
        return data.get("data", {})

    async def checkEmailOrPhoneExist_a(
        self, _type: UserContactType, email: str = "", countryCode: str = "", phoneNumber: str = ""
    ) -> dict[str, bool]:
        data: dict[str, dict[str, bool]] = await self.runGqlQuery_a(
            gq.UTILS_Q.get("checkEmailOrPhoneExistQ", ""),
            {"type": _type.value, "email": email, "countryCode": countryCode, "phoneNumber": phoneNumber},
            "CheckEmailOrPhoneExist",
        )
        return data.get("data", {})

    ########## SECTION QUERY end ##########

    ########## SECTION MUTATION start ##########

    async def sendText_a(self, wuid: str, text: str) -> bool:
        # ownUser id
        result = await self.runGqlQuery_a(gm.WATCH_M.get("sendChatTextM", ""), {"uid": wuid, "text": text}, "SendChatText")
        errors = result.get("errors", None)
        if errors is not None:
            for error in errors:
                _LOGGER.error(error)
        if result.get("data", {})["sendChatText"] is not None:
            return True
        return False

    async def addStep_a(self, stepCount: int) -> dict[str, Any]:
        return (await self.runGqlQuery_a(gm.STEP_M.get("addM", ""), {"stepCount": stepCount}, "AddStep")).get("data", {})

    async def shutdown_a(self, wuid: str) -> bool:
        # ownUser id
        return await self.isAdmin_a(wuid, gm.WATCH_M.get("shutdownM", ""), {"uid": wuid}, "ShutDown")

    async def reboot_a(self, wuid: str) -> bool:
        # ownUser id
        return await self.isAdmin_a(wuid, gm.WATCH_M.get("rebootM", ""), {"uid": wuid}, "reboot")

    async def modifyAlert_a(self, _id: str, yesOrNo: str) -> dict[str, Any]:
        # function?
        return await self.runGqlQuery_a(gm.WATCH_M.get("modifyAlertM", ""), {"uid": _id, "remind": yesOrNo}, "modifyAlert")

    async def setEnableSilentTime_a(self, silent_id: str, status: str = NormalStatus.ENABLE.value) -> dict[str, Any]:
        return (
            await self.runGqlQuery_a(
                gm.WATCH_M.get("setEnableSlientTimeM", ""), {"silentId": silent_id, "status": status}, "SetEnableSlientTime"
            )
        ).get("data", {})

    async def setEnableAlarmTime_a(self, alarm_id: str, status: str = NormalStatus.ENABLE.value) -> dict[str, Any]:
        return (
            await self.runGqlQuery_a(
                gm.WATCH_M.get("modifyAlarmM", ""), {"alarmId": alarm_id, "status": status}, "ModifyAlarm"
            )
        ).get("data", {})

    async def setReadChatMsg_a(self, wuid: str, msgId: str, _id: str) -> dict[str, Any]:
        return (
            await self.runGqlQuery_a(
                gm.WATCH_M.get("setReadChatMsgM", ""), {"uid": wuid, "msgId": msgId, "id": _id}, "setReadChatMsg"
            )
        ).get("data", {})

    async def submitIncorrectLocationData_a(self, wuid: str, lat: str, lng: str, timestamp: str) -> dict[str, Any]:
        return (
            await self.runGqlQuery_a(
                gm.WATCH_M.get("submitIncorrectLocationDataM", ""),
                {"uid": wuid, "lat": lat, "lng": lng, "timestamp": timestamp},
                "SubmitIncorrectLocationData",
            )
        ).get("data", {})

    async def modifyContact_a(self, contactId: str, isAdmin: bool, contactName: str = "", fileId: str = "") -> dict[str, Any]:
        return await self.runGqlQuery_a(
            gm.WATCH_M.get("modifyContactM", ""),
            {"contactId": contactId, "contactName": contactName, "fileId": fileId, "isAdmin": isAdmin},
        )

    async def issueEmailOrPhoneCode_a(
        self,
        purpose: EmailAndPhoneVerificationTypeV2 = EmailAndPhoneVerificationTypeV2.UNKNOWN__,
        _type: UserContactType = UserContactType.UNKNOWN__,
        email: str = "",
        phoneNumber: str = "",
        countryCode: str = "",
        previousToken: str = "",
        lang: str = "",
    ) -> dict[str, Any]:
        return await self.runGqlQuery_a(
            gm.SIGN_M.get("issueEmailOrPhoneCodeM", ""),
            {
                "purpose": purpose.value,
                "type": _type.value,
                "email": email,
                "phoneNumber": phoneNumber,
                "countryCode": countryCode,
                "previousToken": previousToken,
                "lang": lang,
            },
            "IssueEmailOrPhoneCode",
        )

    async def signUpWithEmailAndPhoneV2_a(
        self,
        countryPhoneCode: str = "",
        phoneNumber: str = "",
        password: str = "",
        name: str = "",
        emailAddress: str = "",
        emailConsent: int = -1,
    ) -> dict[str, Any]:
        return await self.runGqlQuery_a(
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

    async def verifyCaptcha_a(self, captchaString: str = "", _type: str = "") -> dict[str, Any]:
        return await self.runGqlQuery_a(
            gm.SIGN_M.get("verifyCaptchaM", ""), {"captchaString": captchaString, "type": _type}, "verifyCaptcha"
        )

    async def verifyEmailOrPhoneCode_a(
        self,
        _type: UserContactType = UserContactType.UNKNOWN__,
        email: str = "",
        phoneNumber: str = "",
        countryCode: str = "",
        verifyCode: str = "",
        verificationToken: str = "",
    ) -> dict[str, Any]:
        return await self.runGqlQuery_a(
            gm.SIGN_M.get("verifyEmailOrPhoneCodeM", ""),
            {
                "type": _type.value,
                "email": email,
                "phoneNumber": phoneNumber,
                "countryCode": countryCode,
                "verifyCode": verifyCode,
                "verificationToken": verificationToken,
            },
            "verifyEmailOrPhoneCode",
        )

    async def deleteMessageFromApp_a(self, wuid: str, msgId: str):
        return (
            await self.runGqlQuery_a(
                gm.WATCH_M.get("deleteChatMessageM", ""), {"uid": wuid, "msgId": msgId}, "DeleteChatMessage"
            )
        ).get("data", {})

    async def connect360_a(self):
        data = await self.runGqlQuery_a(gm.SIGN_M.get("connect360M", ""), {}, "connect360")
        return data.get("data", {})

    async def refresh_token_a(self, wuid: str, refresh_token: str) -> str | None:
        data = await self.runGqlQuery_a(
            gm.SIGN_M.get("refreshTokenM", ""), {"uid": wuid, "refreshToken": refresh_token}, "RefreshToken"
        )
        return data.get("data", {})

    ########## SECTION MUTATION end ##########
