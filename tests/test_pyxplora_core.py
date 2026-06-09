from __future__ import annotations

import pytest

from pyxplora_api.exception_classes import ChildNoError, XTypeError
from pyxplora_api.pyxplora import PyXplora


def make_client(*, wuid=None) -> PyXplora:
    client = PyXplora("49", "15123456789", "secret", "de-DE", "Europe/Berlin", wuid=wuid)
    client.watchs = [
        {
            "ward": {
                "id": "wuid-1",
                "phoneNumber": "111",
                "name": "Alice",
                "file": {"id": "file-1"},
                "xcoin": "12",
                "currentStep": "345",
                "totalStep": "6789",
            }
        },
        {
            "ward": {
                "id": "wuid-2",
                "phoneNumber": "222",
                "name": "Bob",
                "file": {"id": "file-2"},
                "xcoin": 34,
                "currentStep": 567,
                "totalStep": 8901,
            }
        },
    ]
    return client


def test_connection_and_logoff_state() -> None:
    client = make_client()
    assert client._isConnected() is False
    client.user = {"id": "user"}
    client._issueToken = {"token": "token"}
    client._logoff()
    assert client.user == {}
    assert client._issueToken is None
    client.dtIssueToken = 0
    assert client._hasTokenExpired() is True


def test_user_accessors_return_values_and_defaults() -> None:
    client = make_client()
    assert client.getUserID() == ""
    assert client.getUserName() == ""
    assert client.getUserIcon().endswith("default_icon.png")
    assert client.getUserXcoin() == -1
    assert client.getUserCurrentStep() == -1
    assert client.getUserTotalStep() == -1

    client.user = {
        "id": "user-1",
        "name": "Parent",
        "extra": {"profileIcon": "https://example.test/icon.png"},
        "xcoin": 5,
        "currentStep": 10,
        "totalStep": 15,
        "create": 0,
        "update": 60,
    }
    assert client.getUserID() == "user-1"
    assert client.getUserName() == "Parent"
    assert client.getUserIcon() == "https://example.test/icon.png"
    assert client.getUserXcoin() == 5
    assert client.getUserCurrentStep() == 10
    assert client.getUserTotalStep() == 15
    assert client.getUserCreate() == "1970-01-01 00:00:00"
    assert client.getUserUpdate() == "1970-01-01 00:01:00"


def test_watch_user_accessors_support_all_str_and_filtered_inputs() -> None:
    client = make_client()

    assert client.getWatchUserIDs() == ["wuid-1", "wuid-2"]
    assert client.getWatchUserIDs(["222"]) == ["wuid-2"]
    assert client.getWatchUserPhoneNumbers() == ["111", "222"]
    assert client.getWatchUserPhoneNumbers("wuid-1") == "111"
    assert client.getWatchUserNames() == ["Alice", "Bob"]
    assert client.getWatchUserNames("wuid-2") == "Bob"
    assert client.getWatchUserIcons("wuid-1") == "https://api.myxplora.com/file?id=file-1"
    assert client.getWatchUserIcons(["wuid-1", "wuid-2"]) == [
        "https://api.myxplora.com/file?id=file-1",
        "https://api.myxplora.com/file?id=file-2",
    ]
    assert client.getWatchUserXCoins("wuid-1") == 12
    assert client.getWatchUserXCoins(["wuid-1", "wuid-2"]) == [12, 34]
    assert client.getWatchUserCurrentStep("wuid-1") == 345
    assert client.getWatchUserCurrentStep(["wuid-1", "wuid-2"]) == [345, 567]
    assert client.getWatchUserTotalStep("wuid-1") == 6789
    assert client.getWatchUserTotalStep(["wuid-1", "wuid-2"]) == [6789, 8901]


def test_configured_wuid_overrides_watch_list_ids() -> None:
    assert make_client(wuid="fixed").getWatchUserIDs() == ["fixed"]
    assert make_client(wuid=["one", "two"]).getWatchUserIDs() == ["one", "two"]


def test_watch_user_accessors_raise_for_missing_or_bad_inputs() -> None:
    client = make_client()
    client.watchs = []

    with pytest.raises(ChildNoError, match="Watch ID"):
        client.getWatchUserPhoneNumbers()
    assert client.getWatchUserPhoneNumbers(ignoreError=True) == []

    client = make_client()
    with pytest.raises(XTypeError):
        client.getWatchUserNames(123)  # type: ignore[arg-type]


def test_get_device_and_helper_time() -> None:
    client = make_client()
    client.device = {"wuid-1": {"battery": 88}}
    assert client.getDevice("wuid-1") == {"battery": 88}
    assert client.getDevice("unknown") == {}
    assert PyXplora._helperTime("0") == "00:00"
    assert PyXplora._helperTime("75") == "01:15"
    assert PyXplora._helperTime("1440") == "24:00"
