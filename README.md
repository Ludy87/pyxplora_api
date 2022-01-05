# pyxlpora_api

[![PyPI version](https://badge.fury.io/py/pyxplora-api.svg)](https://badge.fury.io/py/pyxplora-api)
[![GitHub issues](https://img.shields.io/github/issues/Ludy87/pyxplora_api)](https://github.com/Ludy87/pyxplora_api/issues)
[![GitHub forks](https://img.shields.io/github/forks/Ludy87/pyxplora_api)](https://github.com/Ludy87/pyxplora_api)
[![GitHub stars](https://img.shields.io/github/stars/Ludy87/pyxplora_api)](https://github.com/Ludy87/pyxplora_api)
[![GitHub license](https://img.shields.io/github/license/Ludy87/pyxplora_api)](https://github.com/Ludy87/pyxplora_api/blob/main/LICENSE)

Unofficial python library for the Xplora® API

Diese Projekt ist eine Übersetzung von TypeScript zu Python, mit Erweiterungen.
Ein dank geht an @MiGoller mit seinem Projekt [xplora-api.js](https://github.com/MiGoller/xplora-api.js)


# [Sample for beginning](https://github.com/Ludy87/pyxplora_api/tree/main/sample)

# Usage
```
from pyxplora_api import pyxplora_api as PXA

xplora = PXA.PyXploraApi(countryCode, phoneNummer, password, local, timeZone)
```

---
# Feature
---

```
# Watch Info
getContacts()
getUserID()
getUserName()
getUserIcon()
getUserXcoin()
getUserCurrentStep()
getUserTotalStep()
getUserCreate()
getUserUpdate()

# Watch Info
getWatchUserID()
getWatchUserName()
getWatchXcoin()
getWatchCurrentStep()
getWatchTotalStep()
getWatchAlarm()
getWatchBattery()
getWatchIsCharging()
getWatchOnlineStatus()
getWatchUnReadChatMsgCount()
getWatchChats()

# Watch Location Info
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

---
# Country Support

| Country Code | Country |
|-------------:|---------|
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

## Contacts

| sections | mode | type |
|----------|------|------|
| Contacts | read | list |

---
## Login Account

| sections | mode | type |
|----------|------|------|
| UID               | read | str |
| Username          | read | str |
| Icon              | read | str |
| Xcoin             | read | int |
| current Step      | read | int |
| total Step        | read/write | int |
| time of create    | read | str |
| time of update    | read | str |

---
## Watch

| sections | mode | type | comment |
|----------|------|------|---------|
| UID               | read | str |
| Name              | read | str |
| Xcoin             | read | int |
| current Step      | read | int |
| total Step        | read | int |
| Alarms            | read | list |
| Battery           | read | int |
| Charging          | read | bool |
| Online Status     | read | str |
| Unread Msg Count  | read | int | ?BUG? |
| Chats             | read | list | Don't all chats - confused |
| last locate       | read | dict |
| locate Type       | read | str | GPS/WiFi |
| locate now        | read | dict |
| is in Safezone    | read | bool |
| Safezone Lable    | read | str |
| Safezone          | read/write | list |
| track Interval    | read | int |
| ask Watch Locate  | read | bool |
| silents           | read | list | get all/enable/disable - enable all/disable all |
| sendText          | read | bool | sender: logged User |
| shutdown          | read | bool | only admins |
| reboot            | read | bool | only admins |