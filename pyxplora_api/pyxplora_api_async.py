from __future__ import annotations

import logging

from asyncio import sleep
from datetime import datetime
import sys
from time import time
from typing import Any, Dict, List

from .const import VERSION, VERSION_APP
from .exception_classes import FunctionError, LoginError, NoAdminError
from .gql_handler_async import GQLHandler
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

    async def __login(self, forceLogin: bool = False) -> Dict[Any, Any]:
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
                            self._issueToken = await self._gqlHandler.login_a()
                        except Exception:
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
        token = await self.__login(forceLogin)
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
    async def getWatchUserContacts(self, wuid: str) -> List[Dict[str, Any]]:
        retryCounter = 0
        dataOk: List[Any] = []
        contacts_raw: Dict[str, Any]
        contacts: List[Any] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            await self.init()
            try:
                contacts_raw = await self._gqlHandler.getWatchUserContacts_a(wuid)
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
                await sleep(self.retryDelay)
        if dataOk:
            return contacts
        else:
            raise FunctionError(sys._getframe().f_code.co_name)

    async def getWatchAlarm(self, wuid: str) -> List[Dict[str, Any]]:
        retryCounter = 0
        dataOk: List[Any] = []
        alarms_raw: Dict[str, Any]
        alarms: List[Any] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            await self.init()
            try:
                alarms_raw = await self._gqlHandler.getAlarmTime_a(wuid)
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
                await sleep(self.retryDelay)
        if dataOk:
            return alarms
        else:
            raise FunctionError(sys._getframe().f_code.co_name)

    async def loadWatchLocation(self, wuid: str = "", withAsk: bool = True) -> List[Dict[str, Any]]:
        retryCounter = 0
        dataOk: List[Any] = []
        location_raw: Dict[str, Any]
        watch_location: List[Any] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            await self.init()
            try:
                if withAsk:
                    await self.askWatchLocate(wuid)
                await sleep(self.retryDelay)
                location_raw = await self._gqlHandler.getWatchLastLocation_a(wuid)
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
                await sleep(self.retryDelay)
        if dataOk:
            return watch_location
        else:
            raise FunctionError(sys._getframe().f_code.co_name)

    async def getWatchBattery(self, wuid: str) -> int:
        return int((await self.loadWatchLocation(wuid=wuid))[0]["watch_battery"])

    async def getWatchIsCharging(self, wuid: str) -> bool:
        if (await self.loadWatchLocation(wuid=wuid))[0]["watch_charging"]:
            return True
        return False

    async def getWatchOnlineStatus(self, wuid: str) -> str:
        retryCounter = 0
        dataOk = WatchOnlineStatus.UNKNOWN
        asktrack_raw: WatchOnlineStatus = WatchOnlineStatus.UNKNOWN
        while dataOk is WatchOnlineStatus.UNKNOWN and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            await self.init()
            try:
                await self.askWatchLocate(wuid)
                await sleep(self.retryDelay)
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
        if dataOk:
            return asktrack_raw.value
        else:
            raise FunctionError(sys._getframe().f_code.co_name)

    """async def __setReadChatMsg_a(self, msgId, id):
        return (await self._gqlHandler.setReadChatMsg(self.getWatchUserIDs(), msgId, id))["setReadChatMsg"]"""

    async def getWatchUnReadChatMsgCount(self, wuid: str) -> int:
        # bug?
        return (await self._gqlHandler.unReadChatMsgCount_a(wuid))["unReadChatMsgCount"]

    async def getWatchChats(self, wuid: str, offset: int = 0, limit: int = 100, msgId: str = "") -> List[Dict[str, Any]]:
        # bug?
        retryCounter = 0
        dataOk: List[Any] = []
        chats_raw: Dict[str, Any]
        chats: List[Any] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            await self.init()
            try:
                await self.askWatchLocate(wuid)
                await sleep(self.retryDelay)
                chats_raw = await self._gqlHandler.chats_a(wuid, offset, limit, msgId)
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
                await sleep(self.retryDelay)
        if dataOk:
            return chats
        else:
            return chats

    ##### Watch Location Info #####
    async def getWatchLastLocation(self, wuid: str, withAsk: bool = False) -> Dict[str, Any]:
        return (await self.loadWatchLocation(wuid=wuid, withAsk=withAsk))[0]["watch_last_location"]

    async def getWatchLocate(self, wuid: str) -> Dict[str, Any]:
        return (await self.loadWatchLocation(wuid=wuid))[0]

    async def getWatchLocateType(self, wuid: str) -> str:
        return (await self.getWatchLocate(wuid)).get("locateType", LocationType.UNKNOWN.value)

    async def getWatchIsInSafeZone(self, wuid: str) -> bool:
        return (await self.getWatchLocate(wuid))["isInSafeZone"]

    async def getWatchSafeZoneLabel(self, wuid: str) -> str:
        return (await self.getWatchLocate(wuid))["safeZoneLabel"]

    async def getWatchSafeZones(self, wuid: str) -> List[Dict[str, Any]]:
        retryCounter = 0
        dataOk: List[Any] = []
        safeZones_raw: Dict[str, Any]
        safe_zones: List[Any] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            await self.init()
            try:
                await self.askWatchLocate(wuid)
                await sleep(self.retryDelay)
                safeZones_raw = await self._gqlHandler.safeZones_a(wuid)
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
                await sleep(self.retryDelay)
        if dataOk:
            return safe_zones
        else:
            raise FunctionError(sys._getframe().f_code.co_name)

    async def getTrackWatchInterval(self, wuid: str) -> int:
        return (await self._gqlHandler.trackWatch_a(wuid))["trackWatch"]

    async def askWatchLocate(self, wuid: str) -> bool:
        return (await self._gqlHandler.askWatchLocate_a(wuid))["askWatchLocate"]

    ##### Feature #####
    async def getSilentTime(self, wuid: str) -> List[Dict[str, Any]]:
        retryCounter = 0
        dataOk: List[Any] = []
        silentTimes_raw: Dict[str, Any]
        school_silent_mode: List[Any] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            await self.init()
            try:
                await self.askWatchLocate(wuid)
                await sleep(self.retryDelay)
                silentTimes_raw = await self._gqlHandler.silentTimes_a(wuid)
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
                await sleep(self.retryDelay)
        if dataOk:
            return school_silent_mode
        else:
            raise FunctionError(sys._getframe().f_code.co_name)

    async def setEnableSilentTime(self, silentId: str, wuid: str) -> bool:
        retryCounter = 0
        dataOk = ""
        _raw = ""
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            await self.init()
            try:
                await self.askWatchLocate(wuid)
                await sleep(self.retryDelay)
                enable_raw = await self._gqlHandler.setEnableSlientTime_a(silentId)
                if "setEnableSilentTime" in enable_raw:
                    _raw = enable_raw["setEnableSilentTime"]
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if not dataOk:
                self._logoff()
                await sleep(self.retryDelay)
        if dataOk:
            return bool(_raw)
        else:
            raise FunctionError(sys._getframe().f_code.co_name)

    async def setDisableSilentTime(self, silentId: str, wuid: str) -> bool:
        retryCounter = 0
        dataOk = ""
        _raw = ""
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            await self.init()
            try:
                await self.askWatchLocate(wuid)
                await sleep(self.retryDelay)
                disable_raw = await self._gqlHandler.setEnableSlientTime_a(silentId, NormalStatus.DISABLE.value)
                if "setEnableSilentTime" in disable_raw:
                    _raw = disable_raw["setEnableSilentTime"]
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if not dataOk:
                self._logoff()
                await sleep(self.retryDelay)
        if dataOk:
            return bool(_raw)
        else:
            raise FunctionError(sys._getframe().f_code.co_name)

    async def setAllEnableSilentTime(self, wuid: str) -> List[bool]:
        res: List[bool] = []
        for silentTime in await self.getSilentTime(wuid):
            res.append(await self.setEnableSilentTime(silentTime["id"], wuid))
        return res

    async def setAllDisableSilentTime(self, wuid: str) -> List[bool]:
        res: List[bool] = []
        for silentTime in await self.getSilentTime(wuid):
            res.append(await self.setDisableSilentTime(silentTime["id"], wuid))
        return res

    async def setEnableAlarmTime(self, alarmId: str, wuid: str) -> bool:
        retryCounter = 0
        dataOk = ""
        _raw = ""
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            await self.init()
            try:
                await self.askWatchLocate(wuid)
                await sleep(self.retryDelay)
                enable_raw = await self._gqlHandler.setEnableAlarmTime_a(alarmId)
                if "modifyAlarm" in enable_raw:
                    _raw = enable_raw["modifyAlarm"]
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if not dataOk:
                self._logoff()
                await sleep(self.retryDelay)
        if dataOk:
            return bool(_raw)
        else:
            raise FunctionError(sys._getframe().f_code.co_name)

    async def setDisableAlarmTime(self, alarmId: str, wuid: str) -> bool:
        retryCounter = 0
        dataOk = ""
        _raw = ""
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            await self.init()
            try:
                await self.askWatchLocate(wuid)
                await sleep(self.retryDelay)
                disable_raw = await self._gqlHandler.setEnableAlarmTime_a(alarmId, NormalStatus.DISABLE.value)
                if "modifyAlarm" in disable_raw:
                    _raw = disable_raw["modifyAlarm"]
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if not dataOk:
                self._logoff()
                await sleep(self.retryDelay)
        if dataOk:
            return bool(_raw)
        else:
            raise FunctionError(sys._getframe().f_code.co_name)

    async def setAllEnableAlarmTime(self, wuid: str) -> List[bool]:
        res: List[bool] = []
        for alarmTime in await self.getWatchAlarm(wuid):
            res.append(await self.setEnableAlarmTime(alarmTime["id"], wuid))
        return res

    async def setAllDisableAlarmTime(self, wuid: str) -> List[bool]:
        res: List[bool] = []
        for alarmTime in await self.getWatchAlarm(wuid):
            res.append(await self.setDisableAlarmTime(alarmTime["id"], wuid))
        return res

    async def sendText(self, text: str, wuid: str) -> bool:
        # sender is login User
        return await self._gqlHandler.sendText_a(wuid, text)

    async def isAdmin(self, wuid: str) -> bool:
        contacts = await self.getWatchUserContacts(wuid)
        for contact in contacts:
            try:
                id = contact["id"]
            except KeyError and TypeError:
                id = None
            if self.getUserID() == id:
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
        c: Dict[str, Any] = await self._gqlHandler.getFollowRequestWatchCount_a()
        return c.get("followRequestWatchCount", 0)

    async def getWatches(self, wuid: str) -> List[Dict[str, Any]]:
        retryCounter = 0
        dataOk: List[Any] = []
        watches_raw: Dict[str, Any]
        watches: List[Any] = []
        while not dataOk and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            self.init()
            try:
                watches_raw = await self._gqlHandler.getWatches_a(wuid)
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

    async def getSWInfo(self, wuid: str) -> Dict[str, Any]:
        qrCode: str = (await self.getWatches(wuid=wuid))[0]["qrCode"]
        return await self._gqlHandler.getSWInfo_a(qrCode.split("=")[1])

    async def getWatchState(self, wuid: str) -> Dict[str, Any]:
        w: List[Dict[str, Any]] = await self.getWatches(wuid=wuid)
        qrCode: str = w[0]["qrCode"]
        return await self._gqlHandler.getWatchState_a(qrCode.split("=")[1])

    async def conv360IDToO2OID(self, qid: str, deviceId: str) -> Dict[str, Any]:
        return await self._gqlHandler.conv360IDToO2OID_a(qid, deviceId)

    async def campaigns(self, id: str, categoryId: str) -> Dict[str, Any]:
        return await self._gqlHandler.campaigns_a(id, categoryId)

    async def getCountries(self) -> List[Dict[str, str]]:
        countries: Dict[str, Any] = await self._gqlHandler.countries_a()
        return countries.get("countries", [])

    async def getWatchLocHistory(self, wuid: str, date: int, tz: str, limit: int) -> Dict[str, Any]:
        return await self._gqlHandler.getWatchLocHistory_a(wuid, date, tz, limit)

    async def watchesDynamic(self) -> Dict[str, Any]:
        return await self._gqlHandler.watchesDynamic_a()

    async def watchGroups(self, id: str = "") -> Dict[str, Any]:
        return await self._gqlHandler.watchGroups_a(id)

    async def familyInfo(self, wuid: str, watchId: str, tz: str, date: int) -> Dict[str, Any]:
        return await self._gqlHandler.familyInfo_a(wuid, watchId, tz, date)

    async def avatars(self, id: str) -> Dict[str, Any]:
        return await self._gqlHandler.avatars_a(id)

    async def getWatchUserSteps(self, wuid: str, date: int) -> Dict[str, Any]:
        userSteps = await self._gqlHandler.getWatchUserSteps_a(wuid=wuid, tz=self._timeZone, date=date)
        if not userSteps:
            return userSteps
        userSteps = userSteps.get("userSteps", {})
        if not userSteps:
            return {}
        return userSteps
