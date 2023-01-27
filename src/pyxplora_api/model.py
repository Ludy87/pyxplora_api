from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from dataclasses_json import DataClassJsonMixin, dataclass_json

from .status import ChatType, Emoticon


@dataclass_json
@dataclass
class SmallChat(DataClassJsonMixin):
    msgId: str
    type: ChatType.__str__
    sender_id: str
    sender_name: str
    receiver_id: str
    receiver_name: str
    data_text: str
    data_sender_name: str
    create: str
    emoticon_id: Optional[Emoticon.__str__] = Emoticon.UNKNOWN__.value
    delete_flag: int = 0


@dataclass_json
@dataclass
class SmallChatList(DataClassJsonMixin):
    small_chat_list: list[SmallChat] = field(default_factory=list[SmallChat])


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
    delete_flag: Optional[int] = 0


@dataclass_json
@dataclass
class SimpleChat(DataClassJsonMixin):
    id: Optional[str]
    msgId: Optional[str]
    readFlag: Optional[int]
    sender: Optional[User]
    receiver: Optional[User]
    data: Optional[Data]
    create: Optional[int]
    type: Optional[ChatType.__str__] = ChatType.UNKNOWN__.value


@dataclass_json
@dataclass
class ChatsNew(DataClassJsonMixin):
    list: Optional[list[SimpleChat]] = field(default_factory=list[SimpleChat])


@dataclass_json
@dataclass
class Chats(DataClassJsonMixin):
    chatsNew: Optional[ChatsNew]
