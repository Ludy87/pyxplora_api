import hashlib
import math
import time
from datetime import date, datetime, timezone
from python_graphql_client import GraphqlClient

from enum import Enum

from . import gql_mutations as gm
from . import gql_queries as gq

class NormalStatus(Enum):
    ENABLE = "ENABLE"
    DISABLE = "DISABLE"
    UNKNOWN__ = "UNKNOWN__"

class WatchOnlineStatus(Enum):
    UNKNOWN = "UNKNOWN"
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    UNKNOWN__ = "UNKNOWN__"

class GQLHandler:
    def __init__(self, countryPhoneNumber: str, phoneNumber: str, password: str, userLang: str, timeZone: str):
        # init vars
        self.sessionId = None
        self.accessToken = None
        self.accessTokenExpire = 0
        self.userLocale = userLang
        self.timeZone = timeZone
        self.countryPhoneNumber = countryPhoneNumber
        self.phoneNumber = phoneNumber
        self.passwordMD5 = hashlib.md5(password.encode()).hexdigest()
        self.API_KEY = "270072d0fb4811ebacd96f6726fbdbb1"
        self.API_SECRET = "2d0288d0fb4811ebabfbd57e57c6ae64"
        self.issueDate = 0
        self.expireDate = 0
        self.userId = None
        self.ENDPOINT = "https://api.myxplora.com/api"
        self.variables = {
            "countryPhoneNumber": self.countryPhoneNumber,
            "phoneNumber": self.phoneNumber,
            "password": self.passwordMD5,
            "userLang": self.userLocale,
            "timeZone": self.timeZone
        }
        self.issueToken = None

    def getRequestHeaders(self, acceptedContentType: str):
        if acceptedContentType == "" or acceptedContentType == None:
            raise Exception("acceptedContentType MUST NOT be empty!")
        if self.API_KEY == None:
            raise Exception("Xplorao2o API_KEY MUST NOT be empty!")
        if self.API_SECRET == None:
            raise Exception("Xplorao2o API_SECRET MUST NOT be empty!")
        requestHeaders = {}
        if self.accessToken == None:
            # OPEN authorization
            authorizationHeader = f"Open {self.API_KEY}:{self.API_SECRET}"
        else:
            # BEARER authorization
            authorizationHeader = f"Bearer {self.accessToken}:{self.API_SECRET}"
            rfc1123DateString = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S") + " GMT"
            requestHeaders["H-Date"] = rfc1123DateString
            requestHeaders["H-Authorization"] = authorizationHeader
        requestHeaders["H-BackDoor-Authorization"] = authorizationHeader
        requestHeaders["Accept"] = acceptedContentType
        requestHeaders["Content-Type"] = acceptedContentType
        requestHeaders["H-Tid"] = str(math.floor(time.time()))
        return requestHeaders

    def runGqlQuery(self, query: str, variables):
        if query == None:
            raise Exception("GraphQL guery string MUST NOT be empty!")
        # Add Xplora® API headers
        requestHeaders = self.getRequestHeaders("application/json; charset=UTF-8")
        # create GQLClient
        gqlClient = GraphqlClient(endpoint=self.ENDPOINT, headers=requestHeaders)
        # execute QUERY|MUTATION
        data = gqlClient.execute(query=query, variables=variables)
        return data

    def runAuthorizedGqlQuery(self, query: str, variables):
        if self.accessToken == None:
            raise Exception("You have to login to the Xplora® API first.")
        # Run GraphQL query and return
        return self.runGqlQuery(query, variables)

    def login(self):
        data = self.runGqlQuery(gm.MUTATION["tokenM"], self.variables)['data']
        if data['issueToken'] == None:
            # Login failed.
            raise LoginError("Login to Xplora® API failed. Check your input!")
        self.issueToken = data['issueToken']

        #  Login succeeded
        self.sessionId = self.issueToken['id'];
        self.userId = self.issueToken['user']['id'];
        self.accessToken = self.issueToken['token'];
        self.issueDate = self.issueToken['issueDate'];
        self.expireDate = self.issueToken['expireDate'];
    
        if self.issueToken['app'] != None:
            #  Update API_KEY and API_SECRET?
            if self.issueToken['app']['apiKey']:
                self.API_KEY = self.issueToken['app']['apiKey']
            if self.issueToken['app']['apiSecret']:
                self.API_SECRET = self.issueToken['app']['apiSecret']
        return self.issueToken

    def isAdmin(self, ownId, query, variables, key):
        contacts = self.getContacts(ownId)
        for contact in contacts['contacts']['contacts']:
            try:
                id = contact['contactUser']['id']
            except KeyError and TypeError:
                id = None
            if self.userId == id:
                if contact['guardianType'] == 'FIRST':
                    return self.runAuthorizedGqlQuery(query, variables)['data'][key]
        raise Exception("no Admin!")

########## SECTION QUERY start ##########

    def getMyInfo(self): # Profil from login Account
        self.isLogged()
        return self.runAuthorizedGqlQuery(gq.QUERY['readMyInfoQ'], {})['data']

    def getContacts(self, ownId): # Contacts from ownUser
        return self.runAuthorizedGqlQuery(gq.QUERY['contactsQ'], { "uid": ownId })['data']

    def getWatchCount(self):
        return self.runAuthorizedGqlQuery(gq.QUERY['watchCountQ'], {})['data']

    def getWatches(self, ownId):
        return self.runAuthorizedGqlQuery(gq.QUERY['watchesQ'], { "uid": ownId })['data']

    def getWatchLastLocation(self, ownId):
        return self.runAuthorizedGqlQuery(gq.QUERY['watchLastLocateQ'], { "uid": ownId })['data']

    def trackWatch(self, ownId): # tracking time - seconds
        res = self.runAuthorizedGqlQuery(gq.QUERY['trackWatchQ'], { "uid": ownId })['data']
        if res['trackWatch'] != None:
            return res
        return { 'trackWatch': -1 }

    def askWatchLocate(self, ownId):
        res = self.runAuthorizedGqlQuery(gq.QUERY['askWatchLocateQ'], { "uid": ownId })['data']
        if res['askWatchLocate'] != None:
            return res
        return { 'askWatchLocate': False }

    def getAlarms(self, ownId):
        return self.runAuthorizedGqlQuery(gq.QUERY['alarmsQ'], { "uid": ownId })['data']

    def getWifi(self, id): # without function?
        return self.runAuthorizedGqlQuery(gq.QUERY['getWifiQ'], { "uid": id })['data']

    def avatars(self, id): # without function?
        return self.runAuthorizedGqlQuery(gq.QUERY['avatarsQ'], { 'id': id })['data']

    def unReadChatMsgCount(self, ownId):
        return self.runAuthorizedGqlQuery(gq.QUERY['unReadChatMsgCountQ'], { 'uid': ownId })['data']

    def chats(self, ownId): # ownUser id
        return self.runAuthorizedGqlQuery(gq.QUERY['chatsQ'], { 'uid': ownId })['data']

    def notice(self): # without function?
        return self.runAuthorizedGqlQuery(gq.QUERY['noticeQ'], {})['data']

    def staticCard(self):
        return self.runAuthorizedGqlQuery(gq.QUERY['staticCardQ'], {})['data']

    def campaignUserProfiles(self):
        return self.runAuthorizedGqlQuery(gq.QUERY['CampaignUserProfilesQ'], {})['data']

    def subscribedCampaign(self, id, needDetail=False):
        return self.runAuthorizedGqlQuery(gq.QUERY['subscribedCampaignQ'], { 'uid': id, 'needDetail': needDetail })['data']

    def getReviewStatus(self, id):
        return self.runAuthorizedGqlQuery(gq.QUERY['GetReviewStatusQ'], { 'uid': id })['data']

    def countries(self): # Country Support
        return self.runAuthorizedGqlQuery(gq.QUERY['CountriesQ'], {})['data']

    def safeZones(self, ownId):
        return self.runAuthorizedGqlQuery(gq.QUERY['safeZonesQ'], { 'uid': ownId })['data']

    def safeZoneGroups(self):
        return self.runAuthorizedGqlQuery(gq.QUERY['safeZoneGroupsQ'], {})['data']

    def silentTimes(self, ownId):
        return self.runAuthorizedGqlQuery(gq.QUERY['silentTimesQ'], { 'uid': ownId })['data']

########## SECTION QUERY end ##########
    
########## SECTION MUTATION start ##########

    def sendText(self, ownId, text): # ownUser id
        if self.runAuthorizedGqlQuery(gm.MUTATION['sendTextM'], { "uid": ownId, "text": text })['data']['sendChatText'] != None:
            return True
        return False

    def addStep(self, stepCount):
        return self.runAuthorizedGqlQuery(gm.MUTATION['addStepM'], { "stepCount": stepCount })['data']

    def shutdown(self, ownId): # ownUser id
        return self.isAdmin(ownId, gm.MUTATION['shutdownM'], { "uid": ownId }, 'reboot')

    def reboot(self, ownId): # ownUser id
        return self.isAdmin(ownId, gm.MUTATION['rebootM'], { "uid": ownId }, 'reboot')

    def modifyAlert(self, id, YesOrNo): # function?
        return self.runAuthorizedGqlQuery(gm.MUTATION['modifyAlertM'], { "uid": id, "remind": YesOrNo })

    def setEnableSlientTime(self, silentId, status: NormalStatus=NormalStatus.ENABLE.value):
        return self.runAuthorizedGqlQuery(gm.MUTATION['setEnableSlientTimeM'], { 'silentId': silentId, 'status': status })['data']

    def setEnableAlarmTime(self, alarmId, status: NormalStatus=NormalStatus.ENABLE.value):
        return self.runAuthorizedGqlQuery(gm.MUTATION['ModifyAlarmM'], { 'alarmId': alarmId, 'status': status })['data']

    def setReadChatMsg(self, ownId, msgId, id):
        return self.runAuthorizedGqlQuery(gm.MUTATION['setReadChatMsg'], { "uid": ownId, 'msgId': msgId, 'id': id })['data']

########## SECTION MUTATION end ##########

class Error(Exception):
    pass

class LoginError(Error):
    def __init__(self, message, res=1):
        self.message = message
        self.res = res
        super().__init__(self.message, self.res)

    def __str__(self):
        return f'{self.message} - {self.res}'