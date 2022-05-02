from __future__ import annotations

from typing import Any, Dict

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
    ) -> None:
        super().__init__(countryPhoneNumber, phoneNumber, password, userLang, timeZone)

    async def runGqlQuery_a(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        if query is None:
            raise Exception("GraphQL guery string MUST NOT be empty!")
        # Add Xplora® API headers
        requestHeaders = self.getRequestHeaders("application/json; charset=UTF-8")
        # create GQLClient
        gqlClient = GraphqlClient(endpoint=ENDPOINT, headers=requestHeaders)
        # execute QUERY|MUTATION
        data: Dict[str, Any] = await gqlClient.execute_async(query=query, variables=variables)
        return data

    async def runAuthorizedGqlQuery_a(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        if self.accessToken is None:
            raise Exception("You must first login to the Xplora® API.")
        # Run GraphQL query and return
        return await self.runGqlQuery_a(query, variables)

    async def login_a(self) -> Dict[str, Any]:
        data: Dict[str, Any] = (await self.runGqlQuery_a(gm.SIGN_M.get("issueTokenM", ""), self.variables))["data"]
        if data["issueToken"] is None:
            # Login failed.
            raise LoginError("Login to Xplora® API failed. Check your input!")
        self.issueToken = data["issueToken"]

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

    async def isAdmin_a(self, wuid: str, query: str, variables: Dict[str, Any], key: str) -> bool:
        contacts: Dict[str, Any] = await self.getWatchUserContacts_a(wuid)
        for contact in contacts["contacts"]["contacts"]:
            try:
                id = contact["contactUser"]["id"]
            except KeyError and TypeError:
                id = None
            if self.userId == id:
                if contact["guardianType"] == "FIRST":
                    return (await self.runAuthorizedGqlQuery_a(query, variables))["data"][key]
        raise NoAdminError()

    ########## SECTION QUERY start ##########

    async def askWatchLocate_a(self, wuid: str) -> Dict[str, Any]:
        res: Dict[str, Any] = (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("askLocateQ", ""), {"uid": wuid}))["data"]
        if res["askWatchLocate"] is not None:
            return res
        return {"askWatchLocate": False}

    async def getWatchUserContacts_a(self, wuid: str) -> Dict[str, Any]:
        # Contacts from ownUser
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("contactsQ", ""), {"uid": wuid}))["data"]

    async def getWatches_a(self, wuid: str) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("watchesQ", ""), {"uid": wuid}))["data"]

    async def getSWInfo_a(self, qrCode: str) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("checkByQrCodeQ", ""), {"qrCode": qrCode}))["data"]

    async def getWatchState_a(self, qrCode: str, qrt: str = "", qrc: str = "") -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("stateQ", ""), {"qrCode": qrCode, "qrt": qrt, "qrc": qrc}))[
            "data"
        ]

    async def getWatchLastLocation_a(self, wuid: str) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("locateQ", ""), {"uid": wuid}))["data"]

    async def trackWatch_a(self, wuid: str) -> Dict[str, Any]:
        # tracking time - seconds
        res = (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("trackQ", ""), {"uid": wuid}))["data"]
        if res["trackWatch"] is not None:
            return res
        return {"trackWatch": -1}

    async def getAlarmTime_a(self, wuid: str) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("alarmsQ", ""), {"uid": wuid}))["data"]

    async def getWifi_a(self, wuid: str) -> Dict[str, Any]:
        # without function?
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("getWifisQ", ""), {"uid": wuid}))["data"]

    async def unReadChatMsgCount_a(self, wuid: str) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("unReadChatMsgCountQ", ""), {"uid": wuid}))["data"]

    async def safeZones_a(self, wuid: str) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("safeZonesQ", ""), {"uid": wuid}))["data"]

    async def safeZoneGroups_a(self) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("safeZoneGroupsQ", ""), {}))["data"]

    async def silentTimes_a(self, wuid: str) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("silentTimesQ", ""), {"uid": wuid}))["data"]

    async def chats_a(self, wuid: str, offset: int = 0, limit: int = 100, msgId: str = "") -> Dict[str, Any]:
        # ownUser id
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.WATCH_Q.get("chatsQ", ""), {"uid": wuid, "offset": offset, "limit": limit, "msgId": msgId}
            )
        )["data"]

    async def fetchChatImage_a(self, wuid: str, msgId: str) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("fetchChatImageQ", ""), {"uid": wuid, "msgId": msgId}))[
            "data"
        ]

    async def fetchChatMp3_a(self, wuid: str, msgId: str) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("fetchChatMp3Q", ""), {"uid": wuid, "msgId": msgId}))["data"]

    async def fetchChatShortVideo_a(self, wuid: str, msgId: str) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("fetchChatShortVideoQ", ""), {"uid": wuid, "msgId": msgId}))[
            "data"
        ]

    async def fetchChatVoice_a(self, wuid: str, msgId: str) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("fetchChatVoiceQ", ""), {"uid": wuid, "msgId": msgId}))[
            "data"
        ]

    async def watchImei_a(self, imei: str, qrCode: str, deviceKey: str) -> Dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.WATCH_Q.get("imeiQ", ""), {"imei": imei, "qrCode": qrCode, "deviceKey": deviceKey}
            )
        )["data"]

    async def getWatchLocHistory_a(self, wuid: str, date: int, tz: str, limit: int) -> Dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.WATCH_Q.get("locHistoryQ", ""), {"uid": wuid, "date": date, "tz": tz, "limit": limit}
            )
        )["data"]

    async def watchesDynamic_a(self) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q.get("watchesDynamicQ", ""), {}))["data"]

    async def coinHistory_a(self, wuid: str, start: int, end: int, type: str, offset: int, limit: int) -> Dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.XCOIN_Q.get("historyQ", ""),
                {"uid": wuid, "start": start, "end": end, "type": type, "offset": offset, "limit": limit},
            )
        )["data"]

    async def reminders_a(self, wuid: str) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.XMOVE_Q.get("remindersQ", ""), {"uid": wuid}))["data"]

    async def groups_a(self, isCampaign: bool) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.CARD_Q.get("groupsQ", ""), {"isCampaign": isCampaign}))["data"]

    async def dynamic_a(self) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.CARD_Q.get("dynamicQ", ""), {}))["data"]

    async def staticCard_a(self) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.CARD_Q.get("staticQ", ""), {}))["data"]

    async def familyInfo_a(self, wuid: str, watchId: str, tz: str, date: int) -> Dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.FAMILY_Q.get("infoQ", ""), {"uid": wuid, "watchId": watchId, "tz": tz, "date": date}
            )
        )["data"]

    async def getMyTotalInfo_a(
        self, wuid: str, tz: str, date: int, start: int, end: int, type: str, offset: int, limit: int
    ) -> Dict[str, Any]:
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
        )["data"]

    async def myInfoWithCoinHistory_a(
        self, wuid: str, start: int, end: int, tz: str, type: str, offset: int, limit: int
    ) -> Dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.MYINFO_Q.get("coinHistoryQ", ""),
                {"uid": wuid, "start": start, "end": end, "tz": tz, "type": type, "offset": offset, "limit": limit},
            )
        )["data"]

    async def getMyInfo_a(self) -> Dict[str, Any]:
        # Profil from login Account
        return (await self.runAuthorizedGqlQuery_a(gq.MYINFO_Q.get("readQ", ""), {}))["data"]

    async def readCampaignProfile_a(self) -> Dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gq.MYINFO_Q.get("readCampaignProfileQ", ""),
                {},
            )
        )["data"]

    async def getReviewStatus_a(self, wuid: str) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.REVIEW_Q.get("getStatusQ", ""), {"uid": wuid}))["data"]

    async def getWatchUserSteps_a(self, wuid: str, tz: str, date: int) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.STEP_Q.get("userQ", ""), {"uid": wuid, "tz": tz, "date": date}))["data"]

    async def countries_a(self) -> Dict[str, Any]:
        # Country Support
        return (await self.runAuthorizedGqlQuery_a(gq.UTILS_Q.get("countriesQ", ""), {}))["data"]

    async def subscribedCampaign_a(self, wuid: str, needDetail: bool = False) -> Dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(gq.CAMPAIGN_Q.get("subscribedQ", ""), {"uid": wuid, "needDetail": needDetail})
        )["data"]

    async def avatars_a(self, id: str) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.CAMPAIGN_Q.get("avatarsQ", ""), {"id": id}))["data"]

    async def getFollowRequestWatchCount_a(self) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.CAMPAIGN_Q.get("followRequestWatchCountQ", ""), {}))["data"]

    async def campaigns_a(self, id: str, categoryId: str) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.CAMPAIGN_Q.get("campaignsQ", ""), {"id": id, "categoryId": categoryId}))[
            "data"
        ]

    async def isSubscribed_a(self, id: str, wuid: str) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.CAMPAIGN_Q.get("isSubscribedQ", ""), {"id": id, "uid": wuid}))["data"]

    async def subscribed_a(self, wuid: str, needDetail: bool) -> Dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(gq.CAMPAIGN_Q.get("subscribedQ", ""), {"uid": wuid, "needDetail": needDetail})
        )["data"]

    async def ranks_a(self, campaignId: str) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.CAMPAIGN_Q.get("ranksQ", ""), {"campaignId": campaignId}))["data"]

    async def campaignUserProfiles_a(self) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.CAMPAIGN_Q.get("campaignUserProfilesQ", ""), {}))["data"]

    async def conv360IDToO2OID_a(self, qid: str, deviceId: str) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY.get("conv360IDToO2OIDQ", ""), {"qid": qid, "deviceId": deviceId}))[
            "data"
        ]

    async def watchGroups_a(self, id: str = "") -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gq.WATCHGROUP_Q.get("watchGroupsQ", ""), {"id": id}))["data"]

    ########## SECTION QUERY end ##########

    ########## SECTION MUTATION start ##########

    async def sendText_a(self, wuid: str, text: str) -> bool:
        # ownUser id
        if (await self.runAuthorizedGqlQuery_a(gm.WATCH_M.get("sendChatTextM", ""), {"uid": wuid, "text": text}))["data"][
            "sendChatText"
        ] is not None:
            return True
        return False

    async def addStep_a(self, stepCount: int) -> Dict[str, Any]:
        return (await self.runAuthorizedGqlQuery_a(gm.STEP_M.get("addM", ""), {"stepCount": stepCount}))["data"]

    async def shutdown_a(self, wuid: str) -> bool:
        # ownUser id
        return await self.isAdmin_a(wuid, gm.WATCH_M.get("shutdownM", ""), {"uid": wuid}, "shutDown")

    async def reboot_a(self, wuid: str) -> bool:
        # ownUser id
        return await self.isAdmin_a(wuid, gm.WATCH_M.get("rebootM", ""), {"uid": wuid}, "reboot")

    async def modifyAlert_a(self, id: str, yesOrNo: YesOrNo) -> Dict[str, Any]:
        # function?
        return await self.runAuthorizedGqlQuery_a(gm.WATCH_M.get("modifyAlertM", ""), {"uid": id, "remind": yesOrNo})

    async def setEnableSlientTime_a(self, silentId: str, status: str = NormalStatus.ENABLE.value) -> Dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(
                gm.WATCH_M.get("setEnableSlientTimeM", ""),
                {"silentId": silentId, "status": status},
            )
        )["data"]

    async def setEnableAlarmTime_a(self, alarmId: str, status: str = NormalStatus.ENABLE.value) -> Dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(gm.WATCH_M.get("modifyAlarmM", ""), {"alarmId": alarmId, "status": status})
        )["data"]

    async def setReadChatMsg(self, wuid: str, msgId: str, id: str) -> Dict[str, Any]:
        return (
            await self.runAuthorizedGqlQuery_a(gm.WATCH_M.get("setReadChatMsgM", ""), {"uid": wuid, "msgId": msgId, "id": id})
        )["data"]

    ########## SECTION MUTATION end ##########
