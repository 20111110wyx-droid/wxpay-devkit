"""
WeChat Pay Callback Handler — 回调通知处理

自动解密微信支付回调通知中的 resource 字段，
验证回调签名，确保通知来源可信。
"""

import base64
import json
import time
from typing import Dict, Tuple, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class CallbackError(Exception):
    """回调处理异常"""
    pass


class SignatureVerificationError(CallbackError):
    """签名验证失败"""
    pass


class DecryptionError(CallbackError):
    """解密失败"""
    pass


class CallbackHandler:
    """微信支付回调处理器

    Args:
        api_v3_key: API v3 密钥 (商户平台设置)
    """

    def __init__(self, api_v3_key: str):
        self.api_v3_key = api_v3_key

    def decrypt(
        self,
        headers: Dict[str, str],
        body: str,
        verify_signature: bool = True,
    ) -> Dict:
        """解密并验证回调通知

        Args:
            headers: HTTP 请求头 (dict)
            body: HTTP 请求体 (JSON 字符串)
            verify_signature: 是否验证签名 (默认 True)

        Returns:
            解密后的通知数据 dict

        Raises:
            DecryptionError: 解密失败
            SignatureVerificationError: 签名验证失败
        """
        # 1. 解析 body
        try:
            notification = json.loads(body)
        except json.JSONDecodeError as e:
            raise DecryptionError(f"Invalid JSON body: {e}")

        resource = notification.get("resource", {})
        if not resource:
            raise DecryptionError("Missing 'resource' field in notification")

        # 2. 解密 resource
        decrypted_data = self._decrypt_resource(
            ciphertext=resource.get("ciphertext", ""),
            nonce=resource.get("nonce", ""),
            associated_data=resource.get("associated_data", "")
        )

        # 3. 签名验证
        if verify_signature:
            self._verify_signature(headers, body)

        try:
            return json.loads(decrypted_data)
        except json.JSONDecodeError as e:
            raise DecryptionError(f"Failed to parse decrypted data: {e}")

    def _decrypt_resource(
        self,
        ciphertext: str,
        nonce: str,
        associated_data: str,
    ) -> str:
        """使用 AES-GCM 解密 resource

        微信支付使用 AEAD_AES_256_GCM 算法
        """
        if not all([ciphertext, nonce]) or not self.api_v3_key:
            raise DecryptionError("Missing parameters: ciphertext, nonce, or api_v3_key")

        try:
            aesgcm = AESGCM(self.api_v3_key.encode("utf-8"))
            plaintext = aesgcm.decrypt(
                nonce=nonce.encode("utf-8"),
                data=base64.b64decode(ciphertext),
                associated_data=associated_data.encode("utf-8") if associated_data else None,
            )
            return plaintext.decode("utf-8")
        except Exception as e:
            raise DecryptionError(f"AES-GCM decryption failed: {e}")

    def _verify_signature(self, headers: Dict[str, str], body: str):
        """验证回调签名

        TODO: 需要平台证书公钥进行签名的 SHA256 with RSA 验证
        当前版本仅做请求头验证，完整验证将在 v1.1 实现。
        """
        # 基本校验
        wechatpay_headers = {
            key.lower(): value
            for key, value in headers.items()
            if key.lower().startswith("wechatpay")
        }

        required = ["wechatpay-signature", "wechatpay-timestamp", "wechatpay-nonce"]
        for key in required:
            if key not in wechatpay_headers:
                raise SignatureVerificationError(f"Missing header: {key}")

        # 时间戳容差检查 (5分钟内)
        ts = int(wechatpay_headers["wechatpay-timestamp"])
        if abs(int(time.time()) - ts) > 300:
            raise SignatureVerificationError(
                f"Timestamp too old or too new: {ts}, current: {int(time.time())}"
            )

    def decrypt_and_parse(
        self,
        headers: Dict[str, str],
        body: str,
    ) -> Tuple[str, Dict]:
        """解密后返回 (事件类型, 数据)

        Returns:
            (event_type, data_dict)
            event_type 如: "TRANSACTION.SUCCESS", "REFUND.SUCCESS"
        """
        notification = json.loads(body)
        decrypted = self.decrypt(headers, body)
        event_type = notification.get("event_type", "UNKNOWN")
        return event_type, decrypted
