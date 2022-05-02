from __future__ import annotations

import logging

from datetime import datetime
import sys
from time import time, sleep
from typing import Any, Dict, List

from .const import VERSION, VERSION_APP
from .exception_classes import FunctionError, LoginError, NoAdminError
from .gql_handler import GQLHandler
from .pyxplora import PyXplora
from .status import LocationType, NormalStatus, WatchOnlineStatus

_LOGGER = logging.getLogger(__name__)


class PyXploraApi(PyXplora):
    def __init__(
        self,
        countrycode: str,
        phoneNumber: str,
        password: str,
        userLang: str,
        timeZone: str,
        childPhoneNumber: List[str] = [],
    ) -> None:
        super().__init__(countrycode, phoneNumber, password, userLang, timeZone, childPhoneNumber)

    def __login(self, forceLogin: bool = False) -> Dict[Any, Any]:
        if not self._isConnected() or self._hasTokenExpired() or forceLogin:
            try:
                self._logoff()
                self._gqlHandler: GQLHandler = GQLHandler(
                    self._countrycode,
                    self._phoneNumber,
                    self._password,
                    self._userLang,
                    self._timeZone,
                ).c()
                if self._gqlHandler:
                    retryCounter = 0
                    while not self._isConnected() and (retryCounter < self.maxRetries + 2):
                        retryCounter += 1

                        # Try to login
                        try:
                            self._issueToken = self._gqlHandler.login()
                        except Exception:
                            pass

                        # Wait for next try
                        if not self._issueToken:
                            sleep(self.retryDelay)
                    if self._issueToken:
                        self.dtIssueToken = int(time())
                else:
                    raise Exception("Unknown error creating a new GraphQL handler instance.")
            except Exception:
                # Login failed.
                self._logoff()
        return self._issueToken

    def init(self, forceLogin: bool = False) -> None:
        token = self.__login(forceLogin)
        if token:
            if "user" in token:
                if not self._childPhoneNumber:
                    self.watchs = token["user"]["children"]
                else:
                    for watch in token["user"]["children"]:
                        if watch["ward"]["phoneNumber"] in self._childPhoneNumber:
                            self.watchs.append(watch)
                self.user = token["user"]
                return
        raise LoginError("Login to Xplora® API failed. Check your input!")

    def version(self) -> str:
        return "{0}-{1}".format(VERSION, VERSION_APP)

    ##### Contact Info #####
    def getWatchUserContacts(self, wuid: str) -> List[Dict[str, Any]]:
        retryCounter = 0
        dataOk: List[Any] = []
        contacts_raw: Dict[str, Any]
        contacts: List[Any] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            self.init()
            try:
                contacts_raw = self._gqlHandler.getWatchUserContacts(wuid)
                if "contacts" in contacts_raw:
                    if contacts_raw["contacts"] is None:
                        dataOk.append({})
                        return contacts
                    if "contacts" in contacts_raw["contacts"]:
                        if not contacts_raw["contacts"]["contacts"]:
                            dataOk.append({})
                            return contacts
                        for contact in contacts_raw["contacts"]["contacts"]:
                            try:
                                xcoin = contact["contactUser"]["xcoin"]
                                id = contact["contactUser"]["id"]
                            except TypeError:
                                # None - XCoins
                                xcoin = -1
                                id = None
                            contacts.append(
                                {
                                    "id": id,
                                    "guardianType": contact["guardianType"],
                                    "create": datetime.fromtimestamp(contact["create"]).strftime("%Y-%m-%d %H:%M:%S"),
                                    "update": datetime.fromtimestamp(contact["update"]).strftime("%Y-%m-%d %H:%M:%S"),
                                    "name": contact["name"],
                                    "phoneNumber": f"+{contact['countryPhoneNumber']}{contact['phoneNumber']}",
                                    "xcoin": xcoin,
                                }
                            )
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = contacts
            if not dataOk:
                self._logoff()
                sleep(self.retryDelay)
        if dataOk:
            return contacts
        else:
            raise FunctionError(sys._getframe().f_code.co_name)

    def getWatchAlarm(self, wuid: str) -> List[Dict[str, Any]]:
        retryCounter = 0
        dataOk: List[Any] = []
        alarms_raw: Dict[str, Any]
        alarms: List[Any] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            self.init()
            try:
                alarms_raw = self._gqlHandler.getAlarmTime(wuid)
                if "alarms" in alarms_raw:
                    if not alarms_raw["alarms"]:
                        dataOk.append({})
                        return alarms
                    for alarm in alarms_raw["alarms"]:
                        alarms.append(
                            {
                                "id": alarm["id"],
                                "vendorId": alarm["vendorId"],
                                "name": alarm["name"],
                                "start": self._helperTime(alarm["occurMin"]),
                                "weekRepeat": alarm["weekRepeat"],
                                "status": alarm["status"],
                            }
                        )
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = alarms
            if not dataOk:
                self._logoff()
                sleep(self.retryDelay)
        if dataOk:
            return alarms
        else:
            raise FunctionError(sys._getframe().f_code.co_name)

    def loadWatchLocation(self, wuid: str = "", withAsk: bool = True) -> List[Dict[str, Any]]:
        retryCounter = 0
        dataOk: List[Any] = []
        location_raw: Dict[str, Any]
        watch_location: List[Any] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            self.init()
            try:
                if withAsk:
                    self.askWatchLocate(wuid)
                sleep(self.retryDelay)
                location_raw = self._gqlHandler.getWatchLastLocation(wuid)
                if "watchLastLocate" in location_raw:
                    if location_raw["watchLastLocate"] is not None:
                        watch_location.append(
                            {
                                "tm": datetime.fromtimestamp(location_raw["watchLastLocate"]["tm"]).strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                "lat": location_raw["watchLastLocate"]["lat"],
                                "lng": location_raw["watchLastLocate"]["lng"],
                                "rad": location_raw["watchLastLocate"]["rad"],
                                "poi": location_raw["watchLastLocate"]["poi"],
                                "city": location_raw["watchLastLocate"]["city"],
                                "province": location_raw["watchLastLocate"]["province"],
                                "country": location_raw["watchLastLocate"]["country"],
                                "locateType": location_raw["watchLastLocate"]["locateType"],
                                "isInSafeZone": location_raw["watchLastLocate"]["isInSafeZone"],
                                "safeZoneLabel": location_raw["watchLastLocate"]["safeZoneLabel"],
                                "watch_battery": location_raw["watchLastLocate"]["battery"],
                                "watch_charging": location_raw["watchLastLocate"]["isCharging"],
                                "watch_last_location": location_raw["watchLastLocate"],
                            }
                        )
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = watch_location
            if not dataOk:
                self._logoff()
                sleep(self.retryDelay)
        if dataOk:
            return watch_location
        else:
            raise FunctionError(sys._getframe().f_code.co_name)

    def getWatchBattery(self, wuid: str) -> int:
        return int(self.loadWatchLocation(wuid=wuid)[0]["watch_battery"])

    def getWatchIsCharging(self, wuid: str) -> bool:
        if self.loadWatchLocation(wuid=wuid)[0]["watch_charging"]:
            return True
        return False

    def getWatchOnlineStatus(self, wuid: str) -> str:
        retryCounter = 0
        dataOk = WatchOnlineStatus.UNKNOWN
        asktrack_raw: WatchOnlineStatus = WatchOnlineStatus.UNKNOWN
        while dataOk is WatchOnlineStatus.UNKNOWN and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            self.init()
            try:
                self.askWatchLocate(wuid)
                sleep(self.retryDelay)
                ask_raw = self.askWatchLocate(wuid)
                track_raw = self.getTrackWatchInterval(wuid)
                if ask_raw or (track_raw != -1):
                    asktrack_raw = WatchOnlineStatus.ONLINE
                else:
                    asktrack_raw = WatchOnlineStatus.OFFLINE
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = asktrack_raw
            if dataOk is WatchOnlineStatus.UNKNOWN:
                self._logoff()
                sleep(self.retryDelay)
        if dataOk:
            return asktrack_raw.value
        else:
            raise FunctionError(sys._getframe().f_code.co_name)

    """def __setReadChatMsg(self, msgId, id):
        return (self._gqlHandler.setReadChatMsg(self.getWatchUserIDs(), msgId, id))["setReadChatMsg"]"""

    def getWatchUnReadChatMsgCount(self, wuid: str) -> int:
        # bug?
        return (self._gqlHandler.unReadChatMsgCount(wuid))["unReadChatMsgCount"]

    def getWatchChats(self, wuid: str, offset: int = 0, limit: int = 100, msgId: str = "") -> List[Dict[str, Any]]:
        # bug?
        retryCounter = 0
        dataOk: List[Any] = []
        chats_raw: Dict[str, Any]
        chats: List[Any] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            self.init()
            try:
                self.askWatchLocate(wuid)
                sleep(self.retryDelay)
                chats_raw = self._gqlHandler.chats(wuid, offset, limit, msgId)
                # print(chats_raw)
                if "chatsNew" in chats_raw:
                    if "list" in chats_raw["chatsNew"]:
                        if not chats_raw["chatsNew"]["list"]:
                            dataOk.append({})
                            return chats
                        for chat in chats_raw["chatsNew"]["list"]:
                            chats.append(
                                {
                                    "msgId": chat["msgId"],
                                    "type": chat["type"],
                                    # chat['sender'],
                                    "sender_id": chat["sender"]["id"],
                                    "sender_name": chat["sender"]["name"],
                                    # chat['receiver'],
                                    "receiver_id": chat["receiver"]["id"],
                                    "receiver_name": chat["receiver"]["name"],
                                    # chat['data'],
                                    "data_text": chat["data"]["text"],
                                    "data_sender_name": chat["data"]["sender_name"],
                                    "create": datetime.fromtimestamp(chat["create"]).strftime("%Y-%m-%d %H:%M:%S"),
                                }
                            )
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = chats
            if not dataOk:
                self._logoff()
                sleep(self.retryDelay)
        if dataOk:
            return chats
        else:
            return chats

    ##### Watch Location Info #####
    def getWatchLastLocation(self, wuid: str, withAsk: bool = False) -> Dict[str, Any]:
        return self.loadWatchLocation(wuid=wuid, withAsk=withAsk)[0]["watch_last_location"]

    def getWatchLocate(self, wuid: str) -> Dict[str, Any]:
        return self.loadWatchLocation(wuid=wuid)[0]

    def getWatchLocateType(self, wuid: str) -> str:
        return self.getWatchLocate(wuid).get("locateType", LocationType.UNKNOWN.value)

    def getWatchIsInSafeZone(self, wuid: str) -> bool:
        return self.getWatchLocate(wuid)["isInSafeZone"]

    def getWatchSafeZoneLabel(self, wuid: str) -> str:
        return self.getWatchLocate(wuid)["safeZoneLabel"]

    def getWatchSafeZones(self, wuid: str) -> List[Dict[str, Any]]:
        retryCounter = 0
        dataOk: List[Any] = []
        safeZones_raw: Dict[str, Any]
        safe_zones: List[Any] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            self.init()
            try:
                self.askWatchLocate(wuid)
                sleep(self.retryDelay)
                safeZones_raw = self._gqlHandler.safeZones(wuid)
                if "safeZones" in safeZones_raw:
                    if not safeZones_raw["safeZones"]:
                        dataOk.append({})
                        return safe_zones
                    for safeZone in safeZones_raw["safeZones"]:
                        safe_zones.append(
                            {
                                "vendorId": safeZone["vendorId"],
                                "groupName": safeZone["groupName"],
                                "name": safeZone["name"],
                                "lat": safeZone["lat"],
                                "lng": safeZone["lng"],
                                "rad": safeZone["rad"],
                                "address": safeZone["address"],
                            }
                        )
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = safe_zones
            if not dataOk:
                self._logoff()
                sleep(self.retryDelay)
        if dataOk:
            return safe_zones
        else:
            raise FunctionError(sys._getframe().f_code.co_name)

    def getTrackWatchInterval(self, wuid: str) -> int:
        return self._gqlHandler.trackWatch(wuid)["trackWatch"]

    def askWatchLocate(self, wuid: str) -> bool:
        return self._gqlHandler.askWatchLocate(wuid)["askWatchLocate"]

    ##### Feature #####
    def getSilentTime(self, wuid: str) -> List[Dict[str, Any]]:
        retryCounter = 0
        dataOk: List[Any] = []
        silentTimes_raw: Dict[str, Any]
        school_silent_mode: List[Any] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            self.init()
            try:
                self.askWatchLocate(wuid)
                sleep(self.retryDelay)
                silentTimes_raw = self._gqlHandler.silentTimes(wuid)
                if "silentTimes" in silentTimes_raw:
                    if not silentTimes_raw["silentTimes"]:
                        dataOk.append({})
                        return school_silent_mode
                    for silentTime in silentTimes_raw["silentTimes"]:
                        school_silent_mode.append(
                            {
                                "id": silentTime["id"],
                                "vendorId": silentTime["vendorId"],
                                "start": self._helperTime(silentTime["start"]),
                                "end": self._helperTime(silentTime["end"]),
                                "weekRepeat": silentTime["weekRepeat"],
                                "status": silentTime["status"],
                            }
                        )
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = school_silent_mode
            if not dataOk:
                self._logoff()
                sleep(self.retryDelay)
        if dataOk:
            return school_silent_mode
        else:
            raise FunctionError(sys._getframe().f_code.co_name)

    def setEnableSilentTime(self, silentId: str, wuid: str) -> bool:
        retryCounter = 0
        dataOk = ""
        _raw = ""
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            self.init()
            try:
                self.askWatchLocate(wuid)
                sleep(self.retryDelay)
                enable_raw = self._gqlHandler.setEnableSlientTime(silentId)
                if "setEnableSilentTime" in enable_raw:
                    _raw = enable_raw["setEnableSilentTime"]
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if not dataOk:
                self._logoff()
                sleep(self.retryDelay)
        if dataOk:
            return bool(_raw)
        else:
            raise FunctionError(sys._getframe().f_code.co_name)

    def setDisableSilentTime(self, silentId: str, wuid: str) -> bool:
        retryCounter = 0
        dataOk = ""
        _raw = ""
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            self.init()
            try:
                self.askWatchLocate(wuid)
                sleep(self.retryDelay)
                disable_raw = self._gqlHandler.setEnableSlientTime(silentId, NormalStatus.DISABLE.value)
                if "setEnableSilentTime" in disable_raw:
                    _raw = disable_raw["setEnableSilentTime"]
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if not dataOk:
                self._logoff()
                sleep(self.retryDelay)
        if dataOk:
            return bool(_raw)
        else:
            raise FunctionError(sys._getframe().f_code.co_name)

    def setAllEnableSilentTime(self, wuid: str) -> List[bool]:
        res: List[bool] = []
        for silentTime in self.getSilentTime(wuid):
            res.append(self.setEnableSilentTime(silentTime["id"], wuid))
        return res

    def setAllDisableSilentTime(self, wuid: str) -> List[bool]:
        res: List[bool] = []
        for silentTime in self.getSilentTime(wuid):
            res.append(self.setDisableSilentTime(silentTime["id"], wuid))
        return res

    def setEnableAlarmTime(self, alarmId: str, wuid: str) -> bool:
        retryCounter = 0
        dataOk = ""
        _raw = ""
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            self.init()
            try:
                self.askWatchLocate(wuid)
                sleep(self.retryDelay)
                enable_raw = self._gqlHandler.setEnableAlarmTime(alarmId)
                if "modifyAlarm" in enable_raw:
                    _raw = enable_raw["modifyAlarm"]
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if not dataOk:
                self._logoff()
                sleep(self.retryDelay)
        if dataOk:
            return bool(_raw)
        else:
            raise FunctionError(sys._getframe().f_code.co_name)

    def setDisableAlarmTime(self, alarmId: str, wuid: str) -> bool:
        retryCounter = 0
        dataOk = ""
        _raw = ""
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            self.init()
            try:
                self.askWatchLocate(wuid)
                sleep(self.retryDelay)
                disable_raw = self._gqlHandler.setEnableAlarmTime(alarmId, NormalStatus.DISABLE.value)
                if "modifyAlarm" in disable_raw:
                    _raw = disable_raw["modifyAlarm"]
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if not dataOk:
                self._logoff()
                sleep(self.retryDelay)
        if dataOk:
            return bool(_raw)
        else:
            raise FunctionError(sys._getframe().f_code.co_name)

    def setAllEnableAlarmTime(self, wuid: str) -> List[bool]:
        res: List[bool] = []
        for alarmTime in self.getWatchAlarm(wuid):
            res.append(self.setEnableAlarmTime(alarmTime["id"], wuid))
        return res

    def setAllDisableAlarmTime(self, wuid: str) -> List[bool]:
        res: List[bool] = []
        for alarmTime in self.getWatchAlarm(wuid):
            res.append(self.setDisableAlarmTime(alarmTime["id"], wuid))
        return res

    def sendText(self, text: str, wuid: str) -> bool:
        # sender is login User
        return self._gqlHandler.sendText(wuid, text)

    def isAdmin(self, wuid: str) -> bool:
        contacts = self.getWatchUserContacts(wuid)
        for contact in contacts:
            try:
                id = contact["id"]
            except KeyError and TypeError:
                id = None
            if self.getUserID() == id:
                if contact["guardianType"] == "FIRST":
                    return True
        return False

    def shutdown(self, wuid: str) -> bool:
        if self.isAdmin(wuid):
            return self._gqlHandler.shutdown(wuid)
        raise NoAdminError()

    def reboot(self, wuid: str) -> bool:
        if self.isAdmin(wuid):
            return self._gqlHandler.reboot(wuid)
        raise NoAdminError()

    def getFollowRequestWatchCount(self) -> int:
        c: Dict[str, Any] = self._gqlHandler.getFollowRequestWatchCount()
        return c.get("followRequestWatchCount", 0)

    def getWatches(self, wuid: str) -> List[Dict[str, Any]]:
        retryCounter = 0
        dataOk: List[Any] = []
        watches_raw: Dict[str, Any]
        watches: List[Any] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            self.init()
            try:
                watches_raw = self._gqlHandler.getWatches(wuid)
                if "watches" in watches_raw:
                    if not watches_raw["watches"]:
                        dataOk.append({})
                        return watches
                    for watch in watches_raw["watches"]:
                        watches.append(
                            {
                                "imei": watch["swKey"],
                                "osVersion": watch["osVersion"],
                                "qrCode": watch["qrCode"],
                            }
                        )
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = watches
            if not dataOk:
                self._logoff()
                sleep(self.retryDelay)
        if dataOk:
            return watches
        else:
            raise FunctionError(sys._getframe().f_code.co_name)

    def getSWInfo(self, wuid: str) -> Dict[str, Any]:
        qrCode: str = self.getWatches(wuid=wuid)[0]["qrCode"]
        return self._gqlHandler.getSWInfo(qrCode.split("=")[1])

    def getWatchState(self, wuid: str) -> Dict[str, Any]:
        qrCode: str = self.getWatches(wuid=wuid)[0]["qrCode"]
        return self._gqlHandler.getWatchState(qrCode.split("=")[1])

    def conv360IDToO2OID(self, qid: str, deviceId: str) -> Dict[str, Any]:
        return self._gqlHandler.conv360IDToO2OID(qid, deviceId)

    def campaigns(self, id: str, categoryId: str) -> Dict[str, Any]:
        return self._gqlHandler.campaigns(id, categoryId)

    def getCountries(self) -> List[Dict[str, str]]:
        countries: Dict[str, Any] = self._gqlHandler.countries()
        return countries.get("countries", [])

    def getWatchLocHistory(self, wuid: str, date: int, tz: str, limit: int) -> Dict[str, Any]:
        return self._gqlHandler.getWatchLocHistory(wuid, date, tz, limit)

    def watchesDynamic(self) -> Dict[str, Any]:
        return self._gqlHandler.watchesDynamic()

    def watchGroups(self, id: str = "") -> Dict[str, Any]:
        return self._gqlHandler.watchGroups(id)

    def familyInfo(self, wuid: str, watchId: str, tz: str, date: int) -> Dict[str, Any]:
        return self._gqlHandler.familyInfo(wuid, watchId, tz, date)

    def avatars(self, id: str) -> Dict[str, Any]:
        return self._gqlHandler.avatars(id)

    def getWatchUserSteps(self, wuid: str, date: int) -> Dict[str, Any]:
        userSteps = self._gqlHandler.getWatchUserSteps(wuid=wuid, tz=self._timeZone, date=date)
        if not userSteps:
            return userSteps
        userSteps = userSteps.get("userSteps", {})
        if not userSteps:
            return {}
        return userSteps
