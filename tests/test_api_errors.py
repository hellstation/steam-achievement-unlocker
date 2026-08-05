import pytest
import requests

from src.api.steam_web_api import SteamWebAPI
from src.errors import APIResponseError, AuthError, NetworkError


class _Session:
    def __init__(self, response=None, error=None):
        self._response = response
        self._error = error

    def get(self, *args, **kwargs):
        if self._error:
            raise self._error
        return self._response


class _Response401:
    status_code = 401

    def raise_for_status(self):
        raise requests.HTTPError("401", response=self)

    def json(self):
        return {}


class _ResponseInvalidJson:
    def raise_for_status(self):
        return None

    def json(self):
        raise ValueError("invalid")


class _ResponseList:
    def raise_for_status(self):
        return None

    def json(self):
        return []


def test_get_maps_401_to_auth_error():
    api = SteamWebAPI("a" * 32, "76561197989341403")
    api._session = _Session(response=_Response401())
    with pytest.raises(AuthError):
        api._get("https://example.com")


def test_get_maps_request_exception_to_network_error():
    api = SteamWebAPI("a" * 32, "76561197989341403")
    api._session = _Session(error=requests.ConnectionError("nope"))
    with pytest.raises(NetworkError):
        api._get("https://example.com")


def test_get_maps_invalid_json_to_api_response_error():
    api = SteamWebAPI("a" * 32, "76561197989341403")
    api._session = _Session(response=_ResponseInvalidJson())
    with pytest.raises(APIResponseError):
        api._get("https://example.com")


def test_get_maps_non_dict_payload_to_api_response_error():
    api = SteamWebAPI("a" * 32, "76561197989341403")
    api._session = _Session(response=_ResponseList())
    with pytest.raises(APIResponseError):
        api._get("https://example.com")


def test_get_owned_games_invalid_games_type():
    api = SteamWebAPI("a" * 32, "76561197989341403")
    api._get = lambda *_args, **_kwargs: {"response": {"games": {"bad": True}}}
    with pytest.raises(APIResponseError):
        api.get_owned_games()
