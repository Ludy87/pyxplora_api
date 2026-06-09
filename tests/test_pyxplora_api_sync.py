from __future__ import annotations

from pyxplora_api.const_version import VERSION, VERSION_APP
from pyxplora_api.pyxplora_api import PyXploraApi
from pyxplora_api.status import LocationType, NormalStatus, WatchOnlineStatus


class FakeGQLHandler:
    accessToken = "access-token"

    def __init__(self) -> None:
        self.locate_calls = []
        self.set_silent_calls = []
        self.set_alarm_calls = []

    def login(self):
        return {
            "token": "access-token",
            "id": "session-id",
            "user": {
                "id": "parent-id",
                "name": "Parent",
                "children": [
                    {"ward": {"id": "wuid-1", "phoneNumber": "111"}},
                    {"ward": {"id": "wuid-2", "phoneNumber": "222"}},
                ],
            },
        }

    def getAlarmTime(self, wuid):
        return {"alarms": [{"id": "alarm-1", "vendorId": "vendor", "name": "Wake", "occurMin": "450", "weekRepeat": "1111100", "status": "ENABLE"}]}

    def getWatchLastLocation(self, wuid):
        return {
            "watchLastLocate": {
                "tm": 1700000000,
                "lat": "52.5",
                "lng": "13.4",
                "rad": 25,
                "poi": "Park",
                "city": "Berlin",
                "province": "BE",
                "country": "DE",
                "locateType": "GPS",
                "isInSafeZone": True,
                "safeZoneLabel": "Home",
                "battery": 87,
                "isCharging": True,
            }
        }

    def askWatchLocate(self, wuid):
        self.locate_calls.append(wuid)
        return {"askWatchLocate": True}

    def trackWatch(self, wuid):
        return {"trackWatch": -1}

    def safeZones(self, wuid):
        return {"safeZones": [{"vendorId": "vendor", "groupName": "Family", "name": "Home", "lat": "52", "lng": "13", "rad": 100, "address": "Street"}]}

    def silentTimes(self, wuid):
        return {"silentTimes": [{"id": "silent-1", "vendorId": "vendor", "start": "480", "end": "540", "weekRepeat": "1111100", "status": "ENABLE"}]}

    def setEnableSilentTime(self, silent_id, status=NormalStatus.ENABLE.value):
        self.set_silent_calls.append((silent_id, status))
        return {"setEnableSilentTime": True}

    def setEnableAlarmTime(self, alarm_id, status):
        self.set_alarm_calls.append((alarm_id, status))
        return {"modifyAlarm": True}

    def getWatchUserContacts(self, wuid):
        return {
            "contacts": {
                "contacts": [
                    {
                        "guardianType": "FIRST",
                        "create": 0,
                        "update": 60,
                        "name": "Parent",
                        "countryPhoneNumber": "49",
                        "phoneNumber": "15123456789",
                        "contactUser": {"id": "parent-id", "xcoin": 99},
                    }
                ]
            }
        }

    def shutdown(self, wuid):
        return True

    def reboot(self, wuid):
        return True

    def getFollowRequestWatchCount(self):
        return {"followRequestWatchCount": 3}

    def getWatches(self, wuid):
        return {"watches": [{"swKey": "imei", "osVersion": "1.2.3", "qrCode": "code=qr", "groupName": "X5"}]}

    def getSWInfo(self, qr):
        return {"qr": qr, "version": "1.2.3"}

    def getWatchState(self, qrCode):
        return {"qrCode": qrCode, "state": "ok"}

    def getWatchUserSteps(self, wuid, tz, date):
        return {"userSteps": {"wuid": wuid, "tz": tz, "date": date, "steps": 42}}

    def addStep(self, step):
        return {"addStep": True}

    def submitIncorrectLocationData(self, wuid, lat, lng, timestamp):
        return {"submitIncorrectLocationData": True}

    def checkEmailOrPhoneExist(self, type, email, countryCode, phoneNumber):
        return {"checkEmailOrPhoneExist": True}

    def deleteMessageFromApp(self, wuid, msgId):
        return {"deleteMsg": True}

    def fetchChatVoice(self, wuid, msgId):
        return {"fetchChatVoice": b"voice"}


def make_api() -> PyXploraApi:
    api = PyXploraApi("49", "15123456789", "secret", "de-DE", "Europe/Berlin", childPhoneNumber=["222"])
    api._gql_handler = FakeGQLHandler()
    api.delay = lambda _seconds: None
    return api


def test_init_uses_login_token_and_filters_children(monkeypatch) -> None:
    api = make_api()
    monkeypatch.setattr(api, "initHandler", lambda signup: None)

    api.init()

    assert api.user["id"] == "parent-id"
    assert api.watchs == [{"ward": {"id": "wuid-2", "phoneNumber": "222"}}]


def test_version_combines_library_and_app_versions() -> None:
    assert PyXploraApi.version() == f"{VERSION}-{VERSION_APP}"


def test_watch_location_and_status_helpers_transform_gql_payload() -> None:
    api = make_api()

    location = api.loadWatchLocation("wuid-1")

    assert api._gql_handler.locate_calls == ["wuid-1"]
    assert location["lat"] == "52.5"
    assert location["locateType"] == "GPS"
    assert location["isInSafeZone"] is True
    assert location["watch_battery"] == 87
    assert api.getWatchBattery("wuid-1") == 87
    assert api.getWatchIsCharging("wuid-1") is True
    assert api.getWatchOnlineStatus("wuid-1") == WatchOnlineStatus.ONLINE.value
    assert api.getWatchLastLocation("wuid-1")["city"] == "Berlin"
    assert api.getWatchLocateType("unknown") in {"GPS", LocationType.UNKNOWN.value}


def test_alarm_safe_zone_and_silent_time_transforms() -> None:
    api = make_api()

    assert api.getWatchAlarm("wuid-1") == [
        {"id": "alarm-1", "vendorId": "vendor", "name": "Wake", "start": "07:30", "weekRepeat": "1111100", "status": "ENABLE"}
    ]
    assert api.getWatchSafeZones("wuid-1") == [
        {"vendorId": "vendor", "groupName": "Family", "name": "Home", "lat": "52", "lng": "13", "rad": 100, "address": "Street"}
    ]
    assert api.getSilentTime("wuid-1") == [
        {"id": "silent-1", "vendorId": "vendor", "start": "08:00", "end": "09:00", "weekRepeat": "1111100", "status": "ENABLE"}
    ]
    assert api.setEnableSilentTime("silent-1") is True
    assert api.setDisableSilentTime("silent-1") is True
    assert api._gql_handler.set_silent_calls == [("silent-1", "ENABLE"), ("silent-1", "DISABLE")]
    assert api.setEnableAlarmTime("alarm-1") is True
    assert api.setDisableAlarmTime("alarm-1") is True
    assert api._gql_handler.set_alarm_calls == [("alarm-1", "ENABLE"), ("alarm-1", "DISABLE")]


def test_admin_and_passthrough_helpers() -> None:
    api = make_api()
    api.user = {"id": "parent-id"}

    assert api.getWatchUserContacts("wuid-1")[0]["phoneNumber"] == "+4915123456789"
    assert api.isAdmin("wuid-1") is True
    assert api.shutdown("wuid-1") is True
    assert api.reboot("wuid-1") is True
    assert api.getFollowRequestWatchCount() == 3
    assert api.getWatches("wuid-1") == {"imei": "imei", "osVersion": "1.2.3", "qrCode": "code=qr", "model": "X5"}
    assert api.getSWInfo("wuid-1", {"qrCode": "code=qr"}) == {"qr": "qr", "version": "1.2.3"}
    assert api.getWatchState("wuid-1", {"qrCode": "code=qr"}) == {"qrCode": "qr", "state": "ok"}
    assert api.getWatchUserSteps("wuid-1", 1700000000) == {"wuid": "wuid-1", "tz": "Europe/Berlin", "date": 1700000000, "steps": 42}
    assert api.addStep(100) is True
    assert api.submitIncorrectLocationData("wuid-1", "52", "13", "1700000000") is True
    assert api.checkEmailOrPhoneExist(type="EMAIL", email="user@example.test") is True
    assert api.deleteMessageFromApp("wuid-1", "msg-1") is True
    assert api.get_chat_voice("wuid-1", "msg-1") == b"voice"
