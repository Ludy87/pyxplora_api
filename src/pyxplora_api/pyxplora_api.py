from __future__ import annotations

import logging
from datetime import datetime
from time import time
from typing import Any

from .const import VERSION, VERSION_APP
from .exception_classes import ErrorMSG, LoginError, NoAdminError
from .gql_handler import GQLHandler
from .model import Chats, ChatsNew, SimpleChat
from .pyxplora import PyXplora
from .status import LocationType, NormalStatus, UserContactType, WatchOnlineStatus

_LOGGER = logging.getLogger(__name__)

LIST_DICT: list[dict[str, any]] = []


class PyXploraApi(PyXplora):
    def __init__(
        self,
        countrycode: str = "",
        phoneNumber: str = "",
        password: str = "",
        userLang: str = "",
        timeZone: str = "",
        childPhoneNumber: list[str] = [],
        wuid: str | list | None = None,
        email: str | None = None,
    ) -> None:
        super().__init__(countrycode, phoneNumber, password, userLang, timeZone, childPhoneNumber, wuid, email)

    def _login(self, forceLogin: bool = False, signup: bool = True) -> dict[Any, Any]:
        if not self._isConnected() or self._hasTokenExpired() or forceLogin:
            try:
                self._logoff()
                self._gqlHandler: GQLHandler = GQLHandler(
                    self._countrycode,
                    self._phoneNumber,
                    self._password,
                    self._userLang,
                    self._timeZone,
                    self._email,
                    signup,
                )
                if self._gqlHandler:
                    retryCounter = 0
                    while not self._isConnected() and (retryCounter < self.maxRetries + 2):
                        retryCounter += 1

                        # Try to login
                        try:
                            self._issueToken = self._gqlHandler.login()
                        except LoginError as error:
                            self.error_message = error.message
                        except Exception:
                            if retryCounter == self.maxRetries + 2:
                                self.error_message = ErrorMSG.SERVER_ERR
                            else:
                                pass

                        # Wait for next try
                        if not self._issueToken:
                            self.delay(self.retryDelay)
                    if self._issueToken:
                        self.dtIssueToken = int(time())
                else:
                    raise Exception("Unknown error creating a new GraphQL handler instance.")
            except Exception:
                # Login failed.
                self._logoff()
        return self._issueToken

    def init(self, forceLogin: bool = False, signup: bool = True) -> None:
        token = self._login(forceLogin, signup)
        if signup:
            if token:
                if token.get("user", {}):
                    if not self._childPhoneNumber:
                        self.watchs = token.get("user", {}).get("children", LIST_DICT)
                    else:
                        for watch in token.get("user", {}).get("children", LIST_DICT):
                            if watch["ward"]["phoneNumber"] in self._childPhoneNumber:
                                self.watchs.append(watch)
                    self.user = token.get("user", {})
                    return
            raise LoginError(self.error_message)
        return

    def version(self) -> str:
        return "{0}-{1}".format(VERSION, VERSION_APP)

    def setDevices(self, ids: list = []) -> list[str]:
        return self._setDevices(ids)

    def _setDevices(self, ids: list = []) -> list[str]:
        if ids:
            wuids = ids
        else:
            wuids: list[str] = self.getWatchUserIDs()
        for wuid in wuids:
            self.device[wuid] = {}
            self.device[wuid]["getWatchAlarm"] = self.getWatchAlarm(wuid=wuid)
            self.device[wuid]["loadWatchLocation"] = self.loadWatchLocation(wuid=wuid)
            self.device[wuid]["watch_battery"] = int(self.device[wuid]["loadWatchLocation"].get("watch_battery", -1))
            self.device[wuid]["watch_charging"] = self.device[wuid]["loadWatchLocation"].get("watch_charging", False)
            self.device[wuid]["locateType"] = self.device[wuid]["loadWatchLocation"].get(
                "locateType", LocationType.UNKNOWN.value
            )
            self.device[wuid]["lastTrackTime"] = self.device[wuid]["loadWatchLocation"].get(
                "tm", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            self.device[wuid]["isInSafeZone"] = self.device[wuid]["loadWatchLocation"].get("isInSafeZone", False)
            self.device[wuid]["safeZoneLabel"] = self.device[wuid]["loadWatchLocation"].get("safeZoneLabel", "")
            self.device[wuid]["getWatchSafeZones"] = self.getWatchSafeZones(wuid=wuid)
            self.device[wuid]["getSilentTime"] = self.getSilentTime(wuid=wuid)
            self.device[wuid]["getWatches"] = self.getWatches(wuid=wuid)
            self.device[wuid]["getSWInfo"] = self.getSWInfo(wuid=wuid, watches=self.device[wuid]["getWatches"])
            self.device[wuid]["getWatchState"] = self.getWatchState(wuid=wuid, watches=self.device[wuid]["getWatches"])
            d = datetime.now()
            dt = datetime(year=d.year, month=d.month, day=d.day)
            self.device[wuid]["getWatchUserSteps"] = self.getWatchUserSteps(wuid=wuid, date=int(dt.timestamp()))
            self.device[wuid]["getWatchOnlineStatus"] = self.getWatchOnlineStatus(wuid=wuid)
            self.device[wuid]["getWatchUserIcons"] = self.getWatchUserIcons(wuid=wuid)
            self.device[wuid]["getWatchUserXcoins"] = self.getWatchUserXcoins(wuid=wuid)
        return wuids

    ##### Contact Info #####
    def getWatchUserContacts(self, wuid: str) -> list[dict[str, Any]]:
        retryCounter = 0
        dataOk: list[dict[str, Any]] = []
        contacts_raw: dict[str, Any] = {}
        contacts: list[dict[str, Any]] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                contacts_raw = self._gqlHandler.getWatchUserContacts(wuid)
                _contacts: dict[str, Any] = contacts_raw.get("contacts", {})
                if not _contacts:
                    dataOk.append({})
                    return contacts
                _contacts_contacts = _contacts.get("contacts", LIST_DICT)
                if not _contacts_contacts:
                    dataOk.append({})
                    return contacts
                for contact in _contacts.get("contacts", LIST_DICT):
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
                self.delay(self.retryDelay)
        return contacts

    def getWatchAlarm(self, wuid: str) -> list[dict[str, Any]]:
        retryCounter = 0
        dataOk: list[dict[str, Any]] = []
        alarms_raw: dict[str, Any] = {}
        alarms: list[dict[str, Any]] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
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
                self.delay(self.retryDelay)
        return alarms

    def loadWatchLocation(self, wuid: str = "", withAsk: bool = True) -> dict[str, Any]:
        retryCounter = 0
        dataOk: dict[str, Any] = {}
        location_raw: dict[str, Any] = {}
        watch_location: dict[str, Any] = {}
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                if withAsk:
                    self.askWatchLocate(wuid)
                location_raw = self._gqlHandler.getWatchLastLocation(wuid)
                _watchLastLocate = location_raw.get(
                    "watchLastLocate",
                    {},
                )
                if not _watchLastLocate:
                    return watch_location
                _tm: float = 31532399 if _watchLastLocate.get("tm", None) is None else _watchLastLocate.get("tm", 31532399)
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
                watch_location = {
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
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = watch_location
            if not dataOk:
                self._logoff()
                self.delay(self.retryDelay)
        return watch_location

    def getWatchBattery(self, wuid: str) -> int:
        watch_b: dict[str, Any] = self.loadWatchLocation(wuid=wuid)
        return int(watch_b.get("watch_battery", -1))

    def getWatchIsCharging(self, wuid: str) -> bool:
        watch_c: dict[str, Any] = self.loadWatchLocation(wuid=wuid)
        if watch_c.get("watch_charging", False):
            return True
        return False

    def getWatchOnlineStatus(self, wuid: str) -> str:
        retryCounter = 0
        dataOk = WatchOnlineStatus.UNKNOWN
        asktrack_raw: WatchOnlineStatus = WatchOnlineStatus.UNKNOWN
        while dataOk is WatchOnlineStatus.UNKNOWN and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
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
                self.delay(self.retryDelay)
        return asktrack_raw.value

    """def __setReadChatMsg(self, msgId, id):
        return (self._gqlHandler.setReadChatMsg(self.getWatchUserIDs(), msgId, id))["setReadChatMsg"]"""

    def getWatchUnReadChatMsgCount(self, wuid: str) -> int:
        # bug?
        return (self._gqlHandler.unReadChatMsgCount(wuid)).get("unReadChatMsgCount", -1)

    def getWatchChats(self, wuid: str, offset: int = 0, limit: int = 0, msgId: str = "") -> list[dict[str, Any]]:
        retryCounter = 0
        dataOk: list[dict[str, Any]] = []
        chats: list[dict[str, Any]] = []
        _chatsNew: ChatsNew = {}
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                _chatsNew: ChatsNew = Chats.from_dict(self.getWatchChatsRaw(wuid, offset, limit, msgId)).chatsNew
                _list: list[SimpleChat] = _chatsNew.list
                if not _chatsNew or not _list:
                    return chats
                for chat in _list:
                    chats.append(
                        {
                            "msgId": chat.msgId,
                            "type": chat.type,
                            "sender_id": chat.sender.id,
                            "sender_name": chat.sender.name,
                            "receiver_id": chat.receiver.id,
                            "receiver_name": chat.receiver.name,
                            "data_text": chat.data.text,
                            "data_sender_name": chat.data.sender_name,
                            "create": datetime.fromtimestamp(chat.create).strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = chats
            if not dataOk:
                self._logoff()
                self.delay(self.retryDelay)
        return chats

    def getWatchChatsRaw(self, wuid: str, offset: int = 0, limit: int = 0, msgId: str = "") -> list[dict[str, Any]]:
        retryCounter = 0
        dataOk: dict[str, Any] = []
        _chatsNew: dict[str, Any] = {}
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                _chatsNew = self._gqlHandler.chats(wuid, offset, limit, msgId)
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _chatsNew
            if not dataOk:
                self._logoff()
                self.delay(self.retryDelay)
        return _chatsNew

    ##### Watch Location Info #####
    def getWatchLastLocation(self, wuid: str, withAsk: bool = False) -> dict[str, Any]:
        _loadWatchLocation = self.loadWatchLocation(wuid=wuid, withAsk=withAsk)
        if isinstance(_loadWatchLocation, dict):
            return _loadWatchLocation.get("watch_last_location", {})
        # if not _loadWatchLocation:
        #     return {}
        # for loadWatchLocation in _loadWatchLocation:
        #     return loadWatchLocation.get("watch_last_location", {})
        return {}

    def getWatchLocate(self, wuid: str) -> dict[str, Any]:
        _loadWatchLocation = self.loadWatchLocation(wuid=wuid)
        if isinstance(_loadWatchLocation, dict):
            return _loadWatchLocation
        # if not _loadWatchLocation:
        #     return {}
        # for loadWatchLocation in _loadWatchLocation:
        #     return loadWatchLocation
        return {}

    def getWatchLocateType(self, wuid: str) -> str:
        return self.getWatchLocate(wuid).get("locateType", LocationType.UNKNOWN.value)

    def getWatchIsInSafeZone(self, wuid: str) -> bool:
        return self.getWatchLocate(wuid).get("isInSafeZone", False)

    def getWatchSafeZoneLabel(self, wuid: str) -> str:
        return self.getWatchLocate(wuid).get("safeZoneLabel", "")

    def getWatchSafeZones(self, wuid: str) -> list[dict[str, Any]]:
        retryCounter = 0
        dataOk: list[dict[str, Any]] = []
        safeZones_raw: dict[str, Any] = {}
        safe_zones: list[dict[str, Any]] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
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
                self.delay(self.retryDelay)
        return safe_zones

    def getTrackWatchInterval(self, wuid: str) -> int:
        return self._gqlHandler.trackWatch(wuid).get("trackWatch", -1)

    def askWatchLocate(self, wuid: str) -> bool:
        return self._gqlHandler.askWatchLocate(wuid).get("askWatchLocate", False)

    ##### Feature #####
    def getSilentTime(self, wuid: str) -> list[dict[str, Any]]:
        retryCounter = 0
        dataOk: list[dict[str, Any]] = []
        silentTimes_raw: dict[str, Any] = {}
        school_silent_mode: list[dict[str, Any]] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
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
                self.delay(self.retryDelay)
        return school_silent_mode

    def setEnableSilentTime(self, silentId: str) -> bool:
        retryCounter = 0
        dataOk = ""
        _raw = ""
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                enable_raw = self._gqlHandler.setEnableSlientTime(silentId)
                _setEnableSilentTime = enable_raw.get("setEnableSilentTime", -1)
                if not _setEnableSilentTime:
                    return bool(_raw)
                _raw = _setEnableSilentTime
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if not dataOk:
                self._logoff()
                self.delay(self.retryDelay)
        return bool(_raw)

    def setDisableSilentTime(self, silentId: str) -> bool:
        retryCounter = 0
        dataOk = ""
        _raw = ""
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                disable_raw = self._gqlHandler.setEnableSlientTime(silentId, NormalStatus.DISABLE.value)
                _setEnableSilentTime = disable_raw.get("setEnableSilentTime", -1)
                if not _setEnableSilentTime:
                    return bool(_raw)
                _raw = _setEnableSilentTime
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if not dataOk:
                self._logoff()
                self.delay(self.retryDelay)
        return bool(_raw)

    def setAllEnableSilentTime(self, wuid: str) -> list[bool]:
        res: list[bool] = []
        for silentTime in self.getSilentTime(wuid):
            res.append(self.setEnableSilentTime(silentTime.get("id", "")))
        return res

    def setAllDisableSilentTime(self, wuid: str) -> list[bool]:
        res: list[bool] = []
        for silentTime in self.getSilentTime(wuid):
            res.append(self.setDisableSilentTime(silentTime.get("id", "")))
        return res

    def setEnableAlarmTime(self, alarmId: str) -> bool:
        retryCounter = 0
        dataOk = ""
        _raw = ""
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                enable_raw = self._gqlHandler.setEnableAlarmTime(alarmId)
                _modifyAlarm = enable_raw.get("modifyAlarm", -1)
                if not _modifyAlarm:
                    return bool(_raw)
                _raw = _modifyAlarm
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if not dataOk:
                self._logoff()
                self.delay(self.retryDelay)
        return bool(_raw)

    def setDisableAlarmTime(self, alarmId: str) -> bool:
        retryCounter = 0
        dataOk = ""
        _raw = ""
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                disable_raw = self._gqlHandler.setEnableAlarmTime(alarmId, NormalStatus.DISABLE.value)
                _modifyAlarm = disable_raw.get("modifyAlarm", -1)
                if not _modifyAlarm:
                    return bool(_raw)
                _raw = _modifyAlarm
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if not dataOk:
                self._logoff()
                self.delay(self.retryDelay)
        return bool(_raw)

    def setAllEnableAlarmTime(self, wuid: str) -> list[bool]:
        res: list[bool] = []
        for alarmTime in self.getWatchAlarm(wuid):
            res.append(self.setEnableAlarmTime(alarmTime.get("id", "")))
        return res

    def setAllDisableAlarmTime(self, wuid: str) -> list[bool]:
        res: list[bool] = []
        for alarmTime in self.getWatchAlarm(wuid):
            res.append(self.setDisableAlarmTime(alarmTime.get("id", "")))
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
        c: dict[str, Any] = self._gqlHandler.getFollowRequestWatchCount()
        return c.get("followRequestWatchCount", 0)

    def getWatches(self, wuid: str) -> dict[str, Any]:
        retryCounter = 0
        dataOk: dict[str, Any] = {}
        watches_raw: dict[str, Any] = {}
        watches: dict[str, Any] = {}
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                watches_raw = self._gqlHandler.getWatches(wuid)
                _watches: list[dict[str, Any]] = watches_raw.get("watches", [])
                if not _watches:
                    return watches
                for watch in _watches:
                    watches = {
                        "imei": watch["swKey"],
                        "osVersion": watch["osVersion"],
                        "qrCode": watch["qrCode"],
                        "model": watch["groupName"],
                    }
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = watches
            if not dataOk:
                self._logoff()
                self.delay(self.retryDelay)
        return watches

    def getSWInfo(self, wuid: str, watches: dict[str, Any] = {}) -> dict[str, Any]:
        wqr: dict[str, Any] = watches if watches else self.getWatches(wuid=wuid)
        qrCode: str = wqr.get("qrCode", "=")
        return self._gqlHandler.getSWInfo(qrCode.split("=")[1])

    def getWatchState(self, wuid: str, watches: dict[str, Any] = {}) -> dict[str, Any]:
        wqr: dict[str, Any] = watches if watches else self.getWatches(wuid=wuid)
        qrCode: str = wqr.get("qrCode", "=")
        try:
            return self._gqlHandler.getWatchState(qrCode=qrCode.split("=")[1])
        except Exception as error:
            _LOGGER.debug(error)
            return {}

    def conv360IDToO2OID(self, qid: str, deviceId: str) -> dict[str, Any]:
        return self._gqlHandler.conv360IDToO2OID(qid, deviceId)

    def campaigns(self, id: str, categoryId: str) -> dict[str, Any]:
        return self._gqlHandler.campaigns(id, categoryId)

    def getCountries(self) -> list[dict[str, str]]:
        countries: dict[str, Any] = self._gqlHandler.countries()
        return countries.get("countries", {})

    def getWatchLocHistory(self, wuid: str, date: int, tz: str, limit: int) -> dict[str, Any]:
        return self._gqlHandler.getWatchLocHistory(wuid, date, tz, limit)

    def watchesDynamic(self) -> dict[str, Any]:
        return self._gqlHandler.watchesDynamic()

    def watchGroups(self, id: str = "") -> dict[str, Any]:
        return self._gqlHandler.watchGroups(id)

    def familyInfo(self, wuid: str, watchId: str, tz: str, date: int) -> dict[str, Any]:
        return self._gqlHandler.familyInfo(wuid, watchId, tz, date)

    def avatars(self, id: str) -> dict[str, Any]:
        return self._gqlHandler.avatars(id)

    def getWatchUserSteps(self, wuid: str, date: int) -> dict[str, Any]:
        userSteps = self._gqlHandler.getWatchUserSteps(wuid=wuid, tz=self._timeZone, date=date)
        if not userSteps:
            return {}
        userSteps = userSteps.get("userSteps", {})
        if not userSteps:
            return {}
        return userSteps

    # start tracking for 30min
    def getStartTrackingWatch(self, wuid: str) -> int:
        data: dict[str, Any] = self._gqlHandler.getStartTrackingWatch(wuid)
        return data.get("startTrackingWatch", -1)

    # stop tracking from getStartTrackingWatch
    def getEndTrackingWatch(self, wuid: str) -> int:
        data: dict[str, Any] = self._gqlHandler.getEndTrackingWatch(wuid)
        return data.get("endTrackingWatch", -1)

    def addStep(self, step: int) -> bool:
        s: dict[str, bool] = self._gqlHandler.addStep(step)
        return s.get("addStep", False)

    def submitIncorrectLocationData(self, wuid: str, lat: str, lng: str, timestamp: str) -> bool:
        data: dict[str, bool] = self._gqlHandler.submitIncorrectLocationData(wuid, lat, lng, timestamp)
        return data.get("submitIncorrectLocationData", False)

    def getAppVersion(self):
        data = self._gqlHandler.getAppVersion()
        return data

    def checkEmailOrPhoneExist(
        self, type: UserContactType, email: str = "", countryCode: str = "", phoneNumber: str = ""
    ) -> bool:
        data = self._gqlHandler.checkEmailOrPhoneExist(type, email, countryCode, phoneNumber)
        return data.get("checkEmailOrPhoneExist", False)

    def modifyContact(
        self, contactId: str, isAdmin: bool | None = None, contactName: str = "", fileId: str = ""
    ) -> dict[str, Any]:
        data = self._gqlHandler.modifyContact(contactId, isAdmin, contactName, fileId)
        return data
