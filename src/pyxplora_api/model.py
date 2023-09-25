from __future__ import annotations

from dataclasses import dataclass, field

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
    emoticon_id: Emoticon.__str__ | None = Emoticon.UNKNOWN__.value
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
    text: str | None = None
    Text: str | None = None
    battery: int | None = None
    poi: str | None = None
    city: str | None = None
    address: str | None = None
    province: str | None = None
    locate_type: str | None = None
    emoticon_id: Emoticon.__str__ | None = Emoticon.UNKNOWN__.value
    emoji_id: Emoticon.__str__ | None = Emoticon.UNKNOWN__.value
    call_name: str | None = None
    call_time: int | None = None
    call_type: int | None = None
    lat: float | None = None
    lng: float | None = None
    radius: int | None = None
    delete_flag: int | None = 0


@dataclass_json
@dataclass
class SimpleChat(DataClassJsonMixin):
    id: str | None
    msgId: str | None  # noqa: N815
    readFlag: int | None  # noqa: N815
    sender: User | None
    receiver: User | None
    data: Data | None
    create: int | None
    type: ChatType.__str__ | None = ChatType.UNKNOWN__.value


@dataclass_json
@dataclass
class ChatsNew(DataClassJsonMixin):
    list: list[SimpleChat] | None = field(default_factory=list[SimpleChat])


@dataclass_json
@dataclass
class Chats(DataClassJsonMixin):
    chatsNew: ChatsNew | None  # noqa: N815
