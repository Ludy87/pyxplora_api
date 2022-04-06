from __future__ import annotations

import logging

from asyncio import sleep
from datetime import datetime
from time import time

from .const import VERSION
from .exception_classes import LoginError
from .gql_handler_async import GQLHandler
from .pyxplora import PyXplora
from .status import NormalStatus, WatchOnlineStatus

_LOGGER = logging.getLogger(__name__)


class PyXploraApi(PyXplora):
    def __init__(self, countrycode: str, phoneNumber: str, password: str, userLang: str, timeZone: str, childPhoneNumber=[]) -> None:
        super().__init__(countrycode, phoneNumber, password, userLang, timeZone, childPhoneNumber)

    async def __login(self, forceLogin=False) -> dict:
        if not self._isConnected() or self._hasTokenExpired() or forceLogin:
            try:
                self._logoff()
                self._gqlHandler = GQLHandler(self._countrycode, self._phoneNumber, self._password, self._userLang, self._timeZone)
                if (self._gqlHandler):
                    retryCounter = 0
                    while (not self._isConnected() and (retryCounter < self.maxRetries + 2)):
                        retryCounter += 1

                        # Try to login
                        try:
                            self._issueToken = await self._gqlHandler.login_a()
                        except Exception:
                            pass

                        # Wait for next try
                        if (not self._issueToken):
                            await sleep(self.retryDelay)
                    if (self._issueToken):
                        self.dtIssueToken = int(time())
                else:
                    raise Exception("Unknown error creating a new GraphQL handler instance.")
            except Exception:
                # Login failed.
                self._gqlHandler = None
                self._issueToken = None
        return self._issueToken

    async def init(self, forceLogin=False) -> None:
        token = await self.__login(forceLogin)
        if token:
            if ('user' in token):
                if not self._childPhoneNumber:
                    self.watchs = token['user']['children']
                else:
                    for watch in token['user']['children']:
                        if int(watch['ward']['phoneNumber']) in self._childPhoneNumber:
                            self.watchs.append(watch)
                self.user = token['user']
                return
        raise LoginError("Login to Xplora® API failed. Check your input!")

    def version(self) -> str:
        return VERSION

    ##### Contact Info #####
    async def getContacts(self, watchID) -> list:
        retryCounter = 0
        dataOk = False
        contacts_raw = None
        contacts = []
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            await self.init()
            try:
                contacts_raw = await self._gqlHandler.getContacts_a(watchID)
                if 'contacts' in contacts_raw:
                    if contacts_raw['contacts'] is None:
                        dataOk = True
                        return contacts
                    if 'contacts' in contacts_raw['contacts']:
                        if not contacts_raw['contacts']['contacts']:
                            dataOk = True
                            return contacts
                        for contact in contacts_raw['contacts']['contacts']:
                            try:
                                xcoin = contact['contactUser']['xcoin']
                                id = contact['contactUser']['id']
                            except TypeError:
                                # None - XCoins
                                xcoin = -1
                                id = None
                            contacts.append({
                                'id': id,
                                'guardianType': contact['guardianType'],
                                'create': datetime.fromtimestamp(contact['create']).strftime('%Y-%m-%d %H:%M:%S'),
                                'update': datetime.fromtimestamp(contact['update']).strftime('%Y-%m-%d %H:%M:%S'),
                                'name': contact['name'],
                                'phoneNumber': f"+{contact['countryPhoneNumber']}{contact['phoneNumber']}",
                                'xcoin': xcoin,
                            })
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = contacts
            if (not dataOk):
                self._logoff()
                await sleep(self.retryDelay)
        if dataOk:
            return contacts
        else:
            raise Exception('Xplora API call finally failed with response: ')

    async def getWatchAlarm(self, watchID) -> list:
        retryCounter = 0
        dataOk = False
        alarms_raw = None
        alarms = []
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            await self.init()
            try:
                alarms_raw = await self._gqlHandler.getAlarms_a(watchID)
                if 'alarms' in alarms_raw:
                    if not alarms_raw['alarms']:
                        dataOk = True
                        return alarms
                    for alarm in alarms_raw['alarms']:
                        alarms.append({
                            'id': alarm['id'],
                            'vendorId': alarm['vendorId'],
                            'name': alarm['name'],
                            'start': self._helperTime(alarm['occurMin']),
                            'weekRepeat': alarm['weekRepeat'],
                            'status': alarm['status'],
                        })
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = alarms
            if (not dataOk):
                self._logoff()
                await sleep(self.retryDelay)
        if (dataOk):
            return alarms
        else:
            raise Exception('Xplora API call finally failed with response: ')

    async def loadWatchLocation(self, withAsk=True, watchID=0) -> list:
        retryCounter = 0
        dataOk = False
        location_raw = None
        watch_location = []
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            await self.init()
            try:
                if withAsk:
                    await self.askWatchLocate(watchID)
                await sleep(self.retryDelay)
                location_raw = await self._gqlHandler.getWatchLastLocation_a(watchID)
                if 'watchLastLocate' in location_raw:
                    if location_raw['watchLastLocate'] is not None:
                        watch_location.append({
                            'tm': datetime.fromtimestamp(location_raw['watchLastLocate']['tm']).strftime('%Y-%m-%d %H:%M:%S'),
                            'lat': location_raw['watchLastLocate']['lat'],
                            'lng': location_raw['watchLastLocate']['lng'],
                            'rad': location_raw['watchLastLocate']['rad'],
                            'poi': location_raw['watchLastLocate']['poi'],
                            'city': location_raw['watchLastLocate']['city'],
                            'province': location_raw['watchLastLocate']['province'],
                            'country': location_raw['watchLastLocate']['country'],
                            'locateType': location_raw['watchLastLocate']['locateType'],
                            'isInSafeZone': location_raw['watchLastLocate']['isInSafeZone'],
                            'safeZoneLabel': location_raw['watchLastLocate']['safeZoneLabel'],
                            'watch_battery': location_raw['watchLastLocate']['battery'],
                            'watch_charging': location_raw['watchLastLocate']['isCharging'],
                            'watch_last_location': location_raw['watchLastLocate'],
                        })
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = watch_location
            if (not dataOk):
                self._logoff()
                await sleep(self.retryDelay)
        if (dataOk):
            return watch_location
        else:
            raise Exception('Xplora API call finally failed with response: ')

    async def getWatchBattery(self, watchID) -> int:
        return (await self.loadWatchLocation(watchID=watchID))[0]['watch_battery']
    async def getWatchIsCharging(self, watchID) -> bool:
        if (await self.loadWatchLocation(watchID=watchID))[0]['watch_charging']:
            return True
        return False
    async def getWatchOnlineStatus(self, watchID) -> WatchOnlineStatus:
        retryCounter = 0
        dataOk = False
        asktrack_raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            await self.init()
            try:
                await self.askWatchLocate(watchID)
                await sleep(self.retryDelay)
                ask_raw = await self.askWatchLocate(watchID)
                track_raw = await self.trackWatchInterval(watchID)
                if ask_raw or (track_raw != -1):
                    asktrack_raw = WatchOnlineStatus.ONLINE.value
                else:
                    asktrack_raw = WatchOnlineStatus.OFFLINE.value
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = asktrack_raw
            if (not dataOk):
                self._logoff()
                await sleep(self.retryDelay)
        if (dataOk):
            return asktrack_raw
        else:
            raise Exception('Xplora API call finally failed with response: ')
    async def __setReadChatMsg_a(self, msgId, id):
        return (await self._gqlHandler.setReadChatMsg(await self.getWatchUserID(), msgId, id))['setReadChatMsg']
    async def getWatchUnReadChatMsgCount(self, watchID) -> int:
        # bug?
        return (await self._gqlHandler.unReadChatMsgCount_a(watchID))['unReadChatMsgCount']
    async def getWatchChats(self, watchID) -> list:
        # bug?
        retryCounter = 0
        dataOk = False
        chats_raw = None
        chats = []
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            await self.init()
            try:
                await self.askWatchLocate(watchID)
                await sleep(self.retryDelay)
                chats_raw = await self._gqlHandler.chats_a(watchID)
                if 'chats' in chats_raw:
                    if 'list' in chats_raw['chats']:
                        if not chats_raw['chats']['list']:
                            dataOk = True
                            return chats
                        for chat in chats_raw['chats']['list']:
                            chats.append({
                                'msgId': chat['msgId'],
                                'type': chat['type'],
                                # chat['sender'],
                                'sender_id': chat['sender']['id'],
                                'sender_name': chat['sender']['name'],
                                # chat['receiver'],
                                'receiver_id': chat['receiver']['id'],
                                'receiver_name': chat['receiver']['name'],
                                # chat['data'],
                                'data_text': chat['data']['text'],
                                'data_sender_name': chat['data']['sender_name'],
                            })
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = chats
            if (not dataOk):
                self._logoff()
                await sleep(self.retryDelay)
        if (dataOk):
            return chats
        else:
            return chats

    ##### Watch Location Info #####
    async def getWatchLastLocation(self, watchID, withAsk: bool = False) -> dict:
        return (await self.loadWatchLocation(withAsk, watchID=watchID))[0]['watch_last_location']
    async def getWatchLocate(self, watchID) -> dict:
        return (await self.loadWatchLocation(watchID=watchID))[0]
    async def getWatchLocateType(self, watchID) -> str:
        return (await self.getWatchLocate(watchID))['locateType']
    async def getWatchIsInSafeZone(self, watchID) -> bool:
        return (await self.getWatchLocate(watchID))['isInSafeZone']
    async def getWatchSafeZoneLabel(self, watchID) -> str:
        return (await self.getWatchLocate(watchID))['safeZoneLabel']
    async def getSafeZones(self, watchID) -> list:
        retryCounter = 0
        dataOk = False
        safeZones_raw = None
        safe_zones = []
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            await self.init()
            try:
                await self.askWatchLocate(watchID)
                await sleep(self.retryDelay)
                safeZones_raw = await self._gqlHandler.safeZones_a(watchID)
                if 'safeZones' in safeZones_raw:
                    if not safeZones_raw['safeZones']:
                        dataOk = True
                        return safe_zones
                    for safeZone in safeZones_raw['safeZones']:
                        safe_zones.append({
                            'vendorId': safeZone['vendorId'],
                            'groupName': safeZone['groupName'],
                            'name': safeZone['name'],
                            'lat': safeZone['lat'],
                            'lng': safeZone['lng'],
                            'rad': safeZone['rad'],
                            'address': safeZone['address'],
                        })
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = safe_zones
            if (not dataOk):
                self._logoff()
                await sleep(self.retryDelay)
        if (dataOk):
            return safe_zones
        else:
            raise Exception('Xplora API call finally failed with response: ')
    async def trackWatchInterval(self, watchID) -> int:
        return (await self._gqlHandler.trackWatch_a(watchID))['trackWatch']
    async def askWatchLocate(self, watchID) -> bool:
        return (await self._gqlHandler.askWatchLocate_a(watchID))['askWatchLocate']

    ##### Feature #####
    async def schoolSilentMode(self, watchID) -> list:
        retryCounter = 0
        dataOk = False
        silentTimes_raw = None
        school_silent_mode = []
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            await self.init()
            try:
                await self.askWatchLocate(watchID)
                await sleep(self.retryDelay)
                silentTimes_raw = await self._gqlHandler.silentTimes_a(watchID)
                if 'silentTimes' in silentTimes_raw:
                    if not silentTimes_raw['silentTimes']:
                        dataOk = True
                        return school_silent_mode
                    for silentTime in silentTimes_raw['silentTimes']:
                        school_silent_mode.append({
                            'id': silentTime['id'],
                            'vendorId': silentTime['vendorId'],
                            'start': self._helperTime(silentTime['start']),
                            'end': self._helperTime(silentTime['end']),
                            'weekRepeat': silentTime['weekRepeat'],
                            'status': silentTime['status'],
                        })
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = school_silent_mode
            if (not dataOk):
                self._logoff()
                await sleep(self.retryDelay)
        if (dataOk):
            return school_silent_mode
        else:
            raise Exception('Xplora API call finally failed with response: ')
    async def setEnableSilentTime(self, silentId, watchID) -> bool:
        retryCounter = 0
        dataOk = False
        _raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            await self.init()
            try:
                await self.askWatchLocate(watchID)
                await sleep(self.retryDelay)
                enable_raw = await self._gqlHandler.setEnableSlientTime_a(silentId)
                if 'setEnableSilentTime' in enable_raw:
                    _raw = enable_raw['setEnableSilentTime']
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if (not dataOk):
                self._logoff()
                await sleep(self.retryDelay)
        if (dataOk):
            return bool(_raw)
        else:
            raise Exception('Xplora API call finally failed with response: ')
    async def setDisableSilentTime(self, silentId: str, watchID) -> bool:
        retryCounter = 0
        dataOk = False
        _raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            await self.init()
            try:
                await self.askWatchLocate(watchID)
                await sleep(self.retryDelay)
                disable_raw = await self._gqlHandler.setEnableSlientTime_a(silentId, NormalStatus.DISABLE.value)
                if 'setEnableSilentTime' in disable_raw:
                    _raw = disable_raw['setEnableSilentTime']
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if (not dataOk):
                self._logoff()
                await sleep(self.retryDelay)
        if (dataOk):
            return bool(_raw)
        else:
            raise Exception('Xplora API call finally failed with response: ')
    async def setAllEnableSilentTime(self, watchID) -> list:
        res = []
        for silentTime in (await self.schoolSilentMode(watchID)):
            res.append(await self.setEnableSilentTime(silentTime['id'], watchID))
        return res
    async def setAllDisableSilentTime(self, watchID) -> list:
        res = []
        for silentTime in (await self.schoolSilentMode(watchID)):
            res.append(await self.setDisableSilentTime(silentTime['id'], watchID))
        return res

    async def setEnableAlarmTime(self, alarmId, watchID) -> bool:
        retryCounter = 0
        dataOk = False
        _raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            await self.init()
            try:
                await self.askWatchLocate(watchID)
                await sleep(self.retryDelay)
                enable_raw = await self._gqlHandler.setEnableAlarmTime_a(alarmId)
                if 'modifyAlarm' in enable_raw:
                    _raw = enable_raw['modifyAlarm']
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if (not dataOk):
                self._logoff()
                await sleep(self.retryDelay)
        if (dataOk):
            return bool(_raw)
        else:
            raise Exception('Xplora API call finally failed with response: ')
    async def setDisableAlarmTime(self, alarmId, watchID) -> bool:
        retryCounter = 0
        dataOk = False
        _raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            await self.init()
            try:
                await self.askWatchLocate(watchID)
                await sleep(self.retryDelay)
                disable_raw = await self._gqlHandler.setEnableAlarmTime_a(alarmId, NormalStatus.DISABLE.value)
                if 'modifyAlarm' in disable_raw:
                    _raw = disable_raw['modifyAlarm']
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if (not dataOk):
                self._logoff()
                await sleep(self.retryDelay)
        if (dataOk):
            return bool(_raw)
        else:
            raise Exception('Xplora API call finally failed with response: ')
    async def setAllEnableAlarmTime(self, watchID) -> list:
        res = []
        for alarmTime in (await self.getWatchAlarm(watchID)):
            res.append(await self.setEnableAlarmTime(alarmTime['id'], watchID))
        return res
    async def setAllDisableAlarmTime(self, watchID) -> list:
        res = []
        for alarmTime in (await self.getWatchAlarm(watchID)):
            res.append(await self.setDisableAlarmTime(alarmTime['id'], watchID))
        return res

    async def sendText(self, text, watchID) -> bool:
        # sender is login User
        return await self._gqlHandler.sendText_a(watchID, text)
    async def isAdmin(self, watchID) -> bool:
        for contact in await self.getContacts(watchID):
            if (contact['id'] == self.getUserID()):
                return True
        return False
    async def shutdown(self, watchID) -> bool:
        if self.isAdmin(watchID):
            return await self._gqlHandler.shutdown_a(watchID)
        raise Exception("no Admin")
    async def reboot(self, watchID) -> bool:
        if self.isAdmin(watchID):
            return await self._gqlHandler.reboot_a(watchID)
        raise Exception("no Admin")
