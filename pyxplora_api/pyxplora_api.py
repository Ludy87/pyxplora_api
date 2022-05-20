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

_LIST_DICT: List[Dict[str, Any]] = []


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
            if token.get("user", {}):
                if not self._childPhoneNumber:
                    self.watchs = token.get("user", {}).get("children", _LIST_DICT)
                else:
                    for watch in token.get("user", {}).get("children", _LIST_DICT):
                        if watch["ward"]["phoneNumber"] in self._childPhoneNumber:
                            self.watchs.append(watch)
                self.user = token.get("user", {})
                return
        raise LoginError("Login to Xplora® API failed. Check your input!")

    def version(self) -> str:
        return "{0}-{1}".format(VERSION, VERSION_APP)

    ##### Contact Info #####
    def getWatchUserContacts(self, wuid: str) -> List[Dict[str, Any]]:
        retryCounter = 0
        dataOk: List[Dict[str, Any]] = []
        contacts_raw: Dict[str, Any] = {}
        contacts: List[Dict[str, Any]] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            self.init()
            try:
                contacts_raw = self._gqlHandler.getWatchUserContacts(wuid)
                _contacts: Dict[str, Any] = contacts_raw.get("contacts", {})
                if not _contacts:
                    dataOk.append({})
                    return contacts
                _contacts_contacts = _contacts.get("contacts", _LIST_DICT)
                if not _contacts_contacts:
                    dataOk.append({})
                    return contacts
                for contact in _contacts.get("contacts", _LIST_DICT):
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
        dataOk: List[Dict[str, Any]] = []
        alarms_raw: Dict[str, Any] = {}
        alarms: List[Dict[str, Any]] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            self.init()
            try:
                alarms_raw = self._gqlHandler.getAlarmTime(wuid)
                _alarms = alarms_raw.get("alarms", [])
                if not _alarms:
                    dataOk.append({})
                    return alarms
                for alarm in _alarms:
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
        dataOk: List[Dict[str, Any]] = []
        location_raw: Dict[str, Any] = {}
        watch_location: List[Dict[str, Any]] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            self.init()
            try:
                if withAsk:
                    self.askWatchLocate(wuid)
                sleep(self.retryDelay)
                location_raw = self._gqlHandler.getWatchLastLocation(wuid)
                _watchLastLocate = location_raw.get(
                    "watchLastLocate",
                    {},
                )
                if not _watchLastLocate:
                    dataOk.append({})
                    return watch_location
                _tm = 31532399 if _watchLastLocate.get("tm") is None else _watchLastLocate.get("tm")
                _lat = "0.0" if _watchLastLocate.get("lat") is None else _watchLastLocate.get("lat")
                _lng = "0.0" if _watchLastLocate.get("lng") is None else _watchLastLocate.get("lng")
                _rad = -1 if _watchLastLocate.get("rad") is None else _watchLastLocate.get("rad")
                _poi = "" if _watchLastLocate.get("poi") is None else _watchLastLocate.get("poi")
                _city = "" if _watchLastLocate.get("city") is None else _watchLastLocate.get("city")
                _province = "" if _watchLastLocate.get("province") is None else _watchLastLocate.get("province")
                _country = "" if _watchLastLocate.get("country") is None else _watchLastLocate.get("country")
                _locateType = (
                    LocationType.UNKNOWN.value
                    if _watchLastLocate.get("locateType") is None
                    else _watchLastLocate.get("locateType")
                )
                _isInSafeZone = False if _watchLastLocate.get("isInSafeZone") is None else _watchLastLocate.get("isInSafeZone")
                _safeZoneLabel = "" if _watchLastLocate.get("safeZoneLabel") is None else _watchLastLocate.get("safeZoneLabel")
                _watch_battery = -1 if _watchLastLocate.get("battery") is None else _watchLastLocate.get("battery")
                _watch_charging = False if _watchLastLocate.get("isCharging") is None else _watchLastLocate.get("isCharging")
                watch_location.append(
                    {
                        "tm": datetime.fromtimestamp(_tm).strftime("%Y-%m-%d %H:%M:%S"),
                        "lat": _lat,
                        "lng": _lng,
                        "rad": _rad,
                        "poi": _poi,
                        "city": _city,
                        "province": _province,
                        "country": _country,
                        "locateType": _locateType,
                        "isInSafeZone": _isInSafeZone,
                        "safeZoneLabel": _safeZoneLabel,
                        "watch_battery": _watch_battery,
                        "watch_charging": _watch_charging,
                        "watch_last_location": _watchLastLocate,
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
        return int(self.loadWatchLocation(wuid=wuid)[0].get("watch_battery", -1))

    def getWatchIsCharging(self, wuid: str) -> bool:
        if self.loadWatchLocation(wuid=wuid)[0].get("watch_charging", False):
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
        return (self._gqlHandler.unReadChatMsgCount(wuid)).get("unReadChatMsgCount", -1)

    def getWatchChats(self, wuid: str, offset: int = 0, limit: int = 100, msgId: str = "") -> List[Dict[str, Any]]:
        # bug?
        retryCounter = 0
        dataOk: List[Dict[str, Any]] = []
        chats_raw: Dict[str, Any] = {}
        chats: List[Dict[str, Any]] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            self.init()
            try:
                self.askWatchLocate(wuid)
                sleep(self.retryDelay)
                chats_raw = self._gqlHandler.chats(wuid, offset, limit, msgId)
                _chatsNew = chats_raw.get("chatsNew", {})
                if not _chatsNew:
                    dataOk.append({})
                    return chats
                _list = _chatsNew.get("list", [])
                if not _list:
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
            raise FunctionError(sys._getframe().f_code.co_name)

    ##### Watch Location Info #####
    def getWatchLastLocation(self, wuid: str, withAsk: bool = False) -> Dict[str, Any]:
        _loadWatchLocation = self.loadWatchLocation(wuid=wuid, withAsk=withAsk)
        if not _loadWatchLocation:
            return {}
        for loadWatchLocation in _loadWatchLocation:
            return loadWatchLocation.get("watch_last_location", {})
        return {}

    def getWatchLocate(self, wuid: str) -> Dict[str, Any]:
        _loadWatchLocation = self.loadWatchLocation(wuid=wuid)
        if not _loadWatchLocation:
            return {}
        for loadWatchLocation in _loadWatchLocation:
            return loadWatchLocation
        return {}

    def getWatchLocateType(self, wuid: str) -> str:
        return self.getWatchLocate(wuid).get("locateType", LocationType.UNKNOWN.value)

    def getWatchIsInSafeZone(self, wuid: str) -> bool:
        return self.getWatchLocate(wuid).get("isInSafeZone", False)

    def getWatchSafeZoneLabel(self, wuid: str) -> str:
        return self.getWatchLocate(wuid).get("safeZoneLabel", "")

    def getWatchSafeZones(self, wuid: str) -> List[Dict[str, Any]]:
        retryCounter = 0
        dataOk: List[Dict[str, Any]] = []
        safeZones_raw: Dict[str, Any] = {}
        safe_zones: List[Dict[str, Any]] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            self.init()
            try:
                self.askWatchLocate(wuid)
                sleep(self.retryDelay)
                safeZones_raw = self._gqlHandler.safeZones(wuid)
                _safeZones = safeZones_raw.get("safeZones", [])
                if not _safeZones:
                    dataOk.append({})
                    return safe_zones
                for safeZone in _safeZones:
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
        return self._gqlHandler.trackWatch(wuid).get("trackWatch", -1)

    def askWatchLocate(self, wuid: str) -> bool:
        return self._gqlHandler.askWatchLocate(wuid).get("askWatchLocate", False)

    ##### Feature #####
    def getSilentTime(self, wuid: str) -> List[Dict[str, Any]]:
        retryCounter = 0
        dataOk: List[Dict[str, Any]] = []
        silentTimes_raw: Dict[str, Any] = {}
        school_silent_mode: List[Dict[str, Any]] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            self.init()
            try:
                self.askWatchLocate(wuid)
                sleep(self.retryDelay)
                silentTimes_raw = self._gqlHandler.silentTimes(wuid)
                _silentTimes = silentTimes_raw.get("silentTimes", [])
                if not _silentTimes:
                    dataOk.append({})
                    return school_silent_mode
                for silentTime in _silentTimes:
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
                _setEnableSilentTime = enable_raw.get("setEnableSilentTime", -1)
                if not _setEnableSilentTime:
                    dataOk = "0"
                    return bool(_raw)
                _raw = _setEnableSilentTime
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
                _setEnableSilentTime = disable_raw.get("setEnableSilentTime", -1)
                if not _setEnableSilentTime:
                    dataOk = "0"
                    return bool(_raw)
                _raw = _setEnableSilentTime
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
            res.append(self.setEnableSilentTime(silentTime.get("id", ""), wuid))
        return res

    def setAllDisableSilentTime(self, wuid: str) -> List[bool]:
        res: List[bool] = []
        for silentTime in self.getSilentTime(wuid):
            res.append(self.setDisableSilentTime(silentTime.get("id", ""), wuid))
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
                _modifyAlarm = enable_raw.get("modifyAlarm", -1)
                if not _modifyAlarm:
                    dataOk = "0"
                    return bool(_raw)
                _raw = _modifyAlarm
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
                _modifyAlarm = disable_raw.get("modifyAlarm", -1)
                if not _modifyAlarm:
                    dataOk = "0"
                    return bool(_raw)
                _raw = _modifyAlarm
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
            res.append(self.setEnableAlarmTime(alarmTime.get("id", ""), wuid))
        return res

    def setAllDisableAlarmTime(self, wuid: str) -> List[bool]:
        res: List[bool] = []
        for alarmTime in self.getWatchAlarm(wuid):
            res.append(self.setDisableAlarmTime(alarmTime.get("id", ""), wuid))
        return res

    def sendText(self, text: str, wuid: str) -> bool:
        # sender is login User
        return self._gqlHandler.sendText(wuid, text)

    def isAdmin(self, wuid: str) -> bool:
        contacts = self.getWatchUserContacts(wuid)
        for contact in contacts:
            _id = contact.get("id", None)
            if self.getUserID() == _id:
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
        dataOk: List[Dict[str, Any]] = []
        watches_raw: Dict[str, Any] = {}
        watches: List[Dict[str, Any]] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            self.init()
            try:
                watches_raw = self._gqlHandler.getWatches(wuid)
                _watches = watches_raw.get("watches", {})
                if not _watches:
                    dataOk.append({})
                    return watches
                for watch in _watches:
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
        return countries.get("countries", {})

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
            return {}
        userSteps = userSteps.get("userSteps", {})
        if not userSteps:
            return {}
        return userSteps

    def addStep(self, step: int) -> bool:
        s: Dict[str, bool] = self._gqlHandler.addStep(step)
        return s.get("addStep", False)
