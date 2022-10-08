from __future__ import annotations

from python_graphql_client import GraphqlClient

from .const import ENDPOINT
from .exception_classes import LoginError, NoAdminError
from .handler_gql import HandlerGQL
from .status import NormalStatus, YesOrNo

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
        email: str = None,
    ) -> None:
        super().__init__(countryPhoneNumber, phoneNumber, password, userLang, timeZone, email)

    async def runGqlQuery_a(self, query: str, variables: dict[str, any]) -> dict[str, any]:
        if query is None:
            raise Exception("GraphQL guery string MUST NOT be empty!")
        # Add Xplora® API headers
        requestHeaders = self.getRequestHeaders("application/json; charset=UTF-8")
        # create GQLClient
        gqlClient = GraphqlClient(endpoint=ENDPOINT, headers=requestHeaders)
        # execute QUERY|MUTATION
        data: dict[str, any] = await gqlClient.execute_async(query=query, variables=variables)
        return data

    async def runAuthorizedGqlQuery_a(self, query: str, variables: dict[str, any]) -> dict[str, any]:
        if self.accessToken is None:
            raise Exception("You must first login to the Xplora® API.")
        # Run GraphQL query and return
        return await self.runGqlQuery_a(query, variables)

    async def login_a(self) -> dict[str, any]:
        if self.email:
            dataAll: dict[str, any] = await self.runGqlQuery_a(gm.SIGN_M.get("signInWithEmailOrPhoneM", ""), self.variables)
        else:
            dataAll: dict[str, any] = await self.runGqlQuery_a(gm.SIGN_M.get("issueTokenM", ""), self.variables)
        errors = dataAll.get("errors", [])
        if errors:
            self.errors.append({"function": "login", "errors": errors})
        data: dict[str, any] = dataAll.get("data", {})
        if data.get("issueToken", data.get("signInWithEmailOrPhone", None)) is None:
            error_message: list[dict[str, str]] = dataAll.get("errors", [{"message": ""}])
            # Login failed.
            raise LoginError("Login to Xplora® API failed. Check your input!\n{}".format(error_message[0].get("message", "")))
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

    async def isAdmin_a(self, wuid: str, query: str, variables: dict[str, any], key: str) -> bool:
        contacts: dict[str, any] = await self.getWatchUserContacts_a(wuid)
        for contact in contacts["contacts"]["contacts"]:
            try:
                id = contact["contactUser"]["id"]
            except KeyError and TypeError:
                id = None
            if self.userId == id:
                if contact["guardianType"] == "FIRST":
                    data: dict[str, any] = (await self.runAuthorizedGqlQuery_a(query, variables)).get("data", {})
                    return data.get(key, False)
        raise NoAdminError()

    ########## SECTION QUERY start ##########

    async def askWatchLocate_a(self, wuid: str) -> dict[str, any]:
        data: dict[str, any] = await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("askLocateQ", ""), {"uid": wuid})
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "askWatchLocate", "errors": errors})
        res: dict[str, any] = data.get("data", {})
        if res["askWatchLocate"] is not None:
            return res
        return {"askWatchLocate": False}

    async def getWatchUserContacts_a(self, wuid: str) -> dict[str, any]:
        # Contacts from ownUser
        data: dict[str, any] = await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("contactsQ", ""), {"uid": wuid})
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchUserContacts", "errors": errors})
        return data.get("data", {})

    async def getWatches_a(self, wuid: str) -> dict[str, any]:
        data: dict[str, any] = await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("watchesQ", ""), {"uid": wuid})
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatches", "errors": errors})
        return data.get("data", {})

    async def getSWInfo_a(self, qrCode: str) -> dict[str, any]:
        data: dict[str, any] = await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("checkByQrCodeQ", ""), {"qrCode": qrCode})
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getSWInfo", "errors": errors})
        return data.get("data", {})

    async def getWatchState_a(self, qrCode: str, qrt: str = "", qrc: str = "") -> dict[str, any]:
        vari = {}
        if qrCode != "":
            vari["qrCode"] = qrCode
        if qrt != "":
            vari["qrt"] = qrt
        if qrc != "":
            vari["qrc"] = qrc
        data: dict[str, any] = await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("stateQ", ""), vari)
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchState", "errors": errors})
        return data.get("data", {})

    async def getWatchLastLocation_a(self, wuid: str) -> dict[str, any]:
        data: dict[str, any] = await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("locateQ", ""), {"uid": wuid})
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchLastLocation", "errors": errors})
        return data.get("data", {})

    async def trackWatch_a(self, wuid: str) -> dict[str, any]:
        # tracking time - seconds
        data: dict[str, any] = await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("trackQ", ""), {"uid": wuid})
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "trackWatch", "errors": errors})
        res = data.get("data", {})
        if res.get("trackWatch", {"trackWatch": -1}):
            return res
        return {"trackWatch": -1}

    async def getAlarmTime_a(self, wuid: str) -> dict[str, any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("alarmsQ", ""), {"uid": wuid})).get("data", {})

    async def getWifi_a(self, wuid: str) -> dict[str, any]:
        # without function?
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("getWifisQ", ""), {"uid": wuid})).get("data", {})

    async def unReadChatMsgCount_a(self, wuid: str) -> dict[str, any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("unReadChatMsgCountQ", ""), {"uid": wuid})).get("data", {})

    async def safeZones_a(self, wuid: str) -> dict[str, any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("safeZonesQ", ""), {"uid": wuid})).get("data", {})

    async def safeZoneGroups_a(self) -> dict[str, any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("safeZoneGroupsQ", ""), {})).get("data", {})

    async def silentTimes_a(self, wuid: str) -> dict[str, any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("silentTimesQ", ""), {"uid": wuid})).get("data", {})

    async def chats_a(self, wuid: str, offset: int = 0, limit: int = 100, msgId: str = "") -> dict[str, any]:
        # ownUser id
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.WATCH_Q.get("chatsQ", ""), {"uid": wuid, "offset": offset, "limit": limit, "msgId": msgId}
            )
        ).get("data", {})

    async def fetchChatImage_a(self, wuid: str, msgId: str) -> dict[str, any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("fetchChatImageQ", ""), {"uid": wuid, "msgId": msgId})).get(
            "data", {}
        )

    async def fetchChatMp3_a(self, wuid: str, msgId: str) -> dict[str, any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("fetchChatMp3Q", ""), {"uid": wuid, "msgId": msgId})).get(
            "data", {}
        )

    async def fetchChatShortVideo_a(self, wuid: str, msgId: str) -> dict[str, any]:
        return (
            await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("fetchChatShortVideoQ", ""), {"uid": wuid, "msgId": msgId})
        ).get("data", {})

    async def fetchChatShortVideoCover_a(self, wuid: str, msgId: str) -> dict[str, any]:
        return (
            await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("fetchChatShortVideoCoverQ", ""), {"uid": wuid, "msgId": msgId})
        ).get("data", {})

    async def fetchChatVoice_a(self, wuid: str, msgId: str) -> dict[str, any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("fetchChatVoiceQ", ""), {"uid": wuid, "msgId": msgId})).get(
            "data", {}
        )

    async def watchImei_a(self, imei: str, qrCode: str, deviceKey: str) -> dict[str, any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.WATCH_Q.get("imeiQ", ""), {"imei": imei, "qrCode": qrCode, "deviceKey": deviceKey}
            )
        ).get("data", {})

    async def getWatchLocHistory_a(self, wuid: str, date: int, tz: str, limit: int) -> dict[str, any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.WATCH_Q.get("locHistoryQ", ""), {"uid": wuid, "date": date, "tz": tz, "limit": limit}
            )
        ).get("data", {})

    async def watchesDynamic_a(self) -> dict[str, any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("watchesDynamicQ", ""), {})).get("data", {})

    async def coinHistory_a(self, wuid: str, start: int, end: int, type: str, offset: int, limit: int) -> dict[str, any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.XCOIN_Q.get("historyQ", ""),
                {"uid": wuid, "start": start, "end": end, "type": type, "offset": offset, "limit": limit},
            )
        ).get("data", {})

    async def reminders_a(self, wuid: str) -> dict[str, any]:
        return (await self.runAuthorizedGqlQuery_a(gq.XMOVE_Q.get("remindersQ", ""), {"uid": wuid})).get("data", {})

    async def groups_a(self, isCampaign: bool) -> dict[str, any]:
        return (await self.runAuthorizedGqlQuery_a(gq.CARD_Q.get("groupsQ", ""), {"isCampaign": isCampaign})).get("data", {})

    async def dynamic_a(self) -> dict[str, any]:
        return (await self.runAuthorizedGqlQuery_a(gq.CARD_Q.get("dynamicQ", ""), {})).get("data", {})

    async def staticCard_a(self) -> dict[str, any]:
        return (await self.runAuthorizedGqlQuery_a(gq.CARD_Q.get("staticQ", ""), {})).get("data", {})

    async def familyInfo_a(self, wuid: str, watchId: str, tz: str, date: int) -> dict[str, any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.FAMILY_Q.get("infoQ", ""), {"uid": wuid, "watchId": watchId, "tz": tz, "date": date}
            )
        ).get("data", {})

    async def getMyTotalInfo_a(
        self, wuid: str, tz: str, date: int, start: int, end: int, type: str, offset: int, limit: int
    ) -> dict[str, any]:
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
            )
        ).get("data", {})

    async def myInfoWithCoinHistory_a(
        self, wuid: str, start: int, end: int, tz: str, type: str, offset: int, limit: int
    ) -> dict[str, any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.MYINFO_Q.get("coinHistoryQ", ""),
                {"uid": wuid, "start": start, "end": end, "tz": tz, "type": type, "offset": offset, "limit": limit},
            )
        ).get("data", {})

    async def getMyInfo_a(self) -> dict[str, any]:
        # Profil from login Account
        return (await self.runAuthorizedGqlQuery_a(gq.MYINFO_Q.get("readQ", ""), {})).get("data", {})

    async def readCampaignProfile_a(self) -> dict[str, any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.MYINFO_Q.get("readCampaignProfileQ", ""),
                {},
            )
        ).get("data", {})

    async def getReviewStatus_a(self, wuid: str) -> dict[str, any]:
        return (await self.runAuthorizedGqlQuery_a(gq.REVIEW_Q.get("getStatusQ", ""), {"uid": wuid})).get("data", {})

    async def getWatchUserSteps_a(self, wuid: str, tz: str, date: int) -> dict[str, any]:
        data: dict[str, any] = await self.runAuthorizedGqlQuery_a(
            gq.STEP_Q.get("userQ", ""), {"uid": wuid, "tz": tz, "date": date}
        )
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchUserSteps", "errors": errors})
        return data.get("data", {})

    async def countries_a(self) -> dict[str, any]:
        # Country Support
        return (await self.runAuthorizedGqlQuery_a(gq.UTILS_Q.get("countriesQ", ""), {})).get("data", {})

    async def subscribedCampaign_a(self, wuid: str, needDetail: bool = False) -> dict[str, any]:
        return (
            await self.runAuthorizedGqlQuery_a(gq.CAMPAIGN_Q.get("subscribedQ", ""), {"uid": wuid, "needDetail": needDetail})
        ).get("data", {})

    async def avatars_a(self, id: str) -> dict[str, any]:
        return (await self.runAuthorizedGqlQuery_a(gq.CAMPAIGN_Q.get("avatarsQ", ""), {"id": id})).get("data", {})

    async def getFollowRequestWatchCount_a(self) -> dict[str, any]:
        return (await self.runAuthorizedGqlQuery_a(gq.CAMPAIGN_Q.get("followRequestWatchCountQ", ""), {})).get("data", {})

    async def campaigns_a(self, id: str, categoryId: str) -> dict[str, any]:
        return (
            await self.runAuthorizedGqlQuery_a(gq.CAMPAIGN_Q.get("campaignsQ", ""), {"id": id, "categoryId": categoryId})
        ).get("data", {})

    async def isSubscribed_a(self, id: str, wuid: str) -> dict[str, any]:
        return (await self.runAuthorizedGqlQuery_a(gq.CAMPAIGN_Q.get("isSubscribedQ", ""), {"id": id, "uid": wuid})).get(
            "data", {}
        )

    async def subscribed_a(self, wuid: str, needDetail: bool) -> dict[str, any]:
        return (
            await self.runAuthorizedGqlQuery_a(gq.CAMPAIGN_Q.get("subscribedQ", ""), {"uid": wuid, "needDetail": needDetail})
        ).get("data", {})

    async def ranks_a(self, campaignId: str) -> dict[str, any]:
        return (await self.runAuthorizedGqlQuery_a(gq.CAMPAIGN_Q.get("ranksQ", ""), {"campaignId": campaignId})).get(
            "data", {}
        )

    async def campaignUserProfiles_a(self) -> dict[str, any]:
        return (await self.runAuthorizedGqlQuery_a(gq.CAMPAIGN_Q.get("campaignUserProfilesQ", ""), {})).get("data", {})

    async def conv360IDToO2OID_a(self, qid: str, deviceId: str) -> dict[str, any]:
        return (
            await self.runAuthorizedGqlQuery_a(gq.QUERY.get("conv360IDToO2OIDQ", ""), {"qid": qid, "deviceId": deviceId})
        ).get("data", {})

    async def getAppVersion_a(self) -> dict[str, any]:
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY.get("getAppVersionQ", ""), {})).get("data", {})

    async def watchGroups_a(self, id: str = "") -> dict[str, any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCHGROUP_Q.get("watchGroupsQ", ""), {"id": id})).get("data", {})

    async def getStartTrackingWatch_a(self, wuid: str) -> dict[str, any]:
        data = await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("startTrackingWatchQ", ""), {"uid": wuid})
        errors: list[dict[str, str]] = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getStartTrackingWatch", "error": errors})
        return data.get("data", {})

    async def getEndTrackingWatch_a(self, wuid: str) -> dict[str, any]:
        data = await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("endTrackingWatchQ", ""), {"uid": wuid})
        errors: list[dict[str, str]] = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getEndTrackingWatch", "error": errors})
        return data.get("data", {})

    ########## SECTION QUERY end ##########

    ########## SECTION MUTATION start ##########

    async def sendText_a(self, wuid: str, text: str) -> bool:
        # ownUser id
        if (await self.runAuthorizedGqlQuery_a(gm.WATCH_M.get("sendChatTextM", ""), {"uid": wuid, "text": text})).get(
            "data", {}
        )["sendChatText"] is not None:
            return True
        return False

    async def addStep_a(self, stepCount: int) -> dict[str, any]:
        return (await self.runAuthorizedGqlQuery_a(gm.STEP_M.get("addM", ""), {"stepCount": stepCount})).get("data", {})

    async def shutdown_a(self, wuid: str) -> bool:
        # ownUser id
        return await self.isAdmin_a(wuid, gm.WATCH_M.get("shutdownM", ""), {"uid": wuid}, "shutDown")

    async def reboot_a(self, wuid: str) -> bool:
        # ownUser id
        return await self.isAdmin_a(wuid, gm.WATCH_M.get("rebootM", ""), {"uid": wuid}, "reboot")

    async def modifyAlert_a(self, id: str, yesOrNo: YesOrNo) -> dict[str, any]:
        # function?
        return await self.runAuthorizedGqlQuery_a(gm.WATCH_M.get("modifyAlertM", ""), {"uid": id, "remind": yesOrNo})

    async def setEnableSlientTime_a(self, silentId: str, status: str = NormalStatus.ENABLE.value) -> dict[str, any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gm.WATCH_M.get("setEnableSlientTimeM", ""),
                {"silentId": silentId, "status": status},
            )
        ).get("data", {})

    async def setEnableAlarmTime_a(self, alarmId: str, status: str = NormalStatus.ENABLE.value) -> dict[str, any]:
        return (
            await self.runAuthorizedGqlQuery_a(gm.WATCH_M.get("modifyAlarmM", ""), {"alarmId": alarmId, "status": status})
        ).get("data", {})

    async def setReadChatMsg(self, wuid: str, msgId: str, id: str) -> dict[str, any]:
        return (
            await self.runAuthorizedGqlQuery_a(gm.WATCH_M.get("setReadChatMsgM", ""), {"uid": wuid, "msgId": msgId, "id": id})
        ).get("data", {})

    async def submitIncorrectLocationData(self, wuid: str, lat: str, lng: str, timestamp: str) -> dict[str, any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gm.WATCH_M.get("submitIncorrectLocationDataM", ""),
                {"uid": wuid, "lat": lat, "lng": lng, "timestamp": timestamp},
            )
        ).get("data", {})

    ########## SECTION MUTATION end ##########
