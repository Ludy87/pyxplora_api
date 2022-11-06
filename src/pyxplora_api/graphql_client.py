"""Module containing graphQL client."""
from __future__ import annotations

import aiohttp
import logging
import requests

from typing import Any


class GraphqlClient:
    """Class which represents the interface to make graphQL requests through."""

    def __init__(self, endpoint: str, headers: dict = {}, **kwargs: Any):
        """Insantiate the client."""
        self.logger = logging.getLogger(__name__)
        self.endpoint = endpoint
        self.headers = headers
        self.options = kwargs

    def __request_body(self, query: str, variables: dict | None = None, operation_name: str | None = None) -> dict:
        json: dict[str, Any] = {"query": query}

        if variables:
            json.update({"variables": variables})

        if operation_name:
            json.update({"operationName": operation_name})

        return json

    def execute(
        self, query: str, variables: dict | None = None, operation_name: str | None = None, headers: dict = {}, **kwargs: Any
    ):
        """Make synchronous request to graphQL server."""
        request_body = self.__request_body(query=query, variables=variables, operation_name=operation_name)

        result = requests.post(
            self.endpoint, json=request_body, headers={**self.headers, **headers}, **{**self.options, **kwargs}
        )

        result.raise_for_status()
        return result.json()

    async def execute_async(
        self, query: str, variables: dict | None = None, operation_name: str | None = None, headers: dict = {}
    ):
        """Make asynchronous request to graphQL server."""
        request_body = self.__request_body(query=query, variables=variables, operation_name=operation_name)

        async with aiohttp.ClientSession() as session:
            async with session.post(self.endpoint, json=request_body, headers={**self.headers, **headers}) as response:
                return await response.json()
