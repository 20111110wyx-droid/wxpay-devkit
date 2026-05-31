"""
WeChat Pay API v3 — 主客户端

整合签名、解密、HTTP 请求，提供一站式支付接口调用。
"""

import json
import logging
from typing import Dict, Any, Optional
import urllib.request
import urllib.error

from .signer import Signer
from .decrypt import CallbackHandler

logger = logging.getLogger("wxpay-devkit")

# 微信支付 API 基础地址
API_BASE = "https://api.mch.weixin.qq.com"
API_BASE_SANDBOX = "https://api.mch.weixin.qq.com/sandboxnew"


class WechatPay:
    """微信支付 API v3 客户端

    Args:
        mchid: 商户号
        serial_no: 商户 API 证书序列号
        private_key_path: 商户 API 私钥文件路径
        private_key_str: 商户 API 私钥字符串
        api_v3_key: API v3 密钥 (32 字节)
        sandbox: 是否使用沙箱环境
    """

    def __init__(
        self,
        mchid: str,
        serial_no: str,
        private_key_path: Optional[str] = None,
        private_key_str: Optional[str] = None,
        api_v3_key: Optional[str] = None,
        sandbox: bool = False,
    ):
        self.mchid = mchid
        self.signer = Signer(mchid, serial_no, private_key_path, private_key_str)
        self.callback = CallbackHandler(api_v3_key or "")
        self.base_url = API_BASE_SANDBOX if sandbox else API_BASE

    def _request(
        self,
        method: str,
        url: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict:
        """发送签名后的 HTTP 请求"""
        full_url = self.base_url + url
        headers = self.signer.sign_header_dict(method, url, body)

        data = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(full_url, data=data, headers=headers, method=method.upper())

        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            logger.error(
                f"WeChatPay API error: {e.code} {e.reason}\n"
                f"URL: {method} {url}\n"
                f"Response: {error_body}"
            )
            try:
                return json.loads(error_body)
            except json.JSONDecodeError:
                raise RuntimeError(
                    f"WeChatPay HTTP {e.code}: {e.reason}\n{error_body}"
                ) from e

    # ========== 支付下单 ==========

    def jsapi_pay(
        self,
        appid: str,
        description: str,
        out_trade_no: str,
        amount_total: int,
        openid: str,
        notify_url: str,
        **kwargs,
    ) -> Dict:
        """JSAPI 支付下单 (公众号/小程序)

        Args:
            appid: 公众号/小程序 APPID
            description: 商品描述
            out_trade_no: 商户订单号
            amount_total: 金额 (单位: 分)
            openid: 用户 OpenID
            notify_url: 回调通知地址
        """
        body = {
            "appid": appid,
            "mchid": self.mchid,
            "description": description,
            "out_trade_no": out_trade_no,
            "notify_url": notify_url,
            "amount": {"total": amount_total, "currency": "CNY"},
            "payer": {"openid": openid},
            **kwargs,
        }
        return self._request("POST", "/v3/pay/transactions/jsapi", body)

    def native_pay(
        self,
        appid: str,
        description: str,
        out_trade_no: str,
        amount_total: int,
        notify_url: str,
        **kwargs,
    ) -> Dict:
        """Native 支付下单 (扫码支付)

        Returns:
            {"code_url": "weixin://wxpay/bizpayurl?pr=..."}
        """
        body = {
            "appid": appid,
            "mchid": self.mchid,
            "description": description,
            "out_trade_no": out_trade_no,
            "notify_url": notify_url,
            "amount": {"total": amount_total, "currency": "CNY"},
            **kwargs,
        }
        return self._request("POST", "/v3/pay/transactions/native", body)

    def h5_pay(
        self,
        appid: str,
        description: str,
        out_trade_no: str,
        amount_total: int,
        notify_url: str,
        scene_info: Dict,
        **kwargs,
    ) -> Dict:
        """H5 支付下单

        Args:
            scene_info: {"payer_client_ip": "...", "h5_info": {"type": "Wap"}}
        """
        body = {
            "appid": appid,
            "mchid": self.mchid,
            "description": description,
            "out_trade_no": out_trade_no,
            "notify_url": notify_url,
            "amount": {"total": amount_total, "currency": "CNY"},
            "scene_info": scene_info,
            **kwargs,
        }
        return self._request("POST", "/v3/pay/transactions/h5", body)

    def app_pay(
        self,
        appid: str,
        description: str,
        out_trade_no: str,
        amount_total: int,
        notify_url: str,
        **kwargs,
    ) -> Dict:
        """APP 支付下单"""
        body = {
            "appid": appid,
            "mchid": self.mchid,
            "description": description,
            "out_trade_no": out_trade_no,
            "notify_url": notify_url,
            "amount": {"total": amount_total, "currency": "CNY"},
            **kwargs,
        }
        return self._request("POST", "/v3/pay/transactions/app", body)

    # ========== 订单查询 ==========

    def query_order(self, out_trade_no: str) -> Dict:
        """按商户订单号查询订单"""
        url = f"/v3/pay/transactions/out-trade-no/{out_trade_no}?mchid={self.mchid}"
        return self._request("GET", url)

    def query_order_by_transaction_id(self, transaction_id: str) -> Dict:
        """按微信支付订单号查询订单"""
        url = f"/v3/pay/transactions/id/{transaction_id}?mchid={self.mchid}"
        return self._request("GET", url)

    # ========== 订单关闭 ==========

    def close_order(self, out_trade_no: str) -> Dict:
        """关闭订单"""
        url = f"/v3/pay/transactions/out-trade-no/{out_trade_no}/close"
        return self._request("POST", url, {"mchid": self.mchid})

    # ========== 退款 ==========

    def refund(
        self,
        out_trade_no: str,
        out_refund_no: str,
        amount_total: int,
        amount_refund: int,
        reason: str = "",
        notify_url: Optional[str] = None,
        **kwargs,
    ) -> Dict:
        """申请退款

        Args:
            out_trade_no: 原商户订单号
            out_refund_no: 退款单号
            amount_total: 原订单金额 (分)
            amount_refund: 退款金额 (分)
            reason: 退款原因
            notify_url: 退款回调地址
        """
        body = {
            "out_trade_no": out_trade_no,
            "out_refund_no": out_refund_no,
            "amount": {
                "refund": amount_refund,
                "total": amount_total,
                "currency": "CNY",
            },
            **kwargs,
        }
        if reason:
            body["reason"] = reason
        if notify_url:
            body["notify_url"] = notify_url

        return self._request("POST", "/v3/refund/domestic/refunds", body)

    def query_refund(self, out_refund_no: str) -> Dict:
        """查询退款单"""
        url = f"/v3/refund/domestic/refunds/{out_refund_no}"
        return self._request("GET", url)
