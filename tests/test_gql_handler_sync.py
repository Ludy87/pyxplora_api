from __future__ import annotations

import pytest

from pyxplora_api.exception_classes import HandlerException, LoginError, NoAdminError
from pyxplora_api.gql_handler import GQLHandler
from pyxplora_api.status import NormalStatus, UserContactType


class CapturingGQLHandler(GQLHandler):
    def __init__(self) -> None:
        super().__init__("49", "15123456789", "secret", "de-DE", "Europe/Berlin")
        self.calls = []
        self.next_response = {"data": {}}

    def runAuthorizedGqlQuery(self, query, variables=None, operation_name=None):
        self.calls.append({"query": query, "variables": variables, "operation_name": operation_name})
        return self.next_response


def test_run_gql_query_rejects_none_query() -> None:
    handler = GQLHandler("49", "15123456789", "secret", "de-DE", "Europe/Berlin")

    with pytest.raises(HandlerException, match="GraphQL query"):
        handler.runGqlQuery(None)  # type: ignore[arg-type]


def test_login_populates_token_fields(monkeypatch) -> None:
    handler = GQLHandler("49", "15123456789", "secret", "de-DE", "Europe/Berlin")
    token = {"id": "session", "token": "token", "user": {"id": "user"}}
    monkeypatch.setattr(
        handler,
        "runGqlQuery",
        lambda query, variables=None, operation_name=None: {"data": {"signInWithEmailOrPhone": token}},
    )

    assert handler.login() == token
    assert handler.issueToken == token
    assert handler.sessionId == "session"
    assert handler.userId == "user"
    assert handler.accessToken == "token"


def test_login_raises_login_error_when_payload_has_no_token(monkeypatch) -> None:
    handler = GQLHandler("49", "15123456789", "secret", "de-DE", "Europe/Berlin")
    monkeypatch.setattr(
        handler,
        "runGqlQuery",
        lambda query, variables=None, operation_name=None: {"errors": [{"message": "bad credentials"}], "data": {}},
    )

    with pytest.raises(LoginError, match="bad credentials"):
        handler.login()
    assert handler.errors[-1]["function"] == "login"


def test_is_admin_returns_true_for_first_guardian_and_raises_otherwise(monkeypatch) -> None:
    handler = GQLHandler("49", "15123456789", "secret", "de-DE", "Europe/Berlin")
    handler.userId = "user-1"

    monkeypatch.setattr(
        handler,
        "getWatchUserContacts",
        lambda wuid: {"contacts": {"contacts": [{"contactUser": {"id": "user-1"}, "guardianType": "FIRST"}]}},
    )
    monkeypatch.setattr(handler, "runAuthorizedGqlQuery", lambda query, variables, key: {"data": {"contacts": True}})
    assert handler.isAdmin("wuid-1", "query", {"uid": "wuid-1"}, "Contacts") is True

    monkeypatch.setattr(
        handler,
        "getWatchUserContacts",
        lambda wuid: {"contacts": {"contacts": [{"contactUser": {"id": "user-1"}, "guardianType": "SECOND"}]}},
    )
    with pytest.raises(NoAdminError):
        handler.isAdmin("wuid-1", "query", {"uid": "wuid-1"}, "Contacts")


def test_common_query_wrappers_return_data_and_capture_variables() -> None:
    handler = CapturingGQLHandler()
    handler.next_response = {"data": {"countries": [{"name": "Germany"}]}}
    assert handler.countries() == {"countries": [{"name": "Germany"}]}
    assert handler.calls[-1]["variables"] == {}
    assert handler.calls[-1]["operation_name"] == "Countries"

    handler.next_response = {"data": {"setEnableSilentTime": True}}
    assert handler.setEnableSilentTime("silent-1", NormalStatus.DISABLE.value) == {"setEnableSilentTime": True}
    assert handler.calls[-1]["variables"] == {"silentId": "silent-1", "status": "DISABLE"}

    handler.next_response = {"data": {"sendChatText": True}}
    assert handler.sendText("wuid-1", "Hallo") is True
    assert handler.calls[-1]["variables"] == {"uid": "wuid-1", "text": "Hallo"}

    handler.next_response = {"data": {"checkEmailOrPhoneExist": False}}
    assert handler.checkEmailOrPhoneExist(UserContactType.EMAIL, "user@example.test") == {"checkEmailOrPhoneExist": False}
    assert handler.calls[-1]["variables"] == {
        "type": "EMAIL",
        "email": "user@example.test",
        "countryCode": "",
        "phoneNumber": "",
    }
