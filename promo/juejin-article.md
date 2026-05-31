# 微信支付 API v3 签名原理深度解析：为什么你总是 401 SIGN_ERROR？

## 引言

接入微信支付 API v3 的第一关——签名，大概劝退了 80% 的开发者。

照着官方文档一步一步来，curl 就是返回：

```json
{"code":"SIGN_ERROR","message":"签名错误"}
```

本文从原理出发，带你彻底搞懂微信支付 API v3 的签名机制，并给出一个开箱即用的 Python 工具包。

---

## 一、签名流程全景

微信支付 API v3 使用 **HTTP 签名**（类似 Amazon Signature V4），核心流程：

```
HTTP方法 + URL + 时间戳 + 随机串 + 请求体
           ↓
      拼接签名串
           ↓
    SHA256-RSA2048 签名（商户私钥）
           ↓
      构造 Authorization 头
           ↓
      发送 HTTP 请求
```

### 签名串的格式（最容易错的一步）

```
HTTP请求方法\n
URL（仅路径，不含域名）\n
时间戳\n
随机字符串\n
请求报文主体\n
```

**注意每一个 `\n` 都是真的换行符，不是字面字符串！** 这是踩坑重灾区。

---

## 二、签名实现（逐行拆解）

### 2.1 加载商户私钥

```python
from cryptography.hazmat.primitives.serialization import load_pem_private_key

with open("apiclient_key.pem", "rb") as f:
    private_key = load_pem_private_key(f.read(), password=None)
```

关键点：微信商户平台上「API 安全」→「申请 API 证书」下载的 `apiclient_key.pem`，不是 `apiclient_cert.pem`。

### 2.2 构造签名串

```python
def build_sign_string(method, url, timestamp, nonce_str, body):
    if body is None:
        body_str = ""
    elif isinstance(body, str):
        body_str = body
    else:
        body_str = json.dumps(body, separators=(",", ":"), ensure_ascii=False)

    return f"{method.upper()}\n{url}\n{timestamp}\n{nonce_str}\n{body_str}\n"
```

⚠️ 这里三个陷阱：

1. **body 为 None 时用空字符串**，不是 `"null"` 或 `"None"`
2. **JSON 序列化不要多余空格**：`separators=(",", ":")` 
3. **签名串末尾必须有一个换行符 `\n`**

最后这个换行符——无数人卡在这里。

### 2.3 SHA256-RSA2048 签名

```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import base64

signature = private_key.sign(
    sign_string.encode("utf-8"),
    padding.PKCS1v15(),        # 微信用的是 PKCS#1 v1.5
    hashes.SHA256()            # 哈希算法 SHA256
)
signature_b64 = base64.b64encode(signature).decode("utf-8")
```

### 2.4 构造 Authorization 响应头

```python
auth = (
    f'WECHATPAY2-SHA256-RSA2048 '
    f'mchid="{mchid}",'
    f'nonce_str="{nonce_str}",'
    f'signature="{signature_b64}",'
    f'timestamp="{timestamp}",'
    f'serial_no="{serial_no}"'
)
```

最终效果：

```
Authorization: WECHATPAY2-SHA256-RSA2048 mchid="1900000001",nonce_str="abc123...",signature="ABCD...",timestamp="1717171200",serial_no="ABC123..."
```

---

## 三、5 个高频踩坑

### ❌ 坑 1：签名串末尾少 `\n`

签名串最后一行（body 后面）必须有一个 `\n`。官方文档提到了但不明显，很多人漏掉。

### ❌ 坑 2：URL 包含域名

签名串的 URL 只取路径部分：
- ✅ `/v3/pay/transactions/jsapi`
- ❌ `https://api.mch.weixin.qq.com/v3/pay/transactions/jsapi`

### ❌ 坑 3：JSON 序列化多了空格

```python
# ✅ 正确
body = json.dumps({"a": 1})
# → '{"a":1}'

# ❌ 错误
body = json.dumps({"a": 1}, indent=2)
# → '{\n  "a": 1\n}'   ← 签名会错！
```

### ❌ 坑 4：GET 请求带了 body

GET 请求签名时 body 用空字符串 `""`，而不是 `None` 转成的字符串。

### ❌ 坑 5：时间戳差太多

微信服务器容忍 5 分钟误差。确保服务器时间准确。

---

## 四、回调解密：AES-GCM

支付成功后微信回调你的服务器，但 `resource` 字段是加密的：

```json
{
  "resource": {
    "algorithm": "AEAD_AES_256_GCM",
    "ciphertext": "base64...",
    "nonce": "base64...",
    "associated_data": ""
  }
}
```

解密步骤：

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# 1. 解码
ciphertext = base64.b64decode(resource["ciphertext"])
nonce = base64.b64decode(resource["nonce"])
aad = resource["associated_data"].encode("utf-8")

# 2. 解密（api_v3_key 是商户平台设置的 32 字节密钥）
aesgcm = AESGCM(api_v3_key.encode("utf-8"))
plaintext = aesgcm.decrypt(nonce, ciphertext, aad)

# 3. 反序列化
order_data = json.loads(plaintext.decode("utf-8"))
print(order_data["out_trade_no"])  # 商户订单号
print(order_data["trade_state"])   # SUCCESS
```

---

## 五、一行代码解决

我把上面所有逻辑封装成了 wxpay-devkit：

```bash
pip install wxpay-devkit
```

### 30 秒接入支付

```python
from wxpay_devkit import WechatPay

pay = WechatPay(
    mchid="1900000001",
    serial_no="YOUR_SERIAL",
    private_key_path="apiclient_key.pem",
    api_v3_key="your-api-v3-key"
)

# Native 扫码支付
resp = pay.native_pay(
    appid="wx1234567890",
    description="测试商品",
    out_trade_no="ORDER001",
    amount_total=500,  # 5 元
    notify_url="https://your-domain.com/notify"
)
print(resp["code_url"])  # → 拿去生成二维码
```

### 回调处理：5 行

```python
from wxpay_devkit import CallbackHandler

handler = CallbackHandler(api_v3_key="your-api-v3-key")
event_type, data = handler.decrypt_and_parse(
    request.headers, request.body
)
# data = {"out_trade_no": "ORDER001", "trade_state": "SUCCESS", ...}
```

---

## 六、总结

微信支付 API v3 的签名机制其实不复杂，但文档细节太多、容易遗漏。核心就记住三件事：

1. 签名串格式：`METHOD\nURL\nTIMESTAMP\nNONCE\nBODY\n`
2. 签名算法：SHA256-RSA2048（商户私钥）
3. 回调解密：AEAD_AES_256_GCM（API v3 密钥）

希望这篇文章帮你少走弯路。

项目地址：[github.com/20111110wyx-droid/wxpay-devkit](https://github.com/20111110wyx-droid/wxpay-devkit)

如果对你有帮助，⭐ Star 或者 ☕ Sponsor 支持一下。我还在逐步扩展合单支付、分账、商品券等功能，敬请期待！

---

*作者：20111110wyx-droid | MIT 开源 | 欢迎 PR*
