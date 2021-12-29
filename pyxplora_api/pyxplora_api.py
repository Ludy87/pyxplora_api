from .gql_handler import *
from datetime import datetime

class PyXploraApi:
    def __init__(self, countryPhoneNumber: str, phoneNumber: str, password: str, userLang: str, timeZone: str, watchNo: int=0):
        self.handler = GQLHandler(countryPhoneNumber, phoneNumber, password, userLang, timeZone)
        self.handler.login()

        self.watch_no = watchNo

        self.myInfo = self.handler.getMyInfo()['readMyInfo']
        self.watch_user_id = self.myInfo['children'][self.watch_no]['ward']['id']
        self.watch_user_name = self.myInfo['children'][self.watch_no]['ward']['name']

        self.watch_last_location = self.handler.getWatchLastLocation(self.watch_user_id)['watchLastLocate']

        self.contacts = []
        self.alarms = []
        self.chats = []
        self.safe_zones = []
        self.school_silent_mode = []

##### Contact Info #####
    def getContacts(self):
        for contact in self.handler.getContacts(self.watch_user_id)['contacts']['contacts']:
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
    def getUserName(self):
        return self.myInfo['name']
    def getUserIcon(self):
        return self.myInfo['extra']['profileIcon']
    def getUserXcoin(self):
        return self.myInfo['xcoin']
    def getUserCurrentStep(self):
        return self.myInfo['currentStep']
    def getUserTotalStep(self):
        return self.myInfo['totalStep']
    def getUserCreate(self):
        return datetime.fromtimestamp(self.myInfo['create']).strftime('%Y-%m-%d %H:%M:%S')
    def getUserUpdate(self):
        return datetime.fromtimestamp(self.myInfo['update']).strftime('%Y-%m-%d %H:%M:%S')

##### Watch Info #####
    def getWatchCurrentStep(self):
        return self.myInfo['children'][self.watch_no]['ward']['currentStep']
    def getWatchTotalStep(self):
        return self.myInfo['children'][self.watch_no]['ward']['totalStep']
    def getWatchAlarm(self):
        for alarm in self.handler.getAlarms(self.watch_user_id)['alarms']:
            self.alarms.append({
                'name': alarm['name'],
                'start': alarm['start'],
                'weekRepeat': alarm['weekRepeat'],
                'status': alarm['status'],
            })
        return self.alarms
    def getWatchUserID(self):
        return self.watch_user_id
    def getWatchUserName(self):
        return self.watch_user_name
    def getWatchXcoin(self):
        return self.myInfo[0]['ward']['xcoin']
    def getWatchBattery(self):
        return self.watch_last_location['battery']
    def getWatchIsCharging(self):
        return self.watch_last_location['isCharging']
    def getWatchOnlineStatus(self):
        return self.handler.getWatches(self.watch_user_id)['watches'][self.watch_no]['onlineStatus']
    def getWatchUnReadChatMsgCount(self): # bug?
        return self.handler.unReadChatMsgCount(self.watch_user_id)['unReadChatMsgCount']
    def getWatchChats(self): # bug?
        for chat in self.handler.chats(self.watch_user_id)['chats']['list']:
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
    def getWatchLastLocation(self):
        return self.watch_last_location
    def getWatchLocateType(self):
        return self.watch_last_location['locateType']
    def getWatchLocate(self):
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
    def getWatchIsInSafeZone(self):
        return self.watch_last_location['isInSafeZone']
    def getWatchSafeZoneLabel(self):
        return self.watch_last_location['safeZoneLabel']
    def getSafeZones(self):
        for safeZone in self.handler.safeZones(self.watch_user_id)['safeZones']:
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
    def trackWatchInterval(self):
        return self.handler.trackWatch(self.watch_user_id)['trackWatch']
    def askWatchLocate(self):
        return self.handler.askWatchLocate(self.watch_user_id)['askWatchLocate']
    def schoolSilentMode(self):
        for sientTime in self.handler.silentTimes(self.watch_user_id)['silentTimes']:
            self.school_silent_mode.append({
                'id': sientTime['id'],
                'start': self.helperTime(sientTime['start']),
                'end': self.helperTime(sientTime['end']),
                'weekRepeat': sientTime['weekRepeat'],
                'status': sientTime['status'],
            })
        return self.school_silent_mode
    def setEnableSilentTime(self, silentId):
        return self.handler.setEnableSlientTime(silentId)['setEnableSilentTime']
    def setDisableSilentTime(self, silentId):
        return self.handler.setEnableSlientTime(silentId, NormalStatus.DISABLE)['setEnableSilentTime']
    def setAllEnableSilentTime(self):
        res = []
        for silentTime in self.schoolSilentMode():
            res.append(self.setEnableSilentTime(silentTime['id']))
        return res
    def setAllDisableSilentTime(self):
        res = []
        for silentTime in self.schoolSilentMode():
            res.append(self.setDisableSilentTime(silentTime['id']))
        return res
    def shutdown(self):
        return self.handler.shutdown(self.watch_user_id)
    def reboot(self):
        return self.handler.reboot(self.watch_user_id)
    def helperTime(self, time):
        h = str(int(time) /60).split('.')
        h2 = str(int(h[1]) *60).zfill(2)[:2]
        return h[0].zfill(2) + ":" + str(h2).zfill(2)
