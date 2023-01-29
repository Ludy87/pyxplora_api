from __future__ import annotations

import logging
from typing import Any

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
    ) -> dict[str, Any]:
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
    ) -> dict[str, Any]:
        if self.accessToken is None and self.signup:
            self.login()
            # raise Exception("You must first login to the Xplora® API.")
        # Run GraphQL query and return
        return self.runGqlQuery(query, variables, operation_name)

    def login(self) -> dict[str, Any]:
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
        self.issueDate = self.issueToken["issueDate"]
        self.expireDate = self.issueToken["expireDate"]

        app = self.issueToken.get("app")
        if app:
            apiKey = app.get("apiKey")
            if apiKey:
                self._API_KEY = apiKey
            apiSecret = app.get("apiSecret")
            if apiSecret:
                self._API_SECRET = apiSecret

        return self.issueToken

    def isAdmin(self, wuid: str, query: str, variables: dict[str, Any], key: str) -> bool:
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

    def askWatchLocate(self, wuid: str) -> dict[str, Any]:
        data: dict[str, Any] = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("askLocateQ", ""), {"uid": wuid}, "AskWatchLocate")
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "askWatchLocate", "errors": errors})
        res: dict[str, Any] = data.get("data", {})
        if res["askWatchLocate"] is not None:
            return res
        return {"askWatchLocate": False}

    def getWatchUserContacts(self, wuid: str) -> dict[str, Any]:
        # Contacts from ownUser
        data: dict[str, Any] = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("contactsQ", ""), {"uid": wuid}, "Contacts")
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchUserContacts", "errors": errors})
        return data.get("data", {})

    def getWatches(self, wuid: str) -> dict[str, Any]:
        data: dict[str, Any] = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("watchesQ", ""), {"uid": wuid}, "Watches")
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatches", "errors": errors})
        return data.get("data", {})

    def getSWInfo(self, qrCode: str) -> dict[str, Any]:
        data: dict[str, Any] = self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("checkByQrCodeQ", ""), {"qrCode": qrCode}, "CheckWatchByQrCode"
        )
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getSWInfo", "errors": errors})
        return data.get("data", {})

    def getWatchState(self, qrCode: str, qrt: str = "", qrc: str = "") -> dict[str, Any]:
        vari = {}
        if qrCode != "":
            vari["qrCode"] = qrCode
        if qrt != "":
            vari["qrt"] = qrt
        if qrc != "":
            vari["qrc"] = qrc
        data: dict[str, Any] = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("stateQ", ""), vari, "WatchState")
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchState", "errors": errors})
        return data.get("data", {})

    def getWatchLastLocation(self, wuid: str) -> dict[str, Any]:
        data: dict[str, Any] = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("locateQ", ""), {"uid": wuid}, "WatchLastLocate")
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchLastLocation", "errors": errors})
        return data.get("data", {})

    def trackWatch(self, wuid: str) -> dict[str, Any]:
        # tracking time - seconds
        data: dict[str, Any] = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("trackQ", ""), {"uid": wuid}, "TrackWatch")
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "trackWatch", "errors": errors})
        res = data.get("data", {})
        if res.get("trackWatch", {"trackWatch": -1}):
            return res
        return {"trackWatch": -1}

    def getAlarmTime(self, wuid: str) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("alarmsQ", ""), {"uid": wuid}, "Alarms").get("data", {})

    def getWifi(self, wuid: str) -> dict[str, Any]:
        # without function?
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("getWifisQ", ""), {"uid": wuid}, "GetWifis").get("data", {})

    def unReadChatMsgCount(self, wuid: str) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("unReadChatMsgCountQ", ""), {"uid": wuid}, "UnReadChatMsgCount").get(
            "data", {}
        )

    def safeZones(self, wuid: str) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("safeZonesQ", ""), {"uid": wuid}, "SafeZones").get("data", {})

    def safeZoneGroups(self) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("safeZoneGroupsQ", ""), {}, "SafeZoneGroups").get("data", {})

    def silentTimes(self, wuid: str) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("silentTimesQ", ""), {"uid": wuid}, "SlientTimes").get("data", {})

    def chats(self, wuid: str, offset: int = 0, limit: int = 0, msgId: str = "", asObject=False) -> dict[str, Any]:
        # ownUser id
        res: dict = self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("chatsQ", ""), {"uid": wuid, "offset": offset, "limit": limit, "msgId": msgId}, "Chats"
        )
        if res.get("errors", None) or res.get("data", None) is None:
            if asObject:
                _LOGGER.error(res.get("data", {}))
                return Chats.from_dict(res.get("data", {}))
            return {}
        if asObject:
            return Chats.from_dict(res.get("data", {}))
        return res.get("data", {})

    def fetchChatImage(self, wuid: str, msgId: str) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("fetchChatImageQ", ""), {"uid": wuid, "msgId": msgId}, "FetchChatImage"
        ).get("data", {})

    def fetchChatMp3(self, wuid: str, msgId: str) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("fetchChatMp3Q", ""), {"uid": wuid, "msgId": msgId}, "FetchChatMp3"
        ).get("data", {})

    def fetchChatShortVideo(self, wuid: str, msgId: str) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("fetchChatShortVideoQ", ""), {"uid": wuid, "msgId": msgId}, "FetchChatShortVideo"
        ).get("data", {})

    def fetchChatShortVideoCover(self, wuid: str, msgId: str) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("fetchChatShortVideoCoverQ", ""), {"uid": wuid, "msgId": msgId}, "FetchChatShortVideoCover"
        ).get("data", {})

    def fetchChatVoice(self, wuid: str, msgId: str) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("fetchChatVoiceQ", ""), {"uid": wuid, "msgId": msgId}, "FetchChatVoice"
        ).get("data", {})

    def watchImei(self, imei: str, qrCode: str, deviceKey: str) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("imeiQ", ""), {"imei": imei, "qrCode": qrCode, "deviceKey": deviceKey}, "WatchImei"
        ).get("data", {})

    def getWatchLocHistory(self, wuid: str, date: int, tz: str, limit: int) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("locHistoryQ", ""), {"uid": wuid, "date": date, "tz": tz, "limit": limit}, "LocHistory"
        ).get("data", {})

    def watchesDynamic(self) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("watchesDynamicQ", ""), {}, "WatchesDynamic").get("data", {})

    def coinHistory(self, wuid: str, start: int, end: int, type: str, offset: int, limit: int) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.XCOIN_Q.get("historyQ", ""),
            {"uid": wuid, "start": start, "end": end, "type": type, "offset": offset, "limit": limit},
            "CoinHistory",
        ).get("data", {})

    def reminders(self, wuid: str) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.XMOVE_Q.get("remindersQ", ""), {"uid": wuid}, "Reminders").get("data", {})

    def groups(self, isCampaign: bool) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.CARD_Q.get("groupsQ", ""), {"isCampaign": isCampaign}, "CardGroups").get(
            "data", {}
        )

    def dynamic(self) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.CARD_Q.get("dynamicQ", ""), {}, "DynamicCards").get("data", {})

    def staticCard(self) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.CARD_Q.get("staticQ", ""), {}, "StaticCard").get("data", {})

    def familyInfo(self, wuid: str, watchId: str, tz: str, date: int) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.FAMILY_Q.get("infoQ", ""), {"uid": wuid, "watchId": watchId, "tz": tz, "date": date}, "FamilyInfo"
        ).get("data", {})

    def getMyTotalInfo(
        self, wuid: str, tz: str, date: int, start: int, end: int, type: str, offset: int, limit: int
    ) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.MYINFO_Q.get("getMyTotalInfoQ", ""),
            {"uid": wuid, "tz": tz, "date": date, "start": start, "end": end, "type": type, "offset": offset, "limit": limit},
            "GetMyTotalInfo",
        ).get("data", {})

    def myInfoWithCoinHistory(
        self, wuid: str, start: int, end: int, tz: str, type: str, offset: int, limit: int
    ) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.MYINFO_Q.get("coinHistoryQ", ""),
            {"uid": wuid, "start": start, "end": end, "tz": tz, "type": type, "offset": offset, "limit": limit},
            "MyInfoWithCoinHistory",
        ).get("data", {})

    def getMyInfo(self) -> dict[str, Any]:
        # Profil from login Account
        return self.runAuthorizedGqlQuery(gq.MYINFO_Q.get("readQ", ""), {}, "ReadMyInfo").get("data", {})

    def readCampaignProfile(self, wuid: str) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.MYINFO_Q.get("readCampaignProfileQ", ""),
            {"uid": wuid},
        ).get("data", {})

    def getReviewStatus(self, wuid: str) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.REVIEW_Q.get("getStatusQ", ""), {"uid": wuid}, "GetReviewStatus").get("data", {})

    def getWatchUserSteps(self, wuid: str, tz: str, date: int) -> dict[str, Any]:
        data: dict[str, Any] = self.runAuthorizedGqlQuery(
            gq.STEP_Q.get("userQ", ""), {"uid": wuid, "tz": tz, "date": date}, "UserSteps"
        )
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchUserSteps", "errors": errors})
        return data.get("data", {})

    def countries(self) -> dict[str, Any]:
        # Country Support
        return self.runAuthorizedGqlQuery(gq.UTILS_Q.get("countriesQ", ""), {}, "Countries").get("data", {})

    def avatars(self, id: str) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.CAMPAIGN_Q.get("avatarsQ", ""), {"id": id}, "Avatars").get("data", {})

    def getFollowRequestWatchCount(self) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.CAMPAIGN_Q.get("followRequestWatchCountQ", ""), {}, "FollowRequestWatchCount"
        ).get("data", {})

    def campaigns(self, id: str, categoryId: str) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.CAMPAIGN_Q.get("campaignsQ", ""), {"id": id, "categoryId": categoryId}, "Campaigns"
        ).get("data", {})

    def isSubscribed(self, id: str, wuid: str) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.CAMPAIGN_Q.get("isSubscribedQ", ""), {"id": id, "uid": wuid}, "IsSubscribedCampaign"
        ).get("data", {})

    def subscribed(self, wuid: str, needDetail: bool) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.CAMPAIGN_Q.get("subscribedQ", ""), {"uid": wuid, "needDetail": needDetail}, "SubscribedCampaign"
        ).get("data", {})

    def ranks(self, campaignId: str) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.CAMPAIGN_Q.get("ranksQ", ""), {"campaignId": campaignId}, "Ranks").get("data", {})

    def conv360IDToO2OID(self, qid: str, deviceId: str) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.QUERY.get("conv360IDToO2OIDQ", ""), {"qid": qid, "deviceId": deviceId}, "Conv360IDToO2OID"
        ).get("data", {})

    def getAppVersion(self) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.QUERY.get("getAppVersionQ", ""), {}, "GetAppVersion").get("data", {})

    def watchGroups(self, id: str = "") -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.WATCHGROUP_Q.get("watchGroupsQ", ""), {"id": id}, "WatchGroups").get("data", {})

    def getStartTrackingWatch(self, wuid: str) -> dict[str, Any]:
        data = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("startTrackingWatchQ", ""), {"uid": wuid}, "StartTrackingWatch")
        errors: list[dict[str, str]] = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getStartTrackingWatch", "error": errors})
        return data.get("data", {})

    def getEndTrackingWatch(self, wuid: str) -> dict[str, Any]:
        data = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("endTrackingWatchQ", ""), {"uid": wuid}, "EndTrackingWatch")
        errors: list[dict[str, str]] = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getEndTrackingWatch", "error": errors})
        return data.get("data", {})

    def checkEmailOrPhoneExist(
        self, type: UserContactType, email: str = "", countryCode: str = "", phoneNumber: str = ""
    ) -> dict[str, bool]:
        data = self.runAuthorizedGqlQuery(
            gq.UTILS_Q.get("checkEmailOrPhoneExistQ", ""),
            {"type": type.value, "email": email, "countryCode": countryCode, "phoneNumber": phoneNumber},
            "CheckEmailOrPhoneExist",
        )
        return data.get("data", {})

    ########## SECTION QUERY end ##########

    ########## SECTION MUTATION start ##########

    def sendText(self, wuid: str, text: str) -> bool:
        # ownUser id
        if (
            self.runAuthorizedGqlQuery(gm.WATCH_M.get("sendChatTextM", ""), {"uid": wuid, "text": text}, "SendChatText").get(
                "data", {}
            )["sendChatText"]
            is not None
        ):
            return True
        return False

    def addStep(self, stepCount: int) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(gm.STEP_M.get("addM", ""), {"stepCount": stepCount}, "AddStep").get("data", {})

    def shutdown(self, wuid: str) -> bool:
        # ownUser id
        return self.isAdmin(wuid, gm.WATCH_M.get("shutdownM", ""), {"uid": wuid}, "ShutDown")

    def reboot(self, wuid: str) -> bool:
        # ownUser id
        return self.isAdmin(wuid, gm.WATCH_M.get("rebootM", ""), {"uid": wuid}, "reboot")

    def modifyAlert(self, id: str, yesOrNo: str) -> dict[str, Any]:
        # function?
        return self.runAuthorizedGqlQuery(gm.WATCH_M.get("modifyAlertM", ""), {"uid": id, "remind": yesOrNo}, "modifyAlert")

    def setEnableSilentTime(self, silentId: str, status: str = NormalStatus.ENABLE.value) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gm.WATCH_M.get("setEnableSlientTimeM", ""), {"silentId": silentId, "status": status}, "SetEnableSlientTime"
        ).get("data", {})

    def setEnableAlarmTime(self, alarmId: str, status: str = NormalStatus.ENABLE.value) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gm.WATCH_M.get("modifyAlarmM", ""), {"alarmId": alarmId, "status": status}, "ModifyAlarm"
        ).get("data", {})

    def setReadChatMsg(self, wuid: str, msgId: str, id: str) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gm.WATCH_M.get("setReadChatMsgM", ""), {"uid": wuid, "msgId": msgId, "id": id}, "setReadChatMsg"
        ).get("data", {})

    def submitIncorrectLocationData(self, wuid: str, lat: str, lng: str, timestamp: str) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gm.WATCH_M.get("submitIncorrectLocationDataM", ""),
            {"uid": wuid, "lat": lat, "lng": lng, "timestamp": timestamp},
            "SubmitIncorrectLocationData",
        ).get("data", {})

    def modifyContact(self, contactId: str, isAdmin: bool, contactName: str = "", fileId: str = "") -> dict[str, Any]:
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
    ) -> dict[str, Any]:
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
    ) -> dict[str, Any]:
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

    def verifyCaptcha(self, captchaString: str = "", type: str = "") -> dict[str, Any]:
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
    ) -> dict[str, Any]:
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

    async def deleteMessageFromApp(self, wuid: str, msgId: str) -> dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gm.WATCH_M.get("deleteChatMessageM", ""), {"uid": wuid, "msgId": msgId}, "DeleteChatMessage"
        ).get("data", {})

    ########## SECTION MUTATION end ##########
