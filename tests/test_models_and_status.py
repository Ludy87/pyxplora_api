from __future__ import annotations

from pyxplora_api.model import (
    Chats,
    ChatsNew,
    Data,
    SimpleChat,
    SmallChat,
    SmallChatList,
    User,
    int_or_none,
)
from pyxplora_api.status import (
    ChatType,
    Emoji,
    Emoticon,
    LocationType,
    NormalStatus,
    UserContactType,
    WatchOnlineStatus,
)


def test_int_or_none_handles_valid_and_invalid_values() -> None:
    assert int_or_none("42") == 42
    assert int_or_none(7) == 7
    assert int_or_none(None) is None
    assert int_or_none("not-a-number") is None


def test_dataclasses_json_decodes_nested_chat_payload() -> None:
    payload = {
        "chatsNew": {
            "list": [
                {
                    "msgId": "msg-1",
                    "readFlag": "1",
                    "sender": {"id": "sender", "name": "Parent"},
                    "receiver": {"id": "receiver", "name": "Child"},
                    "data": {
                        "tm": "1700000000",
                        "text": "Hallo",
                        "battery": "88",
                        "delete_flag": "0",
                    },
                    "create": "1700000001",
                    "type": ChatType.TEXT.value,
                }
            ]
        }
    }

    chats = Chats.from_dict(payload)

    assert isinstance(chats.chatsNew, ChatsNew)
    assert len(chats.chatsNew.list) == 1
    chat = chats.chatsNew.list[0]
    assert isinstance(chat, SimpleChat)
    assert chat.readFlag == 1
    assert chat.create == 1700000001
    assert isinstance(chat.sender, User)
    assert isinstance(chat.data, Data)
    assert chat.data.tm == 1700000000
    assert chat.data.battery == 88


def test_dataclass_defaults_and_serialization_round_trip() -> None:
    small = SmallChat(msgId="msg", type=ChatType.EMOTICON.value, data_text="🙂")
    small_list = SmallChatList([small])

    assert small.emoticon_id == Emoticon.UNKNOWN__.value
    assert small.delete_flag == 0
    assert SmallChatList.from_dict(small_list.to_dict()).small_chat_list[0].msgId == "msg"


def test_selected_status_enum_values_are_stable() -> None:
    assert NormalStatus.ENABLE.value == "ENABLE"
    assert WatchOnlineStatus.OFFLINE.value == "OFFLINE"
    assert LocationType.UNKNOWN.value == "UNKNOWN"
    assert UserContactType.EMAIL.value == "EMAIL"
    assert Emoji.M1001.value == "😄"
