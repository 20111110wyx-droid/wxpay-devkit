# 贡献指南

感谢你对 WeChat Pay DevKit 的关注！欢迎任何形式的贡献。

## 如何贡献

### 🐛 报告问题

在 [Issues](https://github.com/20111110wyx-droid/wxpay-devkit/issues) 提交，请包含：

- 使用的 wxpay-devkit 版本
- Python 版本和操作系统
- 复现步骤
- 错误日志

### 🔧 提交代码

1. Fork 本仓库
2. 创建分支：`git checkout -b feat/your-feature`
3. 提交更改：`git commit -m "feat: 添加某某功能"`
4. 推送到你的仓库
5. 提交 Pull Request

### 📝 代码规范

- 使用 type hints
- 遵循 PEP 8
- 新功能需要添加测试

### 🧪 运行测试

```bash
python -m pytest tests/ -v
```

## 功能路线图

如果你不知道从哪开始，下面是想法：

- [ ] 合单支付 (Combine Orders)
- [ ] 分账接口 (Profit Sharing)
- [ ] 商品券 (Product Coupon)
- [ ] 微信支付分 (WeChat Pay Score)
- [ ] 支付即服务 (Payment As Service)
- [ ] Django/Flask/FastAPI 中间件
- [ ] CLI 命令行工具
- [ ] Web UI 调试面板

## 交流

- 提 Issue 是首选
- 也欢迎在 PR 下面直接讨论

---

再次感谢！你的 Star ⭐ 和 Sponsor 💝 是最大的动力。
