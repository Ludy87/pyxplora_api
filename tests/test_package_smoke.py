from __future__ import annotations

import importlib

import pyxplora_api.gql_mutations as gql_mutations
import pyxplora_api.gql_queries as gql_queries


def test_all_public_modules_import() -> None:
    modules = [
        "pyxplora_api",
        "pyxplora_api.const",
        "pyxplora_api.const_version",
        "pyxplora_api.exception_classes",
        "pyxplora_api.gql_handler",
        "pyxplora_api.gql_handler_async",
        "pyxplora_api.gql_mutations",
        "pyxplora_api.gql_queries",
        "pyxplora_api.graphql_client",
        "pyxplora_api.handler_gql",
        "pyxplora_api.model",
        "pyxplora_api.pyxplora",
        "pyxplora_api.pyxplora_api",
        "pyxplora_api.pyxplora_api_async",
        "pyxplora_api.status",
    ]

    for module_name in modules:
        assert importlib.import_module(module_name).__name__ == module_name


def test_query_and_mutation_catalogs_contain_expected_entries() -> None:
    assert gql_queries.WATCH_Q["askLocateQ"]
    assert gql_queries.UTILS_Q["countriesQ"]
    assert gql_mutations.SIGN_M["signInWithEmailOrPhoneM"]
    assert gql_mutations.WATCH_M["sendChatTextM"]
