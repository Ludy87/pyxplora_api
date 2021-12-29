# pyxlpora_api

[![PyPI version](https://badge.fury.io/py/pyxplora-api.svg)](https://badge.fury.io/py/pyxplora-api)

Unofficial python library for the Xplora API

Diese Projekt ist eine Übersetzung von TypeScript zu Python, mit Erweiterungen.
Ein dank geht an @MiGoller mit seinem Projekt [xplora-api.js](https://github.com/MiGoller/xplora-api.js)


# [Sample for beginning](https://github.com/Ludy87/pyxplora_api/tree/main/sample)


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

| sections | mode | type |
|----------|------|------|
| current Step      | read | int |
| total Step        | read | int |
| Alarm             | read | list |
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
| shutdown          | read | bool | admin |
| reboot            | read | bool | admin |