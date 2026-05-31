# 微信支付 API v3 签名搞到崩溃？写了个工具箱，30 秒搞定

最近在接微信支付 API v3，被三个问题折磨得够呛：

1. **签名算不对** —— 照着文档一步步来，永远给你 401 SIGN_ERROR，排查半天发现是签名串最后多了一个换行符
2. **回调解不开** —— AES-GCM 解密，`AEAD_AES_256_GCM` 参数搞不明白，文档翻烂了
3. **证书晕头转向** —— 商户证书、平台证书、序列号，哪个用在哪个地方完全记不住

于是花了一个周末，把这套流程封装成了一个 Python 工具包：**wxpay-devkit**

## 能做什么

```python
from wxpay_devkit import Signer

# 30 秒生成 Authorization 签名头
signer = Signer(mchid="1900000001", serial_no="xxx", private_key_path="key.pem")
headers = signer.sign_header_dict("POST", "/v3/pay/transactions/native", body)
# → 直接塞进 requests，完事
```

```python
from wxpay_devkit import CallbackHandler

# 5 行代码解密回调通知
handler = CallbackHandler(api_v3_key="your-key")
event_type, data = handler.decrypt_and_parse(request.headers, request.body)
# → 拿到解密后的订单数据，直接入库
```

## 特点

- 零依赖理解微信支付文档，直接用
- 支持 Native/JSAPI/H5/APP 四种支付方式
- 内置签名、验签、回调解密、订单查询、退款
- MIT 开源，随便用

## 项目地址

👉 [github.com/20111110wyx-droid/wxpay-devkit](https://github.com/20111110wyx-droid/wxpay-devkit)

如果觉得有用，给个 Star ⭐ 或者 Sponsor 一杯咖啡 ☕（5 块就行），有动力继续加合单支付和商品券的功能。

也欢迎提 Issue 和 PR，一起把这个工具做完善 🙏
