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

    async def runGqlQuery_a(self, query: str, variables):
        if query == None:
            raise Exception("GraphQL guery string MUST NOT be empty!")
        # Add Xplora® API headers
        requestHeaders = self.getRequestHeaders("application/json; charset=UTF-8")
        # create GQLClient
        gqlClient = GraphqlClient(endpoint=self.ENDPOINT, headers=requestHeaders)
        # execute QUERY|MUTATION
        data = await gqlClient.execute_async(query=query, variables=variables)
        return data

    async def runAuthorizedGqlQuery_a(self, query: str, variables):
        if self.accessToken == None:
            raise Exception("You have to login to the Xplora® API first.")
        # Run GraphQL query and return
        return (await self.runGqlQuery_a(query, variables))

    async def login_a(self):
        data = (await self.runGqlQuery_a(gm.MUTATION["tokenM"], self.variables))['data']
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

    async def isAdmin_a(self, ownId, query, variables, key):
        contacts = await self.getContacts_a(ownId)
        for contact in contacts['contacts']['contacts']:
            try:
                id = contact['contactUser']['id']
            except KeyError and TypeError:
                id = None
            if self.userId == id:
                if contact['guardianType'] == 'FIRST':
                    return (await self.runAuthorizedGqlQuery_a(query, variables))['data'][key]
        raise Exception("no Admin!")

########## SECTION QUERY start ##########

    async def getMyInfo_a(self): # Profil from login Account
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY['readMyInfoQ'], {}))['data']

    async def getContacts_a(self, ownId): # Contacts from ownUser
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY['contactsQ'], { "uid": ownId }))['data']

    async def getWatchCount_a(self):
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY['watchCountQ'], {}))['data']

    async def getWatches_a(self, ownId):
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY['watchesQ'], { "uid": ownId }))['data']

    async def getWatchLastLocation_a(self, ownId):
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY['watchLastLocateQ'], { "uid": ownId }))['data']

    async def trackWatch_a(self, ownId): # tracking time - seconds
        res = (await self.runAuthorizedGqlQuery_a(gq.QUERY['trackWatchQ'], { "uid": ownId }))['data']
        if res['trackWatch'] != None:
            return res
        return { 'trackWatch': -1 }

    async def askWatchLocate_a(self, ownId):
        res = (await self.runAuthorizedGqlQuery_a(gq.QUERY['askWatchLocateQ'], { "uid": ownId }))['data']
        if res['askWatchLocate'] != None:
            return res
        return { 'askWatchLocate': False }

    async def getAlarms_a(self, ownId):
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY['alarmsQ'], { "uid": ownId }))['data']

    async def getWifi_a(self, id): # without function?
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY['getWifiQ'], { "uid": id }))['data']

    async def avatars_a(self, id): # without function?
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY['avatarsQ'], { 'id': id }))['data']

    async def unReadChatMsgCount_a(self, ownId):
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY['unReadChatMsgCountQ'], { 'uid': ownId }))['data']

    async def chats_a(self, ownId): # ownUser id
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY['chatsQ'], { 'uid': ownId }))['data']

    async def notice_a(self): # without function?
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY['noticeQ'], {}))['data']

    async def staticCard_a(self):
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY['staticCardQ'], {}))['data']

    async def campaignUserProfiles_a(self):
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY['CampaignUserProfilesQ'], {}))['data']

    async def subscribedCampaign_a(self, id, needDetail=False):
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY['subscribedCampaignQ'], { 'uid': id, 'needDetail': needDetail }))['data']

    async def getReviewStatus_a(self, id):
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY['GetReviewStatusQ'], { 'uid': id }))['data']

    async def countries_a(self): # Country Support
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY['CountriesQ'], {}))['data']

    async def safeZones_a(self, ownId):
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY['safeZonesQ'], { 'uid': ownId }))['data']

    async def safeZoneGroups_a(self):
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY['safeZoneGroupsQ'], {}))['data']

    async def silentTimes_a(self, ownId):
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY['silentTimesQ'], { 'uid': ownId }))['data']

########## SECTION QUERY end ##########
    
########## SECTION MUTATION start ##########

    async def sendText_a(self, ownId, text): # ownUser id
        if (await self.runAuthorizedGqlQuery_a(gm.MUTATION['sendTextM'], { "uid": ownId, "text": text }))['data']['sendChatText'] != None:
            return True
        return False

    async def addStep_a(self, stepCount):
        return (await self.runAuthorizedGqlQuery_a(gm.MUTATION['addStepM'], { "stepCount": stepCount }))['data']

    async def shutdown_a(self, ownId): # ownUser id
        return await self.isAdmin_a(ownId, gm.MUTATION['shutdownM'], { "uid": ownId }, 'reboot')

    async def reboot_a(self, ownId): # ownUser id
        return await self.isAdmin_a(ownId, gm.MUTATION['rebootM'], { "uid": ownId }, 'reboot')

    async def modifyAlert_a(self, id, YesOrNo): # function?
        return await self.runAuthorizedGqlQuery_a(gm.MUTATION['modifyAlertM'], { "uid": id, "remind": YesOrNo })

    async def setEnableSlientTime_a(self, silentId, status: NormalStatus=NormalStatus.ENABLE.value):
        return (await self.runAuthorizedGqlQuery_a(gm.MUTATION['setEnableSlientTimeM'], { 'silentId': silentId, 'status': status }))['data']

    async def setEnableAlarmTime_a(self, alarmId, status: NormalStatus=NormalStatus.ENABLE.value):
        return (await self.runAuthorizedGqlQuery_a(gm.MUTATION['ModifyAlarmM'], { 'alarmId': alarmId, 'status': status }))['data']

    async def setReadChatMsg(self, ownId, msgId, id):
        return (await self.runAuthorizedGqlQuery_a(gm.MUTATION['setReadChatMsg'], { "uid": ownId, 'msgId': msgId, 'id': id }))['data']

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