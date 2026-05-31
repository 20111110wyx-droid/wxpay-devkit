# 🧧 WeChat Pay DevKit

> 微信支付开发者工具箱 —— 一站式解决签名、验签、解密、下单、回调处理

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Sponsor](https://img.shields.io/badge/Sponsor-♥-ea4aaa?logo=github)](https://github.com/sponsors/20111110wyx-droid)

## 😤 为什么要做这个？

微信支付 API v3 接入有三座大山：
1. **签名算不对** — 各种 401 SIGN_ERROR
2. **回调解不开** — AES-GCM / AEAD_AES_256_GCM 一脸懵
3. **证书绕不明白** — 平台证书、商户证书傻傻分不清

本工具 100 行代码解决全部问题。

## 🚀 快速开始

```bash
pip install wxpay-devkit
```

### 30 秒搞定签名

```python
from wxpay_devkit import Signer

signer = Signer(
    mchid="1900000001",
    serial_no="YOUR_SERIAL_NO",
    private_key_path="/path/to/apiclient_key.pem"
)

# 生成 Authorization 头
auth_header = signer.sign(
    method="POST",
    url="/v3/pay/transactions/jsapi",
    body={"appid": "wx...", "mchid": "...", "amount": {"total": 1}}
)

print(auth_header)
# WECHATPAY2-SHA256-RSA2048 mchid="1900000001",nonce_str="...",signature="...",...
```

### 5 行代码解密回调

```python
from wxpay_devkit import CallbackHandler

handler = CallbackHandler(api_v3_key="your-api-v3-key")

# 自动解密 resource 字段
decrypted = handler.decrypt(headers, body)
print(decrypted["out_trade_no"])  # "ORDER20240531001"
```

## 📦 功能

| 功能 | 说明 |
|---|---|
| 🔐 签名生成 | 自动生成 `Authorization` 请求头，支持 GET/POST/PUT/DELETE |
| 🔓 回调解密 | 自动解析回调通知，解密 `resource` 字段，验证签名 |
| 📜 证书管理 | 自动下载/更新微信支付平台证书 |
| 🧪 沙箱测试 | 内置测试用例，一键验证签名逻辑 |
| 📝 完整示例 | Native/JSAPI/H5/APP 下单 + 回调处理示例 |

## 📖 示例

```python
from wxpay_devkit import WechatPay

pay = WechatPay(
    mchid="1900000001",
    serial_no="YOUR_SERIAL_NO",
    private_key_path="/path/to/apiclient_key.pem",
    api_v3_key="your-api-v3-key"
)

# Native 下单
resp = pay.native_pay(
    appid="wx1234567890",
    description="测试商品-5块钱",
    out_trade_no="ORDER20240531001",
    amount_total=500,  # 金额：分 (500 = 5元)
    notify_url="https://your-domain.com/notify"
)

print(resp["code_url"])  # weixin://wxpay/bizpayurl?pr=...
```

## 🗺️ 路线图

- [x] 签名 / 验签工具
- [x] 回调解密
- [x] Native / JSAPI 支付示例
- [ ] 合单支付支持
- [ ] 分账接口
- [ ] 商品券支持
- [ ] GUI 调试面板

## 🤝 贡献

欢迎 PR / Issue / Star ⭐

## 💝 支持项目

如果这个工具帮你省了时间，请考虑 [Sponsor](https://github.com/sponsors/20111110wyx-droid) —— 一杯咖啡的钱，支持我写出更好的开发者工具。

---

## ☕ 支持作者

如果这个项目帮你省了时间，欢迎请我喝杯奶茶～

<div align="center">
  <img src="assets/wechat-qrcode.jpg" width="240" alt="微信赞赏码"/>
  <br/>
  <sub>微信扫码 · 5 块钱也能开心一整天 🧧</sub>
</div>

---

> Made with ❤️ for WeChat Pay developers.
