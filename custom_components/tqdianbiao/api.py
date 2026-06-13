"""TQ 电表 API 封装。

仅包含 leheyuan.py 中原有的 5 个接口：
  login / getUserlist / payInfo / queryRecord / getDetailPayHistory

加密协议：
  请求: base64(json) + md5(base64(json) + "__SIGN__" + uuid)
  响应: json → data 字段 → base64 解码 → json
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import re
from typing import Any

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


def _parse_html(html: str) -> float:
    match = re.findall(r"green>&nbsp;(.+?)</font", html)
    return float(match[0])


class TqApi:
    """TQ 电表 API 客户端。"""

    def __init__(self, account: str, password: str) -> None:
        self._account = account
        self._password = password
        self._session = requests.Session()
        self._session.trust_env = False  # 忽略 HTTP_PROXY 环境变量
        self._session.headers.update({
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        })
        self._token: str | None = None
        self._meter_id: str | None = None
        self._customer_id: str | None = None
        self._partern_type: str | None = None
        self._device_info: dict = {
            "deviceType": "app",
            "platform": "Android",
            "uuid": UUID,
            "av": "2.1.0",
            "rv": "",
            "app_token": None,
            "cookie": "",
        }

    # ----- 加密通讯层（与 leheyuan.py 完全一致） -----

    def _post(self, uri: str, data: dict) -> dict:
        """发送加密 POST 请求并解密响应。"""
        url = HOST + uri
        encoded = _b64encode(data)
        sign = _sign(data)
        resp = self._session.post(
            url, data={"data": encoded, "_sign": sign}
        )
        if resp.status_code != 200:
            raise ConnectionError(
                f"HTTP {resp.status_code} {resp.reason} for {url}: {resp.text[:500]}"
            )
        return _b64decode(resp.json()["data"])

    # ----- 第一个接口：登录 -----

    def login(self) -> str:
        """POST /App2/AppAccount/login"""
        data = {**self._device_info, "username": self._account, "password": self._password}
        result = self._post("/App2/AppAccount/login", data)
        self._token = result["data"]
        _LOGGER.debug("登录成功")
        return self._token

    def _ensure_login(self) -> None:
        if not self._token:
            self.login()

    # ----- 第二个接口：获取电表信息 -----

    def _ensure_user_info(self) -> None:
        """POST /App2/AppMain/getUserlist"""
        self._ensure_login()
        if self._meter_id:
            return
        data = {**self._device_info, "app_token": self._token, "account": self._account}
        result = self._post("/App2/AppMain/getUserlist", data)
        user = result["data"][0]["items"][0]
        self._meter_id = user["id"]
        self._customer_id = user["customerid"]
        self._partern_type = user["partern_type"]
        _LOGGER.debug("meterId=%s, customerId=%s, type=%s",
                       self._meter_id, self._customer_id, self._partern_type)

    def _simple_post(self, uri: str, extra: dict) -> dict:
        """带通用参数（deviceInfo + token）的 POST 请求。"""
        self._ensure_user_info()
        data = {
            **self._device_info,
            "app_token": self._token,
            **extra,
        }
        return self._post(uri, data)

    # ----- 第三个接口：缴费信息 -----

    def fetch_pay_info(self) -> dict[str, Any]:
        """POST /App2/AppMain/payInfo"""
        result = self._simple_post("/App2/AppMain/payInfo", {
            "customerId": self._customer_id,
            "meterId": self._meter_id,
            "type": self._partern_type,
        })
        dashboard = result["data"]["dashboard"]
        return {
            "balance": float(dashboard["value"]),
            "total_usage": float(dashboard["items"][2]["value"].split(" ")[0]),
            "update_time": dashboard["items"][0]["value"],
        }

    # ----- 第四个接口：历史记录 -----

    def fetch_yesterday_usage(self) -> float:
        """POST /App2/AppMain/queryRecord (selectItem=1 电量)"""
        result = self._simple_post("/App2/AppMain/queryRecord", {
            "meterId": self._meter_id,
            "type": self._partern_type,
            "selectItem": "1",
        })
        rows = result["data"]["rows"]
        now_kwh = _parse_html(rows[0]["html"])
        yesterday_kwh = _parse_html(rows[1]["html"])
        return round(now_kwh - yesterday_kwh, 2)

    # ----- 第五个接口：充值记录 -----

    def fetch_latest_pay(self) -> dict[str, Any]:
        """POST /App2/AppMain/getDetailPayHistory"""
        result = self._simple_post("/App2/AppMain/getDetailPayHistory", {
            "customerId": self._customer_id,
            "meterId": self._meter_id,
            "type": self._partern_type,
            "offset": 0,
            "limit": 20,
        })
        rows = result.get("data", {}).get("rows", [])
        if rows:
            return {
                "amount": float(rows[0]["fee"].split(" ")[0]),
                "date": rows[0]["date"],
            }
        return {"amount": 0, "date": ""}

    # ----- 批量获取 -----

    def fetch_all(self) -> dict[str, Any]:
        """依次调用 login → getUserlist → payInfo → queryRecord → getDetailPayHistory"""
        pay = self.fetch_pay_info()
        yesterday = self.fetch_yesterday_usage()
        latest = self.fetch_latest_pay()
        return {
            "balance": pay["balance"],
            "total_usage": pay["total_usage"],
            "update_time": pay["update_time"],
            "yesterday_usage": yesterday,
            "latest_pay_amount": latest["amount"],
            "latest_pay_date": latest["date"],
        }
