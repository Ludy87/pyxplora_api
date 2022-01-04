from .gql_handler import *
from datetime import datetime
import asyncio

class PyXploraApi:
    def __init__(self, countryPhoneNumber: str, phoneNumber: str, password: str, userLang: str, timeZone: str, watchNo: int=0) -> None:
        self._countryPhoneNumber = countryPhoneNumber
        self._phoneNumber = phoneNumber
        self._password = password
        self._userLang = userLang
        self._timeZone = timeZone
        self._watchNo = watchNo
        self.__handler: GQLHandler = []
        self.__login()

    def __checkLogin(self) -> None:
        self.__handler = GQLHandler(self._countryPhoneNumber, self._phoneNumber, self._password, self._userLang, self._timeZone)
        self.__handler.login()
        print("Login!")
        self.update()

    def __login(self) -> None:
        if not self.__handler:
            try:
                self.__checkLogin()
            except LoginError as error:
                print(f"Error: -> First faill. {error.args[0]}")
                try:
                    self.__checkLogin()
                except LoginError as error:
                    print(f"Error: -> Login canceled! {error.args[0]}")
                    raise Exception(f"{error.args[0]}")

    def update(self) -> None:
        self.__login()
        print("update")

        self.watch_no = self._watchNo

        self.myInfo = self.__handler.getMyInfo()['readMyInfo']
        self.watch_user_id = self.myInfo['children'][self.watch_no]['ward']['id']
        self.watch_user_name = self.myInfo['children'][self.watch_no]['ward']['name']

        self.watch_last_location = self.__handler.getWatchLastLocation(self.watch_user_id)['watchLastLocate']

        self.contacts = []
        self.alarms = []
        self.chats = []
        self.safe_zones = []
        self.school_silent_mode = []

    def version(self) -> str:
        return "1.0.25"

##### Contact Info #####
    def getContacts(self) -> list:
        self.__login()
        for contact in self.__handler.getContacts(self.watch_user_id)['contacts']['contacts']:
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
    def getWatchAlarm(self) -> list:
        for alarm in self.__handler.getAlarms(self.watch_user_id)['alarms']:
            self.alarms.append({
                'name': alarm['name'],
                'start': alarm['start'],
                'weekRepeat': alarm['weekRepeat'],
                'status': alarm['status'],
            })
        return self.alarms
    def getWatchBattery(self) -> int:
        return self.watch_last_location['battery']
    async def getWatchBattery_a(self) -> int:
        await self.askWatchLocate_async()
        await asyncio.sleep(15)
        self.watch_last_location = (await self.__handler.getWatchLastLocation_a(self.watch_user_id))['watchLastLocate']
        if self.watch_last_location != None:
            if (int(datetime.timestamp(datetime.now())) - self.watch_last_location['tm']) < 30:
                return self.watch_last_location['battery']
        watch_location = await self.__askHelper()
        await asyncio.sleep(1)
        return watch_location['battery']
    def getWatchIsCharging(self) -> bool:
        try:
            return self.watch_last_location['isCharging']
        except TypeError:
            return False
    def getWatchOnlineStatus(self) -> WatchOnlineStatus:
        if self.askWatchLocate() == False:
            return WatchOnlineStatus.OFFLINE.value
        try:
            if self.trackWatchInterval() == -1:
                return WatchOnlineStatus.OFFLINE.value
            return self.__handler.getWatches(self.watch_user_id)['watches'][self.watch_no]['onlineStatus']
        except TypeError:
            return WatchOnlineStatus.UNKNOWN.value
    def getWatchUnReadChatMsgCount(self) -> int: # bug?
        return self.__handler.unReadChatMsgCount(self.watch_user_id)['unReadChatMsgCount']
    def getWatchChats(self) -> list: # bug?
        for chat in self.__handler.chats(self.watch_user_id)['chats']['list']:
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
    def getWatchLocate(self) -> dict:
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
    def getWatchIsInSafeZone(self) -> bool:
        return self.watch_last_location['isInSafeZone']
    def getWatchSafeZoneLabel(self) -> str:
        return self.watch_last_location['safeZoneLabel']
    def getSafeZones(self) -> list:
        for safeZone in self.__handler.safeZones(self.watch_user_id)['safeZones']:
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
    def trackWatchInterval(self) -> int:
        return self.__handler.trackWatch(self.watch_user_id)['trackWatch']
    def askWatchLocate(self) -> bool:
        return self.__handler.askWatchLocate(self.watch_user_id)['askWatchLocate']
    async def askWatchLocate_async(self) -> bool:
        return (await self.__handler.askWatchLocate_a(self.watch_user_id))['askWatchLocate']

##### Feature #####
    def schoolSilentMode(self) -> list:
        for sientTime in self.__handler.silentTimes(self.watch_user_id)['silentTimes']:
            self.school_silent_mode.append({
                'id': sientTime['id'],
                'start': self.__helperTime(sientTime['start']),
                'end': self.__helperTime(sientTime['end']),
                'weekRepeat': sientTime['weekRepeat'],
                'status': sientTime['status'],
            })
        return self.school_silent_mode
    def setEnableSilentTime(self, silentId) -> bool:
        return bool(self.__handler.setEnableSlientTime(silentId)['setEnableSilentTime'])
    def setDisableSilentTime(self, silentId) -> bool:
        return bool(self.__handler.setEnableSlientTime(silentId, NormalStatus.DISABLE)['setEnableSilentTime'])
    def setAllEnableSilentTime(self) -> list:
        res = []
        for silentTime in self.schoolSilentMode():
            res.append(bool(self.setEnableSilentTime(silentTime['id'])))
        return res
    def setAllDisableSilentTime(self):
        res = []
        for silentTime in self.schoolSilentMode():
            res.append(bool(self.setDisableSilentTime(silentTime['id'])))
        return res
    def sendText(self, text): # sender is login User
        return self.__handler.sendText(self.watch_user_id, text)
    def shutdown(self) -> bool:
        return self.__handler.shutdown(self.watch_user_id)
    def reboot(self) -> bool:
        return self.__handler.reboot(self.watch_user_id)

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
