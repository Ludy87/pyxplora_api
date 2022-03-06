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
```python
from pyxplora_api import pyxplora_api as PXA

xplora = PXA.PyXploraApi(countryCode, phoneNummer, password, local, timeZone)
```

---
# Feature
---

```python
# Watch Info
getUserID()
getUserName()
getUserIcon()
getUserXcoin()
getUserCurrentStep()
getUserTotalStep()
getUserCreate()
getUserUpdate()

# Watch Info
id:list = getWatchUserID()
getContacts(watchID=id)
getWatchUserName(watchID=id)
getWatchXcoin(watchID=id)
getWatchCurrentStep(watchID=id)
getWatchTotalStep(watchID=id)
getWatchAlarm(watchID=id)
getWatchBattery(watchID=id)
getWatchIsCharging(watchID=id)
getWatchOnlineStatus(watchID=id)
getWatchUnReadChatMsgCount(watchID=id)
getWatchChats(watchID=id)

# Watch Location Info
getWatchLastLocation(watchID=id)
getWatchLocateType(watchID=id)
getWatchLocate(watchID=id)
getWatchIsInSafeZone(watchID=id)
getWatchSafeZoneLabel(watchID=id)
getSafeZones(watchID=id)
trackWatchInterval(watchID=id)
askWatchLocate(watchID=id)

# Feature
schoolSilentMode(watchID=id)
setEnableSilentTime(silentId='', watchID=id)
setDisableSilentTime(silentId='', watchID=id)
setAllEnableSilentTime(watchID=id)
setAllDisableSilentTime(watchID=id)

sentText(text='', watchID=id)
shutdown(watchID=id)
reboot(watchID=id)
```

---
# Country Support

| Country Code | Country |
|-------------:|---------|
| 45 | Denmark |
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