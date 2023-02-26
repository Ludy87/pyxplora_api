from __future__ import annotations

import logging
from datetime import datetime
from time import time
from typing import Any, Dict, List, Optional, Union

from .const import VERSION, VERSION_APP
from .exception_classes import Error, ErrorMSG, LoginError, NoAdminError
from .gql_handler import GQLHandler
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
    ) -> None:
        super().__init__(countrycode, phoneNumber, password, userLang, timeZone, childPhoneNumber, wuid, email)

    def initHandler(self, sign_up):
        self._gql_handler: GQLHandler = GQLHandler(
            self._countrycode, self._phoneNumber, self._password, self._userLang, self._timeZone, self._email, sign_up
        )

    def _login(self, force_login: bool = False, sign_up: bool = True) -> Dict[str, Any]:
        if not self._isConnected() or self._hasTokenExpired() or force_login:
            retryCounter = 0
            while not self._isConnected() and (retryCounter < self.maxRetries + 2):
                retryCounter += 1

                # Try to login
                try:
                    self._issueToken = self._gql_handler.login()
                except LoginError as error:
                    self.error_message = error.error_message
                    retryCounter = self.maxRetries + 2
                except Error:
                    if retryCounter == self.maxRetries + 2:
                        self.error_message = ErrorMSG.SERVER_ERR
                    else:
                        self.delay(self.retryDelay)

            if self._issueToken:
                self.dtIssueToken = int(time())
        return self._issueToken

    def init(self, forceLogin: bool = False, signup: bool = True) -> None:
        self.initHandler(signup)
        token = self._login(forceLogin, signup)
        if not signup:
            return
        if not token:
            raise LoginError(self.error_message)

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

    def setDevices(self, ids: Optional[Union[str, List[str]]] = None) -> List[str]:
        if isinstance(ids, str):
            ids = [ids]
        return self._setDevices(ids or [])

    def _setDevices(self, ids: List[str] = None) -> List[str]:
        wuids = ids if ids else self.getWatchUserIDs()
        return wuids

    def _setDevice(self, ids: list = None) -> List[str]:
        wuids = ids or self.getWatchUserIDs()
        for wuid in wuids:
            self.device[wuid] = {}
            self.device[wuid]["getWatchAlarm"] = self.getWatchAlarm(wuid=wuid)
            self.device[wuid]["loadWatchLocation"] = self.loadWatchLocation(wuid=wuid)
            loc = self.device[wuid]["loadWatchLocation"]
            self.device[wuid]["watch_battery"] = int(loc.get("watch_battery", -1))
            self.device[wuid]["watch_charging"] = loc.get("watch_charging", False)
            self.device[wuid]["locateType"] = loc.get("locateType", LocationType.UNKNOWN.value)
            self.device[wuid]["lastTrackTime"] = loc.get("tm", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            self.device[wuid]["isInSafeZone"] = loc.get("isInSafeZone", False)
            self.device[wuid]["safeZoneLabel"] = loc.get("safeZoneLabel", "")
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
            self.device[wuid]["getWatchUserXCoins"] = self.getWatchUserXCoins(wuid=wuid)
        return wuids

    ##### Contact Info #####
    def getWatchUserContacts(self, wuid: str) -> List[dict[str, Any]]:
        retries = 0
        contacts = []
        while retries < self.maxRetries + 2:
            try:
                raw_contacts = self._gql_handler.getWatchUserContacts(wuid)
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
                self.delay(self.retryDelay)
        return contacts

    def getWatchAlarm(self, wuid: str) -> List[Dict[str, Any]]:
        retry_counter = 0
        alarms: List[Dict[str, Any]] = []

        while retry_counter < self.maxRetries + 2:
            try:
                alarms_raw = self._gql_handler.getAlarmTime(wuid)
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
                self.delay(self.retryDelay)
        return alarms

    def loadWatchLocation(self, wuid: str = "", with_ask: bool = True) -> Dict[str, Any]:
        retry_counter = 0
        watch_location = {}
        while retry_counter < self.maxRetries + 1:
            try:
                if with_ask:
                    self.askWatchLocate(wuid)
                location_raw = self._gql_handler.getWatchLastLocation(wuid)
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

                self.delay(self.retryDelay)

        return watch_location

    def getWatchBattery(self, wuid: str) -> int:
        watch_b = self.loadWatchLocation(wuid=wuid)
        return int(watch_b.get("watch_battery", -1))

    def getWatchIsCharging(self, wuid: str) -> bool:
        watch_c: dict[str, Any] = self.loadWatchLocation(wuid=wuid)
        return watch_c.get("watch_charging", False)

    def getWatchOnlineStatus(self, wuid: str) -> str:
        retries = 0
        status = WatchOnlineStatus.UNKNOWN

        while status is WatchOnlineStatus.UNKNOWN and retries < self.maxRetries + 2:
            try:
                ask_raw = self.askWatchLocate(wuid)
                track_raw = self.getTrackWatchInterval(wuid)
                status = WatchOnlineStatus.ONLINE if ask_raw or track_raw != -1 else WatchOnlineStatus.OFFLINE
            except Error as error:
                _LOGGER.debug(error)
                retries += 1
            if status is WatchOnlineStatus.UNKNOWN:
                self.delay(self.retryDelay)

        return status.value

    def getWatchUnReadChatMsgCount(self, wuid: str) -> int:
        try:
            unread_count = self._gql_handler.unReadChatMsgCount(wuid)
            if isinstance(unread_count, dict):
                return unread_count.get("unReadChatMsgCount", -1)
            return -1
        except Error as e:
            _LOGGER.error(f"Error getting unread chat message count: {e}")
            return -1

    def getWatchChats(
        self, wuid: str, offset: int = 0, limit: int = 0, msgId: str = "", show_del_msg: bool = True, asObject=False
    ) -> Union[List[Dict[str, Any]], SmallChatList]:
        retry_counter = 0
        chats: List[Dict[str, Any]] = []

        while not chats and retry_counter < self.maxRetries + 2:
            retry_counter += 1
            try:
                _chats_new = self.getWatchChatsRaw(wuid, offset, limit, msgId, show_del_msg, asObject)
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
                self.delay(self.retryDelay)

        if asObject:
            return SmallChatList(chats)
        return chats

    def getWatchChatsRaw(
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
                result = self._gql_handler.chats(wuid, offset, limit, msgId, asObject)
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

                result = ChatsNew.from_dict(result)

                filtered_chats = [chat for chat in result.list if show_del_msg or chat.data.delete_flag == 0]
                chats_new = ChatsNew(filtered_chats).to_dict()
            except Error as error:
                _LOGGER.debug(error)

            if not chats_new:
                self.delay(self.retryDelay)

        return ChatsNew.from_dict(chats_new, infer_missing=True) if asObject else chats_new

    ##### Watch Location Info #####
    def getWatchLastLocation(self, wuid: str, withAsk: bool = False) -> Dict[str, Any]:
        loc = self.loadWatchLocation(wuid, withAsk)
        return loc.get("watch_last_location", {}) if isinstance(loc, dict) else {}

    def getWatchLocate(self, wuid: str) -> Dict[str, Any]:
        return self.loadWatchLocation(wuid=wuid) or {}

    def getWatchLocateType(self, wuid: str) -> str:
        locate_info = self.getWatchLocate(wuid)
        return locate_info.get("locateType", LocationType.UNKNOWN.value)

    def getWatchIsInSafeZone(self, wuid: str) -> bool:
        return self.getWatchLocate(wuid).get("isInSafeZone", False)

    def getWatchSafeZoneLabel(self, wuid: str) -> str:
        return self.getWatchLocate(wuid).get("safeZoneLabel", "")

    def getWatchSafeZones(self, wuid: str) -> List[dict[str, Any]]:
        retry_counter = 0
        safe_zones = []
        while retry_counter < self.maxRetries + 2:
            try:
                safe_zones_raw = self._gql_handler.safeZones(wuid)
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
                self.delay(self.retryDelay)
        return safe_zones

    def getTrackWatchInterval(self, wuid: str) -> int:
        return self._gql_handler.trackWatch(wuid).get("trackWatch", -1)

    def askWatchLocate(self, wuid: str) -> bool:
        return self._gql_handler.askWatchLocate(wuid).get("askWatchLocate", False)

    ##### Feature #####
    def getSilentTime(self, wuid: str) -> List[Dict[str, Any]]:
        retry_counter = 0
        data_ok: List[Dict[str, Any]] = []
        silent_times_raw: Dict[str, Any] = {}
        school_silent_mode: List[Dict[str, Any]] = []
        while not data_ok and (retry_counter < self.maxRetries + 2):
            retry_counter += 1
            try:
                silent_times_raw = self._gql_handler.silentTimes(wuid)
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
                self.delay(self.retryDelay)
        return school_silent_mode

    def setEnableSilentTime(self, silent_id: str) -> bool:
        retries = 0
        result = ""

        while not result and retries < self.maxRetries + 2:
            retries += 1
            try:
                response = self._gql_handler.setEnableSilentTime(silent_id)
                result = response.get("setEnableSilentTime", False)
            except Error as error:
                _LOGGER.debug(error)

            if not result:
                self.delay(self.retryDelay)

        return bool(result)

    def setDisableSilentTime(self, silent_id: str) -> bool:
        retry_counter = 0
        result = ""

        while not result and retry_counter < self.maxRetries + 2:
            retry_counter += 1
            try:
                disable_raw = self._gql_handler.setEnableSilentTime(silent_id, NormalStatus.DISABLE.value)
                result = disable_raw.get("setEnableSilentTime", False)
            except Error as error:
                _LOGGER.debug(error)
            if not result:
                self.delay(self.retryDelay)

        return bool(result)

    def setAllEnableSilentTime(self, wuid: str) -> List[bool]:
        results = []
        silent_times = self.getSilentTime(wuid)
        for silent_time in silent_times:
            id = silent_time.get("id")
            if id:
                results.append(self.setEnableSilentTime(id))
        return results

    def setAllDisableSilentTime(self, wuid: str) -> List[bool]:
        results = []
        for silentTime in self.getSilentTime(wuid):
            results.append(self.setDisableSilentTime(silentTime.get("id", "")))
        return results

    def setAlarmTime(self, alarm_id: str, status: NormalStatus) -> bool:
        retryCounter = 0
        result = ""
        while not result and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                raw = self._gql_handler.setEnableAlarmTime(alarm_id, status.value)
                modifyAlarm = raw.get("modifyAlarm", -1)
                if not modifyAlarm:
                    return False
                result = modifyAlarm
            except Error as error:
                _LOGGER.debug(error)
            if not result:
                self.delay(self.retryDelay)
        return bool(result)

    def setEnableAlarmTime(self, alarm_id: str) -> bool:
        return self.setAlarmTime(alarm_id, NormalStatus.ENABLE)

    def setDisableAlarmTime(self, alarm_id: str) -> bool:
        return self.setAlarmTime(alarm_id, NormalStatus.DISABLE)

    def setAllEnableAlarmTime(self, wuid: str) -> List[bool]:
        res: list[bool] = []
        for alarmTime in self.getWatchAlarm(wuid):
            res.append(self.setEnableAlarmTime(alarmTime.get("id", "")))
        return res

    def setAllDisableAlarmTime(self, wuid: str) -> List[bool]:
        res: list[bool] = []
        for alarmTime in self.getWatchAlarm(wuid):
            res.append(self.setDisableAlarmTime(alarmTime.get("id", "")))
        return res

    def sendText(self, text: str, wuid: str) -> bool:
        # sender is login User
        return self._gql_handler.sendText(wuid, text)

    def isAdmin(self, wuid: str) -> bool:
        user_id = self.getUserID()
        contacts = self.getWatchUserContacts(wuid)
        return any(contact["id"] == user_id and contact["guardianType"] == "FIRST" for contact in contacts)

    def shutdown(self, wuid: str) -> bool:
        if self.isAdmin(wuid):
            return self._gql_handler.shutdown(wuid)
        raise NoAdminError()

    def reboot(self, wuid: str) -> bool:
        if self.isAdmin(wuid):
            return self._gql_handler.reboot(wuid)
        raise NoAdminError()

    def getFollowRequestWatchCount(self) -> int:
        c: dict[str, Any] = self._gql_handler.getFollowRequestWatchCount()
        return c.get("followRequestWatchCount", 0)

    def getWatches(self, wuid: str) -> Dict[str, Any]:
        retryCounter = 0
        watches_raw: dict[str, Any] = {}
        watch: dict[str, Any] = {}
        while not watch and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            try:
                watches_raw = self._gql_handler.getWatches(wuid)
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
                self.delay(self.retryDelay)
        return watch

    def getSWInfo(self, wuid: str, watches: dict[str, Any] = {}) -> Dict[str, Any]:
        wqr: dict[str, Any] = watches if watches else self.getWatches(wuid=wuid)
        qrCode: str = wqr.get("qrCode", "=")
        return self._gql_handler.getSWInfo(qrCode.split("=")[1])

    def getWatchState(self, wuid: str, watches: dict[str, Any] = {}) -> Dict[str, Any]:
        wqr: dict[str, Any] = watches if watches else self.getWatches(wuid=wuid)
        qrCode: str = wqr.get("qrCode", "=")
        return self._gql_handler.getWatchState(qrCode=qrCode.split("=")[1])

    def conv360IDToO2OID(self, qid: str, deviceId: str) -> Dict[str, Any]:
        return self._gql_handler.conv360IDToO2OID(qid, deviceId)

    def campaigns(self, id: str, categoryId: str) -> Dict[str, Any]:
        return self._gql_handler.campaigns(id, categoryId)

    def getCountries(self) -> List[dict[str, str]]:
        countries: dict[str, Any] = self._gql_handler.countries()
        return countries.get("countries", {})

    def getWatchLocHistory(self, wuid: str, date: int, tz: str, limit: int) -> Dict[str, Any]:
        return self._gql_handler.getWatchLocHistory(wuid, date, tz, limit)

    def watchesDynamic(self) -> Dict[str, Any]:
        return self._gql_handler.watchesDynamic()

    def watchGroups(self, id: str = "") -> Dict[str, Any]:
        return self._gql_handler.watchGroups(id)

    def familyInfo(self, wuid: str, watchId: str, tz: str, date: int) -> Dict[str, Any]:
        return self._gql_handler.familyInfo(wuid, watchId, tz, date)

    def avatars(self, id: str) -> Dict[str, Any]:
        return self._gql_handler.avatars(id)

    def getWatchUserSteps(self, wuid: str, date: int) -> Dict[str, Any]:
        userSteps = self._gql_handler.getWatchUserSteps(wuid=wuid, tz=self._timeZone, date=date)
        if not userSteps:
            return {}
        userSteps = userSteps.get("userSteps", {})
        if not userSteps:
            return {}
        return userSteps

    # start tracking for 30min
    def getStartTrackingWatch(self, wuid: str) -> int:
        data: dict[str, Any] = self._gql_handler.getStartTrackingWatch(wuid)
        return data.get("startTrackingWatch", -1)

    # stop tracking from getStartTrackingWatch
    def getEndTrackingWatch(self, wuid: str) -> int:
        data: dict[str, Any] = self._gql_handler.getEndTrackingWatch(wuid)
        return data.get("endTrackingWatch", -1)

    def addStep(self, step: int) -> bool:
        s: dict[str, bool] = self._gql_handler.addStep(step)
        return s.get("addStep", False)

    def submitIncorrectLocationData(self, wuid: str, lat: str, lng: str, timestamp: str) -> bool:
        data: dict[str, bool] = self._gql_handler.submitIncorrectLocationData(wuid, lat, lng, timestamp)
        return data.get("submitIncorrectLocationData", False)

    def getAppVersion(self) -> Dict[str, Any]:
        data = self._gql_handler.getAppVersion()
        return data

    def checkEmailOrPhoneExist(
        self, type: UserContactType, email: str = "", countryCode: str = "", phoneNumber: str = ""
    ) -> bool:
        data = self._gql_handler.checkEmailOrPhoneExist(type, email, countryCode, phoneNumber)
        return data.get("checkEmailOrPhoneExist", False)

    def modifyContact(
        self, contactId: str, isAdmin: bool | None = None, contactName: str = "", fileId: str = ""
    ) -> Dict[str, Any]:
        data = self._gql_handler.modifyContact(contactId, isAdmin, contactName, fileId)
        return data

    def deleteMessageFromApp(self, wuid: str, msgId: str) -> bool:
        data = self._gql_handler.deleteMessageFromApp(wuid, msgId)
        if data.get("deleteMsg", False):
            return True
        return False

    def get_chat_voice(self, wuid: str, msgId: str):
        data = self._gql_handler.fetchChatVoice(wuid, msgId)
        if data.get("fetchChatVoice"):
            return data.get("fetchChatVoice")
        return None
