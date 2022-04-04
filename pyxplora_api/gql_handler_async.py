from __future__ import annotations

from python_graphql_client import GraphqlClient

from .const import ENDPOINT
from .exception_classes import LoginError
from .handler_gql import HandlerGQL
from .status import NormalStatus, YesOrNo

from . import gql_mutations as gm
from . import gql_queries as gq


class GQLHandler(HandlerGQL):
    def __init__(self, countryPhoneNumber: str, phoneNumber: str, password: str, userLang: str, timeZone: str):
        super().__init__(countryPhoneNumber, phoneNumber, password, userLang, timeZone)

    async def runGqlQuery_a(self, query: str, variables):
        if query is None:
            raise Exception("GraphQL guery string MUST NOT be empty!")
        # Add Xplora® API headers
        requestHeaders = self.getRequestHeaders("application/json; charset=UTF-8")
        # create GQLClient
        gqlClient = GraphqlClient(endpoint=ENDPOINT, headers=requestHeaders)
        # execute QUERY|MUTATION
        data = await gqlClient.execute_async(query=query, variables=variables)
        return data

    async def runAuthorizedGqlQuery_a(self, query: str, variables):
        if self.accessToken is None:
            raise Exception("You have to login to the Xplora® API first.")
        # Run GraphQL query and return
        return await self.runGqlQuery_a(query, variables)

    async def login_a(self):
        data = (await self.runGqlQuery_a(gm.SIGN_M["issueTokenM"], self.variables))['data']
        if data['issueToken'] is None:
            # Login failed.
            raise LoginError("Login to Xplora® API failed. Check your input!")
        self.issueToken = data['issueToken']

        # Login succeeded
        self.sessionId = self.issueToken['id']
        self.userId = self.issueToken['user']['id']
        self.accessToken = self.issueToken['token']
        self.issueDate = self.issueToken['issueDate']
        self.expireDate = self.issueToken['expireDate']

        if self.issueToken['app'] is not None:
            # Update API_KEY and API_SECRET?
            if self.issueToken['app']['apiKey']:
                self._API_KEY = self.issueToken['app']['apiKey']
            if self.issueToken['app']['apiSecret']:
                self._API_SECRET = self.issueToken['app']['apiSecret']
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

    async def getMyInfo_a(self):
        # Profil from login Account
        return (await self.runAuthorizedGqlQuery_a(gq.MYINFO_Q['readQ'], {}))['data']

    async def getContacts_a(self, ownId):
        # Contacts from ownUser
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q['contactsQ'], { "uid": ownId }))['data']

    async def getWatchCount_a(self):
        return (await self.runAuthorizedGqlQuery_a(gq.QUERY['followRequestWatchCountQ'], {}))['data']

    async def getWatches_a(self, ownId):
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q['watchesQ'], { "uid": ownId }))['data']

    async def getWatchLastLocation_a(self, ownId):
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q['locateQ'], { "uid": ownId }))['data']

    async def trackWatch_a(self, ownId):
        # tracking time - seconds
        res = (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q['trackQ'], { "uid": ownId }))['data']
        if res['trackWatch'] is not None:
            return res
        return { 'trackWatch': -1 }

    async def askWatchLocate_a(self, ownId):
        res = (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q['askLocateQ'], { "uid": ownId }))['data']
        if res['askWatchLocate'] is not None:
            return res
        return { 'askWatchLocate': False }

    async def getAlarms_a(self, ownId):
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q['alarmsQ'], { "uid": ownId }))['data']

    async def getWifi_a(self, id):
        # without function?
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q['getWifisQ'], { "uid": id }))['data']

    async def avatars_a(self, id):
        # without function?
        return (await self.runAuthorizedGqlQuery_a(gq.CAMPAIGN_Q['avatarsQ'], { 'id': id }))['data']

    async def unReadChatMsgCount_a(self, ownId):
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q['unReadChatMsgCountQ'], { 'uid': ownId }))['data']

    async def chats_a(self, ownId):
        # ownUser id
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q['chatsQ'], { 'uid': ownId }))['data']

    async def staticCard_a(self):
        return (await self.runAuthorizedGqlQuery_a(gq.CARD_Q['staticQ'], {}))['data']

    async def campaignUserProfiles_a(self):
        return (await self.runAuthorizedGqlQuery_a(gq.MYINFO_Q['campaignUserProfilesQ'], {}))['data']

    async def subscribedCampaign_a(self, id, needDetail=False):
        return (await self.runAuthorizedGqlQuery_a(gq.CAMPAIGN_Q['subscribedQ'], { 'uid': id, 'needDetail': needDetail }))['data']

    async def getReviewStatus_a(self, id):
        return (await self.runAuthorizedGqlQuery_a(gq.REVIEW_Q['getStatusQ'], { 'uid': id }))['data']

    async def countries_a(self):
        # Country Support
        return (await self.runAuthorizedGqlQuery_a(gq.UTILS_Q['countriesQ'], {}))['data']

    async def safeZones_a(self, ownId):
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q['safeZonesQ'], { 'uid': ownId }))['data']

    async def safeZoneGroups_a(self):
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q['safeZoneGroupsQ'], {}))['data']

    async def silentTimes_a(self, ownId):
        return (await self.runAuthorizedGqlQuery_a(gq.WATCH_Q['silentTimesQ'], { 'uid': ownId }))['data']

########## SECTION QUERY end ##########

########## SECTION MUTATION start ##########

    async def sendText_a(self, ownId, text):
        # ownUser id
        if (await self.runAuthorizedGqlQuery_a(gm.WATCH_M['sendChatTextM'], { "uid": ownId, "text": text }))['data']['sendChatText'] is not None:
            return True
        return False

    async def addStep_a(self, stepCount):
        return (await self.runAuthorizedGqlQuery_a(gm.STEP_M['addM'], { "stepCount": stepCount }))['data']

    async def shutdown_a(self, ownId):
        # ownUser id
        return await self.isAdmin_a(ownId, gm.WATCH_M['shutdownM'], { "uid": ownId }, 'reboot')

    async def reboot_a(self, ownId):
        # ownUser id
        return await self.isAdmin_a(ownId, gm.WATCH_M['rebootM'], { "uid": ownId }, 'reboot')

    async def modifyAlert_a(self, id, yesOrNo: YesOrNo):
        # function?
        return await self.runAuthorizedGqlQuery_a(gm.WATCH_M['modifyAlertM'], { "uid": id, "remind": yesOrNo })

    async def setEnableSlientTime_a(self, silentId, status: NormalStatus = NormalStatus.ENABLE.value):
        return (await self.runAuthorizedGqlQuery_a(gm.WATCH_M['setEnableSlientTimeM'], { 'silentId': silentId, 'status': status }))['data']

    async def setEnableAlarmTime_a(self, alarmId, status: NormalStatus = NormalStatus.ENABLE.value):
        return (await self.runAuthorizedGqlQuery_a(gm.WATCH_M['modifyAlarmM'], { 'alarmId': alarmId, 'status': status }))['data']

    async def setReadChatMsg(self, ownId, msgId, id):
        return (await self.runAuthorizedGqlQuery_a(gm.WATCH_M['setReadChatMsgM'], { "uid": ownId, 'msgId': msgId, 'id': id }))['data']

########## SECTION MUTATION end ##########
