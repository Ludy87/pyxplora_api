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

    def runGqlQuery(self, query: str, variables: dict[str, any]) -> dict[str, any]:
        if query is None:
            raise Exception("GraphQL guery string MUST NOT be empty!")
        # Add Xplora® API headers
        requestHeaders = self.getRequestHeaders("application/json; charset=UTF-8")
        # create GQLClient
        gqlClient = GraphqlClient(endpoint=ENDPOINT, headers=requestHeaders)
        # execute QUERY|MUTATION
        data: dict[str, any] = gqlClient.execute(query=query, variables=variables)
        return data

    def runAuthorizedGqlQuery(self, query: str, variables: dict[str, any]) -> dict[str, any]:
        if self.accessToken is None:
            raise Exception("You must first login to the Xplora® API.")
        # Run GraphQL query and return
        return self.runGqlQuery(query, variables)

    def login(self) -> dict[str, any]:
        if self.email:
            dataAll: dict[str, any] = self.runGqlQuery(gm.SIGN_M.get("signInWithEmailOrPhoneM", ""), self.variables)
        else:
            dataAll: dict[str, any] = self.runGqlQuery(gm.SIGN_M.get("issueTokenM", ""), self.variables)
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

    def isAdmin(self, wuid: str, query: str, variables: dict[str, any], key: str) -> bool:
        contacts: dict[str, any] = self.getWatchUserContacts(wuid)
        for contact in contacts["contacts"]["contacts"]:
            try:
                id = contact["contactUser"]["id"]
            except KeyError and TypeError:
                id = None
            if self.userId == id:
                if contact["guardianType"] == "FIRST":
                    data: dict[str, any] = self.runAuthorizedGqlQuery(query, variables).get("data", {})
                    return data.get(key, False)
        raise NoAdminError()

    ########## SECTION QUERY start ##########

    def askWatchLocate(self, wuid: str) -> dict[str, any]:
        data: dict[str, any] = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("askLocateQ", ""), {"uid": wuid})
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "askWatchLocate", "errors": errors})
        res: dict[str, any] = data.get("data", {})
        if res["askWatchLocate"] is not None:
            return res
        return {"askWatchLocate": False}

    def getWatchUserContacts(self, wuid: str) -> dict[str, any]:
        # Contacts from ownUser
        data: dict[str, any] = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("contactsQ", ""), {"uid": wuid})
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchUserContacts", "errors": errors})
        return data.get("data", {})

    def getWatches(self, wuid: str) -> dict[str, any]:
        data: dict[str, any] = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("watchesQ", ""), {"uid": wuid})
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatches", "errors": errors})
        return data.get("data", {})

    def getSWInfo(self, qrCode: str) -> dict[str, any]:
        data: dict[str, any] = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("checkByQrCodeQ", ""), {"qrCode": qrCode})
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getSWInfo", "errors": errors})
        return data.get("data", {})

    def getWatchState(self, qrCode: str, qrt: str = "", qrc: str = "") -> dict[str, any]:
        vari = {}
        if qrCode != "":
            vari["qrCode"] = qrCode
        if qrt != "":
            vari["qrt"] = qrt
        if qrc != "":
            vari["qrc"] = qrc
        data: dict[str, any] = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("stateQ", ""), vari)
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchState", "errors": errors})
        return data.get("data", {})

    def getWatchLastLocation(self, wuid: str) -> dict[str, any]:
        data: dict[str, any] = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("locateQ", ""), {"uid": wuid})
        errors = data.get("errors", [])
        if errors:
            self.errors.append({"function": "getWatchLastLocation", "errors": errors})
        return data.get("data", {})

    def trackWatch(self, wuid: str) -> dict[str, any]:
        # tracking time - seconds
        res: dict[str, any] = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("trackQ", ""), {"uid": wuid}).get("data", {})
        if res.get("trackWatch", {"trackWatch": -1}):
            return res
        return {"trackWatch": -1}

    def getAlarmTime(self, wuid: str) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("alarmsQ", ""), {"uid": wuid}).get("data", {})

    def getWifi(self, wuid: str) -> dict[str, any]:
        # without function?
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("getWifisQ", ""), {"uid": wuid}).get("data", {})

    def unReadChatMsgCount(self, wuid: str) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("unReadChatMsgCountQ", ""), {"uid": wuid}).get("data", {})

    def safeZones(self, wuid: str) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("safeZonesQ", ""), {"uid": wuid}).get("data", {})

    def safeZoneGroups(self) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("safeZoneGroupsQ", ""), {}).get("data", {})

    def silentTimes(self, wuid: str) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("silentTimesQ", ""), {"uid": wuid}).get("data", {})

    def chats(self, wuid: str, offset: int = 0, limit: int = 100, msgId: str = "") -> dict[str, any]:
        # ownUser id
        return self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("chatsQ", ""), {"uid": wuid, "offset": offset, "limit": limit, "msgId": msgId}
        ).get("data", {})

    def fetchChatImage(self, wuid: str, msgId: str) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("fetchChatImageQ", ""), {"uid": wuid, "msgId": msgId}).get("data", {})

    def fetchChatMp3(self, wuid: str, msgId: str) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("fetchChatMp3Q", ""), {"uid": wuid, "msgId": msgId}).get("data", {})

    def fetchChatShortVideo(self, wuid: str, msgId: str) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("fetchChatShortVideoQ", ""), {"uid": wuid, "msgId": msgId}).get(
            "data", {}
        )

    def fetchChatShortVideoCover(self, wuid: str, msgId: str) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("fetchChatShortVideoCoverQ", ""), {"uid": wuid, "msgId": msgId}).get(
            "data", {}
        )

    def fetchChatVoice(self, wuid: str, msgId: str) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("fetchChatVoiceQ", ""), {"uid": wuid, "msgId": msgId}).get("data", {})

    def watchImei(self, imei: str, qrCode: str, deviceKey: str) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("imeiQ", ""), {"imei": imei, "qrCode": qrCode, "deviceKey": deviceKey}
        ).get("data", {})

    def getWatchLocHistory(self, wuid: str, date: int, tz: str, limit: int) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(
            gq.WATCH_Q.get("locHistoryQ", ""), {"uid": wuid, "date": date, "tz": tz, "limit": limit}
        ).get("data", {})

    def watchesDynamic(self) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.WATCH_Q.get("watchesDynamicQ", ""), {}).get("data", {})

    def coinHistory(self, wuid: str, start: int, end: int, type: str, offset: int, limit: int) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(
            gq.XCOIN_Q.get("historyQ", ""),
            {"uid": wuid, "start": start, "end": end, "type": type, "offset": offset, "limit": limit},
        ).get("data", {})

    def reminders(self, wuid: str) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.XMOVE_Q.get("remindersQ", ""), {"uid": wuid}).get("data", {})

    def groups(self, isCampaign: bool) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.CARD_Q.get("groupsQ", ""), {"isCampaign": isCampaign}).get("data", {})

    def dynamic(self) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.CARD_Q.get("dynamicQ", ""), {}).get("data", {})

    def staticCard(self) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.CARD_Q.get("staticQ", ""), {}).get("data", {})

    def familyInfo(self, wuid: str, watchId: str, tz: str, date: int) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(
            gq.FAMILY_Q.get("infoQ", ""), {"uid": wuid, "watchId": watchId, "tz": tz, "date": date}
        ).get("data", {})

    def getMyTotalInfo(
        self, wuid: str, tz: str, date: int, start: int, end: int, type: str, offset: int, limit: int
    ) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(
            gq.MYINFO_Q.get("getMyTotalInfoQ", ""),
            {"uid": wuid, "tz": tz, "date": date, "start": start, "end": end, "type": type, "offset": offset, "limit": limit},
        ).get("data", {})

    def myInfoWithCoinHistory(
        self, wuid: str, start: int, end: int, tz: str, type: str, offset: int, limit: int
    ) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(
            gq.MYINFO_Q.get("coinHistoryQ", ""),
            {"uid": wuid, "start": start, "end": end, "tz": tz, "type": type, "offset": offset, "limit": limit},
        ).get("data", {})

    def getMyInfo(self) -> dict[str, any]:
        # Profil from login Account
        return self.runAuthorizedGqlQuery(gq.MYINFO_Q.get("readQ", ""), {}).get("data", {})

    def readCampaignProfile(self) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(
            gq.MYINFO_Q.get("readCampaignProfileQ", ""),
            {},
        ).get("data", {})

    def getReviewStatus(self, wuid: str) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.REVIEW_Q.get("getStatusQ", ""), {"uid": wuid}).get("data", {})

    def getWatchUserSteps(self, wuid: str, tz: str, date: int) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.STEP_Q.get("userQ", ""), {"uid": wuid, "tz": tz, "date": date}).get("data", {})

    def countries(self) -> dict[str, any]:
        # Country Support
        return self.runAuthorizedGqlQuery(gq.UTILS_Q.get("countriesQ", ""), {}).get("data", {})

    def subscribedCampaign(self, wuid: str, needDetail: bool = False) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.CAMPAIGN_Q.get("subscribedQ", ""), {"uid": wuid, "needDetail": needDetail}).get(
            "data", {}
        )

    def avatars(self, id: str) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.CAMPAIGN_Q.get("avatarsQ", ""), {"id": id}).get("data", {})

    def getFollowRequestWatchCount(self) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.CAMPAIGN_Q.get("followRequestWatchCountQ", ""), {}).get("data", {})

    def campaigns(self, id: str, categoryId: str) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.CAMPAIGN_Q.get("campaignsQ", ""), {"id": id, "categoryId": categoryId}).get(
            "data", {}
        )

    def isSubscribed(self, id: str, wuid: str) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.CAMPAIGN_Q.get("isSubscribedQ", ""), {"id": id, "uid": wuid}).get("data", {})

    def subscribed(self, wuid: str, needDetail: bool) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.CAMPAIGN_Q.get("subscribedQ", ""), {"uid": wuid, "needDetail": needDetail}).get(
            "data", {}
        )

    def ranks(self, campaignId: str) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.CAMPAIGN_Q.get("ranksQ", ""), {"campaignId": campaignId}).get("data", {})

    def campaignUserProfiles(self) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.CAMPAIGN_Q.get("campaignUserProfilesQ", ""), {}).get("data", {})

    def conv360IDToO2OID(self, qid: str, deviceId: str) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.QUERY.get("conv360IDToO2OIDQ", ""), {"qid": qid, "deviceId": deviceId}).get(
            "data", {}
        )

    def getAppVersion(self) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.QUERY.get("getAppVersionQ", ""), {}).get("data", {})

    def watchGroups(self, id: str = "") -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gq.WATCHGROUP_Q.get("watchGroupsQ", ""), {"id": id}).get("data", {})

    def getStartTrackingWatch(self, wuid: str) -> dict[str, any]:
        data = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("startTrackingWatchQ", ""), {"uid": wuid})
        errors: list[dict[str, str]] = data.get("errors", [])
        if errors:
            for error in errors:
                self.errors.append({"function": "getStartTrackingWatch", "error": error})
        return data.get("data", {})

    def getEndTrackingWatch(self, wuid: str) -> dict[str, any]:
        data = self.runAuthorizedGqlQuery(gq.WATCH_Q.get("endTrackingWatchQ", ""), {"uid": wuid})
        errors: list[dict[str, str]] = data.get("errors", [])
        if errors:
            for error in errors:
                self.errors.append({"function": "getEndTrackingWatch", "error": error})
        return data.get("data", {})

    ########## SECTION QUERY end ##########

    ########## SECTION MUTATION start ##########

    def sendText(self, wuid: str, text: str) -> bool:
        # ownUser id
        if (
            self.runAuthorizedGqlQuery(gm.WATCH_M.get("sendChatTextM", ""), {"uid": wuid, "text": text}).get("data", {})[
                "sendChatText"
            ]
            is not None
        ):
            return True
        return False

    def addStep(self, stepCount: int) -> dict[str, bool]:
        return self.runAuthorizedGqlQuery(gm.STEP_M.get("addM", ""), {"stepCount": stepCount}).get("data", {})

    def shutdown(self, wuid: str) -> bool:
        # ownUser id
        return self.isAdmin(wuid, gm.WATCH_M.get("shutdownM", ""), {"uid": wuid}, "shutDown")

    def reboot(self, wuid: str) -> bool:
        # ownUser id
        return self.isAdmin(wuid, gm.WATCH_M.get("rebootM", ""), {"uid": wuid}, "reboot")

    def modifyAlert(self, id: str, yesOrNo: YesOrNo) -> dict[str, any]:
        # function?
        return self.runAuthorizedGqlQuery(gm.WATCH_M.get("modifyAlertM", ""), {"uid": id, "remind": yesOrNo})

    def setEnableSlientTime(self, silentId: str, status: str = NormalStatus.ENABLE.value) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(
            gm.WATCH_M.get("setEnableSlientTimeM", ""), {"silentId": silentId, "status": status}
        ).get("data", {})

    def setEnableAlarmTime(self, alarmId: str, status: str = NormalStatus.ENABLE.value) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gm.WATCH_M.get("modifyAlarmM", ""), {"alarmId": alarmId, "status": status}).get(
            "data", {}
        )

    def setReadChatMsg(self, wuid: str, msgId: str, id: str) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(gm.WATCH_M.get("setReadChatMsgM", ""), {"uid": wuid, "msgId": msgId, "id": id}).get(
            "data", {}
        )

    def submitIncorrectLocationData(self, wuid: str, lat: str, lng: str, timestamp: str) -> dict[str, any]:
        return self.runAuthorizedGqlQuery(
            gm.WATCH_M.get("submitIncorrectLocationDataM", ""), {"uid": wuid, "lat": lat, "lng": lng, "timestamp": timestamp}
        ).get("data", {})

    ########## SECTION MUTATION end ##########
