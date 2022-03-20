import logging
import time

from asyncio import sleep
from datetime import datetime

from .const import VERSION
from .exception_classes import LoginError
from .gql_handler_async import GQLHandler, NormalStatus, WatchOnlineStatus

_LOGGER = logging.getLogger(__name__)


class PyXploraApi:
    def __init__(self, countrycode: str, phoneNumber: str, password: str, userLang: str, timeZone: str, childPhoneNumber=[]) -> None:
        self._countrycode = countrycode
        self._phoneNumber = phoneNumber
        self._password = password
        self._userLang = userLang
        self._timeZone = timeZone

        self._childPhoneNumber = childPhoneNumber

        self.tokenExpiresAfter = 240
        self.maxRetries = 3
        self.retryDelay = 2

        self.dtIssueToken = int(time.time()) - (self.tokenExpiresAfter * 1000)

        self.__gqlHandler = None
        self.__issueToken = None

        self.watchs = []

        self.user = None

    async def __login(self, forceLogin=False) -> dict:
        if not self.__isConnected() or self.__hasTokenExpired() or forceLogin:
            try:
                self.__logoff()
                self.__gqlHandler = GQLHandler(self._countrycode, self._phoneNumber, self._password, self._userLang, self._timeZone)
                if (self.__gqlHandler):
                    retryCounter = 0
                    while (not self.__isConnected() and (retryCounter < self.maxRetries + 2)):
                        retryCounter += 1

                        # Try to login
                        try:
                            self.__issueToken = await self.__gqlHandler.login_a()
                        except Exception:
                            pass

                        # Wait for next try
                        if (not self.__issueToken):
                            await sleep(self.retryDelay)
                    if (self.__issueToken):
                        self.dtIssueToken = int(time.time())
                else:
                    raise Exception("Unknown error creating a new GraphQL handler instance.")
            except Exception:
                # Login failed.
                self.__gqlHandler = None
                self.__issueToken = None
        return self.__issueToken

    def __isConnected(self) -> bool:
        return (self.__gqlHandler and self.__issueToken)

    def __logoff(self) -> None:
        self.__gqlHandler = None
        self.__issueToken = None

    def __hasTokenExpired(self) -> bool:
        return ((int(time.time()) - self.dtIssueToken) > (self.tokenExpiresAfter * 1000))

    async def init_async(self, forceLogin=False) -> None:
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
    async def getContacts_async(self, watchID) -> list:
        retryCounter = 0
        dataOk = False
        contacts_raw = None
        contacts = []
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            await self.init_async()
            try:
                contacts_raw = await self.__gqlHandler.getContacts_a(watchID)
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
                self.__logoff()
                await sleep(self.retryDelay)
        if dataOk:
            return contacts
        else:
            raise Exception('Xplora API call finally failed with response: ')

##### User Info #####
    async def getUserID_async(self) -> str:
        return self.user['id']
    async def getUserName_async(self) -> str:
        return self.user['name']
    async def getUserIcon_async(self) -> str:
        return self.user['extra']['profileIcon']
    async def getUserXcoin_async(self) -> int:
        return self.user['xcoin']
    async def getUserCurrentStep_async(self) -> int:
        return self.user['currentStep']
    async def getUserTotalStep_async(self) -> int:
        return self.user['totalStep']
    async def getUserCreate_async(self) -> str:
        return datetime.fromtimestamp(self.user['create']).strftime('%Y-%m-%d %H:%M:%S')
    async def getUserUpdate_async(self) -> str:
        return datetime.fromtimestamp(self.user['update']).strftime('%Y-%m-%d %H:%M:%S')

##### Watch Info #####
    async def getWatchUserID_async(self, child_no: list = []) -> str:
        watch_IDs = []
        for watch in self.watchs:
            if child_no:
                if watch['ward']['phoneNumber'] in child_no:
                    watch_IDs.append(watch['ward']['id'])
            else:
                watch_IDs.append(watch['ward']['id'])
        return watch_IDs
    async def getWatchUserPhoneNumber_async(self) -> str:
        watch_IDs = []
        for watch in self.watchs:
            watch_IDs.append(watch['ward']['phoneNumber'])
        return watch_IDs
    async def getWatchUserName_async(self, watchID) -> str:
        for watch in self.watchs:
            if watch['ward']['id'] == watchID:
                return watch['ward']['name']
        raise Exception("Child phonenumber not found!")
    async def getWatchUserIcon_async(self, watchID) -> str:
        for watch in self.watchs:
            if watch['ward']['id'] == watchID:
                return f"https://api.myxplora.com/file?id={watch['ward']['file']['id']}"
        raise Exception("Child phonenumber not found!")
    async def getWatchXcoin_async(self, watchID) -> int:
        for watch in self.watchs:
            if watch['ward']['id'] == watchID:
                return watch['ward']['xcoin']
        raise Exception("Child phonenumber not found!")
    async def getWatchCurrentStep_async(self, watchID) -> int:
        for watch in self.watchs:
            if watch['ward']['id'] == watchID:
                return watch['ward']['currentStep']
        raise Exception("Child phonenumber not found!")
    async def getWatchTotalStep_async(self, watchID) -> int:
        for watch in self.watchs:
            if watch['ward']['id'] == watchID:
                return watch['ward']['totalStep']
        raise Exception("Child phonenumber not found!")

    async def getWatchAlarm_async(self, watchID) -> list:
        retryCounter = 0
        dataOk = False
        alarms_raw = None
        alarms = []
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            await self.init_async()
            try:
                alarms_raw = await self.__gqlHandler.getAlarms_a(watchID)
                if 'alarms' in alarms_raw:
                    if not alarms_raw['alarms']:
                        dataOk = True
                        return alarms
                    for alarm in alarms_raw['alarms']:
                        alarms.append({
                            'id': alarm['id'],
                            'vendorId': alarm['vendorId'],
                            'name': alarm['name'],
                            'start': self.__helperTime(alarm['occurMin']),
                            'weekRepeat': alarm['weekRepeat'],
                            'status': alarm['status'],
                        })
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = alarms
            if (not dataOk):
                self.__logoff()
                await sleep(self.retryDelay)
        if (dataOk):
            return alarms
        else:
            raise Exception('Xplora API call finally failed with response: ')

    async def loadWatchLocation_async(self, withAsk=True, watchID=0) -> list:
        retryCounter = 0
        dataOk = False
        location_raw = None
        watch_location = []
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            await self.init_async()
            try:
                if withAsk:
                    await self.askWatchLocate_async(watchID)
                await sleep(self.retryDelay)
                location_raw = await self.__gqlHandler.getWatchLastLocation_a(watchID)
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
                self.__logoff()
                await sleep(self.retryDelay)
        if (dataOk):
            return watch_location
        else:
            raise Exception('Xplora API call finally failed with response: ')

    async def getWatchBattery_async(self, watchID) -> int:
        return (await self.loadWatchLocation_async(watchID=watchID))[0]['watch_battery']
    async def getWatchIsCharging_async(self, watchID) -> bool:
        if (await self.loadWatchLocation_async(watchID=watchID))[0]['watch_charging']:
            return True
        return False
    async def getWatchOnlineStatus_async(self, watchID) -> WatchOnlineStatus:
        retryCounter = 0
        dataOk = False
        asktrack_raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            await self.init_async()
            try:
                await self.askWatchLocate_async(watchID)
                await sleep(self.retryDelay)
                ask_raw = await self.askWatchLocate_async(watchID)
                track_raw = await self.trackWatchInterval_async(watchID)
                if ask_raw or (track_raw != -1):
                    asktrack_raw = WatchOnlineStatus.ONLINE.value
                else:
                    asktrack_raw = WatchOnlineStatus.OFFLINE.value
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = asktrack_raw
            if (not dataOk):
                self.__logoff()
                await sleep(self.retryDelay)
        if (dataOk):
            return asktrack_raw
        else:
            raise Exception('Xplora API call finally failed with response: ')
    async def __setReadChatMsg_a(self, msgId, id):
        return (await self.__gqlHandler.setReadChatMsg(await self.getWatchUserID_async(), msgId, id))['setReadChatMsg']
    async def getWatchUnReadChatMsgCount_async(self, watchID) -> int:
        # bug?
        return (await self.__gqlHandler.unReadChatMsgCount_a(watchID))['unReadChatMsgCount']
    async def getWatchChats_async(self, watchID) -> list:
        # bug?
        retryCounter = 0
        dataOk = False
        chats_raw = None
        chats = []
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            await self.init_async()
            try:
                await self.askWatchLocate_async(watchID)
                await sleep(self.retryDelay)
                chats_raw = await self.__gqlHandler.chats_a(watchID)
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
                self.__logoff()
                await sleep(self.retryDelay)
        if (dataOk):
            return chats
        else:
            raise Exception('Xplora API call finally failed with response: ')

##### Watch Location Info #####
    async def getWatchLastLocation_async(self, withAsk: bool = False, watchID=0) -> dict:
        return (await self.loadWatchLocation_async(withAsk, watchID=watchID))[0]['watch_last_location']
    async def getWatchLocate_async(self, watchID) -> dict:
        return (await self.loadWatchLocation_async(watchID=watchID))[0]
    async def getWatchLocateType_async(self, watchID) -> str:
        return (await self.getWatchLocate_async(watchID))['locateType']
    async def getWatchIsInSafeZone_async(self, watchID) -> bool:
        return (await self.getWatchLocate_async(watchID))['isInSafeZone']
    async def getWatchSafeZoneLabel_async(self, watchID) -> str:
        return (await self.getWatchLocate_async(watchID))['safeZoneLabel']
    async def getSafeZones_async(self, watchID) -> list:
        retryCounter = 0
        dataOk = False
        safeZones_raw = None
        safe_zones = []
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            await self.init_async()
            try:
                await self.askWatchLocate_async(watchID)
                await sleep(self.retryDelay)
                safeZones_raw = await self.__gqlHandler.safeZones_a(watchID)
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
                self.__logoff()
                await sleep(self.retryDelay)
        if (dataOk):
            return safe_zones
        else:
            raise Exception('Xplora API call finally failed with response: ')
    async def trackWatchInterval_async(self, watchID) -> int:
        return (await self.__gqlHandler.trackWatch_a(watchID))['trackWatch']
    async def askWatchLocate_async(self, watchID) -> bool:
        return (await self.__gqlHandler.askWatchLocate_a(watchID))['askWatchLocate']

##### Feature #####
    async def schoolSilentMode_async(self, watchID) -> list:
        retryCounter = 0
        dataOk = False
        silentTimes_raw = None
        school_silent_mode = []
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            await self.init_async()
            try:
                await self.askWatchLocate_async(watchID)
                await sleep(self.retryDelay)
                silentTimes_raw = await self.__gqlHandler.silentTimes_a(watchID)
                if 'silentTimes' in silentTimes_raw:
                    if not silentTimes_raw['silentTimes']:
                        dataOk = True
                        return school_silent_mode
                    for silentTime in silentTimes_raw['silentTimes']:
                        school_silent_mode.append({
                            'id': silentTime['id'],
                            'vendorId': silentTime['vendorId'],
                            'start': self.__helperTime(silentTime['start']),
                            'end': self.__helperTime(silentTime['end']),
                            'weekRepeat': silentTime['weekRepeat'],
                            'status': silentTime['status'],
                        })
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = school_silent_mode
            if (not dataOk):
                self.__logoff()
                await sleep(self.retryDelay)
        if (dataOk):
            return school_silent_mode
        else:
            raise Exception('Xplora API call finally failed with response: ')
    async def setEnableSilentTime_async(self, silentId, watchID) -> bool:
        retryCounter = 0
        dataOk = False
        _raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            await self.init_async()
            try:
                await self.askWatchLocate_async(watchID)
                await sleep(self.retryDelay)
                enable_raw = await self.__gqlHandler.setEnableSlientTime_a(silentId)
                if 'setEnableSilentTime' in enable_raw:
                    _raw = enable_raw['setEnableSilentTime']
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if (not dataOk):
                self.__logoff()
                await sleep(self.retryDelay)
        if (dataOk):
            return bool(_raw)
        else:
            raise Exception('Xplora API call finally failed with response: ')
    async def setDisableSilentTime_async(self, silentId: str, watchID) -> bool:
        retryCounter = 0
        dataOk = False
        _raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            await self.init_async()
            try:
                await self.askWatchLocate_async(watchID)
                await sleep(self.retryDelay)
                disable_raw = await self.__gqlHandler.setEnableSlientTime_a(silentId, NormalStatus.DISABLE.value)
                if 'setEnableSilentTime' in disable_raw:
                    _raw = disable_raw['setEnableSilentTime']
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if (not dataOk):
                self.__logoff()
                await sleep(self.retryDelay)
        if (dataOk):
            return bool(_raw)
        else:
            raise Exception('Xplora API call finally failed with response: ')
    async def setAllEnableSilentTime_async(self, watchID) -> list:
        res = []
        for silentTime in (await self.schoolSilentMode_async(watchID)):
            res.append(await self.setEnableSilentTime_async(silentTime['id'], watchID))
        return res
    async def setAllDisableSilentTime_async(self, watchID) -> list:
        res = []
        for silentTime in (await self.schoolSilentMode_async(watchID)):
            res.append(await self.setDisableSilentTime_async(silentTime['id'], watchID))
        return res

    async def setEnableAlarmTime_async(self, alarmId, watchID) -> bool:
        retryCounter = 0
        dataOk = False
        _raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            await self.init_async()
            try:
                await self.askWatchLocate_async(watchID)
                await sleep(self.retryDelay)
                enable_raw = await self.__gqlHandler.setEnableAlarmTime_a(alarmId)
                if 'modifyAlarm' in enable_raw:
                    _raw = enable_raw['modifyAlarm']
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if (not dataOk):
                self.__logoff()
                await sleep(self.retryDelay)
        if (dataOk):
            return bool(_raw)
        else:
            raise Exception('Xplora API call finally failed with response: ')
    async def setDisableAlarmTime_async(self, alarmId, watchID) -> bool:
        retryCounter = 0
        dataOk = False
        _raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            await self.init_async()
            try:
                await self.askWatchLocate_async(watchID)
                await sleep(self.retryDelay)
                disable_raw = await self.__gqlHandler.setEnableAlarmTime_a(alarmId, NormalStatus.DISABLE.value)
                if 'modifyAlarm' in disable_raw:
                    _raw = disable_raw['modifyAlarm']
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if (not dataOk):
                self.__logoff()
                await sleep(self.retryDelay)
        if (dataOk):
            return bool(_raw)
        else:
            raise Exception('Xplora API call finally failed with response: ')
    async def setAllEnableAlarmTime_async(self, watchID) -> list:
        res = []
        for alarmTime in (await self.getWatchAlarm_async(watchID)):
            res.append(await self.setEnableAlarmTime_async(alarmTime['id'], watchID))
        return res
    async def setAllDisableAlarmTime_async(self, watchID) -> list:
        res = []
        for alarmTime in (await self.getWatchAlarm_async(watchID)):
            res.append(await self.setDisableAlarmTime_async(alarmTime['id'], watchID))
        return res

    async def sendText(self, text, watchID) -> bool:
        # sender is login User
        return await self.__gqlHandler.sendText_a(watchID, text)
    async def isAdmin(self, watchID) -> bool:
        for contact in await self.getContacts_async(watchID):
            if (contact['id'] == await self.getUserID_async()):
                return True
        return False
    async def shutdown(self, watchID) -> bool:
        if self.isAdmin(watchID):
            return await self.__gqlHandler.shutdown_a(watchID)
        raise Exception("no Admin")
    async def reboot(self, watchID) -> bool:
        if self.isAdmin(watchID):
            return await self.__gqlHandler.reboot_a(watchID)
        raise Exception("no Admin")

##### - #####
    def __helperTime(self, t) -> str:
        h = str(int(t) / 60).split('.')
        h2 = str(int(h[1]) * 60).zfill(2)[:2]
        return h[0].zfill(2) + ":" + str(h2).zfill(2)
