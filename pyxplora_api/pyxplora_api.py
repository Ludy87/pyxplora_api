import logging

from datetime import datetime
from time import time, sleep

from .const import VERSION
from .exception_classes import LoginError
from .gql_handler import GQLHandler, NormalStatus, WatchOnlineStatus

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

        self.contacts = []
        self.alarms = []
        self.chats = []
        self.safe_zones = []
        self.school_silent_mode = []
        self.watch_location = []
        self.watch_last_location = []
        self.watch_battery = None
        self.watch_charging = None

        self.__gqlHandler = None
        self.__issueToken = None
        # self.watch = None

        self.watchs = []

        self.user = None

    def __login(self, forceLogin=False) -> dict:
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
                            self.__issueToken = self.__gqlHandler.login()
                        except Exception:
                            pass

                        # Wait for next try
                        if (not self.__issueToken):
                            sleep(self.retryDelay)
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

    def init(self, forceLogin=False) -> None:
        token = self.__login(forceLogin)
        if token:
            if ('user' in token):
                # self.watch = token['user']['children'][self.watch_no]['ward']
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
    def getContacts(self, watchID) -> list:
        retryCounter = 0
        dataOk = False
        contacts_raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            self.init()
            try:
                contacts_raw = self.__gqlHandler.getContacts(watchID)
                if 'contacts' in contacts_raw:
                    if contacts_raw['contacts'] is None:
                        continue
                    if 'contacts' in contacts_raw['contacts']:
                        for contact in contacts_raw['contacts']['contacts']:
                            try:
                                xcoin = contact['contactUser']['xcoin']
                                id = contact['contactUser']['id']
                            except TypeError:
                                # None - XCoins
                                xcoin = -1
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
                _LOGGER.debug(error)
            dataOk = self.contacts
            if (not dataOk):
                self.__logoff()
                sleep(self.retryDelay)
        if dataOk:
            return self.contacts
        else:
            raise Exception('Xplora API call finally failed with response: ')

##### User Info #####
    def getUserID(self) -> str:
        return self.user['id']
    def getUserName(self) -> str:
        return self.user['name']
    def getUserIcon(self) -> str:
        return self.user['extra']['profileIcon']
    def getUserXcoin(self) -> int:
        return self.user['xcoin']
    def getUserCurrentStep(self) -> int:
        return self.user['currentStep']
    def getUserTotalStep(self) -> int:
        return self.user['totalStep']
    def getUserCreate(self) -> str:
        return datetime.fromtimestamp(self.user['create']).strftime('%Y-%m-%d %H:%M:%S')
    def getUserUpdate(self) -> str:
        return datetime.fromtimestamp(self.user['update']).strftime('%Y-%m-%d %H:%M:%S')

##### Watch Info #####
    def getWatchUserID(self, child_no: list = []) -> str:
        watch_IDs = []
        for watch in self.watchs:
            if child_no:
                if watch['ward']['phoneNumber'] in child_no:
                    watch_IDs.append(watch['ward']['id'])
            else:
                watch_IDs.append(watch['ward']['id'])
        return watch_IDs
    def getWatchUserPhoneNumber(self) -> str:
        watch_IDs = []
        for watch in self.watchs:
            watch_IDs.append(watch['ward']['phoneNumber'])
        return watch_IDs
    def getWatchUserName(self, watchID) -> str:
        for watch in self.watchs:
            if watch['ward']['id'] == watchID:
                return watch['ward']['name']
        raise Exception("Child phonenumber not found!")
    def getWatchUserIcon(self, watchID) -> str:
        for watch in self.watchs:
            if watch['ward']['id'] == watchID:
                return f"https://api.myxplora.com/file?id={watch['ward']['file']['id']}"
        raise Exception("Child phonenumber not found!")
    def getWatchXcoin(self, watchID) -> int:
        for watch in self.watchs:
            if watch['ward']['id'] == watchID:
                return watch['ward']['xcoin']
        raise Exception("Child phonenumber not found!")
    def getWatchCurrentStep(self, watchID) -> int:
        for watch in self.watchs:
            if watch['ward']['id'] == watchID:
                return watch['ward']['currentStep']
        raise Exception("Child phonenumber not found!")
    def getWatchTotalStep(self, watchID) -> int:
        for watch in self.watchs:
            if watch['ward']['id'] == watchID:
                return watch['ward']['totalStep']
        raise Exception("Child phonenumber not found!")

    def getWatchAlarm(self, watchID) -> list:
        retryCounter = 0
        dataOk = False
        alarms_raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            self.init()
            try:
                alarms_raw = self.__gqlHandler.getAlarms(watchID)
                if 'alarms' in alarms_raw:
                    if not alarms_raw['alarms']:
                        dataOk = True
                        return self.alarms
                    for alarm in alarms_raw['alarms']:
                        self.alarms.append({
                            'id': alarm['id'],
                            'name': alarm['name'],
                            'start': self.__helperTime(alarm['occurMin']),
                            'weekRepeat': alarm['weekRepeat'],
                            'status': alarm['status'],
                        })
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = self.alarms
            if (not dataOk):
                self.__logoff()
                sleep(self.retryDelay)
        if (dataOk):
            return self.alarms
        else:
            raise Exception('Xplora API call finally failed with response: ')
        return self.alarms

    def loadWatchLocation(self, withAsk=True, watchID=0) -> list:
        retryCounter = 0
        dataOk = False
        location_raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            self.init()
            try:
                if withAsk:
                    self.askWatchLocate(watchID)
                sleep(self.retryDelay)
                location_raw = self.__gqlHandler.getWatchLastLocation(watchID)
                if 'watchLastLocate' in location_raw:
                    if location_raw['watchLastLocate'] is not None:
                        self.watch_location.append({
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
                        })
                        self.watch_battery = location_raw['watchLastLocate']['battery']
                        self.watch_charging = location_raw['watchLastLocate']['isCharging']
                        self.watch_last_location = location_raw['watchLastLocate']
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = self.watch_location
            if (not dataOk):
                self.__logoff()
                sleep(self.retryDelay)
        if (dataOk):
            return self.watch_location
        else:
            raise Exception('Xplora API call finally failed with response: ')

    def getWatchBattery(self, watchID) -> int:
        self.loadWatchLocation(watchID=watchID)
        return self.watch_battery
    def getWatchIsCharging(self, watchID) -> bool:
        self.loadWatchLocation(watchID=watchID)
        if self.watch_charging:
            return True
        return False
    def getWatchOnlineStatus(self, watchID) -> WatchOnlineStatus:
        retryCounter = 0
        dataOk = False
        asktrack_raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            self.init()
            try:
                self.askWatchLocate(watchID)
                sleep(self.retryDelay)
                ask_raw = self.askWatchLocate(watchID)
                track_raw = self.trackWatchInterval(watchID)
                if ask_raw or (track_raw != -1):
                    asktrack_raw = WatchOnlineStatus.ONLINE.value
                else:
                    asktrack_raw = WatchOnlineStatus.OFFLINE.value
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = asktrack_raw
            if (not dataOk):
                self.__logoff()
                sleep(self.retryDelay)
        if (dataOk):
            return asktrack_raw
        else:
            raise Exception('Xplora API call finally failed with response: ')
    def __setReadChatMsg(self, msgId, id):
        return (self.__gqlHandler.setReadChatMsg(self.getWatchUserID(), msgId, id))['setReadChatMsg']
    def getWatchUnReadChatMsgCount(self, watchID) -> int:
        # bug?
        return (self.__gqlHandler.unReadChatMsgCount(watchID))['unReadChatMsgCount']
    def getWatchChats(self, watchID) -> list:
        # bug?
        retryCounter = 0
        dataOk = False
        chats_raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            self.init()
            try:
                self.askWatchLocate(watchID)
                sleep(self.retryDelay)
                chats_raw = self.__gqlHandler.chats(watchID)
                if 'chats' in chats_raw:
                    if 'list' in chats_raw['chats']:
                        for chat in chats_raw['chats']['list']:
                            self.chats.append({
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
            dataOk = self.chats
            if (not dataOk):
                self.__logoff()
                sleep(self.retryDelay)
        if (dataOk):
            return self.chats
        else:
            raise Exception('Xplora API call finally failed with response: ')

##### Watch Location Info #####
    def getWatchLastLocation(self, withAsk: bool = False, watchID=0) -> dict:
        self.loadWatchLocation(withAsk, watchID=watchID)
        return self.watch_last_location
    def getWatchLocate(self, watchID) -> dict:
        self.loadWatchLocation(watchID=watchID)
        return self.watch_location
    def getWatchLocateType(self, watchID) -> str:
        self.getWatchLocate(watchID)
        return self.watch_last_location['locateType']
    def getWatchIsInSafeZone(self, watchID) -> bool:
        self.getWatchLocate(watchID)
        return self.watch_last_location['isInSafeZone']
    def getWatchSafeZoneLabel(self, watchID) -> str:
        self.getWatchLocate(watchID)
        return self.watch_last_location['safeZoneLabel']
    def getSafeZones(self, watchID) -> list:
        retryCounter = 0
        dataOk = False
        safeZones_raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            self.init()
            try:
                self.askWatchLocate(watchID)
                sleep(self.retryDelay)
                safeZones_raw = self.__gqlHandler.safeZones(watchID)
                if 'safeZones' in safeZones_raw:
                    for safeZone in safeZones_raw['safeZones']:
                        self.safe_zones.append({
                            # safeZone,
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
            dataOk = self.safe_zones
            if (not dataOk):
                self.__logoff()
                sleep(self.retryDelay)
        if (dataOk):
            return self.safe_zones
        else:
            raise Exception('Xplora API call finally failed with response: ')
    def trackWatchInterval(self, watchID) -> int:
        return self.__gqlHandler.trackWatch(watchID)['trackWatch']
    def askWatchLocate(self, watchID) -> bool:
        return self.__gqlHandler.askWatchLocate(watchID)['askWatchLocate']

##### Feature #####
    def schoolSilentMode(self, watchID) -> list:
        retryCounter = 0
        dataOk = False
        sientTimes_raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            self.init()
            try:
                self.askWatchLocate(watchID)
                sleep(self.retryDelay)
                sientTimes_raw = self.__gqlHandler.silentTimes(watchID)
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
                _LOGGER.debug(error)
            dataOk = self.school_silent_mode
            if (not dataOk):
                self.__logoff()
                sleep(self.retryDelay)
        if (dataOk):
            return self.school_silent_mode
        else:
            raise Exception('Xplora API call finally failed with response: ')
    def setEnableSilentTime(self, silentId, watchID) -> bool:
        retryCounter = 0
        dataOk = False
        _raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            self.init()
            try:
                self.askWatchLocate(watchID)
                sleep(self.retryDelay)
                enable_raw = self.__gqlHandler.setEnableSlientTime(silentId)
                if 'setEnableSilentTime' in enable_raw:
                    _raw = enable_raw['setEnableSilentTime']
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if (not dataOk):
                self.__logoff()
                sleep(self.retryDelay)
        if (dataOk):
            return bool(_raw)
        else:
            raise Exception('Xplora API call finally failed with response: ')
    def setDisableSilentTime(self, silentId, watchID) -> bool:
        retryCounter = 0
        dataOk = False
        _raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            self.init()
            try:
                self.askWatchLocate(watchID)
                sleep(self.retryDelay)
                disable_raw = self.__gqlHandler.setEnableSlientTime(silentId, NormalStatus.DISABLE.value)
                if 'setEnableSilentTime' in disable_raw:
                    _raw = disable_raw['setEnableSilentTime']
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if (not dataOk):
                self.__logoff()
                sleep(self.retryDelay)
        if (dataOk):
            return bool(_raw)
        else:
            raise Exception('Xplora API call finally failed with response: ')
    def setAllEnableSilentTime(self, watchID) -> list:
        res = []
        for silentTime in (self.schoolSilentMode(watchID)):
            res.append(self.setEnableSilentTime(silentTime['id'], watchID))
        return res
    def setAllDisableSilentTime(self, watchID) -> list:
        res = []
        for silentTime in (self.schoolSilentMode(watchID)):
            res.append(self.setDisableSilentTime(silentTime['id'], watchID))
        return res

    def setEnableAlarmTime(self, alarmId, watchID) -> bool:
        retryCounter = 0
        dataOk = False
        _raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            self.init()
            try:
                self.askWatchLocate(watchID)
                sleep(self.retryDelay)
                enable_raw = self.__gqlHandler.setEnableAlarmTime(alarmId)
                if 'modifyAlarm' in enable_raw:
                    _raw = enable_raw['modifyAlarm']
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if (not dataOk):
                self.__logoff()
                sleep(self.retryDelay)
        if (dataOk):
            return bool(_raw)
        else:
            raise Exception('Xplora API call finally failed with response: ')
    def setDisableAlarmTime(self, alarmId, watchID) -> bool:
        retryCounter = 0
        dataOk = False
        _raw = None
        while (not dataOk and (retryCounter < self.maxRetries + 2)):
            retryCounter += 1
            self.init()
            try:
                self.askWatchLocate(watchID)
                sleep(self.retryDelay)
                disable_raw = self.__gqlHandler.setEnableAlarmTime(alarmId, NormalStatus.DISABLE.value)
                if 'modifyAlarm' in disable_raw:
                    _raw = disable_raw['modifyAlarm']
            except Exception as error:
                _LOGGER.debug(error)
            dataOk = _raw
            if (not dataOk):
                self.__logoff()
                sleep(self.retryDelay)
        if (dataOk):
            return bool(_raw)
        else:
            raise Exception('Xplora API call finally failed with response: ')
    def setAllEnableAlarmTime(self, watchID) -> list:
        res = []
        for alarmTime in (self.getWatchAlarm(watchID)):
            res.append(self.setEnableAlarmTime(alarmTime['id'], watchID))
        return res
    def setAllDisableAlarmTime(self, watchID) -> list:
        res = []
        for alarmTime in (self.getWatchAlarm(watchID)):
            res.append(self.setDisableAlarmTime(alarmTime['id'], watchID))
        return res

    def sendText(self, text, watchID) -> bool:
        # sender is login User
        return self.__gqlHandler.sendText(watchID, text)
    def isAdmin(self, watchID) -> bool:
        for contact in self.getContacts(watchID):
            if (contact['id'] == self.getUserID()):
                return True
        return False
    def shutdown(self, watchID) -> bool:
        if self.isAdmin(watchID):
            return self.__gqlHandler.shutdown(watchID)
        raise Exception("no Admin")
    def reboot(self, watchID) -> bool:
        if self.isAdmin(watchID):
            return self.__gqlHandler.reboot(watchID)
        raise Exception("no Admin")

##### - #####
    def __helperTime(self, time) -> str:
        h = str(int(time) / 60).split('.')
        h2 = str(int(h[1]) * 60).zfill(2)[:2]
        return h[0].zfill(2) + ":" + str(h2).zfill(2)
