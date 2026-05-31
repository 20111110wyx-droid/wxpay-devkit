"""
WeChat Pay API v3 Signer — 签名工具

根据微信支付 API v3 规范自动生成 Authorization 请求头。
签名算法：使用商户私钥对构造的签名串进行 SHA256 with RSA 签名。
"""

import os
import time
import uuid
import base64
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend


class Signer:
    """微信支付 API v3 签名器

    Args:
        mchid: 商户号
        serial_no: 商户 API 证书序列号
        private_key_path: 商户 API 私钥文件路径 (pem 格式)
        private_key_str: 商户 API 私钥字符串 (与 private_key_path 二选一)
    """

    def __init__(
        self,
        mchid: str,
        serial_no: str,
        private_key_path: Optional[str] = None,
        private_key_str: Optional[str] = None,
    ):
        self.mchid = mchid
        self.serial_no = serial_no
        self._private_key = self._load_private_key(private_key_path, private_key_str)

    def _load_private_key(self, path: Optional[str], key_str: Optional[str]):
        """加载商户私钥"""
        if key_str:
            return serialization.load_pem_private_key(
                key_str.encode("utf-8"), password=None, backend=default_backend()
            )
        if path:
            with open(os.path.expanduser(path), "rb") as f:
                return serialization.load_pem_private_key(
                    f.read(), password=None, backend=default_backend()
                )
        raise ValueError("请提供 private_key_path 或 private_key_str")

    def sign(
        self,
        method: str,
        url: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> str:
        """生成 Authorization 请求头

        Args:
            method: HTTP 方法 (GET/POST/PUT/DELETE)
            url: 请求 URL 路径部分 (如 /v3/pay/transactions/jsapi)
            body: 请求体 dict (GET 请求为 None)

        Returns:
            Authorization 请求头完整字符串
        """
        nonce_str = uuid.uuid4().hex
        timestamp = str(int(time.time()))

        # 构造签名串
        body_str = ""
        if body is not None:
            import json
            body_str = json.dumps(body, separators=(",", ":"))

        message = f"{method.upper()}\n{url}\n{timestamp}\n{nonce_str}\n{body_str}\n"

        # SHA256 with RSA 签名
        signature = base64.b64encode(
            self._private_key.sign(
                message.encode("utf-8"),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
        ).decode("utf-8")

        # 构造 Authorization 头
        auth_header = (
            f'WECHATPAY2-SHA256-RSA2048 mchid="{self.mchid}",'
            f'nonce_str="{nonce_str}",'
            f'signature="{signature}",'
            f'timestamp="{timestamp}",'
            f'serial_no="{self.serial_no}"'
        )
        return auth_header

    def sign_header_dict(
        self,
        method: str,
        url: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """返回可直接用于 requests 库的 headers dict

        Example:
            headers = signer.sign_header_dict("POST", "/v3/pay/transactions/jsapi", body)
            resp = requests.post("https://api.mch.weixin.qq.com" + url, json=body, headers=headers)
        """
        return {
            "Authorization": self.sign(method, url, body),
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "wxpay-devkit/1.0",
        }
