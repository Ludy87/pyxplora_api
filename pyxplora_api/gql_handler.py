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

    def runGqlQuery(self, query: str, variables):
        if query is None:
            raise Exception("GraphQL guery string MUST NOT be empty!")
        # Add Xplora® API headers
        requestHeaders = self.getRequestHeaders("application/json; charset=UTF-8")
        # create GQLClient
        gqlClient = GraphqlClient(endpoint=ENDPOINT, headers=requestHeaders)
        # execute QUERY|MUTATION
        data = gqlClient.execute(query=query, variables=variables)
        return data

    def runAuthorizedGqlQuery(self, query: str, variables):
        if self.accessToken is None:
            raise Exception("You have to login to the Xplora® API first.")
        # Run GraphQL query and return
        return self.runGqlQuery(query, variables)

    def login(self):
        data = self.runGqlQuery(gm.SIGN_M["issueTokenM"], self.variables)['data']
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

    def getMyInfo(self):
        # Profil from login Account
        return self.runAuthorizedGqlQuery(gq.MYINFO_Q['readQ'], {})['data']

    def getContacts(self, ownId):
        # Contacts from ownUser
        return self.runAuthorizedGqlQuery(gq.WATCH_Q['contactsQ'], { "uid": ownId })['data']

    def getWatchCount(self):
        return self.runAuthorizedGqlQuery(gq.QUERY['followRequestWatchCountQ'], {})['data']

    def getWatches(self, ownId):
        return self.runAuthorizedGqlQuery(gq.WATCH_Q['watchesQ'], { "uid": ownId })['data']

    def getWatchLastLocation(self, ownId):
        return self.runAuthorizedGqlQuery(gq.WATCH_Q['locateQ'], { "uid": ownId })['data']

    def trackWatch(self, ownId):
        # tracking time - seconds
        res = self.runAuthorizedGqlQuery(gq.WATCH_Q['trackQ'], { "uid": ownId })['data']
        if res['trackWatch'] is not None:
            return res
        return { 'trackWatch': -1 }

    def askWatchLocate(self, ownId):
        res = self.runAuthorizedGqlQuery(gq.WATCH_Q['askLocateQ'], { "uid": ownId })['data']
        if res['askWatchLocate'] is not None:
            return res
        return { 'askWatchLocate': False }

    def getAlarms(self, ownId):
        return self.runAuthorizedGqlQuery(gq.WATCH_Q['alarmsQ'], { "uid": ownId })['data']

    def getWifi(self, id):
        # without function?
        return self.runAuthorizedGqlQuery(gq.WATCH_Q['getWifisQ'], { "uid": id })['data']

    def avatars(self, id):
        # without function?
        return self.runAuthorizedGqlQuery(gq.CAMPAIGN_Q['avatarsQ'], { 'id': id })['data']

    def unReadChatMsgCount(self, ownId):
        return self.runAuthorizedGqlQuery(gq.WATCH_Q['unReadChatMsgCountQ'], { 'uid': ownId })['data']

    def chats(self, ownId):
        # ownUser id
        return self.runAuthorizedGqlQuery(gq.WATCH_Q['chatsQ'], { 'uid': ownId })['data']

    def staticCard(self):
        return self.runAuthorizedGqlQuery(gq.CARD_Q['staticQ'], {})['data']

    def campaignUserProfiles(self):
        return self.runAuthorizedGqlQuery(gq.MYINFO_Q['campaignUserProfilesQ'], {})['data']

    def subscribedCampaign(self, id, needDetail=False):
        return self.runAuthorizedGqlQuery(gq.CAMPAIGN_Q['subscribedQ'], { 'uid': id, 'needDetail': needDetail })['data']

    def getReviewStatus(self, id):
        return self.runAuthorizedGqlQuery(gq.REVIEW_Q['getStatusQ'], { 'uid': id })['data']

    def countries(self):
        # Country Support
        return self.runAuthorizedGqlQuery(gq.UTILS_Q['countriesQ'], {})['data']

    def safeZones(self, ownId):
        return self.runAuthorizedGqlQuery(gq.WATCH_Q['safeZonesQ'], { 'uid': ownId })['data']

    def safeZoneGroups(self):
        return self.runAuthorizedGqlQuery(gq.WATCH_Q['safeZoneGroupsQ'], {})['data']

    def silentTimes(self, ownId):
        return self.runAuthorizedGqlQuery(gq.WATCH_Q['silentTimesQ'], { 'uid': ownId })['data']

########## SECTION QUERY end ##########

########## SECTION MUTATION start ##########

    def sendText(self, ownId, text):
        # ownUser id
        if self.runAuthorizedGqlQuery(gm.WATCH_M['sendChatTextM'], { "uid": ownId, "text": text })['data']['sendChatText'] is not None:
            return True
        return False

    def addStep(self, stepCount):
        return self.runAuthorizedGqlQuery(gm.STEP_M['addM'], { "stepCount": stepCount })['data']

    def shutdown(self, ownId):
        # ownUser id
        return self.isAdmin(ownId, gm.WATCH_M['shutdownM'], { "uid": ownId }, 'reboot')

    def reboot(self, ownId):
        # ownUser id
        return self.isAdmin(ownId, gm.WATCH_M['rebootM'], { "uid": ownId }, 'reboot')

    def modifyAlert(self, id, yesOrNo: YesOrNo):
        # function?
        return self.runAuthorizedGqlQuery(gm.WATCH_M['modifyAlertM'], { "uid": id, "remind": yesOrNo })

    def setEnableSlientTime(self, silentId, status: NormalStatus = NormalStatus.ENABLE.value):
        return self.runAuthorizedGqlQuery(gm.WATCH_M['setEnableSlientTimeM'], { 'silentId': silentId, 'status': status })['data']

    def setEnableAlarmTime(self, alarmId, status: NormalStatus = NormalStatus.ENABLE.value):
        return self.runAuthorizedGqlQuery(gm.WATCH_M['modifyAlarmM'], { 'alarmId': alarmId, 'status': status })['data']

    def setReadChatMsg(self, ownId, msgId, id):
        return self.runAuthorizedGqlQuery(gm.WATCH_M['setReadChatMsgM'], { "uid": ownId, 'msgId': msgId, 'id': id })['data']

########## SECTION MUTATION end ##########
