"""TQ 电表 API 封装 - 只登录 + payInfo。"""
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
        self._token = ""

    def login(self) -> str:
        device_info = {
            "deviceType": "app", "platform": "Android", "uuid": UUID,
            "av": "2.1.0", "rv": "", "app_token": None, "cookie": "",
        }
        data = {**device_info, "username": self._account, "password": self._password}
        resp = self._session.post(
            HOST + "/App2/AppAccount/login",
            data={"data": _b64encode(data), "_sign": _sign(data)},
        )
        if resp.status_code != 200:
            raise ConnectionError(f"登录失败 HTTP {resp.status_code}: {resp.text[:300]}")
        result = _b64decode(resp.json()["data"])
        self._token = result["data"]
        return self._token

    def fetch_pay_info(self) -> dict:
        """登录 → getUserlist → payInfo，返回原始 JSON"""
        device_info = {
            "deviceType": "app", "platform": "Android", "uuid": UUID,
            "av": "2.1.0", "rv": "", "app_token": None, "cookie": "",
        }

        # getUserlist
        ul_data = {**device_info, "app_token": self._token, "account": self._account}
        ul_resp = self._session.post(
            HOST + "/App2/AppMain/getUserlist",
            data={"data": _b64encode(ul_data), "_sign": _sign(ul_data)},
        )
        if ul_resp.status_code != 200:
            return {"error": f"getUserlist HTTP {ul_resp.status_code}", "body": ul_resp.text[:500]}
        ul_result = _b64decode(ul_resp.json()["data"])
        user = ul_result["data"][0]["items"][0]
        mid, cid, ptype = user["id"], user["customerid"], user["partern_type"]

        # payInfo
        pi_data = {**device_info, "app_token": self._token,
                    "customerId": cid, "meterId": mid, "type": ptype}
        pi_resp = self._session.post(
            HOST + "/App2/AppMain/payInfo",
            data={"data": _b64encode(pi_data), "_sign": _sign(pi_data)},
        )
        return {
            "status_code": pi_resp.status_code,
            "body": pi_resp.text[:800],
            "headers": dict(pi_resp.headers),
        }
