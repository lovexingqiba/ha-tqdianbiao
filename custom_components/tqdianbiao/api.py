"""TQ 电表 API 封装 - 最简版：只登录。"""
from __future__ import annotations

import base64
import hashlib
import json
import logging

import requests

_LOGGER = logging.getLogger(__name__)

HOST = "http://app.tqdianbiao.com"
UUID = "1a85667260340dc0"
USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 9; MI 9 Build/PQ3A.190605.08141016; wv) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 "
    "Chrome/91.0.4472.114 Mobile Safari/537.36 x5app/2.1.0"
)


def _b64encode(data: dict) -> str:
    return base64.b64encode(
        json.dumps(data, ensure_ascii=True, separators=(",", ":")).encode()
    ).decode()


def _sign(data: dict) -> str:
    return hashlib.md5(
        (_b64encode(data) + "__SIGN__" + UUID).encode()
    ).hexdigest()


def _b64decode(text: str) -> dict:
    return json.loads(base64.b64decode(text).decode("utf-8"))


class TqApi:
    def __init__(self, account: str, password: str) -> None:
        self._account = account
        self._password = password
        self._session = requests.Session()
        self._session.trust_env = False
        self._session.headers.update({
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        })

    def login(self) -> str:
        """POST /App2/AppAccount/login → 返回 token 字符串"""
        device_info = {
            "deviceType": "app", "platform": "Android", "uuid": UUID,
            "av": "2.1.0", "rv": "", "app_token": None, "cookie": "",
        }
        data = {**device_info, "username": self._account, "password": self._password}
        url = HOST + "/App2/AppAccount/login"
        encoded = _b64encode(data)
        sign = _sign(data)
        resp = self._session.post(url, data={"data": encoded, "_sign": sign})
        if resp.status_code != 200:
            raise ConnectionError(
                f"HTTP {resp.status_code}: {resp.text[:300]}"
            )
        result = _b64decode(resp.json()["data"])
        token = result["data"]
        _LOGGER.debug("登录成功, token=%.20s...", token)
        return token
