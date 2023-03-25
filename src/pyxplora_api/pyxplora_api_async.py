from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from time import time
from typing import Any, Dict, List, Optional, Union

import aiohttp

from .const import VERSION, VERSION_APP
from .exception_classes import Error, ErrorMSG, LoginError, NoAdminError
from .gql_handler_async import GQLHandler
from .model import Chats, ChatsNew, SmallChat, SmallChatList
from .pyxplora import PyXplora
from .status import Emoji, LocationType, NormalStatus, UserContactType, WatchOnlineStatus

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
        childPhoneNumber: list[str] = None,
        wuid: str | list | None = None,
        email: str | None = None,
        sign_up: bool = True,
        session: aiohttp.ClientSession = None,
    ) -> None:
        super().__init__(countrycode, phoneNumber, password, userLang, timeZone, childPhoneNumber, wuid, email)
        self._gql_handler: GQLHandler = GQLHandler(
            self._countrycode, self._phoneNumber, self._password, self._userLang, self._timeZone, self._email, sign_up, session
        )

    async def _login(self, force_login: bool = False, key=None, sec=None) -> Dict[str, Any]:
        if not self._isConnected() or self._hasTokenExpired() or force_login:
            retryCounter = 0
            while not self._isConnected() and (retryCounter < self.maxRetries + 2):
                retryCounter += 1

                # Try to login
                try:
                    self._issueToken = await self._gql_handler.login_a(key, sec)
                except LoginError as error:
                    self.error_message = error.error_message
                    await asyncio.sleep(self.retryDelay)
                except Error:
                    if retryCounter == self.maxRetries + 2:
                        self.error_message = ErrorMSG.SERVER_ERR
                    else:
                        await asyncio.sleep(self.retryDelay)

            if self._issueToken:
                self.dtIssueToken = int(time())
        return self._issueToken

    async def init(self, forceLogin: bool = False, signup: bool = True, key=None, sec=None) -> None:
        # self.initHandler(signup)
        token = await self._login(forceLogin, key, sec)
        if not signup:
            return
        if not token:
            if self.error_message:
                # now = datetime.now()

                # current_time = now.strftime("%H:%M:%S")
                # print("Current Time =", current_time)
                # print(self.error_message)
                raise LoginError(self.error_message)
            self.init(forceLogin, signup, key, sec)

        user = token.get("user", None)
        if not user:
            raise LoginError(self.error_message)

        children = user.get("children", [])
        if not self._childPhoneNumber:
            self.watchs = children
        else:
            self.watchs = [watch for watch in children if watch["ward"]["phoneNumber"] in self._childPhoneNumber]
        self.user = user

    def version(self) -> str:
        return f"{VERSION}-{VERSION_APP}"

    async def setDevices(self, ids: Optional[Union[str, List[str]]] = None) -> List[str]:
        if isinstance(ids, str):
            ids = [ids]
        return await self._setDevices(ids or [])

    async def _setDevices(self, ids: List[str] = None) -> List[str]:
        wuids = ids if ids else self.getWatchUserIDs()
        tasks = [self._setDevice(wuid) for wuid in wuids]
        await asyncio.gather(*tasks)
        return wuids

    async def _setDevice(self, wuid: str) -> None:
        tasks = [
            self.getWatchAlarm(wuid),
            self.loadWatchLocation(wuid),
            self.getWatchBattery(wuid),
            self.getWatchIsCharging(wuid),
            self.getWatchLocateType(wuid),
            self.getWatchSafeZoneLabel(wuid),
            self.getWatchSafeZones(wuid),
            self.getWatchIsInSafeZone(wuid),
            self.getSilentTime(wuid),
            self.getWatches(wuid),
            self.getSWInfo(wuid, watches=await self.getWatches(wuid)),
            self.getWatchUserSteps(
                wuid, date=int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
            ),
            self.getWatchOnlineStatus(wuid),
        ]
        results = await asyncio.gather(*tasks)
        (
            watch_alarm,
            watch_location,
            battery,
            isCharging,
            locateType,
            safeZoneLabel,
            watch_safe_zones,
            isInSafeZone,
            silent_time,
            watches,
            sw_info,
            user_steps,
            online_status,
        ) = results
        self.device[wuid] = {
            "getWatchAlarm": watch_alarm,
            "watch_battery": battery,
            "watch_charging": isCharging,
            "locateType": locateType,
            "lastTrackTime": watch_location.get("tm", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "lat": watch_location.get("lat", None),
            "lng": watch_location.get("lng", None),
            "rad": watch_location.get("rad", -1),
            "step": watch_location.get("watch_last_location", {}).get("step", 0),
            "distance": watch_location.get("watch_last_location", {}).get("distance", -1),
            "isInSafeZone": isInSafeZone,
            "safeZoneLabel": safeZoneLabel,
            "getWatchSafeZones": watch_safe_zones,
            "getSilentTime": silent_time,
            "getWatches": watches,
            "getSWInfo": sw_info,
            "getWatchUserSteps": user_steps,
            "getWatchOnlineStatus": online_status,
            "getWatchUserIcons": self.getWatchUserIcons(wuid),
            "getWatchUserXCoins": self.getWatchUserXCoins(wuid),
        }

    ##### Contact Info #####
    async def getWatchUserContacts(self, wuid: str) -> List[dict[str, Any]]:
        retries = 0
        contacts = []
        while retries < self.maxRetries + 2:
            retries += 1
            try:
                raw_contacts = await self._gql_handler.getWatchUserContacts_a(wuid)
                raw_contacts = raw_contacts.get("contacts", {})
                if not raw_contacts:
                    continue
                raw_contacts = raw_contacts.get("contacts", [])
                for contact in raw_contacts:
                    contactUser = contact.get("contactUser", {})
                    if contactUser:
                        xcoin = contactUser.get("xcoin", -1)
                        id = contactUser.get("id", None)
                        contacts.append(
                            {
                                "id": id,
                                "guardianType": contact["guardianType"],
                                "create": datetime.fromtimestamp(contact["create"]).strftime("%Y-%m-%d %H:%M:%S"),
                                "update": datetime.fromtimestamp(contact["update"]).strftime("%Y-%m-%d %H:%M:%S"),
                                "name": contact["name"],
                                "phoneNumber": f'+{contact["countryPhoneNumber"]}{contact["phoneNumber"]}',
                                "xcoin": xcoin,
                            }
                        )
                break
            except (Error, TypeError) as error:
                _LOGGER.debug(error)
                await asyncio.sleep(self.retryDelay)
        return contacts

    async def getWatchAlarm(self, wuid: str) -> List[Dict[str, Any]]:
        retry_counter = 0
        alarms: List[Dict[str, Any]] = []

        while retry_counter < self.maxRetries + 2:
            try:
                alarms_raw = await self._gql_handler.getAlarmTime_a(wuid)
                raw_alarms = alarms_raw.get("alarms", [])
                if not raw_alarms:
                    return []
                for alarm in raw_alarms:
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
                break
            except Error as error:
                retry_counter += 1
                _LOGGER.debug(error)
                await asyncio.sleep(self.retryDelay)
        return alarms

    async def loadWatchLocation(self, wuid: str = "", with_ask: bool = True) -> Dict[str, Any]:
        retry_counter = 0
        watch_location = {}
        while retry_counter < self.maxRetries + 1:
            try:
                if with_ask:
                    await self.askWatchLocate(wuid)
                    await asyncio.sleep(1)
                location_raw = await self._gql_handler.getWatchLastLocation_a(wuid)
                _watch_last_locate = location_raw.get("watchLastLocate", {})
                if not _watch_last_locate:
                    return watch_location
                _tm = 31532399 if _watch_last_locate.get("tm") is None else _watch_last_locate.get("tm")
                _lat = _watch_last_locate.get("lat", "0.0")
                _lng = _watch_last_locate.get("lng", "0.0")
                _rad = _watch_last_locate.get("rad", -1)
                _poi = _watch_last_locate.get("poi", "")
                _city = _watch_last_locate.get("city", "")
                _province = _watch_last_locate.get("province", "")
                _country = _watch_last_locate.get("country", "")
                _locate_type = (
                    LocationType.UNKNOWN.value
                    if _watch_last_locate.get("locateType") is None
                    else _watch_last_locate.get("locateType")
                )
                _is_in_safe_zone = _watch_last_locate.get("isInSafeZone", False)
                _safe_zone_label = _watch_last_locate.get("safeZoneLabel", "")
                _watch_battery = _watch_last_locate.get("battery", -1)
                _watch_charging = _watch_last_locate.get("isCharging", False)

                watch_location = {
                    "tm": datetime.fromtimestamp(_tm).strftime("%Y-%m-%d %H:%M:%S"),
                    "lat": _lat,
                    "lng": _lng,
                    "rad": _rad,
                    "poi": _poi,
                    "city": _city,
                    "province": _province,
                    "country": _country,
                    "locateType": _locate_type,
                    "isInSafeZone": _is_in_safe_zone,
                    "safeZoneLabel": _safe_zone_label,
                    "watch_battery": _watch_battery,
                    "watch_charging": _watch_charging,
                    "watch_last_location": _watch_last_locate,
                }
                return watch_location

            except Error as error:
                _LOGGER.debug(error)
                retry_counter += 1

            await asyncio.sleep(self.retryDelay)

        return watch_location

    async def getWatchBattery(self, wuid: str) -> int:
        tasks = [self.loadWatchLocation(wuid)]
        results = await asyncio.gather(*tasks)
        if results:
            return results[0].get("watch_battery", -1)
        return -1

    async def getWatchIsCharging(self, wuid: str) -> bool:
        tasks = [self.loadWatchLocation(wuid)]
        results = await asyncio.gather(*tasks)
        if results:
            return results[0].get("watch_charging", False)
        return False

    async def getWatchOnlineStatus(self, wuid: str) -> str:
        retries = 0
        status = WatchOnlineStatus.UNKNOWN

        while status is WatchOnlineStatus.UNKNOWN and retries < self.maxRetries + 2:
            try:
                ask_raw = await self.askWatchLocate(wuid)
                track_raw = await self.getTrackWatchInterval(wuid)
                status = WatchOnlineStatus.ONLINE if ask_raw or track_raw != -1 else WatchOnlineStatus.OFFLINE
            except Error as error:
                _LOGGER.debug(error)
                retries += 1
            if status is WatchOnlineStatus.UNKNOWN:
                await asyncio.sleep(self.retryDelay)

        return status.value

    async def getWatchUnReadChatMsgCount(self, wuid: str) -> int:
        try:
            unread_count = await self._gql_handler.unReadChatMsgCount_a(wuid)
            if isinstance(unread_count, dict):
                return unread_count.get("unReadChatMsgCount", -1)
            return -1
        except Error as e:
            _LOGGER.error(f"Error getting unread chat message count: {e}")
            return -1

    async def getWatchChats(
        self, wuid: str, offset: int = 0, limit: int = 0, msgId: str = "", show_del_msg: bool = True, asObject=False
    ) -> Union[List[Dict[str, Any]], SmallChatList]:
        retry_counter = 0
        chats: List[Dict[str, Any]] = []

        while not chats and retry_counter < self.maxRetries + 2:
            retry_counter += 1
            try:
                _chats_new = await self.getWatchChatsRaw(wuid, offset, limit, msgId, show_del_msg, asObject)
                if isinstance(_chats_new, dict):
                    _chats_new = ChatsNew.from_dict(_chats_new)

                _list = _chats_new.list
                if not _list:
                    continue

                for chat in _list:
                    _chat = {
                        "msgId": chat.msgId,
                        "type": chat.type,
                        "sender_id": chat.sender.id,
                        "sender_name": chat.sender.name,
                        "receiver_id": chat.receiver.id,
                        "receiver_name": chat.receiver.name,
                        "data_text": chat.data.text,
                        "data_sender_name": chat.data.sender_name,
                        "create": datetime.fromtimestamp(chat.create).strftime("%Y-%m-%d %H:%M:%S"),
                        "delete_flag": chat.data.delete_flag,
                        "emoticon_id": chat.data.emoticon_id,
                    }
                    if asObject:
                        chats.append(SmallChat.from_dict(_chat))
                    else:
                        chats.append(_chat)
            except Error as error:
                _LOGGER.debug(error)

            if not chats:
                await asyncio.sleep(self.retryDelay)

        if asObject:
            return SmallChatList(chats)
        return chats

    async def getWatchChatsRaw(
        self,
        wuid: str,
        offset: int = 0,
        limit: int = 0,
        msgId: str = "",
        show_del_msg: bool = True,
        asObject=False,
        with_emoji_id=True,
    ) -> Union[dict, ChatsNew]:
        retry_counter = 0
        chats_new: dict = {}
        while not chats_new and retry_counter < self.maxRetries + 2:
            retry_counter += 1
            try:
                result = await self._gql_handler.chats_a(wuid, offset, limit, msgId, asObject)
                if not result:
                    continue
                if isinstance(result, dict):
                    result = ChatsNew.from_dict(result.get("chatsNew", None))
                elif isinstance(result, Chats):
                    result = result.chatsNew

                if result is None:
                    continue

                if with_emoji_id:
                    for d in result.list:
                        d.data.emoji_id = d.data.emoticon_id
                        d.data.emoticon_id = Emoji[f"M{d.data.emoticon_id}"].value
                        await self.set_read_chat_msg(wuid, d.msgId, d.id)

                result = ChatsNew.from_dict(result)

                filtered_chats = [chat for chat in result.list if show_del_msg or chat.data.delete_flag == 0]
                chats_new = ChatsNew(filtered_chats).to_dict()
            except Error as error:
                _LOGGER.debug(error)

            if not chats_new:
                await asyncio.sleep(self.retryDelay)

        return ChatsNew.from_dict(chats_new, infer_missing=True) if asObject else chats_new

    ##### Watch Location Info #####
    async def getWatchLastLocation(self, wuid: str, withAsk: bool = False) -> Dict[str, Any]:
        tasks = [self.loadWatchLocation(wuid)]
        results = await asyncio.gather(*tasks)
        if results:
            return results[0].get("watch_last_location", {})
        return {}

    async def getWatchLocate(self, wuid: str) -> Dict[str, Any]:
        tasks = [self.loadWatchLocation(wuid)]
        results = await asyncio.gather(*tasks)
        if results:
            return results[0]
        return {}

    async def getWatchLocateType(self, wuid: str) -> str:
        locate_info = await self.getWatchLocate(wuid)
        return locate_info.get("locateType", LocationType.UNKNOWN.value)

    async def getWatchIsInSafeZone(self, wuid: str) -> bool:
        return (await self.getWatchLocate(wuid)).get("isInSafeZone", False)

    async def getWatchSafeZoneLabel(self, wuid: str) -> str:
        return (await self.getWatchLocate(wuid)).get("safeZoneLabel", "")

    async def getWatchSafeZones(self, wuid: str) -> List[dict[str, Any]]:
        retry_counter = 0
        safe_zones = []
        while retry_counter < self.maxRetries + 2:
            try:
                safe_zones_raw = await self._gql_handler.safeZones_a(wuid)
                _safe_zones = safe_zones_raw.get("safeZones", [])
                if not _safe_zones:
                    return []
                safe_zones = [
                    {
                        "vendorId": sz["vendorId"],
                        "groupName": sz["groupName"],
                        "name": sz["name"],
                        "lat": sz["lat"],
                        "lng": sz["lng"],
                        "rad": sz["rad"],
                        "address": sz["address"],
                    }
                    for sz in _safe_zones
                ]
                break
            except Error as error:
                _LOGGER.debug(error)
                retry_counter += 1
                await asyncio.sleep(self.retryDelay)
        return safe_zones

    async def getTrackWatchInterval(self, wuid: str) -> int:
        return (await self._gql_handler.trackWatch_a(wuid)).get("trackWatch", -1)

    async def askWatchLocate(self, wuid: str) -> bool:
        return (await self._gql_handler.askWatchLocate_a(wuid)).get("askWatchLocate", False)

    ##### Feature #####
    async def getSilentTime(self, wuid: str) -> List[Dict[str, Any]]:
        retry_counter = 0
        data_ok: List[Dict[str, Any]] = []
        silent_times_raw: Dict[str, Any] = {}
        school_silent_mode: List[Dict[str, Any]] = []
        while not data_ok and (retry_counter < self.maxRetries + 2):
            retry_counter += 1
            try:
                silent_times_raw = await self._gql_handler.silentTimes_a(wuid)
                _silent_times = silent_times_raw.get("silentTimes", [])
                if not _silent_times:
                    data_ok.append({})
                    return school_silent_mode
                for silent_time in _silent_times:
                    school_silent_mode.append(
                        {
                            "id": silent_time["id"],
                            "vendorId": silent_time["vendorId"],
                            "start": self._helperTime(silent_time["start"]),
                            "end": self._helperTime(silent_time["end"]),
                            "weekRepeat": silent_time["weekRepeat"],
                            "status": silent_time["status"],
                        }
                    )
            except Error as error:
                _LOGGER.debug(error)
            data_ok = school_silent_mode
            if not data_ok:
                await asyncio.sleep(self.retryDelay)
        return school_silent_mode

    async def setEnableSilentTime(self, silent_id: str) -> bool:
        retries = 0
        result = ""

        while not result and retries < self.maxRetries + 2:
            retries += 1
            try:
                response = await self._gql_handler.setEnableSilentTime_a(silent_id)
                result = response.get("setEnableSilentTime", False)
            except Error as error:
                _LOGGER.debug(error)

            if not result:
                await asyncio.sleep(self.retryDelay)

        return bool(result)

    async def setDisableSilentTime(self, silent_id: str) -> bool:
        retry_counter = 0
        result = ""

        while not result and retry_counter < self.maxRetries + 2:
            retry_counter += 1
            try:
                disable_raw = await self._gql_handler.setEnableSilentTime_a(silent_id, NormalStatus.DISABLE.value)
                result = disable_raw.get("setEnableSilentTime", False)
            except Error as error:
                _LOGGER.debug(error)
            if not result:
                await asyncio.sleep(self.retryDelay)

        return bool(result)

    async def setAllEnableSilentTime(self, wuid: str) -> List[bool]:
        results = []
        silent_times = await self.getSilentTime(wuid)
        for silent_time in silent_times:
            id = silent_time.get("id")
            if id:
                results.append(await self.setEnableSilentTime(id))
        return results

    async def setAllDisableSilentTime(self, wuid: str) -> List[bool]:
        results = []
        for silentTime in await self.getSilentTime(wuid):
            results.append(await self.setDisableSilentTime(silentTime.get("id", "")))
        return results

    async def setAlarmTime(self, alarm_id: str, status: NormalStatus) -> bool:
        retryCounter = 0
        result = ""
        while not result and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                raw = await self._gql_handler.setEnableAlarmTime_a(alarm_id, status.value)
                modifyAlarm = raw.get("modifyAlarm", -1)
                if not modifyAlarm:
                    return False
                result = modifyAlarm
            except Error as error:
                _LOGGER.debug(error)
            if not result:
                await asyncio.sleep(self.retryDelay)
        return bool(result)

    async def setEnableAlarmTime(self, alarm_id: str) -> bool:
        return await self.setAlarmTime(alarm_id, NormalStatus.ENABLE)

    async def setDisableAlarmTime(self, alarm_id: str) -> bool:
        return await self.setAlarmTime(alarm_id, NormalStatus.DISABLE)

    async def setAllEnableAlarmTime(self, wuid: str) -> List[bool]:
        res: list[bool] = []
        for alarmTime in await self.getWatchAlarm(wuid):
            res.append(await self.setEnableAlarmTime(alarmTime.get("id", "")))
        return res

    async def setAllDisableAlarmTime(self, wuid: str) -> List[bool]:
        res: list[bool] = []
        for alarmTime in await self.getWatchAlarm(wuid):
            res.append(await self.setDisableAlarmTime(alarmTime.get("id", "")))
        return res

    async def sendText(self, text: str, wuid: str) -> bool:
        # sender is login User
        return await self._gql_handler.sendText_a(wuid, text)

    async def isAdmin(self, wuid: str) -> bool:
        user_id = self.getUserID()
        contacts = await self.getWatchUserContacts(wuid)
        return any(contact["id"] == user_id and contact["guardianType"] == "FIRST" for contact in contacts)

    async def shutdown(self, wuid: str) -> bool:
        if await self.isAdmin(wuid):
            return await self._gql_handler.shutdown_a(wuid)
        raise NoAdminError()

    async def reboot(self, wuid: str) -> bool:
        if await self.isAdmin(wuid):
            return await self._gql_handler.reboot_a(wuid)
        raise NoAdminError()

    async def getFollowRequestWatchCount(self) -> int:
        c: dict[str, Any] = await self._gql_handler.getFollowRequestWatchCount_a()
        return c.get("followRequestWatchCount", 0)

    async def getWatches(self, wuid: str) -> Dict[str, Any]:
        retryCounter = 0
        watches_raw: dict[str, Any] = {}
        watch: dict[str, Any] = {}
        while not watch and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                watches_raw = await self._gql_handler.getWatches_a(wuid)
                _watches: list[dict[str, Any]] = watches_raw.get("watches", [])
                if not _watches:
                    return watch
                watch = {
                    "imei": _watches[0]["swKey"],
                    "osVersion": _watches[0]["osVersion"],
                    "qrCode": _watches[0]["qrCode"],
                    "model": _watches[0]["groupName"],
                }
                if watch:
                    return watch
            except Error as error:
                _LOGGER.debug(error)
            if not watch:
                await asyncio.sleep(self.retryDelay)
        return watch

    async def getSWInfo(self, wuid: str, watches: dict[str, Any] = {}) -> Dict[str, Any]:
        wqr: dict[str, Any] = watches if watches else await self.getWatches(wuid=wuid)
        qrCode: str = wqr.get("qrCode", "=")
        return await self._gql_handler.getSWInfo_a(qrCode.split("=")[1])

    async def getWatchState(self, wuid: str, watches: dict[str, Any] = {}) -> Dict[str, Any]:
        wqr: dict[str, Any] = watches if watches else await self.getWatches(wuid=wuid)
        qrCode: str = wqr.get("qrCode", "=")
        return await self._gql_handler.getWatchState_a(qrCode=qrCode.split("=")[1])

    async def conv360IDToO2OID(self, qid: str, deviceId: str) -> Dict[str, Any]:
        return await self._gql_handler.conv360IDToO2OID_a(qid, deviceId)

    async def campaigns(self, id: str, categoryId: str) -> Dict[str, Any]:
        return await self._gql_handler.campaigns_a(id, categoryId)

    async def getCountries(self) -> List[dict[str, str]]:
        countries: dict[str, Any] = await self._gql_handler.countries_a()
        return countries.get("countries", {})

    async def getWatchLocHistory(self, wuid: str, date: int, tz: str, limit: int) -> Dict[str, Any]:
        return await self._gql_handler.getWatchLocHistory_a(wuid, date, tz, limit)

    async def watchesDynamic(self) -> Dict[str, Any]:
        return await self._gql_handler.watchesDynamic_a()

    async def watchGroups(self, id: str = "") -> Dict[str, Any]:
        return await self._gql_handler.watchGroups_a(id)

    async def familyInfo(self, wuid: str, watchId: str, tz: str, date: int) -> Dict[str, Any]:
        return await self._gql_handler.familyInfo_a(wuid, watchId, tz, date)

    async def avatars(self, id: str) -> Dict[str, Any]:
        return await self._gql_handler.avatars_a(id)

    async def getWatchUserSteps(self, wuid: str, date: int) -> Dict[str, Any]:
        userSteps = await self._gql_handler.getWatchUserSteps_a(wuid=wuid, tz=self._timeZone, date=date)
        if not userSteps:
            return {}
        userSteps = userSteps.get("userSteps", {})
        if not userSteps:
            return {}
        return userSteps

    # start tracking for 30min
    async def getStartTrackingWatch(self, wuid: str) -> int:
        data: dict[str, Any] = await self._gql_handler.getStartTrackingWatch_a(wuid)
        return data.get("startTrackingWatch", -1)

    # stop tracking from getStartTrackingWatch
    async def getEndTrackingWatch(self, wuid: str) -> int:
        data: dict[str, Any] = await self._gql_handler.getEndTrackingWatch_a(wuid)
        return data.get("endTrackingWatch", -1)

    async def addStep(self, step: int) -> bool:
        s: dict[str, bool] = await self._gql_handler.addStep_a(step)
        return s.get("addStep", False)

    async def submitIncorrectLocationData(self, wuid: str, lat: str, lng: str, timestamp: str) -> bool:
        data: dict[str, bool] = await self._gql_handler.submitIncorrectLocationData_a(wuid, lat, lng, timestamp)
        return data.get("submitIncorrectLocationData", False)

    async def getAppVersion(self) -> Dict[str, Any]:
        data = await self._gql_handler.getAppVersion_a()
        return data

    async def checkEmailOrPhoneExist(
        self, type: UserContactType, email: str = "", countryCode: str = "", phoneNumber: str = ""
    ) -> bool:
        data = await self._gql_handler.checkEmailOrPhoneExist_a(type, email, countryCode, phoneNumber)
        return data.get("checkEmailOrPhoneExist", False)

    async def modifyContact(self, contactId: str, isAdmin: bool, contactName: str = "", fileId: str = "") -> Dict[str, Any]:
        data = await self._gql_handler.modifyContact_a(contactId, isAdmin, contactName, fileId)
        return data

    async def deleteMessageFromApp(self, wuid: str, msgId: str) -> bool:
        data = await self._gql_handler.deleteMessageFromApp_a(wuid, msgId)
        if data.get("deleteMsg", False):
            return True
        return False

    async def get_chat_voice(self, wuid: str, msgId: str):
        data = await self._gql_handler.fetchChatVoice_a(wuid, msgId)
        if data.get("fetchChatVoice"):
            return data.get("fetchChatVoice")
        return None

    async def set_read_chat_msg(self, wuid: str, msgId: str = "", id: str = ""):
        data = await self._gql_handler.setReadChatMsg_a(wuid, msgId, id)
        return data
