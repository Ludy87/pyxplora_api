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

    def runGqlQuery(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        if query is None:
            raise Exception("GraphQL guery string MUST NOT be empty!")
        # Add Xplora® API headers
        requestHeaders = self.getRequestHeaders("application/json; charset=UTF-8")
        # create GQLClient
        gqlClient = GraphqlClient(endpoint=ENDPOINT, headers=requestHeaders)
        # execute QUERY|MUTATION
        data: Dict[str, Any] = gqlClient.execute(query=query, variables=variables)
        return data

    def runAuthorizedGqlQuery(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        if self.accessToken is None:
            raise Exception("You must first login to the Xplora® API.")
        # Run GraphQL query and return
        return self.runGqlQuery(query, variables)

    def login(self) -> Dict[str, Any]:
        data = self.runGqlQuery(gm.SIGN_M.get("issueTokenM", ""), self.variables)["data"]
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

    def isAdmin(self, wuid: str, query: str, variables: Dict[str, Any], key: str) -> bool:
        contacts: Dict[str, Any] = self.getWatchUserContacts(wuid)
        for contact in contacts["contacts"]["contacts"]:
            try:
                id = contact["contactUser"]["id"]
            except KeyError and TypeError:
                id = None
            if self.userId == id:
                if contact["guardianType"] == "FIRST":
                    return self.runAuthorizedGqlQuery(query, variables)["data"][key]
        raise NoAdminError()

    ########## SECTION QUERY start ##########

    def askWatchLocate(self, wuid: str) -> Dict[str, Any]:
        res: Dict[str, Any] = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("askLocateQ", ""), {"uid": wuid})["data"]
        if res["askWatchLocate"] is not None:
            return res
        return {"askWatchLocate": False}

    def getWatchUserContacts(self, wuid: str) -> Dict[str, Any]:
        # Contacts from ownUser
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("contactsQ", ""), {"uid": wuid})["data"]

    def getWatches(self, wuid: str) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("watchesQ", ""), {"uid": wuid})["data"]

    def getSWInfo(self, qrCode: str) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("checkByQrCodeQ", ""), {"qrCode": qrCode})["data"]

    def getWatchState(self, qrCode: str, qrt: str = "", qrc: str = "") -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("stateQ", ""), {"qrCode": qrCode, "qrt": qrt, "qrc": qrc})["data"]

    def getWatchLastLocation(self, wuid: str) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("locateQ", ""), {"uid": wuid})["data"]

    def trackWatch(self, wuid: str) -> Dict[str, Any]:
        # tracking time - seconds
        res = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("trackQ", ""), {"uid": wuid})["data"]
        if res["trackWatch"] is not None:
            return res
        return {"trackWatch": -1}

    def getAlarmTime(self, wuid: str) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("alarmsQ", ""), {"uid": wuid})["data"]

    def getWifi(self, wuid: str) -> Dict[str, Any]:
        # without function?
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("getWifisQ", ""), {"uid": wuid})["data"]

    def unReadChatMsgCount(self, wuid: str) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("unReadChatMsgCountQ", ""), {"uid": wuid})["data"]

    def safeZones(self, wuid: str) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("safeZonesQ", ""), {"uid": wuid})["data"]

    def safeZoneGroups(self) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("safeZoneGroupsQ", ""), {})["data"]

    def silentTimes(self, wuid: str) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("silentTimesQ", ""), {"uid": wuid})["data"]

    def chats(self, wuid: str, offset: int = 0, limit: int = 100, msgId: str = "") -> Dict[str, Any]:
        # ownUser id
        return self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("chatsQ", ""), {"uid": wuid, "offset": offset, "limit": limit, "msgId": msgId}
        )["data"]

    def fetchChatImage(self, wuid: str, msgId: str) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("fetchChatImageQ", ""), {"uid": wuid, "msgId": msgId})["data"]

    def fetchChatMp3(self, wuid: str, msgId: str) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("fetchChatMp3Q", ""), {"uid": wuid, "msgId": msgId})["data"]

    def fetchChatShortVideo(self, wuid: str, msgId: str) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("fetchChatShortVideoQ", ""), {"uid": wuid, "msgId": msgId})["data"]

    def fetchChatVoice(self, wuid: str, msgId: str) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("fetchChatVoiceQ", ""), {"uid": wuid, "msgId": msgId})["data"]

    def watchImei(self, imei: str, qrCode: str, deviceKey: str) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("imeiQ", ""), {"imei": imei, "qrCode": qrCode, "deviceKey": deviceKey}
        )["data"]

    def getWatchLocHistory(self, wuid: str, date: int, tz: str, limit: int) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("locHistoryQ", ""), {"uid": wuid, "date": date, "tz": tz, "limit": limit}
        )["data"]

    def watchesDynamic(self) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("watchesDynamicQ", ""), {})["data"]

    def coinHistory(self, wuid: str, start: int, end: int, type: str, offset: int, limit: int) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.XCOIN_Q.get("historyQ", ""),
            {"uid": wuid, "start": start, "end": end, "type": type, "offset": offset, "limit": limit},
        )["data"]

    def reminders(self, wuid: str) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.XMOVE_Q.get("remindersQ", ""), {"uid": wuid})["data"]

    def groups(self, isCampaign: bool) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.CARD_Q.get("groupsQ", ""), {"isCampaign": isCampaign})["data"]

    def dynamic(self) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.CARD_Q.get("dynamicQ", ""), {})["data"]

    def staticCard(self) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.CARD_Q.get("staticQ", ""), {})["data"]

    def familyInfo(self, wuid: str, watchId: str, tz: str, date: int) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.FAMILY_Q.get("infoQ", ""), {"uid": wuid, "watchId": watchId, "tz": tz, "date": date}
        )["data"]

    def getMyTotalInfo(
        self, wuid: str, tz: str, date: int, start: int, end: int, type: str, offset: int, limit: int
    ) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.MYINFO_Q.get("getMyTotalInfoQ", ""),
            {"uid": wuid, "tz": tz, "date": date, "start": start, "end": end, "type": type, "offset": offset, "limit": limit},
        )["data"]

    def myInfoWithCoinHistory(
        self, wuid: str, start: int, end: int, tz: str, type: str, offset: int, limit: int
    ) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.MYINFO_Q.get("coinHistoryQ", ""),
            {"uid": wuid, "start": start, "end": end, "tz": tz, "type": type, "offset": offset, "limit": limit},
        )["data"]

    def getMyInfo(self) -> Dict[str, Any]:
        # Profil from login Account
        return self.runAuthorizedGqlQuery(gq.MYINFO_Q.get("readQ", ""), {})["data"]

    def readCampaignProfile(self) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gq.MYINFO_Q.get("readCampaignProfileQ", ""),
            {},
        )["data"]

    def getReviewStatus(self, wuid: str) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.REVIEW_Q.get("getStatusQ", ""), {"uid": wuid})["data"]

    def getWatchUserSteps(self, wuid: str, tz: str, date: int) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.STEP_Q.get("userQ", ""), {"uid": wuid, "tz": tz, "date": date})["data"]

    def countries(self) -> Dict[str, Any]:
        # Country Support
        return self.runAuthorizedGqlQuery(gq.UTILS_Q.get("countriesQ", ""), {})["data"]

    def subscribedCampaign(self, wuid: str, needDetail: bool = False) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.CAMPAIGN_Q.get("subscribedQ", ""), {"uid": wuid, "needDetail": needDetail})[
            "data"
        ]

    def avatars(self, id: str) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.CAMPAIGN_Q.get("avatarsQ", ""), {"id": id})["data"]

    def getFollowRequestWatchCount(self) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.CAMPAIGN_Q.get("followRequestWatchCountQ", ""), {})["data"]

    def campaigns(self, id: str, categoryId: str) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.CAMPAIGN_Q.get("campaignsQ", ""), {"id": id, "categoryId": categoryId})["data"]

    def isSubscribed(self, id: str, wuid: str) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.CAMPAIGN_Q.get("isSubscribedQ", ""), {"id": id, "uid": wuid})["data"]

    def subscribed(self, wuid: str, needDetail: bool) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.CAMPAIGN_Q.get("subscribedQ", ""), {"uid": wuid, "needDetail": needDetail})[
            "data"
        ]

    def ranks(self, campaignId: str) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.CAMPAIGN_Q.get("ranksQ", ""), {"campaignId": campaignId})["data"]

    def campaignUserProfiles(self) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.CAMPAIGN_Q.get("campaignUserProfilesQ", ""), {})["data"]

    def conv360IDToO2OID(self, qid: str, deviceId: str) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.QUERY.get("conv360IDToO2OIDQ", ""), {"qid": qid, "deviceId": deviceId})["data"]

    def watchGroups(self, id: str = "") -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gq.WATCHGROUP_Q.get("watchGroupsQ", ""), {"id": id})["data"]

    ########## SECTION QUERY end ##########

    ########## SECTION MUTATION start ##########

    def sendText(self, wuid: str, text: str) -> bool:
        # ownUser id
        if (
            self.runAuthorizedGqlQuery(gm.WATCH_M.get("sendChatTextM", ""), {"uid": wuid, "text": text})["data"][
                "sendChatText"
            ]
            is not None
        ):
            return True
        return False

    def addStep(self, stepCount: int) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gm.STEP_M.get("addM", ""), {"stepCount": stepCount})["data"]

    def shutdown(self, wuid: str) -> bool:
        # ownUser id
        return self.isAdmin(wuid, gm.WATCH_M.get("shutdownM", ""), {"uid": wuid}, "shutDown")

    def reboot(self, wuid: str) -> bool:
        # ownUser id
        return self.isAdmin(wuid, gm.WATCH_M.get("rebootM", ""), {"uid": wuid}, "reboot")

    def modifyAlert(self, id: str, yesOrNo: YesOrNo) -> Dict[str, Any]:
        # function?
        return self.runAuthorizedGqlQuery(gm.WATCH_M.get("modifyAlertM", ""), {"uid": id, "remind": yesOrNo})

    def setEnableSlientTime(self, silentId: str, status: str = NormalStatus.ENABLE.value) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(
            gm.WATCH_M.get("setEnableSlientTimeM", ""), {"silentId": silentId, "status": status}
        )["data"]

    def setEnableAlarmTime(self, alarmId: str, status: str = NormalStatus.ENABLE.value) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gm.WATCH_M.get("modifyAlarmM", ""), {"alarmId": alarmId, "status": status})["data"]

    def setReadChatMsg(self, wuid: str, msgId: str, id: str) -> Dict[str, Any]:
        return self.runAuthorizedGqlQuery(gm.WATCH_M.get("setReadChatMsgM", ""), {"uid": wuid, "msgId": msgId, "id": id})[
            "data"
        ]

    ########## SECTION MUTATION end ##########
