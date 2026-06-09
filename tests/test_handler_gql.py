from __future__ import annotations

import hashlib

import pytest

from pyxplora_api.const import API_KEY, API_SECRET
from pyxplora_api.exception_classes import HandlerException
from pyxplora_api.handler_gql import HandlerGQL
from pyxplora_api.status import ClientType


def make_handler() -> HandlerGQL:
    return HandlerGQL(
        "49", "15123456789", "secret", "de-DE", "Europe/Berlin", "user@example.test"
    )


def test_constructor_hashes_password_and_builds_login_variables() -> None:
    handler = make_handler()

    assert handler.getApiKey() == API_KEY
    assert handler.getSecret() == API_SECRET
    assert handler.passwordMD5 == hashlib.md5("secret".encode()).hexdigest()
    assert handler.variables == {
        "countryPhoneNumber": "49",
        "phoneNumber": "15123456789",
        "password": handler.passwordMD5,
        "userLang": "de-DE",
        "timeZone": "Europe/Berlin",
        "emailAddress": "user@example.test",
        "client": ClientType.APP.value,
    }


def test_get_request_headers_uses_open_authorization_without_token() -> None:
    headers = make_handler().getRequestHeaders("application/json")

    assert headers["Content-Type"] == "application/json"
    assert headers["H-BackDoor-Authorization"] == f"Open {API_KEY}:{API_SECRET}"
    assert headers["H-Date"].endswith(" GMT")
    assert headers["H-Tid"].isdigit()


@pytest.mark.parametrize("content_type", ["", None])
def test_get_request_headers_rejects_missing_content_type(
    content_type: str | None,
) -> None:
    with pytest.raises(HandlerException, match="acceptedContentType"):
        make_handler().getRequestHeaders(content_type)  # type: ignore[arg-type]


def test_get_request_headers_uses_w360_token_and_updates_credentials() -> None:
    handler = make_handler()
    handler.accessToken = "old-token"
    handler.issueToken = {"w360": {"token": "new-token", "secret": "new-secret"}}

    headers = handler.getRequestHeaders("application/json")

    assert headers["H-BackDoor-Authorization"] == "Bearer new-token:new-secret"
    assert handler.getApiKey() == "new-token"
    assert handler.getSecret() == "new-secret"


def test_get_request_headers_uses_access_token_when_issue_token_has_no_w360() -> None:
    handler = make_handler()
    handler.accessToken = "access-token"
    handler.issueToken = {"id": "session"}

    headers = handler.getRequestHeaders("application/json")

    assert headers["H-BackDoor-Authorization"] == f"Bearer access-token:{API_SECRET}"
