from .gql_handler_async import *
from datetime import datetime
import logging

_LOGGER = logging.getLogger(__name__)

class PyXploraApi:
    def __init__(self, countrycode: str, phoneNumber: str, password: str, userLang: str, timeZone: str, watchNo: int=0) -> None:
        self._countrycode = countrycode
        self._phoneNumber = phoneNumber
        self._password = password
        self._userLang = userLang
        self._timeZone = timeZone
        self.watch_no = watchNo

        self.tokenExpiresAfter = 240
        self.maxRetries = 3
        self.retryDelay = 3

        self.contacts = []
        self.alarms = []
        self.chats = []
        self.safe_zones = []
        self.school_silent_mode = []
        self.watch_location = []
        self.watch_last_location = []
        self.watch_battery = None
        self.watch_charging = None

        self.gqlHandler = None
        self.issueToken = None
        self.watch = None
        self.user = None

    async def login(self, forceLogin=False):
        if not self.isConnected() or self.hasTokenExpired() or forceLogin:
            try:
                self.logoff()
                self.gqlHandler = GQLHandler(self._countrycode, self._phoneNumber, self._password, self._userLang, self._timeZone)
                if (self.gqlHandler):
                    retryCounter = 0
                    while (not self.isConnected() and (retryCounter < self.maxRetries + 2)):
                        retryCounter += 1

                        # Try to login
                        try:
                            self.issueToken = await self.gqlHandler.login_a();
                        except Exception:
                            pass

                        # Wait for next try
                        if (not self.issueToken):
                            time.sleep(self.retryDelay)
                    if (self.issueToken):
                        self.dtIssueToken = int(time.time())
                else:
                    raise Exception("Unknown error creating a new GraphQL handler instance.")
            except Exception as error:
                print(error)
                # Login failed.
                self.gqlHandler = None
                self.issueToken = None
        return self.issueToken

    def isConnected(self):
        return (self.gqlHandler and self.issueToken)

    def logoff(self):
        self.gqlHandler = None
        self.issueToken = None

    def hasTokenExpired(self):
        return ((int(time.time()) - self.dtIssueToken) > (self.tokenExpiresAfter * 1000))

    async def init_async(self, forceLogin=False):
        token = await self.login(forceLogin)
        if token:
            if ('user' in token):
                self.watch = token['user']['children'][self.watch_no]['ward']
                self.user = token['user']
                return
        raise Exception("Fail")

    def version(self) -> str:
        return "1.0.49"

##### Contact Info #####
    async def getContacts_async(self):
        retryCounter = 0
        dataOk = False
        contacts_raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter +=1
            await self.init_async()
            try:
                contacts_raw = await self.gqlHandler.getContacts_a(await self.getWatchUserID_async())
                if 'contacts' in contacts_raw:
                    if 'contacts' in contacts_raw['contacts']:
                        for contact in contacts_raw['contacts']['contacts']:
                            try:
                                xcoin = contact['contactUser']['xcoin']
                                id = contact['contactUser']['id']
                            except TypeError:
                                xcoin = -1 # None - XCoins
                                id = None
                            self.contacts.append({
                                'id': id,
                                'guardianType': contact['guardianType'],
                                'create': datetime.fromtimestamp(contact['create']).strftime('%Y-%m-%d %H:%M:%S'),
                                'update': datetime.fromtimestamp(contact['update']).strftime('%Y-%m-%d %H:%M:%S'),
                                'name': contact['name'],
                                'phoneNumber': f"+{contact['countryPhoneNumber']}{contact['phoneNumber']}",
                                'xcoin': xcoin,
                            })
            except Exception as error:
                print(error)
            dataOk = self.contacts
            print(not dataOk)
            if (not dataOk):
                self.logoff()
                time.sleep(self.retryDelay)
        if (dataOk):
            return self.contacts
        else:
            raise Exception('Xplora API call finally failed with response: ')

##### User Info #####
    async def getUserID_async(self) -> str:
        await self.init_async()
        return self.user['id']
    async def getUserName_async(self) -> str:
        await self.init_async()
        return self.user['name']
    async def getUserIcon_async(self) -> str:
        await self.init_async()
        return self.user['extra']['profileIcon']
    async def getUserXcoin_async(self) -> int:
        await self.init_async()
        return self.user['xcoin']
    async def getUserCurrentStep_async(self) -> int:
        await self.init_async()
        return self.user['currentStep']
    async def getUserTotalStep_async(self) -> int:
        await self.init_async()
        return self.user['totalStep']
    async def getUserCreate_async(self) -> str:
        await self.init_async()
        return datetime.fromtimestamp(self.user['create']).strftime('%Y-%m-%d %H:%M:%S')
    async def getUserUpdate_async(self) -> str:
        await self.init_async()
        return datetime.fromtimestamp(self.user['update']).strftime('%Y-%m-%d %H:%M:%S')

##### Watch Info #####
    async def getWatchUserID_async(self) -> str:
        await self.init_async()
        return self.watch['id']
    async def getWatchUserName_async(self) -> str:
        await self.init_async()
        return self.watch['name']
    async def getWatchXcoin_async(self) -> int:
        await self.init_async()
        return self.watch['xcoin']
    async def getWatchCurrentStep_async(self) -> int:
        await self.init_async()
        return self.watch['currentStep']
    async def getWatchTotalStep_async(self) -> int:
        await self.init_async()
        return self.watch['totalStep']

    async def getWatchAlarm_async(self) -> list:
        retryCounter = 0
        dataOk = False
        alarms_raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter +=1
            await self.init_async()
            try:
                alarms_raw = await self.gqlHandler.getAlarms_a(await self.getWatchUserID_async())
                if 'alarms' in alarms_raw:
                    if not alarms_raw['alarms']:
                        dataOk = True
                        return self.alarms
                    for alarm in alarms_raw['alarms']:
                        self.alarms.append({
                            'name': alarm['name'],
                            'start': alarm['start'],
                            'weekRepeat': alarm['weekRepeat'],
                            'status': alarm['status'],
                        })
            except Exception as error:
                print(error)
            dataOk = self.alarms
            if (not dataOk):
                self.logoff()
                time.sleep(self.retryDelay)
        if (dataOk):
            return self.alarms
        else:
            raise Exception('Xplora API call finally failed with response: ')
        return self.alarms

    async def loadWatchLocation_async(self, withAsk=True):
        retryCounter = 0
        dataOk = False
        location_raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter +=1
            await self.init_async()
            try:
                if withAsk:
                    await self.askWatchLocate_async()
                time.sleep(2)
                location_raw = await self.gqlHandler.getWatchLastLocation_a(await self.getWatchUserID_async())
                if 'watchLastLocate' in location_raw:
                    self.watch_location.append({
                        'tm': datetime.fromtimestamp(location_raw['watchLastLocate']['tm']).strftime('%Y-%m-%d %H:%M:%S'),
                        'lat': location_raw['watchLastLocate']['lat'],
                        'lng': location_raw['watchLastLocate']['lng'],
                        'rad': location_raw['watchLastLocate']['rad'],
                        'poi': location_raw['watchLastLocate']['poi'],
                        'city': location_raw['watchLastLocate']['city'],
                        'province': location_raw['watchLastLocate']['province'],
                        'country': location_raw['watchLastLocate']['country'],
                    })
                    self.watch_battery = location_raw['watchLastLocate']['battery']
                    self.watch_charging = location_raw['watchLastLocate']['isCharging']
                    self.watch_last_location = location_raw['watchLastLocate']
            except Exception as error:
                print(error)
            dataOk = self.watch_location
            if (not dataOk):
                self.logoff()
                time.sleep(self.retryDelay)
        if (dataOk):
            return self.watch_location
        else:
            raise Exception('Xplora API call finally failed with response: ')

    async def getWatchBattery_async(self) -> int:
        await self.loadWatchLocation_async()
        return self.watch_battery
    async def getWatchIsCharging_async(self) -> bool:
        await self.loadWatchLocation_async()
        if self.watch_charging:
            return True
        return False
    async def getWatchOnlineStatus_async(self) -> WatchOnlineStatus:
        await self.init_async()
        if not await self.askWatchLocate_async() and await self.trackWatchInterval_async() == -1:
            return WatchOnlineStatus.OFFLINE.value
        return WatchOnlineStatus.ONLINE.value
    async def __setReadChatMsg_a(self, msgId, id):
        return (await self.gqlHandler.setReadChatMsg(await self.getWatchUserID_async(), msgId, id))['setReadChatMsg']
    async def __getWatchUnReadChatMsgCount_a(self) -> int: # bug?
        return (await self.gqlHandler.unReadChatMsgCount_a(await self.getWatchUserID_async()))['unReadChatMsgCount']
    async def getWatchChats_async(self) -> list: # bug?
        retryCounter = 0
        dataOk = False
        chat_raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter +=1
            await self.init_async()
            try:
                await self.askWatchLocate_async()
                time.sleep(2)
                chats_raw = await self.gqlHandler.chats_a(await self.getWatchUserID_async())
                if 'chats' in chats_raw:
                    if 'list' in chats_raw['chats']:
                        for chat in chats_raw['chats']['list']:
                            self.chats.append({
                                'msgId': chat['msgId'],
                                'type': chat['type'],
                                #chat['sender'],
                                'sender_id': chat['sender']['id'],
                                'sender_name': chat['sender']['name'],
                                #chat['receiver'],
                                'receiver_id': chat['receiver']['id'],
                                'receiver_name': chat['receiver']['name'],
                                #chat['data'],
                                'data_text': chat['data']['text'],
                                'data_sender_name': chat['data']['sender_name'],
                            })
            except Exception as error:
                print(error)
            dataOk = self.chats
            if (not dataOk):
                self.logoff()
                time.sleep(self.retryDelay)
        if (dataOk):
            return self.chats
        else:
            raise Exception('Xplora API call finally failed with response: ')

##### Watch Location Info #####
    async def getWatchLastLocation_async(self) -> dict:
        await self.loadWatchLocation_async(False)
        return self.watch_last_location
    async def getWatchLocate_async(self) -> dict:
        await self.loadWatchLocation_async()
        return self.watch_location
    async def getWatchLocateType_async(self) -> str:
        await self.getWatchLocate_async()
        return self.watch_last_location['locateType']
    async def getWatchIsInSafeZone_async(self) -> bool:
        await self.getWatchLocate_async()
        return self.watch_last_location['isInSafeZone']
    async def getWatchSafeZoneLabel_async(self) -> str:
        await self.getWatchLocate_async()
        return self.watch_last_location['safeZoneLabel']
    async def getSafeZones_async(self) -> list:
        retryCounter = 0
        dataOk = False
        safeZones_raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter +=1
            await self.init_async()
            try:
                await self.askWatchLocate_async()
                time.sleep(2)
                safeZones_raw = await self.gqlHandler.safeZones_a(await self.getWatchUserID_async())
                if 'safeZones' in safeZones_raw:
                    for safeZone in safeZones_raw['safeZones']:
                        self.safe_zones.append({
                            #safeZone,
                            'groupName': safeZone['groupName'],
                            'name': safeZone['name'],
                            'lat': safeZone['lat'],
                            'lng': safeZone['lng'],
                            'rad': safeZone['rad'],
                            'address': safeZone['address'],
                        })
            except Exception as error:
                print(error)
            dataOk = self.safe_zones
            if (not dataOk):
                self.logoff()
                time.sleep(self.retryDelay)
        if (dataOk):
            return self.safe_zones
        else:
            raise Exception('Xplora API call finally failed with response: ')
    async def trackWatchInterval_async(self) -> int:
        await self.init_async()
        return (await self.gqlHandler.trackWatch_a(await self.getWatchUserID_async()))['trackWatch']
    async def askWatchLocate_async(self) -> bool:
        await self.init_async()
        return (await self.gqlHandler.askWatchLocate_a(await self.getWatchUserID_async()))['askWatchLocate']

##### Feature #####
    async def schoolSilentMode_async(self) -> list:
        retryCounter = 0
        dataOk = False
        sientTimes_raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter +=1
            await self.init_async()
            try:
                await self.askWatchLocate_async()
                time.sleep(2)
                sientTimes_raw = await self.gqlHandler.silentTimes_a(await self.getWatchUserID_async())
                if 'silentTimes' in sientTimes_raw:
                    for sientTime in sientTimes_raw['silentTimes']:
                        self.school_silent_mode.append({
                            'id': sientTime['id'],
                            'start': self.__helperTime(sientTime['start']),
                            'end': self.__helperTime(sientTime['end']),
                            'weekRepeat': sientTime['weekRepeat'],
                            'status': sientTime['status'],
                        })
            except Exception as error:
                print(error)
            dataOk = self.school_silent_mode
            if (not dataOk):
                self.logoff()
                time.sleep(self.retryDelay)
        if (dataOk):
            return self.school_silent_mode
        else:
            raise Exception('Xplora API call finally failed with response: ')
    async def setEnableSilentTime_async(self, silentId) -> bool:
        retryCounter = 0
        dataOk = False
        _raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter +=1
            await self.init_async()
            try:
                await self.askWatchLocate_async()
                time.sleep(2)
                enable_raw = await self.gqlHandler.setEnableSlientTime_a(silentId)
                if 'setEnableSilentTime' in enable_raw:
                    _raw = enable_raw['setEnableSilentTime']
            except Exception as error:
                print(error)
            dataOk = _raw
            if (not dataOk):
                self.logoff()
                time.sleep(self.retryDelay)
        if (dataOk):
            return bool(_raw)
        else:
            raise Exception('Xplora API call finally failed with response: ')
    async def setDisableSilentTime_async(self, silentId) -> bool:
        retryCounter = 0
        dataOk = False
        _raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter +=1
            await self.init_async()
            try:
                await self.askWatchLocate_async()
                time.sleep(2)
                disable_raw = await self.gqlHandler.setEnableSlientTime_a(silentId, NormalStatus.DISABLE.value)
                if 'setEnableSilentTime' in disable_raw:
                    _raw = disable_raw['setEnableSilentTime']
            except Exception as error:
                print(error)
            dataOk = _raw
            if (not dataOk):
                self.logoff()
                time.sleep(self.retryDelay)
        if (dataOk):
            return bool(_raw)
        else:
            raise Exception('Xplora API call finally failed with response: ')
    async def setAllEnableSilentTime_async(self) -> list:
        res = []
        for silentTime in (await self.schoolSilentMode_async()):
            res.append(await self.setEnableSilentTime_async(silentTime['id']))
        return res
    async def setAllDisableSilentTime_async(self) -> list:
        res = []
        for silentTime in (await self.schoolSilentMode_async()):
            res.append(await self.setDisableSilentTime_async(silentTime['id']))
        return res
    async def sendText(self, text): # sender is login User
        await self.init_async()
        return await self.gqlHandler.sendText_a(await self.getWatchUserID_async(), text)
    async def shutdown(self) -> bool:
        await self.init_async()
        return await self.gqlHandler.shutdown_a(await self.getWatchUserID_async())
    async def reboot(self) -> bool:
        await self.init_async()
        return await self.gqlHandler.reboot_a(await self.getWatchUserID_async())

##### - #####
    def __helperTime(self, time) -> str:
        h = str(int(time) /60).split('.')
        h2 = str(int(h[1]) *60).zfill(2)[:2]
        return h[0].zfill(2) + ":" + str(h2).zfill(2)
