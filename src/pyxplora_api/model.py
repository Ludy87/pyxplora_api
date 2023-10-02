from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union

from dataclasses_json import DataClassJsonMixin, dataclass_json

from .status import ChatType, Emoticon


@dataclass_json
@dataclass
class SmallChat(DataClassJsonMixin):
    msgId: str  # noqa: N815
    type: ChatType.__str__
    sender_id: str
    sender_name: str
    receiver_id: str
    receiver_name: str
    data_text: str
    data_sender_name: str
    create: str
    emoticon_id: Union[Emoticon.__str__, None] = Emoticon.UNKNOWN__.value
    delete_flag: int = 0


@dataclass_json
@dataclass
class SmallChatList(DataClassJsonMixin):
    small_chat_list: list[SmallChat] = field(default_factory=list[SmallChat])


@dataclass_json
@dataclass
class User(DataClassJsonMixin):
    id: str
    userId: str  # noqa: N815
    name: str
    phoneNumber: str  # noqa: N815


@dataclass_json
@dataclass
class Data(DataClassJsonMixin):
    tm: int
    sender_name: str
    text: Union[str, None] = None
    Text: Union[str, None] = None
    battery: Union[int, None] = None
    poi: Union[str, None] = None
    city: Union[str, None] = None
    address: Union[str, None] = None
    province: Union[str, None] = None
    locate_type: Union[str, None] = None
    emoticon_id: Union[Emoticon.__str__, None] = Emoticon.UNKNOWN__.value
    emoji_id: Union[Emoticon.__str__, None] = Emoticon.UNKNOWN__.value
    call_name: Union[str, None] = None
    call_time: Union[int, None] = None
    call_type: Union[int, None] = None
    lat: Union[float, None] = None
    lng: Union[float, None] = None
    radius: Union[int, None] = None
    delete_flag: Union[int, None] = 0


@dataclass_json
@dataclass
class SimpleChat(DataClassJsonMixin):
    id: Union[str, None]
    msgId: Union[str, None]  # noqa: N815
    readFlag: Union[int, None]  # noqa: N815
    sender: Union[User, None]
    receiver: Union[User, None]
    data: Union[Data, None]
    create: Union[int, None]
    type: Union[ChatType.__str__, None] = ChatType.UNKNOWN__.value


@dataclass_json
@dataclass
class ChatsNew(DataClassJsonMixin):
    list: Union[list[SimpleChat], None] = field(default_factory=list[SimpleChat])


@dataclass_json
@dataclass
class Chats(DataClassJsonMixin):
    chatsNew: Union[ChatsNew, None]  # noqa: N815
