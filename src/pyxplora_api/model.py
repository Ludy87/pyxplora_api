from __future__ import annotations

from dataclasses import dataclass
from typing_extensions import NotRequired
from dataclasses_json import DataClassJsonMixin, dataclass_json
from typing import Optional

from .status import ChatType, Emoticon


@dataclass_json
@dataclass
class User(DataClassJsonMixin):
    id: str
    userId: str
    name: str
    phoneNumber: str


@dataclass_json
@dataclass
class Data(DataClassJsonMixin):
    tm: int
    text: str
    sender_name: str
    battery: Optional[int] = None
    poi: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    province: Optional[str] = None
    locate_type: Optional[str] = None
    emoticon_id: Optional[Emoticon.__str__] = Emoticon.UNKNOWN__.value
    call_name: Optional[str] = None
    call_time: Optional[int] = None
    call_type: Optional[int] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    radius: Optional[int] = None


@dataclass_json
@dataclass
class SimpleChat(DataClassJsonMixin):
    id: str
    msgId: str
    readFlag: int
    type: ChatType.__str__
    sender: User
    receiver: User
    data: Data
    create: int


@dataclass_json
@dataclass
class ChatsNew(DataClassJsonMixin):
    list: list[SimpleChat]


@dataclass_json
@dataclass
class Chats(DataClassJsonMixin):
    chatsNew: ChatsNew
