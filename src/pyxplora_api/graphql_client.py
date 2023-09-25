"""Module containing graphQL client."""
from __future__ import annotations

import logging

import aiohttp
import requests

from .const import DEFAULT_TIMEOUT, DEFAULT_USER_AGENT


class GraphqlClient:
    """Class which represents the interface to make graphQL requests through."""

    def __init__(self, endpoint: str, headers: dict[str, str] = {}, **kwargs: any):
        """Insantiate the client."""
        self.logger = logging.getLogger(__name__)
        self.endpoint = endpoint
        self.headers = headers
        self.options = kwargs

    def __request_body(self, query: str, variables: dict[str, any] = None, operation_name: str = None) -> dict[str, any]:
        json: dict[str, any] = {"query": query}

        if variables:
            json.update({"variables": variables})

        if operation_name:
            json.update({"operationName": operation_name})

        return json

    def execute(self, query: str, variables: dict[str, any] = None, operation_name: str = None, headers: dict[str, str] = {}):
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
        self, query: str, variables: dict[str, any] = None, operation_name: str = None, headers: dict[str, str] = {}
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
        variables: dict[str, any] = None,
        operation_name: str = None,
        headers: dict[str, str] = {},
        session: aiohttp.ClientSession = None,
    ):
        """Make asynchronous request to graphQL server."""
        request_body = self.__request_body(query=query, variables=variables, operation_name=operation_name)

        if "user-agent" not in headers:
            headers["user-agent"] = DEFAULT_USER_AGENT
        async with session.post(self.endpoint, json=request_body, headers={**self.headers, **headers}) as response:
            try:
                response.raise_for_status()
                return await response.json()
            except (aiohttp.ContentTypeError, aiohttp.ClientResponseError) as err:
                self.logger.debug(err)
                return {}
