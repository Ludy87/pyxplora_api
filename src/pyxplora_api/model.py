from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union

from dataclasses_json import DataClassJsonMixin, config, dataclass_json

from .status import ChatType, Emoticon


def int_or_none(value):
    """Convert the given value to an integer, or return None if the value is invalid."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


@dataclass_json
@dataclass
class SmallChat(DataClassJsonMixin):
    msgId: Union[str, None] = None  # noqa: N815
    type: Union[str, None] = ChatType.UNKNOWN__.value
    sender_id: Union[str, None] = None
    sender_name: Union[str, None] = None
    receiver_id: Union[str, None] = None
    receiver_name: Union[str, None] = None
    data_text: Union[str, None] = None
    data_sender_name: Union[str, None] = None
    create: Union[str, None] = None
    emoticon_id: Union[str, None] = Emoticon.UNKNOWN__.value
    delete_flag: int = 0


@dataclass_json
@dataclass
class SmallChatList(DataClassJsonMixin):
    small_chat_list: list[SmallChat] = field(default_factory=list[SmallChat])


@dataclass_json
@dataclass
class User(DataClassJsonMixin):
    id: Union[str, None] = None
    userId: Union[str, None] = None  # noqa: N815
    name: Union[str, None] = None
    phoneNumber: Union[str, None] = None  # noqa: N815


@dataclass_json
@dataclass
class Data(DataClassJsonMixin):
    tm: Union[int, None] = field(default=None, metadata=config(decoder=int_or_none))
    sender_name: Union[str, None] = None
    text: Union[str, None] = None
    Text: Union[str, None] = None
    battery: Union[int, None] = field(default=None, metadata=config(decoder=int_or_none))
    poi: Union[str, None] = None
    city: Union[str, None] = None
    address: Union[str, None] = None
    province: Union[str, None] = None
    locate_type: Union[str, None] = None
    emoticon_id: Union[Emoticon.__str__, None] = Emoticon.UNKNOWN__.value
    emoji_id: Union[Emoticon.__str__, None] = Emoticon.UNKNOWN__.value
    call_name: Union[str, None] = None
    call_time: Union[int, None] = field(default=None, metadata=config(decoder=int_or_none))
    call_type: Union[int, None] = field(default=None, metadata=config(decoder=int_or_none))
    lat: Union[float, None] = None
    lng: Union[float, None] = None
    radius: Union[int, None] = field(default=None, metadata=config(decoder=int_or_none))
    delete_flag: Union[int, None] = 0


@dataclass_json
@dataclass
class SimpleChat(DataClassJsonMixin):
    id: Union[str, None] = None
    msgId: Union[str, None] = None  # noqa: N815
    readFlag: Union[int, None] = field(default=None, metadata=config(decoder=int_or_none))  # noqa: N815
    sender: Union[User, None] = None
    receiver: Union[User, None] = None
    data: Union[Data, None] = None
    create: Union[int, None] = field(default=None, metadata=config(decoder=int_or_none))
    type: Union[ChatType.__str__, None] = field(default=ChatType.UNKNOWN__.value)


@dataclass_json
@dataclass
class ChatsNew(DataClassJsonMixin):
    list: Union[list[SimpleChat], None] = field(default_factory=list[SimpleChat])


@dataclass_json
@dataclass
class Chats(DataClassJsonMixin):
    chatsNew: Union[ChatsNew, None] = None  # noqa: N815
