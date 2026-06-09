from __future__ import annotations

import asyncio

from pyxplora_api.const import DEFAULT_TIMEOUT, DEFAULT_USER_AGENT
from pyxplora_api.graphql_client import GraphqlClient


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload
        self.raised = False

    def raise_for_status(self) -> None:
        self.raised = True

    def json(self) -> dict:
        return self.payload


class AsyncPostContext:
    def __init__(self, response: "AsyncResponse") -> None:
        self.response = response

    async def __aenter__(self) -> "AsyncResponse":
        return self.response

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class AsyncResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.raised = False

    def raise_for_status(self) -> None:
        self.raised = True

    async def json(self) -> dict:
        return self.payload


class FakeSession:
    def __init__(self, response: AsyncResponse) -> None:
        self.response = response
        self.calls = []

    def post(self, endpoint: str, *, json: dict, headers: dict) -> AsyncPostContext:
        self.calls.append({"endpoint": endpoint, "json": json, "headers": headers})
        return AsyncPostContext(self.response)


def test_request_body_omits_empty_optional_fields() -> None:
    body = GraphqlClient._GraphqlClient__request_body("query", {}, "")
    assert body == {"query": "query"}

    body = GraphqlClient._GraphqlClient__request_body("query", {"id": 1}, "Operation")
    assert body == {
        "query": "query",
        "variables": {"id": 1},
        "operationName": "Operation",
    }


def test_execute_posts_merged_headers_and_default_user_agent(monkeypatch) -> None:
    calls = []
    response = FakeResponse({"data": {"ok": True}})

    def fake_post(endpoint: str, *, json: dict, headers: dict, timeout: int, **options):
        calls.append(
            {
                "endpoint": endpoint,
                "json": json,
                "headers": headers,
                "timeout": timeout,
                "options": options,
            }
        )
        return response

    monkeypatch.setattr("pyxplora_api.graphql_client.requests.post", fake_post)
    client = GraphqlClient(
        "https://example.test/graphql", headers={"Authorization": "base"}, verify=False
    )

    assert client.execute(
        "query", {"id": 1}, "Operation", headers={"X-Test": "yes"}
    ) == {"data": {"ok": True}}
    assert response.raised is True
    assert calls == [
        {
            "endpoint": "https://example.test/graphql",
            "json": {
                "query": "query",
                "variables": {"id": 1},
                "operationName": "Operation",
            },
            "headers": {
                "Authorization": "base",
                "X-Test": "yes",
                "user-agent": DEFAULT_USER_AGENT,
            },
            "timeout": DEFAULT_TIMEOUT,
            "options": {"verify": False},
        }
    ]


def test_ha_execute_async_uses_supplied_session_and_default_user_agent() -> None:
    response = AsyncResponse({"data": {"ok": True}})
    session = FakeSession(response)
    client = GraphqlClient(
        "https://example.test/graphql", headers={"Authorization": "base"}
    )

    result = asyncio.run(
        client.ha_execute_async("query", {"id": 2}, "Operation", session=session)
    )

    assert result == {"data": {"ok": True}}
    assert response.raised is True
    assert session.calls == [
        {
            "endpoint": "https://example.test/graphql",
            "json": {
                "query": "query",
                "variables": {"id": 2},
                "operationName": "Operation",
            },
            "headers": {"Authorization": "base", "user-agent": DEFAULT_USER_AGENT},
        }
    ]
