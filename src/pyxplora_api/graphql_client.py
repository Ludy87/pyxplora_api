"""Module containing graphQL client."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import requests

from .const import DEFAULT_TIMEOUT, DEFAULT_USER_AGENT


class GraphqlClient:
    """Class which represents the interface to make graphQL requests through."""

    def __init__(self, endpoint: str, headers: dict[str, str] = {}, **kwargs: Any):
        """Instantiate the client."""
        self.logger = logging.getLogger(__name__)
        self.endpoint = endpoint
        self.headers = headers
        self.options = kwargs

    @staticmethod
    def __request_body(
        query: str, variables: dict[str, Any] | None = None, operation_name: str | None = None
    ) -> dict[str, Any]:
        json: dict[str, Any] = {"query": query}

        if variables:
            json.update({"variables": variables})

        if operation_name:
            json.update({"operationName": operation_name})

        return json

    def execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        operation_name: str | None = None,
        headers: dict[str, str] = {},
    ):
        """Make synchronous request to graphQL server."""
        request_body = self.__request_body(query=query, variables=variables, operation_name=operation_name)

        if "user-agent" not in headers:
            headers["user-agent"] = DEFAULT_USER_AGENT
        result = requests.post(
            self.endpoint,
            json=request_body,
            headers={**self.headers, **headers},
            **self.options,
            timeout=DEFAULT_TIMEOUT,
        )

        result.raise_for_status()
        return result.json()

    async def execute_async(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        operation_name: str | None = None,
        headers: dict[str, str] = {},
    ):
        """Make asynchronous request to graphQL server."""
        request_body = self.__request_body(query=query, variables=variables, operation_name=operation_name)

        if "user-agent" not in headers:
            headers["user-agent"] = DEFAULT_USER_AGENT
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(DEFAULT_TIMEOUT)) as session, session.post(
            self.endpoint, json=request_body, headers={**self.headers, **headers}
        ) as response:
            try:
                response.raise_for_status()
                return await response.json()
            except (aiohttp.ContentTypeError, aiohttp.ClientResponseError) as err:
                self.logger.debug(err)
                return {}

    async def ha_execute_async(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        operation_name: str | None = None,
        headers: dict[str, str] = {},
        session: aiohttp.ClientSession | None = None,
    ):
        """Make asynchronous request to graphQL server."""
        request_body = self.__request_body(query=query, variables=variables, operation_name=operation_name)

        if "user-agent" not in headers:
            headers["user-agent"] = DEFAULT_USER_AGENT
        if session is None:
            return await self.execute_async(query=query, variables=variables, operation_name=operation_name, headers=headers)
        async with session.post(self.endpoint, json=request_body, headers={**self.headers, **headers}) as response:
            try:
                response.raise_for_status()
                return await response.json()
            except (aiohttp.ContentTypeError, aiohttp.ClientResponseError) as err:
                self.logger.debug(err)
                return {}
