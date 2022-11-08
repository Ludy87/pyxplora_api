from __future__ import annotations


from typing import Any

from .const import ENDPOINT
from .exception_classes import ErrorMSG, LoginError, NoAdminError
from .graphql_client import GraphqlClient
from .handler_gql import HandlerGQL
from .status import EmailAndPhoneVerificationTypeV2, NormalStatus, UserContactType

from . import gql_mutations as gm
from . import gql_queries as gq


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

    async def runGqlQuery_a(
        self, query: str, variables: dict[str, Any] | None = None, operation_name: str | None = None
    ) -> dict[str, Any]:
        if query is None:
            raise Exception("GraphQL guery string MUST NOT be empty!")
        # Add Xplora® API headers
        requestHeaders = self.getRequestHeaders("application/json; charset=UTF-8")
        # create GQLClient
        gqlClient = GraphqlClient(endpoint=ENDPOINT, headers=requestHeaders)
        # execute QUERY|MUTATION
        data: dict[str, Any] = await gqlClient.execute_async(query=query, variables=variables, operation_name=operation_name)
        return data

    async def runAuthorizedGqlQuery_a(
        self, query: str, variables: dict[str, Any] | None = None, operation_name: str | None = None
    ) -> dict[str, Any]:
        if self.accessToken is None and self.signup:
            raise Exception("You must first login to the Xplora® API.")
        # Run GraphQL query and return
        return await self.runGqlQuery_a(query, variables, operation_name)

    async def login_a(self) -> dict[str, Any]:
        if self.email:
            dataAll: dict[str, Any] = await self.runGqlQuery_a(
                gm.SIGN_M.get("signInWithEmailOrPhoneM", ""), self.variables, "signInWithEmailOrPhone"
            )
        else:
            dataAll: dict[str, Any] = await self.runGqlQuery_a(gm.SIGN_M.get("issueTokenM", ""), self.variables, "IssueToken")
        errors = dataAll.get("errors", [])
        if errors:
            self.errors.append({"function": "login", "errors": errors})
        data: dict[str, Any] = dataAll.get("data", {})
        if data.get("issueToken", data.get("signInWithEmailOrPhone", None)) is None:
            error_message: list[dict[str, str]] = dataAll.get("errors", [{"message": ""}])
            # Login failed.
            raise LoginError(ErrorMSG.LOGIN_ERR.value.format(error_message[0].get("message", "")))
        self.issueToken = data.get("issueToken", data.get("signInWithEmailOrPhone", None))

        # Login succeeded
        self.sessionId = self.issueToken["id"]
        self.userId = self.issueToken["user"]["id"]
        self.accessToken = self.issueToken["token"]
        self.issueDate = self.issueToken["issueDate"]
        self.expireDate = self.issueToken["expireDate"]

        if self.issueToken["app"] is not None:
            # Update API_KEY and API_SECRET?
            if self.issueToken["app"]["apiKey"]:
                self._API_KEY = self.issueToken["app"]["apiKey"]
            if self.issueToken["app"]["apiSecret"]:
                self._API_SECRET = self.issueToken["app"]["apiSecret"]
        return self.issueToken

    async def isAdmin_a(self, wuid: str, query: str, variables: dict[str, Any], key: str) -> bool:
        contacts: dict[str, Any] = await self.getWatchUserContacts_a(wuid)
        for contact in contacts["contacts"]["contacts"]:
            try:
                id = contact["contactUser"]["id"]
            except KeyError and TypeError:
                id = None
            if self.userId == id:
                if contact["guardianType"] == "FIRST":
                    data: dict[str, Any] = (await self.runAuthorizedGqlQuery_a(query, variables, key)).get("data", {})
                    return data.get(key, False)
        raise NoAdminError()

    ########## SECTION QUERY start ##########

    async def askWatchLocate_a(self, wuid: str) -> dict[str, Any]:
        data: dict[str, Any] = await self.runAuthorizedGqlQuery_a(
            gq.WATCH_Q.get("askLocateQ", ""), {"uid": wuid}, "AskWatchLocate"
        )
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "askWatchLocate", "errors": errors})
        res: dict[str, Any] = data.get("data", {})
        if res["askWatchLocate"] is not None:
            return res
        return {"askWatchLocate": False}

    async def getWatchUserContacts_a(self, wuid: str) -> dict[str, Any]:
        # Contacts from ownUser
        data: dict[str, Any] = await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("contactsQ", ""), {"uid": wuid}, "Contacts")
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchUserContacts", "errors": errors})
        return data.get("data", {})

    async def getWatches_a(self, wuid: str) -> dict[str, Any]:
        data: dict[str, Any] = await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("watchesQ", ""), {"uid": wuid}, "Watches")
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatches", "errors": errors})
        return data.get("data", {})

    async def getSWInfo_a(self, qrCode: str) -> dict[str, Any]:
        data: dict[str, Any] = await self.runAuthorizedGqlQuery_a(
            gq.WATCH_Q.get("checkByQrCodeQ", ""), {"qrCode": qrCode}, "CheckWatchByQrCode"
        )
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getSWInfo", "errors": errors})
        return data.get("data", {})

    async def getWatchState_a(self, qrCode: str, qrt: str = "", qrc: str = "") -> dict[str, Any]:
        vari = {}
        if qrCode != "":
            vari["qrCode"] = qrCode
        if qrt != "":
            vari["qrt"] = qrt
        if qrc != "":
            vari["qrc"] = qrc
        data: dict[str, Any] = await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("stateQ", ""), vari, "WatchState")
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchState", "errors": errors})
        return data.get("data", {})

    async def getWatchLastLocation_a(self, wuid: str) -> dict[str, Any]:
        data: dict[str, Any] = await self.runAuthorizedGqlQuery_a(
            gq.WATCH_Q.get("locateQ", ""), {"uid": wuid}, "WatchLastLocate"
        )
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchLastLocation", "errors": errors})
        return data.get("data", {})

    async def trackWatch_a(self, wuid: str) -> dict[str, Any]:
        # tracking time - seconds
        data: dict[str, Any] = await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("trackQ", ""), {"uid": wuid}, "TrackWatch")
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "trackWatch", "errors": errors})
        res = data.get("data", {})
        if res.get("trackWatch", {"trackWatch": -1}):
            return res
        return {"trackWatch": -1}

    async def getAlarmTime_a(self, wuid: str) -> dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("alarmsQ", ""), {"uid": wuid}, "Alarms")).get("data", {})

    async def getWifi_a(self, wuid: str) -> dict[str, Any]:
        # without function?
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("getWifisQ", ""), {"uid": wuid}, "GetWifis")).get("data", {})

    async def unReadChatMsgCount_a(self, wuid: str) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("unReadChatMsgCountQ", ""), {"uid": wuid}, "UnReadChatMsgCount")
        ).get("data", {})

    async def safeZones_a(self, wuid: str) -> dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("safeZonesQ", ""), {"uid": wuid}, "SafeZones")).get(
            "data", {}
        )

    async def safeZoneGroups_a(self) -> dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("safeZoneGroupsQ", ""), {}, "SafeZoneGroups")).get(
            "data", {}
        )

    async def silentTimes_a(self, wuid: str) -> dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("silentTimesQ", ""), {"uid": wuid}, "SlientTimes")).get(
            "data", {}
        )

    async def chats_a(self, wuid: str, offset: int = 0, limit: int = 0, msgId: str = "") -> dict[str, Any]:
        # ownUser id
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.WATCH_Q.get("chatsQ", ""), {"uid": wuid, "offset": offset, "limit": limit, "msgId": msgId}, "Chats"
            )
        ).get("data", {})

    async def fetchChatImage_a(self, wuid: str, msgId: str) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.WATCH_Q.get("fetchChatImageQ", ""), {"uid": wuid, "msgId": msgId}, "FetchChatImage"
            )
        ).get("data", {})

    async def fetchChatMp3_a(self, wuid: str, msgId: str) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.WATCH_Q.get("fetchChatMp3Q", ""), {"uid": wuid, "msgId": msgId}, "FetchChatMp3"
            )
        ).get("data", {})

    async def fetchChatShortVideo_a(self, wuid: str, msgId: str) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.WATCH_Q.get("fetchChatShortVideoQ", ""), {"uid": wuid, "msgId": msgId}, "FetchChatShortVideo"
            )
        ).get("data", {})

    async def fetchChatShortVideoCover_a(self, wuid: str, msgId: str) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.WATCH_Q.get("fetchChatShortVideoCoverQ", ""), {"uid": wuid, "msgId": msgId}, "FetchChatShortVideoCover"
            )
        ).get("data", {})

    async def fetchChatVoice_a(self, wuid: str, msgId: str) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.WATCH_Q.get("fetchChatVoiceQ", ""), {"uid": wuid, "msgId": msgId}, "FetchChatVoice"
            )
        ).get("data", {})

    async def watchImei_a(self, imei: str, qrCode: str, deviceKey: str) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.WATCH_Q.get("imeiQ", ""), {"imei": imei, "qrCode": qrCode, "deviceKey": deviceKey}, "WatchImei"
            )
        ).get("data", {})

    async def getWatchLocHistory_a(self, wuid: str, date: int, tz: str, limit: int) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.WATCH_Q.get("locHistoryQ", ""), {"uid": wuid, "date": date, "tz": tz, "limit": limit}, "LocHistory"
            )
        ).get("data", {})

    async def watchesDynamic_a(self) -> dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("watchesDynamicQ", ""), {}, "WatchesDynamic")).get(
            "data", {}
        )

    async def coinHistory_a(self, wuid: str, start: int, end: int, type: str, offset: int, limit: int) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.XCOIN_Q.get("historyQ", ""),
                {"uid": wuid, "start": start, "end": end, "type": type, "offset": offset, "limit": limit},
                "CoinHistory",
            )
        ).get("data", {})

    async def reminders_a(self, wuid: str) -> dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.XMOVE_Q.get("remindersQ", ""), {"uid": wuid}, "Reminders")).get(
            "data", {}
        )

    async def groups_a(self, isCampaign: bool) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(gq.CARD_Q.get("groupsQ", ""), {"isCampaign": isCampaign}, "CardGroups")
        ).get("data", {})

    async def dynamic_a(self) -> dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.CARD_Q.get("dynamicQ", ""), {}, "DynamicCards")).get("data", {})

    async def staticCard_a(self) -> dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.CARD_Q.get("staticQ", ""), {}, "StaticCard")).get("data", {})

    async def familyInfo_a(self, wuid: str, watchId: str, tz: str, date: int) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.FAMILY_Q.get("infoQ", ""), {"uid": wuid, "watchId": watchId, "tz": tz, "date": date}, "FamilyInfo"
            )
        ).get("data", {})

    async def getMyTotalInfo_a(
        self, wuid: str, tz: str, date: int, start: int, end: int, type: str, offset: int, limit: int
    ) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.MYINFO_Q.get("getMyTotalInfoQ", ""),
                {
                    "uid": wuid,
                    "tz": tz,
                    "date": date,
                    "start": start,
                    "end": end,
                    "type": type,
                    "offset": offset,
                    "limit": limit,
                },
                "GetMyTotalInfo",
            )
        ).get("data", {})

    async def myInfoWithCoinHistory_a(
        self, wuid: str, start: int, end: int, tz: str, type: str, offset: int, limit: int
    ) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.MYINFO_Q.get("coinHistoryQ", ""),
                {"uid": wuid, "start": start, "end": end, "tz": tz, "type": type, "offset": offset, "limit": limit},
                "MyInfoWithCoinHistory",
            )
        ).get("data", {})

    async def getMyInfo_a(self) -> dict[str, Any]:
        # Profil from login Account
        return (await self.runAuthorizedGqlQuery_a(gq.MYINFO_Q.get("readQ", ""), {}, "ReadMyInfo")).get("data", {})

    async def readCampaignProfile_a(self) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.MYINFO_Q.get("readCampaignProfileQ", ""),
                {},
            )
        ).get("data", {})

    async def getReviewStatus_a(self, wuid: str) -> dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.REVIEW_Q.get("getStatusQ", ""), {"uid": wuid}, "GetReviewStatus")).get(
            "data", {}
        )

    async def getWatchUserSteps_a(self, wuid: str, tz: str, date: int) -> dict[str, Any]:
        data: dict[str, Any] = await self.runAuthorizedGqlQuery_a(
            gq.STEP_Q.get("userQ", ""), {"uid": wuid, "tz": tz, "date": date}, "UserSteps"
        )
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchUserSteps", "errors": errors})
        return data.get("data", {})

    async def countries_a(self) -> dict[str, Any]:
        # Country Support
        return (await self.runAuthorizedGqlQuery_a(gq.UTILS_Q.get("countriesQ", ""), {}, "Countries")).get("data", {})

    async def avatars_a(self, id: str) -> dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.CAMPAIGN_Q.get("avatarsQ", ""), {"id": id}, "Avatars")).get("data", {})

    async def getFollowRequestWatchCount_a(self) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.CAMPAIGN_Q.get("followRequestWatchCountQ", ""), {}, "FollowRequestWatchCount"
            )
        ).get("data", {})

    async def campaigns_a(self, id: str, categoryId: str) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.CAMPAIGN_Q.get("campaignsQ", ""), {"id": id, "categoryId": categoryId}, "Campaigns"
            )
        ).get("data", {})

    async def isSubscribed_a(self, id: str, wuid: str) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.CAMPAIGN_Q.get("isSubscribedQ", ""), {"id": id, "uid": wuid}, "IsSubscribedCampaign"
            )
        ).get("data", {})

    async def subscribed_a(self, wuid: str, needDetail: bool) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.CAMPAIGN_Q.get("subscribedQ", ""), {"uid": wuid, "needDetail": needDetail}, "SubscribedCampaign"
            )
        ).get("data", {})

    async def ranks_a(self, campaignId: str) -> dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.CAMPAIGN_Q.get("ranksQ", ""), {"campaignId": campaignId}, "Ranks")).get(
            "data", {}
        )

    async def campaignUserProfiles_a(self) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(gq.CAMPAIGN_Q.get("campaignUserProfilesQ", ""), {}, "CampaignUserProfiles")
        ).get("data", {})

    async def conv360IDToO2OID_a(self, qid: str, deviceId: str) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.QUERY.get("conv360IDToO2OIDQ", ""), {"qid": qid, "deviceId": deviceId}, "Conv360IDToO2OID"
            )
        ).get("data", {})

    async def getAppVersion_a(self) -> dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY.get("getAppVersionQ", ""), {}, "GetAppVersion")).get("data", {})

    async def watchGroups_a(self, id: str = "") -> dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCHGROUP_Q.get("watchGroupsQ", ""), {"id": id}, "WatchGroups")).get(
            "data", {}
        )

    async def getStartTrackingWatch_a(self, wuid: str) -> dict[str, Any]:
        data = await self.runAuthorizedGqlQuery_a(
            gq.WATCH_Q.get("startTrackingWatchQ", ""), {"uid": wuid}, "StartTrackingWatch"
        )
        errors: list[dict[str, str]] = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getStartTrackingWatch", "error": errors})
        return data.get("data", {})

    async def getEndTrackingWatch_a(self, wuid: str) -> dict[str, Any]:
        data = await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("endTrackingWatchQ", ""), {"uid": wuid}, "EndTrackingWatch")
        errors: list[dict[str, str]] = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getEndTrackingWatch", "error": errors})
        return data.get("data", {})

    async def checkEmailOrPhoneExist_a(
        self, type: UserContactType, email: str = "", countryCode: str = "", phoneNumber: str = ""
    ) -> dict[str, bool]:
        data: dict[str, dict[str, bool]] = await self.runAuthorizedGqlQuery_a(
            gq.UTILS_Q.get("checkEmailOrPhoneExistQ", ""),
            {"type": type.value, "email": email, "countryCode": countryCode, "phoneNumber": phoneNumber},
            "CheckEmailOrPhoneExist",
        )
        return data.get("data", {})

    ########## SECTION QUERY end ##########

    ########## SECTION MUTATION start ##########

    async def sendText_a(self, wuid: str, text: str) -> bool:
        # ownUser id
        if (
            await self.runAuthorizedGqlQuery_a(
                gm.WATCH_M.get("sendChatTextM", ""), {"uid": wuid, "text": text}, "SendChatText"
            )
        ).get("data", {})["sendChatText"] is not None:
            return True
        return False

    async def addStep_a(self, stepCount: int) -> dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gm.STEP_M.get("addM", ""), {"stepCount": stepCount}, "AddStep")).get(
            "data", {}
        )

    async def shutdown_a(self, wuid: str) -> bool:
        # ownUser id
        return await self.isAdmin_a(wuid, gm.WATCH_M.get("shutdownM", ""), {"uid": wuid}, "ShutDown")

    async def reboot_a(self, wuid: str) -> bool:
        # ownUser id
        return await self.isAdmin_a(wuid, gm.WATCH_M.get("rebootM", ""), {"uid": wuid}, "reboot")

    async def modifyAlert_a(self, id: str, yesOrNo: str) -> dict[str, Any]:
        # function?
        return await self.runAuthorizedGqlQuery_a(
            gm.WATCH_M.get("modifyAlertM", ""), {"uid": id, "remind": yesOrNo}, "modifyAlert"
        )

    async def setEnableSlientTime_a(self, silentId: str, status: str = NormalStatus.ENABLE.value) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gm.WATCH_M.get("setEnableSlientTimeM", ""), {"silentId": silentId, "status": status}, "SetEnableSlientTime"
            )
        ).get("data", {})

    async def setEnableAlarmTime_a(self, alarmId: str, status: str = NormalStatus.ENABLE.value) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gm.WATCH_M.get("modifyAlarmM", ""), {"alarmId": alarmId, "status": status}, "ModifyAlarm"
            )
        ).get("data", {})

    async def setReadChatMsg_a(self, wuid: str, msgId: str, id: str) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gm.WATCH_M.get("setReadChatMsgM", ""), {"uid": wuid, "msgId": msgId, "id": id}, "setReadChatMsg"
            )
        ).get("data", {})

    async def submitIncorrectLocationData_a(self, wuid: str, lat: str, lng: str, timestamp: str) -> dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gm.WATCH_M.get("submitIncorrectLocationDataM", ""),
                {"uid": wuid, "lat": lat, "lng": lng, "timestamp": timestamp},
                "SubmitIncorrectLocationData",
            )
        ).get("data", {})

    async def modifyContact_a(self, contactId: str, isAdmin: bool, contactName: str = "", fileId: str = "") -> dict[str, Any]:
        return await self.runAuthorizedGqlQuery_a(
            gm.WATCH_M.get("modifyContactM", ""),
            {"contactId": contactId, "contactName": contactName, "fileId": fileId, "isAdmin": isAdmin},
        )

    async def issueEmailOrPhoneCode_a(
        self,
        purpose: EmailAndPhoneVerificationTypeV2 = EmailAndPhoneVerificationTypeV2.UNKNOWN__,
        type: UserContactType = UserContactType.UNKNOWN__,
        email: str = "",
        phoneNumber: str = "",
        countryCode: str = "",
        previousToken: str = "",
    ) -> dict[str, Any]:
        return await self.runAuthorizedGqlQuery_a(
            gm.SIGN_M.get("issueEmailOrPhoneCodeM", ""),
            {
                "purpose": purpose.value,
                "type": type.value,
                "email": email,
                "phoneNumber": phoneNumber,
                "countryCode": countryCode,
                "previousToken": previousToken,
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
        return await self.runAuthorizedGqlQuery_a(
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

    async def verifyCaptcha_a(self, captchaString: str = "", type: str = "") -> dict[str, Any]:
        return await self.runAuthorizedGqlQuery_a(
            gm.SIGN_M.get("verifyCaptchaM", ""), {"captchaString": captchaString, "type": type}, "verifyCaptcha"
        )

    async def verifyEmailOrPhoneCode_a(
        self,
        type: UserContactType = UserContactType.UNKNOWN__,
        email: str = "",
        phoneNumber: str = "",
        countryCode: str = "",
        verifyCode: str = "",
        verificationToken: str = "",
    ) -> dict[str, Any]:
        return await self.runAuthorizedGqlQuery_a(
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

    ########## SECTION MUTATION end ##########
