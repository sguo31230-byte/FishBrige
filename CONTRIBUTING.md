# 贡献指南

先读 [SECURITY.md](SECURITY.md) 与 [README 的「我们不做什么」](README.md#我们不做什么硬约束)。
以下类型的提交**不会被接受**，请勿浪费时间：

- 检测规避、指纹伪装、多账号轮换、代理池
- 协议逆向、客户端注入、读取其它进程内存、破解加密数据库
- 自动发现并上传用户数据（聊天记录、联系人、密钥）
- 让核心执行聊天消息里的代码或命令

## 欢迎的贡献

| 类型 | 例子 |
|---|---|
官方 API 适配器 | 飞书、企业微信、Telegram、QQ 机器人开放平台 |
官方可访问性接口适配器 | Windows UIA、macOS AX、Chrome DevTools Protocol |
测试 | 崩溃恢复、并发领取、越权会话、异常回执 |
文档 | 适配器写法、核验方法、常见误用 |
缺陷 | 请附版本、错误类型与**脱敏**复现 |

## 开发步骤

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests -v     # 必须全绿
python -m fishbridge.cli --input examples/messages.jsonl --allow demo/local/friends
```

新增适配器时请遵守 [docs/ADAPTERS.md](docs/ADAPTERS.md) 的七条契约，
尤其是第 5、6 条：**"点击成功"不是确认**，确认需要独立的本地回查。

## 提交信息

```
feat(adapters): add feishu MessageSource
fix(core): reject empty event_id
docs: clarify local_confirmed vs simulated
```

## 隐私

测试与示例**不要**包含真实聊天内容、真实账号、真实密钥。
提交前请自查：`git diff` 里有没有个人信息。
