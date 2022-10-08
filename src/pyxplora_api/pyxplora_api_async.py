from __future__ import annotations

import logging

from asyncio import create_task, sleep
from datetime import datetime
from time import time

from .const import VERSION, VERSION_APP
from .exception_classes import LoginError, NoAdminError
from .gql_handler_async import GQLHandler
from .pyxplora import PyXplora
from .status import LocationType, NormalStatus, WatchOnlineStatus

_LOGGER = logging.getLogger(__name__)

_LIST_DICT: list[dict[str, any]] = []


class PyXploraApi(PyXplora):
    def __init__(
        self,
        countrycode: str,
        phoneNumber: str,
        password: str,
        userLang: str,
        timeZone: str,
        childPhoneNumber: list[str] = [],
        wuid: str | list = None,
        email: str = None,
    ) -> None:
        super().__init__(countrycode, phoneNumber, password, userLang, timeZone, childPhoneNumber, wuid, email)

    async def _login(self, forceLogin: bool = False) -> dict[any, any]:
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
                )
                if self._gqlHandler:
                    retryCounter = 0
                    while not self._isConnected() and (retryCounter < self.maxRetries + 2):
                        retryCounter += 1

                        # Try to login
                        try:
                            self._issueToken = await self._gqlHandler.login_a()
                        except LoginError as err:
                            self.error_message = err.message
                        except Exception:
                            if retryCounter == self.maxRetries + 2:
                                self.error_message = "Cannot connect to the server."
                            else:
                                pass

                        # Wait for next try
                        if not self._issueToken:
                            await sleep(self.retryDelay)
                    if self._issueToken:
                        self.dtIssueToken = int(time())
                else:
                    raise Exception("Unknown error creating a new GraphQL handler instance.")
            except Exception:
                # Login failed.
                self._logoff()
        return self._issueToken

    async def init(self, forceLogin: bool = False) -> None:
        token = await self._login(forceLogin)
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
        raise LoginError(self.error_message)

    def version(self) -> str:
        return "{0}-{1}".format(VERSION, VERSION_APP)

    async def setDevices(self, ids: list = []) -> list[dict[str, any]]:
        return await self._setDevices(ids)

    async def _setDevices(self, ids: list = []) -> list[str]:
        if ids:
            wuids = ids
        else:
            wuids: list[str] = self.getWatchUserIDs()
        for wuid in wuids:
            self.device[wuid] = {}
            self.device[wuid]["getWatchAlarm"] = await create_task(self.getWatchAlarm(wuid=wuid))
            self.device[wuid]["loadWatchLocation"] = await create_task(self.loadWatchLocation(wuid=wuid))
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
            self.device[wuid]["getWatchSafeZones"] = await create_task(self.getWatchSafeZones(wuid=wuid))
            self.device[wuid]["getSilentTime"] = await create_task(self.getSilentTime(wuid=wuid))
            self.device[wuid]["getWatches"] = await create_task(self.getWatches(wuid=wuid))
            self.device[wuid]["getSWInfo"] = await create_task(
                self.getSWInfo(wuid=wuid, watches=self.device[wuid]["getWatches"])
            )
            d = datetime.now()
            dt = datetime(year=d.year, month=d.month, day=d.day)
            self.device[wuid]["getWatchUserSteps"] = await create_task(self.getWatchUserSteps(wuid=wuid, date=dt.timestamp()))
            self.device[wuid]["getWatchOnlineStatus"] = await create_task(self.getWatchOnlineStatus(wuid=wuid))
            self.device[wuid]["getWatchUserIcons"] = self.getWatchUserIcons(wuid=wuid)
            self.device[wuid]["getWatchUserXcoins"] = self.getWatchUserXcoins(wuid=wuid)
        return wuids

    ##### Contact Info #####
    async def getWatchUserContacts(self, wuid: str) -> list[dict[str, any]]:
        retryCounter = 0
        dataOk: list[dict[str, any]] = []
        contacts_raw: dict[str, any] = {}
        contacts: list[dict[str, any]] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                contacts_raw = await self._gqlHandler.getWatchUserContacts_a(wuid)
                _contacts: dict[str, any] = contacts_raw.get("contacts", {})
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
                await sleep(self.retryDelay)
        return contacts

    async def getWatchAlarm(self, wuid: str) -> list[dict[str, any]]:
        retryCounter = 0
        dataOk: list[dict[str, any]] = []
        alarms_raw: dict[str, any] = {}
        alarms: list[dict[str, any]] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                alarms_raw = await self._gqlHandler.getAlarmTime_a(wuid)
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
                await sleep(self.retryDelay)
        return alarms

    async def loadWatchLocation(self, wuid: str = "", withAsk: bool = True) -> dict[str, any]:
        retryCounter = 0
        dataOk: list[dict[str, any]] = []
        location_raw: dict[str, any] = {}
        watch_location: dict[str, any] = {}
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                if withAsk:
                    await self.askWatchLocate(wuid)
                location_raw = await self._gqlHandler.getWatchLastLocation_a(wuid)
                _watchLastLocate = location_raw.get(
                    "watchLastLocate",
                    {},
                )
                if not _watchLastLocate:
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
                await sleep(self.retryDelay)
        return watch_location

    async def getWatchBattery(self, wuid: str) -> int:
        watch_b: dict[str, any] = await self.loadWatchLocation(wuid=wuid)
        return int(watch_b.get("watch_battery", -1))

    async def getWatchIsCharging(self, wuid: str) -> bool:
        watch_c: dict[str, any] = await self.loadWatchLocation(wuid=wuid)
        if watch_c.get("watch_charging", False):
            return True
        return False

    async def getWatchOnlineStatus(self, wuid: str) -> str:
        retryCounter = 0
        dataOk = WatchOnlineStatus.UNKNOWN
        asktrack_raw: WatchOnlineStatus = WatchOnlineStatus.UNKNOWN
        while dataOk is WatchOnlineStatus.UNKNOWN and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                ask_raw = await self.askWatchLocate(wuid)
                track_raw = await self.getTrackWatchInterval(wuid)
                if ask_raw or (track_raw != -1):
                    asktrack_raw = WatchOnlineStatus.ONLINE
                else:
                    asktrack_raw = WatchOnlineStatus.OFFLINE
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = asktrack_raw
            if dataOk is WatchOnlineStatus.UNKNOWN:
                self._logoff()
                await sleep(self.retryDelay)
        return asktrack_raw.value

    """async def __setReadChatMsg_a(self, msgId, id):
        return (await self._gqlHandler.setReadChatMsg(self.getWatchUserIDs(), msgId, id))["setReadChatMsg"]"""

    async def getWatchUnReadChatMsgCount(self, wuid: str) -> int:
        # bug?
        return (await self._gqlHandler.unReadChatMsgCount_a(wuid)).get("unReadChatMsgCount", -1)

    async def getWatchChats(self, wuid: str, offset: int = 0, limit: int = 100, msgId: str = "") -> list[dict[str, any]]:
        # bug?
        retryCounter = 0
        dataOk: list[dict[str, any]] = []
        chats_raw: dict[str, any] = {}
        chats: list[dict[str, any]] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                chats_raw = await self._gqlHandler.chats_a(wuid, offset, limit, msgId)
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
                await sleep(self.retryDelay)
        return chats

    ##### Watch Location Info #####
    async def getWatchLastLocation(self, wuid: str, withAsk: bool = False) -> dict[str, any]:
        _loadWatchLocation = await self.loadWatchLocation(wuid=wuid, withAsk=withAsk)
        if isinstance(_loadWatchLocation, dict):
            return _loadWatchLocation.get("watch_last_location", {})
        if not _loadWatchLocation:
            return {}
        for loadWatchLocation in _loadWatchLocation:
            return loadWatchLocation.get("watch_last_location", {})
        return {}

    async def getWatchLocate(self, wuid: str) -> dict[str, any]:
        _loadWatchLocation = await self.loadWatchLocation(wuid=wuid)
        if isinstance(_loadWatchLocation, dict):
            return _loadWatchLocation
        if not _loadWatchLocation:
            return {}
        for loadWatchLocation in _loadWatchLocation:
            return loadWatchLocation
        return {}

    async def getWatchLocateType(self, wuid: str) -> str:
        return (await self.getWatchLocate(wuid)).get("locateType", LocationType.UNKNOWN.value)

    async def getWatchIsInSafeZone(self, wuid: str) -> bool:
        return (await self.getWatchLocate(wuid)).get("isInSafeZone", False)

    async def getWatchSafeZoneLabel(self, wuid: str) -> str:
        return (await self.getWatchLocate(wuid)).get("safeZoneLabel", "")

    async def getWatchSafeZones(self, wuid: str) -> list[dict[str, any]]:
        retryCounter = 0
        dataOk: list[dict[str, any]] = []
        safeZones_raw: dict[str, any] = {}
        safe_zones: list[dict[str, any]] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                safeZones_raw = await self._gqlHandler.safeZones_a(wuid)
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
                await sleep(self.retryDelay)
        return safe_zones

    async def getTrackWatchInterval(self, wuid: str) -> int:
        return (await self._gqlHandler.trackWatch_a(wuid)).get("trackWatch", -1)

    async def askWatchLocate(self, wuid: str) -> bool:
        return (await self._gqlHandler.askWatchLocate_a(wuid)).get("askWatchLocate", False)

    ##### Feature #####
    async def getSilentTime(self, wuid: str) -> list[dict[str, any]]:
        retryCounter = 0
        dataOk: list[dict[str, any]] = []
        silentTimes_raw: dict[str, any] = {}
        school_silent_mode: list[dict[str, any]] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                silentTimes_raw = await self._gqlHandler.silentTimes_a(wuid)
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
                await sleep(self.retryDelay)
        return school_silent_mode

    async def setEnableSilentTime(self, silentId: str) -> bool:
        retryCounter = 0
        dataOk = ""
        _raw = ""
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                enable_raw = await self._gqlHandler.setEnableSlientTime_a(silentId)
                _setEnableSilentTime = enable_raw.get("setEnableSilentTime", -1)
                if not _setEnableSilentTime:
                    return bool(_raw)
                _raw = _setEnableSilentTime
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if not dataOk:
                self._logoff()
                await sleep(self.retryDelay)
        return bool(_raw)

    async def setDisableSilentTime(self, silentId: str) -> bool:
        retryCounter = 0
        dataOk = ""
        _raw = ""
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                disable_raw = await self._gqlHandler.setEnableSlientTime_a(silentId, NormalStatus.DISABLE.value)
                _setEnableSilentTime = disable_raw.get("setEnableSilentTime", -1)
                if not _setEnableSilentTime:
                    return bool(_raw)
                _raw = _setEnableSilentTime
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if not dataOk:
                self._logoff()
                await sleep(self.retryDelay)
        return bool(_raw)

    async def setAllEnableSilentTime(self, wuid: str) -> list[bool]:
        res: list[bool] = []
        for silentTime in await self.getSilentTime(wuid):
            res.append(await self.setEnableSilentTime(silentTime.get("id", "")))
        return res

    async def setAllDisableSilentTime(self, wuid: str) -> list[bool]:
        res: list[bool] = []
        for silentTime in await self.getSilentTime(wuid):
            res.append(await self.setDisableSilentTime(silentTime.get("id", "")))
        return res

    async def setEnableAlarmTime(self, alarmId: str) -> bool:
        retryCounter = 0
        dataOk = ""
        _raw = ""
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                enable_raw = await self._gqlHandler.setEnableAlarmTime_a(alarmId)
                _modifyAlarm = enable_raw.get("modifyAlarm", -1)
                if not _modifyAlarm:
                    return bool(_raw)
                _raw = _modifyAlarm
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if not dataOk:
                self._logoff()
                await sleep(self.retryDelay)
        return bool(_raw)

    async def setDisableAlarmTime(self, alarmId: str) -> bool:
        retryCounter = 0
        dataOk = ""
        _raw = ""
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                disable_raw = await self._gqlHandler.setEnableAlarmTime_a(alarmId, NormalStatus.DISABLE.value)
                _modifyAlarm = disable_raw.get("modifyAlarm", -1)
                if not _modifyAlarm:
                    return bool(_raw)
                _raw = _modifyAlarm
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if not dataOk:
                self._logoff()
                await sleep(self.retryDelay)
        return bool(_raw)

    async def setAllEnableAlarmTime(self, wuid: str) -> list[bool]:
        res: list[bool] = []
        for alarmTime in await self.getWatchAlarm(wuid):
            res.append(await self.setEnableAlarmTime(alarmTime.get("id", "")))
        return res

    async def setAllDisableAlarmTime(self, wuid: str) -> list[bool]:
        res: list[bool] = []
        for alarmTime in await self.getWatchAlarm(wuid):
            res.append(await self.setDisableAlarmTime(alarmTime.get("id", "")))
        return res

    async def sendText(self, text: str, wuid: str) -> bool:
        # sender is login User
        return await self._gqlHandler.sendText_a(wuid, text)

    async def isAdmin(self, wuid: str) -> bool:
        contacts = await self.getWatchUserContacts(wuid)
        for contact in contacts:
            _id = contact.get("id", None)
            if self.getUserID() == _id:
                if contact["guardianType"] == "FIRST":
                    return True
        return False

    async def shutdown(self, wuid: str) -> bool:
        if self.isAdmin(wuid):
            return await self._gqlHandler.shutdown_a(wuid)
        raise NoAdminError()

    async def reboot(self, wuid: str) -> bool:
        if self.isAdmin(wuid):
            return await self._gqlHandler.reboot_a(wuid)
        raise NoAdminError()

    async def getFollowRequestWatchCount(self) -> int:
        c: dict[str, any] = await self._gqlHandler.getFollowRequestWatchCount_a()
        return c.get("followRequestWatchCount", 0)

    async def getWatches(self, wuid: str) -> dict[str, any]:
        retryCounter = 0
        dataOk: dict[str, any] = {}
        watches_raw: dict[str, any] = {}
        watches: dict[str, any] = {}
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                watches_raw = await self._gqlHandler.getWatches_a(wuid)
                _watches: list[dict[str, any]] = watches_raw.get("watches", [])
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
                await sleep(self.retryDelay)
        return watches

    async def getSWInfo(self, wuid: str, watches: dict[str, any] = {}) -> dict[str, any]:
        wqr: dict[str, any] = watches if watches else await self.getWatches(wuid=wuid)
        qrCode: str = wqr.get("qrCode", "=")
        return await self._gqlHandler.getSWInfo_a(qrCode.split("=")[1])

    async def getWatchState(self, wuid: str, watches: dict[str, any] = {}) -> dict[str, any]:
        wqr: dict[str, any] = watches if watches else await self.getWatches(wuid=wuid)
        qrCode: str = wqr.get("qrCode", "=")
        return await self._gqlHandler.getWatchState_a(qrCode=qrCode.split("=")[1])

    async def conv360IDToO2OID(self, qid: str, deviceId: str) -> dict[str, any]:
        return await self._gqlHandler.conv360IDToO2OID_a(qid, deviceId)

    async def campaigns(self, id: str, categoryId: str) -> dict[str, any]:
        return await self._gqlHandler.campaigns_a(id, categoryId)

    async def getCountries(self) -> list[dict[str, str]]:
        countries: dict[str, any] = await self._gqlHandler.countries_a()
        return countries.get("countries", {})

    async def getWatchLocHistory(self, wuid: str, date: int, tz: str, limit: int) -> dict[str, any]:
        return await self._gqlHandler.getWatchLocHistory_a(wuid, date, tz, limit)

    async def watchesDynamic(self) -> dict[str, any]:
        return await self._gqlHandler.watchesDynamic_a()

    async def watchGroups(self, id: str = "") -> dict[str, any]:
        return await self._gqlHandler.watchGroups_a(id)

    async def familyInfo(self, wuid: str, watchId: str, tz: str, date: int) -> dict[str, any]:
        return await self._gqlHandler.familyInfo_a(wuid, watchId, tz, date)

    async def avatars(self, id: str) -> dict[str, any]:
        return await self._gqlHandler.avatars_a(id)

    async def getWatchUserSteps(self, wuid: str, date: int) -> dict[str, any]:
        userSteps = await self._gqlHandler.getWatchUserSteps_a(wuid=wuid, tz=self._timeZone, date=date)
        if not userSteps:
            return {}
        userSteps = userSteps.get("userSteps", {})
        if not userSteps:
            return {}
        return userSteps

    # start tracking for 30min
    async def getStartTrackingWatch(self, wuid: str) -> int:
        data: dict[str, any] = await self._gqlHandler.getStartTrackingWatch_a(wuid)
        return data.get("startTrackingWatch", -1)

    # stop tracking from getStartTrackingWatch
    async def getEndTrackingWatch(self, wuid: str) -> int:
        data: dict[str, any] = await self._gqlHandler.getEndTrackingWatch_a(wuid)
        return data.get("endTrackingWatch", -1)

    async def addStep(self, step: int) -> bool:
        s: dict[str, bool] = await self._gqlHandler.addStep_a(step)
        return s.get("addStep", False)

    async def submitIncorrectLocationData(self, wuid: str, lat: str, lng: str, timestamp: str) -> bool:
        data: dict[str, bool] = await self._gqlHandler.submitIncorrectLocationData(wuid, lat, lng, timestamp)
        return data.get("submitIncorrectLocationData", False)

    async def getAppVersion(self):
        data = await self._gqlHandler.getAppVersion_a()
        return data
