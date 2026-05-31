"""
完整示例：Native 支付 (扫码支付) 全流程

流程：
1. Native 下单 → 获取 code_url
2. 生成支付二维码 (可扫码支付)
3. 处理支付成功回调
4. 查询订单状态
"""

import json
import sys
import os

# 将项目根目录加入 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import WechatPay, CallbackHandler


def main():
    # ==================== 配置 ====================
    pay = WechatPay(
        mchid="1900000001",                    # 商户号
        serial_no="YOUR_CERTIFICATE_SERIAL",    # 证书序列号
        private_key_path="~/.wxpay/apiclient_key.pem",  # 私钥路径
        api_v3_key="YOUR_API_V3_KEY_32BYTES",   # API v3 密钥
        # sandbox=True,  # 测试环境
    )

    # ==================== 1. 下单 ====================
    print("📱 正在生成支付二维码...")

    resp = pay.native_pay(
        appid="wx1234567890",
        description="🧧 测试商品 - 5 块钱",
        out_trade_no=f"ORDER{int(__import__('time').time())}",
        amount_total=500,  # 5 元 = 500 分
        notify_url="https://your-domain.com/api/wechatpay/notify",
    )

    code_url = resp.get("code_url")
    if not code_url:
        print(f"❌ 下单失败: {resp}")
        return

    print(f"✅ 下单成功!")
    print(f"📋 商户订单号: {resp.get('out_trade_no', 'N/A')}")
    print(f"🔗 code_url: {code_url}")
    print(f"\n💡 将 code_url 复制到二维码生成器即可扫码支付")
    print(f"   https://cli.im/ 或 https://qr.io")

    # ==================== 2. 模拟回调处理 ====================
    print(f"\n" + "=" * 60)
    print("📨 模拟处理支付回调...")

    # 微信支付真实回调格式
    mock_notification = {
        "id": "EV-2018022511223320873",
        "create_time": "2024-01-01T12:00:00+08:00",
        "resource_type": "encrypt-resource",
        "event_type": "TRANSACTION.SUCCESS",
        "summary": "支付成功",
        "resource": {
            "algorithm": "AEAD_AES_256_GCM",
            "ciphertext": "...",  # 真实场景下是 Base64 密文
            "associated_data": "",
            "nonce": "...",
            "original_type": "transaction",
        },
    }

    handler = CallbackHandler(api_v3_key="YOUR_API_V3_KEY_32BYTES")
    try:
        event_type, data = handler.decrypt_and_parse(
            headers={
                "Wechatpay-Signature": "...",
                "Wechatpay-Timestamp": str(int(__import__('time').time())),
                "Wechatpay-Nonce": "...",
                "Wechatpay-Serial": "...",
            },
            body=json.dumps(mock_notification),
        )
        print(f"✅ 解密成功: {event_type}")
        print(f"   交易单号: {data.get('transaction_id', 'N/A')}")
        print(f"   金额: {data.get('amount', {}).get('total', 0) / 100} 元")
    except Exception as e:
        print(f"⚠️  回调解密/验签未通过 (预期行为，因为使用的是示例数据): {e}")

    # ==================== 3. 查询订单 ====================
    print(f"\n" + "=" * 60)
    print("🔍 查询订单状态...")
    print("   (实际调用需替换为真实的商户号、密钥、订单号)")
    print(f"\n   代码: pay.query_order(out_trade_no='{resp.get('out_trade_no', 'ORDER...')}')")

    print(f"\n" + "=" * 60)
    print("🎉 示例完成! 接入微信支付就这么简单。")
    print("   ⭐ 如果觉得有用，欢迎 GitHub Sponsor!")
    print("   https://github.com/sponsors/20111110wyx")


if __name__ == "__main__":
    main()
