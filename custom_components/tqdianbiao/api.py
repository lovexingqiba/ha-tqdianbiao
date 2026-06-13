"""TQ 电表 API 封装 - 保持与测试通过版完全一致。"""
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


def _to_iso(dt_str: str) -> str:
    """将 '2026-06-13 00:00:12' 或 '2026-06-03' 转为 ISO 8601 格式"""
    dt_str = dt_str.strip()
    if not dt_str:
        return ""
    dt_str = dt_str.replace(" ", "T")
    # 没有时间部分，补上 00:00:00
    if "T" not in dt_str or dt_str.count(":") == 0:
        dt_str = (dt_str.split("+")[0].split("-")[0:3] if "+" in dt_str
                  else dt_str.split("T")[0] if "T" in dt_str
                  else dt_str) + "T00:00:00"
    # 只有时:分，补:00
    elif dt_str.count(":") == 1:
        dt_str += ":00"
    # 没有时区，加上东八区
    if "+" not in dt_str and "Z" not in dt_str:
        dt_str += "+08:00"
    return dt_str


class TqApi:
    def __init__(self, account: str, password: str) -> None:
        self._account = account
        self._password = password
        self._token = ""
        self._session = requests.Session()
        self._session.trust_env = False
        self._session.headers.update({
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        })

    def _device_info(self) -> dict:
        return {
            "deviceType": "app", "platform": "Android", "uuid": UUID,
            "av": "2.1.0", "rv": "", "app_token": None, "cookie": "",
        }

    def _post(self, uri: str, data: dict) -> dict:
        url = HOST + uri
        encoded = _b64encode(data)
        sign = _sign(data)
        resp = self._session.post(url, data={"data": encoded, "_sign": sign})
        if resp.status_code != 200:
            raise ConnectionError(f"HTTP {resp.status_code} for {url}: {resp.text[:300]}")
        return _b64decode(resp.json()["data"])

    def login(self) -> str:
        data = {**self._device_info(), "username": self._account, "password": self._password}
        result = self._post("/App2/AppAccount/login", data)
        self._token = result["data"]
        return self._token

    def fetch_all(self) -> dict[str, Any]:
        """登录 → getUserlist → payInfo → queryRecord → getDetailPayHistory"""
        info = self._device_info()

        # getUserlist
        ul_data = {**info, "app_token": self._token, "account": self._account}
        ul_result = self._post("/App2/AppMain/getUserlist", ul_data)
        user = ul_result["data"][0]["items"][0]
        mid, cid, ptype = user["id"], user["customerid"], user["partern_type"]

        # payInfo
        pi_data = {**info, "app_token": self._token, "customerId": cid, "meterId": mid, "type": ptype}
        pi_result = self._post("/App2/AppMain/payInfo", pi_data)
        dash = pi_result["data"]["dashboard"]
        balance = float(dash["value"])
        total_usage = float(dash["items"][2]["value"].split(" ")[0])
        update_time = dash["items"][0]["value"]

        # getDetailPayHistory (先查，fee 计算可能要用)
        ph_data = {**info, "app_token": self._token, "customerId": cid, "meterId": mid,
                    "type": ptype, "offset": 0, "limit": 20}
        ph_result = self._post("/App2/AppMain/getDetailPayHistory", ph_data)
        ph_rows = ph_result.get("data", {}).get("rows", [])
        if ph_rows:
            latest_amount = float(ph_rows[0]["fee"].split(" ")[0])
            latest_date = ph_rows[0]["date"]
        else:
            latest_amount = 0
            latest_date = ""

        # queryRecord - 用电量 (selectItem=1)
        qr_data = {**info, "app_token": self._token, "meterId": mid, "type": ptype, "selectItem": "1"}
        qr_result = self._post("/App2/AppMain/queryRecord", qr_data)
        rows = qr_result["data"]["rows"]
        yesterday_usage = round(_parse_html(rows[0]["html"]) - _parse_html(rows[1]["html"]), 2)

        # queryRecord - 电费 (selectItem=2)
        qf_data = {**info, "app_token": self._token, "meterId": mid, "type": ptype, "selectItem": "2"}
        qf_result = self._post("/App2/AppMain/queryRecord", qf_data)
        fee_rows = qf_result["data"]["rows"]
        now_fee = _parse_html(fee_rows[0]["html"])
        yesterday_fee_val = _parse_html(fee_rows[1]["html"])
        yesterday_fee = round(yesterday_fee_val - now_fee, 2)
        if yesterday_fee < 0:
            # 充过值，加上最近充值金额
            yesterday_fee = round(yesterday_fee + latest_amount, 2)

        return {
            "balance": balance,
            "total_usage": total_usage,
            "update_time": _to_iso(update_time),
            "yesterday_usage": yesterday_usage,
            "yesterday_fee": yesterday_fee,
            "latest_pay_amount": latest_amount,
            "latest_pay_date": _to_iso(latest_date),
        }
