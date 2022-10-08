# pyxlpora_api

[![PyPI version](https://badge.fury.io/py/pyxplora-api.svg)](https://badge.fury.io/py/pyxplora-api) [![Downloads](https://pepy.tech/badge/pyxplora-api)](https://pepy.tech/project/pyxplora-api) [![Downloads](https://pepy.tech/badge/pyxplora-api/month)](https://pepy.tech/project/pyxplora-api) [![Downloads](https://pepy.tech/badge/pyxplora-api/week)](https://pepy.tech/project/pyxplora-api)

[![GitHub issues](https://img.shields.io/github/issues/Ludy87/pyxplora_api?style=for-the-badge&logo=appveyor)](https://github.com/Ludy87/pyxplora_api/issues)
[![GitHub forks](https://img.shields.io/github/forks/Ludy87/pyxplora_api?style=for-the-badge&logo=appveyor)](https://github.com/Ludy87/pyxplora_api)
[![GitHub stars](https://img.shields.io/github/stars/Ludy87/pyxplora_api?style=for-the-badge&logo=appveyor)](https://github.com/Ludy87/pyxplora_api)
[![GitHub license](https://img.shields.io/github/license/Ludy87/pyxplora_api?style=for-the-badge&logo=appveyor)](https://github.com/Ludy87/pyxplora_api/blob/main/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge&logo=appveyor)](https://github.com/psf/black)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/Ludy87/pyxplora_api.svg?logo=lgtm&logoWidth=18&style=for-the-badge)](https://lgtm.com/projects/g/Ludy87/pyxplora_api/alerts/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/Ludy87/pyxplora_api.svg?logo=lgtm&logoWidth=18&style=for-the-badge)](https://lgtm.com/projects/g/Ludy87/pyxplora_api/context:python)

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/ludy87)

[![✨ Wishlist from Amazon ✨](https://www.astra-g.org/wp-content/uploads/2022/09/amazon_wish.png)](https://smile.amazon.de/registry/wishlist/2MX8QK8VE9MV1)

---
Unofficial python library for the Xplora® API

Diese Projekt ist eine Übersetzung von TypeScript zu Python, mit Erweiterungen.
Ein dank geht an @MiGoller mit seinem Projekt [xplora-api.js](https://github.com/MiGoller/xplora-api.js)

## [Sample for beginning](https://github.com/Ludy87/pyxplora_api/tree/main/sample)

## Usage

```python
from pyxplora_api import pyxplora_api as PXA

xplora = PXA.PyXploraApi(countryCode, phoneNummer, password, local, timeZone[, childPhoneNumber])
```

---

## User Info

| Function             | Result Type | Return              |
| -------------------- | ----------- | ------------------- |
| getUserID()          | str:        |
| getUserName()        | str:        |
| getUserIcon()        | str:        | Url                 |
| getUserXcoin()       | int:        |
| getUserCurrentStep() | int:        |
| getUserTotalStep()   | int:        |
| getUserCreate()      | str:        | 2021-12-31 23:59:59 |
| getUserUpdate()      | str:        | 2022-01-01 00:00:01 |

## Watch User Info

| Function                                                             | Result Type           | Change Ver. |
| -------------------------------------------------------------------- | --------------------- | ----------- |
| getWatchUserIDs(child_no: list[str] = [])                            | list[str]:            |
| getWatchUserPhoneNumbers(wuid: None, ignoreError: bool = False)      | list[str]:            | 2.1.1       |
| getWatchUserPhoneNumbers(wuid: str, ignoreError: bool = False)       | list[str]:            | 2.1.1       |
| getWatchUserPhoneNumbers(wuid: list[str], ignoreError: bool = False) | list[str]:            |
| getWatchUserNames(None)                                              | list[str]:            | 2.1.1       |
| getWatchUserNames(wuid: str)                                         | list[str]:            | 2.1.1       |
| getWatchUserNames(wuid: list[str])                                   | list[str]:            |
| getWatchUserIcons(None)                                              | list[str]:            | 2.1.1       |
| getWatchUserIcons(wuid: str)                                         | list[str]:            | 2.1.1       |
| getWatchUserIcons(wuid: list[str])                                   | list[str]:            |
| getWatchUserXcoins(None)                                             | list[str]:            | 2.1.1       |
| getWatchUserXcoins(wuid: str)                                        | list[str]:            | 2.1.1       |
| getWatchUserXcoins(wuid: list[str])                                  | list[int]:            |
| getWatchUserCurrentStep(None)                                        | list[str]:            | 2.1.1       |
| getWatchUserCurrentStep(wuid: str)                                   | list[str]:            | 2.1.1       |
| getWatchUserCurrentStep(wuid: list[str])                             | list[int]:            |
| getWatchUserTotalStep(None)                                          | list[str]:            | 2.1.1       |
| getWatchUserTotalStep(wuid: str)                                     | list[str]:            | 2.1.1       |
| getWatchUserTotalStep(wuid: list[str])                               | list[int]:            |
| getWatchUserSteps(wuid: str, date: int)                              | dict[str, any]:       |
| getWatchUserContacts(wuid: str)                                      | list[dict[str, any]]: |

## Watch Info

| Function                              | Result Type           |
| ------------------------------------- | --------------------- |
| getWatchAlarm(wuid: str)              | list[dict[str, any]]: |
| getWatchBattery(wuid: str)            | int:                  |
| getWatchIsCharging(wuid: str)         | bool:                 |
| getWatchOnlineStatus(wuid: str)       | str:                  |
| getWatchUnReadChatMsgCount(wuid: str) | int:                  |
| getWatchChats(wuid: str)              | list[dict[str, any]]: |

## Watch Location Info

| Function                                                      | Result Type           | Retrun        |
| ------------------------------------------------------------- | --------------------- | ------------- |
| getWatchLastLocation(wuid: str, withAsk: bool = False)        | dict[str, any]:       |
| getWatchLocate(wuid: str)                                     | dict[str, any]:       |
| getWatchLocateType(wuid: str)                                 | str:                  | GPS/WIFI/CELL |
| getWatchSafeZones(wuid: str)                                  | list[dict[str, any]]: |
| getWatchIsInSafeZone(wuid: str)                               | bool:                 |
| getWatchSafeZoneLabel(wuid: str)                              | str:                  |
| getWatchLocHistory(wuid: str, date: int, tz: str, limit: int) | dict[str, any]:       |
| getTrackWatchInterval(wuid: str)                              | int:                  | 60            |
| askWatchLocate(wuid: str)                                     | bool:                 |
| getStartTrackingWatch(wuid: str)                              | int:                  | 1800          |
| getEndTrackingWatch(wuid: str)                                | int:                  | 1             |

## Watch Silent Mode

| Function                            | Result Type           | Change Ver. |
| ----------------------------------- | --------------------- | ----------- |
| getSilentTime(wuid: str)            | list[dict[str, any]]: |
| setEnableSilentTime(silentId: str)  | bool:                 | 2.1.1       |
| setDisableSilentTime(silentId: str) | bool:                 | 2.1.1       |
| setAllEnableSilentTime(wuid: str)   | list[bool]:           |
| setAllDisableSilentTime(wuid: str)  | list[bool]:           |

## Watch Alarm

| Function                          | Result Type     | Change Ver. |
| --------------------------------- | --------------- | ----------- |
| getAlarmTime(wuid: str)           | dict[str, any]: |
| setEnableAlarmTime(alarmId: str)  | bool:           | 2.1.1       |
| setDisableAlarmTime(alarmId: str) | bool:           | 2.1.1       |
| setAllEnableAlarmTime(wuid: str)  | list[bool]:     |
| setAllDisableAlarmTime(wuid: str) | list[bool]:     |

## Chat Fetch

| Function                                              | Result Type     |
| ----------------------------------------------------- | --------------- |
| chats(wuid: str, offset: int, limit: int, msgId: str) | dict[str, any]: |
| fetchChatImage(wuid: str, msgId: str)                 | dict[str, any]: |
| fetchChatMp3(wuid: str, msgId: str)                   | dict[str, any]: |
| fetchChatShortVideo(wuid: str, msgId: str)            | dict[str, any]: |
| fetchChatShortVideoCover(wuid: str, msgId: str)       | dict[str, any]: |
| fetchChatVoice(wuid: str, msgId: str)                 | dict[str, any]: |

## Feature

| Function                       | Result Type |
| ------------------------------ | ----------- |
| sendText(text: str, wuid: str) | bool:       |
| isAdmin(wuid: str)             | bool:       |
| shutdown(wuid: str)            | bool:       |
| reboot(wuid: str)              | bool:       |
| addStep(step: int)             | bool:       |

| Function                                                                   | Result Type           |
| -------------------------------------------------------------------------- | --------------------- |
| getFollowRequestWatchCount()                                               | int:                  |
| getWatches(wuid: str)                                                      | list[dict[str, any]]: |
| getSWInfo(wuid: str)                                                       | dict[str, any]:       |
| getWatchState(wuid: str)                                                   | dict[str, any]:       |
| conv360IDToO2OID(qid: str, deviceId: str)                                  | dict[str, any]:       |
| campaigns(id: str, categoryId: str)                                        | dict[str, any]:       |
| getCountries()                                                             | list[dict[str, str]]: |
| watchesDynamic()                                                           | dict[str, any]:       |
| watchGroups(id: str = "")                                                  | dict[str, any]:       |
| familyInfo(wuid: str, watchId: str, tz: str, date: int)                    | dict[str, any]:       |
| avatars(id: str)                                                           | dict[str, any]:       |
| submitIncorrectLocationData(wuid: str, lat: str, lng: str, timestamp: str) | bool                  |
| getAppVersion()                                                            | dict[str, any]:       |

---

## Country Support

| country name                                 | country code |
| -------------------------------------------- | ------------ |
| Afghanistan                                  | 93           |
| Albania                                      | 355          |
| Algeria                                      | 213          |
| AmericanSamoa                                | 1 684        |
| Andorra                                      | 376          |
| Angola                                       | 244          |
| Anguilla                                     | 1 264        |
| Antarctica                                   | 672          |
| Antigua and Barbuda                          | 1268         |
| Argentina                                    | 54           |
| Armenia                                      | 374          |
| Aruba                                        | 297          |
| Australia                                    | 61           |
| Austria                                      | 43           |
| Azerbaijan                                   | 994          |
| Bahamas                                      | 1 242        |
| Bahrain                                      | 973          |
| Bangladesh                                   | 880          |
| Barbados                                     | 1 246        |
| Belarus                                      | 375          |
| Belgium                                      | 32           |
| Belize                                       | 501          |
| Benin                                        | 229          |
| Bermuda                                      | 1 441        |
| Bhutan                                       | 975          |
| Bolivia, Plurinational State of              | 591          |
| Bosnia and Herzegovina                       | 387          |
| Botswana                                     | 267          |
| Brazil                                       | 55           |
| British Indian Ocean Territory               | 246          |
| Brunei Darussalam                            | 673          |
| Bulgaria                                     | 359          |
| Burkina Faso                                 | 226          |
| Burundi                                      | 257          |
| Cambodia                                     | 855          |
| Cameroon                                     | 237          |
| Canada                                       | 1            |
| Cape Verde                                   | 238          |
| Cayman Islands                               | 345          |
| Central African Republic                     | 236          |
| Chad                                         | 235          |
| Chile                                        | 56           |
| China                                        | 86           |
| Christmas Island                             | 61           |
| Cocos (Keeling) Islands                      | 61           |
| Colombia                                     | 57           |
| Comoros                                      | 269          |
| Congo                                        | 242          |
| Congo, The Democratic Republic of the        | 243          |
| Cook Islands                                 | 682          |
| Costa Rica                                   | 506          |
| Cote d'Ivoire                                | 225          |
| Croatia                                      | 385          |
| Cuba                                         | 53           |
| Cyprus                                       | 357          |
| Czech Republic                               | 420          |
| Denmark                                      | 45           |
| Djibouti                                     | 253          |
| Dominica                                     | 1 767        |
| Dominican Republic                           | 1 849        |
| Ecuador                                      | 593          |
| Egypt                                        | 20           |
| El Salvador                                  | 503          |
| Equatorial Guinea                            | 240          |
| Eritrea                                      | 291          |
| Estonia                                      | 372          |
| Ethiopia                                     | 251          |
| Falkland Islands (Malvinas)                  | 500          |
| Faroe Islands                                | 298          |
| Fiji                                         | 679          |
| Finland                                      | 358          |
| France                                       | 33           |
| French Guiana                                | 594          |
| French Polynesia                             | 689          |
| Gabon                                        | 241          |
| Gambia                                       | 220          |
| Georgia                                      | 995          |
| Germany                                      | 49           |
| Ghana                                        | 233          |
| Gibraltar                                    | 350          |
| Greece                                       | 30           |
| Greenland                                    | 299          |
| Grenada                                      | 1 473        |
| Guadeloupe                                   | 590          |
| Guam                                         | 1 671        |
| Guatemala                                    | 502          |
| Guernsey                                     | 44           |
| Guinea                                       | 224          |
| Guinea-Bissau                                | 245          |
| Guyana                                       | 595          |
| Haiti                                        | 509          |
| Holy See (Vatican City State)                | 379          |
| Honduras                                     | 504          |
| Hong Kong                                    | 852          |
| Hungary                                      | 36           |
| Iceland                                      | 354          |
| India                                        | 91           |
| Indonesia                                    | 62           |
| Iran, Islamic Republic of                    | 98           |
| Iraq                                         | 964          |
| Ireland                                      | 353          |
| Isle of Man                                  | 44           |
| Israel                                       | 972          |
| Italy                                        | 39           |
| Jamaica                                      | 1 876        |
| Japan                                        | 81           |
| Jersey                                       | 44           |
| Jordan                                       | 962          |
| Kazakhstan                                   | 7 7          |
| Kenya                                        | 254          |
| Kiribati                                     | 686          |
| Korea, Democratic People's Republic of       | 850          |
| Korea, Republic of                           | 82           |
| Kuwait                                       | 965          |
| Kosovo                                       | 383          |
| Kyrgyzstan                                   | 996          |
| Lao People's Democratic Republic             | 856          |
| Latvia                                       | 371          |
| Lebanon                                      | 961          |
| Lesotho                                      | 266          |
| Liberia                                      | 231          |
| Libyan Arab Jamahiriya                       | 218          |
| Liechtenstein                                | 423          |
| Lithuania                                    | 370          |
| Luxembourg                                   | 352          |
| Macao                                        | 853          |
| Macedonia, The Former Yugoslav Republic of   | 389          |
| Madagascar                                   | 261          |
| Malawi                                       | 265          |
| Malaysia                                     | 60           |
| Maldives                                     | 960          |
| Mali                                         | 223          |
| Malta                                        | 356          |
| Marshall Islands                             | 692          |
| Martinique                                   | 596          |
| Mauritania                                   | 222          |
| Mauritius                                    | 230          |
| Mayotte                                      | 262          |
| Mexico                                       | 52           |
| Micronesia, Federated States of              | 691          |
| Moldova, Republic of                         | 373          |
| Monaco                                       | 377          |
| Mongolia                                     | 976          |
| Montenegro                                   | 382          |
| Montserrat                                   | 1664         |
| Morocco                                      | 212          |
| Mozambique                                   | 258          |
| Myanmar                                      | 95           |
| Namibia                                      | 264          |
| Nauru                                        | 674          |
| Nepal                                        | 977          |
| Netherlands                                  | 31           |
| Netherlands Antilles                         | 599          |
| New Caledonia                                | 687          |
| New Zealand                                  | 64           |
| Nicaragua                                    | 505          |
| Niger                                        | 227          |
| Nigeria                                      | 234          |
| Niue                                         | 683          |
| Norfolk Island                               | 672          |
| Northern Mariana Islands                     | 1 670        |
| Norway                                       | 47           |
| Oman                                         | 968          |
| Pakistan                                     | 92           |
| Palau                                        | 680          |
| Palestinian Territory, Occupied              | 970          |
| Panama                                       | 507          |
| Papua New Guinea                             | 675          |
| Paraguay                                     | 595          |
| Peru                                         | 51           |
| Philippines                                  | 63           |
| Pitcairn                                     | 872          |
| Poland                                       | 48           |
| Portugal                                     | 351          |
| Puerto Rico                                  | 1 939        |
| Qatar                                        | 974          |
| Romania                                      | 40           |
| Russia                                       | 7            |
| Rwanda                                       | 250          |
| Réunion                                      | 262          |
| Saint Barthélemy                             | 590          |
| Saint Helena, Ascension and Tristan Da Cunha | 290          |
| Saint Kitts and Nevis                        | 1 869        |
| Saint Lucia                                  | 1 758        |
| Saint Martin                                 | 590          |
| Saint Pierre and Miquelon                    | 508          |
| Saint Vincent and the Grenadines             | 1 784        |
| Samoa                                        | 685          |
| San Marino                                   | 378          |
| Sao Tome and Principe                        | 239          |
| Saudi Arabia                                 | 966          |
| Senegal                                      | 221          |
| Serbia                                       | 381          |
| Seychelles                                   | 248          |
| Sierra Leone                                 | 232          |
| Singapore                                    | 65           |
| Slovakia                                     | 421          |
| Slovenia                                     | 386          |
| Solomon Islands                              | 677          |
| Somalia                                      | 252          |
| South Africa                                 | 27           |
| South Georgia and the South Sandwich Islands | 500          |
| Spain                                        | 34           |
| Sri Lanka                                    | 94           |
| Sudan                                        | 249          |
| Suriname                                     | 597          |
| Svalbard and Jan Mayen                       | 47           |
| Swaziland                                    | 268          |
| Sweden                                       | 46           |
| Switzerland                                  | 41           |
| Syrian Arab Republic                         | 963          |
| Taiwan, Province of China                    | 886          |
| Tajikistan                                   | 992          |
| Tanzania, United Republic of                 | 255          |
| Thailand                                     | 66           |
| Timor-Leste                                  | 670          |
| Togo                                         | 228          |
| Tokelau                                      | 690          |
| Tonga                                        | 676          |
| Trinidad and Tobago                          | 1 868        |
| Tunisia                                      | 216          |
| Turkey                                       | 90           |
| Turkmenistan                                 | 993          |
| Turks and Caicos Islands                     | 1 649        |
| Tuvalu                                       | 688          |
| Uganda                                       | 256          |
| Ukraine                                      | 380          |
| United Arab Emirates                         | 971          |
| United Kingdom                               | 44           |
| United States                                | 1            |
| Uruguay                                      | 598          |
| Uzbekistan                                   | 998          |
| Vanuatu                                      | 678          |
| Venezuela, Bolivarian Republic of            | 58           |
| Viet Nam                                     | 84           |
| Virgin Islands, British                      | 1284         |
| Virgin Islands, U.S.                         | 1340         |
| Wallis and Futuna                            | 681          |
| Yemen                                        | 967          |
| Zambia                                       | 260          |
| Zimbabwe                                     | 263          |
| Åland Islands                                | 358          |

## Functions

---

## Contacts

| sections | mode | type |
| -------- | ---- | ---- |
| Contacts | read | list |

---

## Login Account

| sections       | mode       | type |
| -------------- | ---------- | ---- |
| UID            | read       | str  |
| Username       | read       | str  |
| Icon           | read       | str  |
| Xcoin          | read       | int  |
| current Step   | read       | int  |
| total Step     | read/write | int  |
| time of create | read       | str  |
| time of update | read       | str  |

---

## Watch

| sections         | mode       | type | comment                                         |
| ---------------- | ---------- | ---- | ----------------------------------------------- |
| UID              | read       | str  |
| Name             | read       | str  |
| Xcoin            | read       | int  |
| current Step     | read       | int  |
| total Step       | read       | int  |
| Alarms           | read       | list | get all/enable/disable - enable all/disable all |
| Battery          | read       | int  |
| Charging         | read       | bool |
| Online Status    | read       | str  |
| Unread Msg Count | read       | int  | ?BUG? Result is always 0                        |
| Chats            | read       | list | Don't all chats - confused                      |
| last locate      | read       | dict |
| locate Type      | read       | str  | GPS/WIFI/CELL                                   |
| locate now       | read       | dict |
| is in Safezone   | read       | bool |
| Safezone Lable   | read       | str  |
| Safezone         | read/write | list |
| track Interval   | read       | int  |
| ask Watch Locate | read       | bool |
| silents          | read       | list | get all/enable/disable - enable all/disable all |
| sendText         | read       | bool | sender: logged User                             |
| shutdown         | read       | bool | only admins                                     |
| reboot           | read       | bool | only admins                                     |
