from .gql_handler_async import *
from datetime import datetime

class PyXploraApi:
    def __init__(self, countryPhoneNumber: str, phoneNumber: str, password: str, userLang: str, timeZone: str, watchNo: int=0) -> None:
        self._countryPhoneNumber = countryPhoneNumber
        self._phoneNumber = phoneNumber
        self._password = password
        self._userLang = userLang
        self._timeZone = timeZone
        self.watch_no = watchNo
        self.__handler: GQLHandler = []

    async def __checkLogin_a(self) -> None:
        self.__handler = GQLHandler(self._countryPhoneNumber, self._phoneNumber, self._password, self._userLang, self._timeZone)
        await self.__handler.login_a()
        #print("Login!")
        #await self.update_a()

    async def __login_a(self) -> None:
        if not self.__handler:
            try:
                await self.__checkLogin_a()
            except LoginError as error:
                #print(f"Error: -> First faill. {error.args[0]}")
                try:
                    await self.__checkLogin_a()
                except LoginError as error:
                    #print(f"Error: -> Login canceled! {error.args[0]}")
                    raise Exception(f"{error.args[0]}")

    async def update_a(self) -> None:
        await self.__login_a()

        self.myInfo = (await self.__handler.getMyInfo_a())['readMyInfo']
        self.watch_user_id = self.myInfo['children'][self.watch_no]['ward']['id']
        self.watch_user_name = self.myInfo['children'][self.watch_no]['ward']['name']

        self.watch_last_location = (await self.__handler.getWatchLastLocation_a(self.watch_user_id))['watchLastLocate']

        self.contacts = []
        self.alarms = []
        self.chats = []
        self.safe_zones = []
        self.school_silent_mode = []

    def version(self) -> str:
        return "1.0.31"

##### Contact Info #####
    async def getContacts_a(self) -> list:
        for contact in (await self.__handler.getContacts_a(self.watch_user_id))['contacts']['contacts']:
            try:
                xcoin = contact['contactUser']['xcoin']
                id = contact['contactUser']['id']
            except KeyError and TypeError:
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
        return self.contacts

##### User Info #####
    def getUserID(self) -> str:
        return self.__checkMyInfo(self.myInfo, 'id', 'n/a')
    def getUserName(self) -> str:
        return self.__checkMyInfo(self.myInfo, 'name', 'n/a')
    def getUserIcon(self) -> str:
        return self.__checkMyInfo(self.__checkMyInfo(self.myInfo, 'extra', 'n/a'), 'profileIcon', 'n/a')
    def getUserXcoin(self) -> int:
        return self.__checkMyInfo(self.myInfo, 'xcoin', -1)
    def getUserCurrentStep(self) -> int:
        return self.__checkMyInfo(self.myInfo, 'currentStep', -1)
    def getUserTotalStep(self) -> int:
        return self.__checkMyInfo(self.myInfo, 'totalStep', -1)
    def getUserCreate(self) -> str:
        return datetime.fromtimestamp(self.__checkMyInfo(self.myInfo, 'create', 0)).strftime('%Y-%m-%d %H:%M:%S')
    def getUserUpdate(self) -> str:
        return datetime.fromtimestamp(self.__checkMyInfo(self.myInfo, 'update', 0)).strftime('%Y-%m-%d %H:%M:%S')

##### Watch Info #####
    def getWatchUserID(self) -> str:
        return self.watch_user_id
    def getWatchUserName(self) -> str:
        return self.watch_user_name
    def getWatchXcoin(self) -> int:
        return self.myInfo['children'][self.watch_no]['ward']['xcoin']
    def getWatchCurrentStep(self) -> int:
        return self.myInfo['children'][self.watch_no]['ward']['currentStep']
    def getWatchTotalStep(self) -> int:
        return self.myInfo['children'][self.watch_no]['ward']['totalStep']
    async def getWatchAlarm_a(self) -> list:
        for alarm in (await self.__handler.getAlarms_a(self.watch_user_id))['alarms']:
            self.alarms.append({
                'name': alarm['name'],
                'start': alarm['start'],
                'weekRepeat': alarm['weekRepeat'],
                'status': alarm['status'],
            })
        return self.alarms
    async def getWatchBattery_a(self) -> int:
        await self.getWatchLocate_a()
        return self.watch_last_location['battery']
    async def getWatchIsCharging_a(self) -> bool:
        await self.getWatchLocate_a()
        try:
            return self.watch_last_location['isCharging']
        except TypeError:
            return False
    async def getWatchOnlineStatus_a(self) -> WatchOnlineStatus:
        if await self.askWatchLocate_a() == True:
            return WatchOnlineStatus.ONLINE.value
        try:
            if await self.trackWatchInterval_a() == -1:
                return WatchOnlineStatus.OFFLINE.value
            return (await self.__handler.getWatches_a(self.watch_user_id))['watches'][self.watch_no]['onlineStatus']
        except TypeError:
            return WatchOnlineStatus.UNKNOWN.value
    async def setReadChatMsg(self, msgId, id):
        return (await self.__handler.setReadChatMsg(self.watch_user_id, msgId, id))['setReadChatMsg']
    async def getWatchUnReadChatMsgCount_a(self) -> int: # bug?
        return (await self.__handler.unReadChatMsgCount_a(self.watch_user_id))['unReadChatMsgCount']
    async def getWatchChats_a(self) -> list: # bug?
        for chat in (await self.__handler.chats_a(self.watch_user_id))['chats']['list']:
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
        return self.chats

##### Watch Location Info #####
    def getWatchLastLocation(self) -> dict:
        return self.watch_last_location
    def getWatchLocateType(self) -> str:
        return self.watch_last_location['locateType']
    async def getWatchLocate_a(self) -> dict:
        await self.askWatchLocate_a()
        return {
            'tm': datetime.fromtimestamp(self.watch_last_location['tm']).strftime('%Y-%m-%d %H:%M:%S'),
            'lat': self.watch_last_location['lat'],
            'lng': self.watch_last_location['lng'],
            'rad': self.watch_last_location['rad'],
            'poi': self.watch_last_location['poi'],
            'city': self.watch_last_location['city'],
            'province': self.watch_last_location['province'],
            'country': self.watch_last_location['country'],
        }
    async def getWatchIsInSafeZone_a(self) -> bool:
        await self.getWatchLocate_a()
        return self.watch_last_location['isInSafeZone']
    def getWatchSafeZoneLabel(self) -> str:
        self.getWatchLastLocation()
        return self.watch_last_location['safeZoneLabel']
    async def getSafeZones_a(self) -> list:
        for safeZone in (await self.__handler.safeZones_a(self.watch_user_id))['safeZones']:
            self.safe_zones.append({
                #safeZone,
                'groupName': safeZone['groupName'],
                'name': safeZone['name'],
                'lat': safeZone['lat'],
                'lng': safeZone['lng'],
                'rad': safeZone['rad'],
                'address': safeZone['address'],
            })
        return self.safe_zones
    async def trackWatchInterval_a(self) -> int:
        return (await self.__handler.trackWatch_a(self.watch_user_id))['trackWatch']
    async def askWatchLocate_a(self) -> bool:
        return (await self.__handler.askWatchLocate_a(self.watch_user_id))['askWatchLocate']

##### Feature #####
    async def schoolSilentMode_a(self) -> list:
        for sientTime in (await self.__handler.silentTimes_a(self.watch_user_id))['silentTimes']:
            self.school_silent_mode.append({
                'id': sientTime['id'],
                'start': self.__helperTime(sientTime['start']),
                'end': self.__helperTime(sientTime['end']),
                'weekRepeat': sientTime['weekRepeat'],
                'status': sientTime['status'],
            })
        return self.school_silent_mode
    async def setEnableSilentTime_a(self, silentId) -> bool:
        return bool((await self.__handler.setEnableSlientTime_a(silentId))['setEnableSilentTime'])
    async def setDisableSilentTime_a(self, silentId) -> bool:
        return bool((await self.__handler.setEnableSlientTime_a(silentId, NormalStatus.DISABLE.value))['setEnableSilentTime'])
    async def setAllEnableSilentTime_a(self) -> list:
        res = []
        for silentTime in (await self.schoolSilentMode_a()):
            res.append(bool(await self.setEnableSilentTime_a(silentTime['id'])))
        return res
    async def setAllDisableSilentTime_a(self) -> list:
        res = []
        for silentTime in (await self.schoolSilentMode_a()):
            res.append(bool(await self.setDisableSilentTime(silentTime['id'])))
        return res
    async def sendText(self, text): # sender is login User
        return await self.__handler.sendText_a(self.watch_user_id, text)
    async def shutdown(self) -> bool:
        return await self.__handler.shutdown_a(self.watch_user_id)
    async def reboot(self) -> bool:
        return await self.__handler.reboot_a(self.watch_user_id)

##### - #####
    def __helperTime(self, time) -> str:
        h = str(int(time) /60).split('.')
        h2 = str(int(h[1]) *60).zfill(2)[:2]
        return h[0].zfill(2) + ":" + str(h2).zfill(2)
    async def __askHelper(self) -> int:
        try:
            return (await self.__handler.getWatchLastLocation_a(self.watch_user_id))['watchLastLocate']
        except TypeError:
            return 0
    def __checkMyInfo(self, func, value: str, res):
        if value in func:
            return func[value]
        return res
