# pyxlpora_api

[![PyPI version](https://badge.fury.io/py/pyxplora-api.svg)](https://badge.fury.io/py/pyxplora-api)

Unofficial python library for the Xplora API

Diese Projekt ist eine Übersetzung von TypeScript zu Python, mit Erweiterungen.
Ein dank geht an @MiGoller mit seinem Projekt [xplora-api.js](https://github.com/MiGoller/xplora-api.js)


# [Sample for beginning](https://github.com/Ludy87/pyxplora_api/tree/main/sample)

# Usage
---
```
from pyxplora_api import pyxplora_api as PXA

xplora = PXA.PyXploraApi(countryCode, phoneNummer, password, local, timeZone)
```

# Feature
---

```
# Watch Info
getContacts()
getUserName()
getUserIcon()
getUserXcoin()
getUserCurrentStep()
getUserTotalStep()
getUserCreate()
getUserUpdate()

# Watch Location Info
getWatchCurrentStep()
getWatchTotalStep()
getWatchAlarm()
getWatchUserID()
getWatchUserName()
getWatchXcoin()
getWatchBattery()
getWatchIsCharging()
getWatchOnlineStatus()
getWatchUnReadChatMsgCount()
getWatchChats()
getWatchLastLocation()
getWatchLocateType()
getWatchLocate()
getWatchIsInSafeZone()
getWatchSafeZoneLabel()
getSafeZones()
trackWatchInterval()
askWatchLocate()

# Feature
schoolSilentMode()
setEnableSilentTime()
setDisableSilentTime()
setAllEnableSilentTime()
setAllDisableSilentTime()

sentText()
shutdown()
reboot()
```

# Country Support
---

| CountryCode | Country |
|-------------|---------|
| 44 | United Kingdom |
| 34 | Spain |
| 49 | Germany |
| 47 | Norway |
| 46 | Sweden |
| 358 | Finland |
| 33 | France |
| 39 | Italy |
| 41 | Switzerland |
| 43 | Austria |

# Functions
---

## Login Account

| sections | mode | type |
|----------|------|------|
| Username          | read | string |
| Icon              | read | string |
| Xcoin             | read | int |
| current Step      | read | int |
| total Step        | read/write | int |
| time of create    | read | string |
| time of update    | read | string |

---
## Watch

| sections | mode | type | comment |
|----------|------|------|---------|
| current Step      | read | int |
| total Step        | read | int |
| Alarms            | read | list |
| UID               | read | string |
| Name              | read | string |
| Xcoin             | read | int |
| Battery           | read | int |
| Charging          | read | bool |
| Unread Msg Count  | read | int | ?BUG? |
| Chats             | read | list | Don't all chats |
| locate Type       | read | string | GPS/WiFi |
| locate            | read | dict |
| is in Safezone    | read | bool |
| Safezone Lable    | read | string |
| Safezone          | read/write | list |
| track Interval    | read | list |
| ask Watch Locate  | read | bool |
| silent Mode       | read | list |
| sendText          | read | bool |
| shutdown          | read | bool | only admins |
| reboot            | read | bool | only admins |