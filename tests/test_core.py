"""
Signer 和 CallbackHandler 单元测试
"""

import unittest
import json
import os
import tempfile
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from src.signer import Signer
from src.decrypt import CallbackHandler


def generate_test_key() -> str:
    """生成测试用 RSA 私钥"""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption(),
    )
    return pem.decode("utf-8")


class TestSigner(unittest.TestCase):
    """签名器测试"""

    @classmethod
    def setUpClass(cls):
        """生成一次测试密钥，所有 Signer 测试共用"""
        cls._test_key = generate_test_key()

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".pem", delete=False
        )
        self.tmp.write(self._test_key)
        self.tmp.close()
        self.signer = Signer(
            mchid="1900000001",
            serial_no="TEST1234567890",
            private_key_path=self.tmp.name,
        )

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_sign_get(self):
        """GET 请求签名"""
        auth = self.signer.sign("GET", "/v3/pay/transactions/out-trade-no/xxx")
        self.assertIn("WECHATPAY2-SHA256-RSA2048", auth)
        self.assertIn('mchid="1900000001"', auth)
        self.assertIn('serial_no="TEST1234567890"', auth)
        self.assertIn("nonce_str=", auth)
        self.assertIn("signature=", auth)
        self.assertIn("timestamp=", auth)

    def test_sign_post(self):
        """POST 请求签名"""
        body = {"appid": "wx123", "mchid": "1900000001", "amount": {"total": 1}}
        auth = self.signer.sign("POST", "/v3/pay/transactions/jsapi", body)
        self.assertIn("WECHATPAY2-SHA256-RSA2048", auth)

    def test_sign_header_dict(self):
        """返回 headers dict"""
        headers = self.signer.sign_header_dict("GET", "/v3/pay/transactions/out-trade-no/xxx")
        self.assertIn("Authorization", headers)
        self.assertEqual(headers["Content-Type"], "application/json")

    def test_invalid_key_path(self):
        """无效的私钥路径"""
        with self.assertRaises(FileNotFoundError):
            Signer(
                mchid="1900000001",
                serial_no="TEST",
                private_key_path="/nonexistent/path.pem",
            )


class TestCallbackHandler(unittest.TestCase):
    """回调处理器测试"""

    def setUp(self):
        self.handler = CallbackHandler(api_v3_key="a" * 32)

    def test_decrypt_missing_resource(self):
        """缺少 resource 字段"""
        with self.assertRaises(Exception):
            self.handler.decrypt(
                headers={"wechatpay-signature": "x", "wechatpay-timestamp": "1", "wechatpay-nonce": "x"},
                body=json.dumps({"event_type": "TEST"}),
            )

    def test_decrypt_invalid_json(self):
        """无效 JSON"""
        with self.assertRaises(Exception):
            self.handler.decrypt(
                headers={},
                body="not json",
            )

    def test_signature_missing_header(self):
        """缺少签名头"""
        body = json.dumps({
            "resource": {
                "algorithm": "AEAD_AES_256_GCM",
                "ciphertext": "dGVzdA==",
                "nonce": "dGVzdA==",
                "associated_data": "",
            }
        })
        with self.assertRaises(Exception):
            self.handler.decrypt(headers={}, body=body)

    def test_timestamp_out_of_range(self):
        """时间戳超出范围"""
        body = json.dumps({
            "resource": {
                "algorithm": "AEAD_AES_256_GCM",
                "ciphertext": "dGVzdA==",
                "nonce": "dGVzdA==",
                "associated_data": "",
            }
        })
        with self.assertRaises(Exception):
            self.handler.decrypt(
                headers={
                    "wechatpay-signature": "x",
                    "wechatpay-timestamp": "1",
                    "wechatpay-nonce": "x",
                },
                body=body,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
