# FishBridge · 小鱼桥

**FishBridge 是面向 AI 智能体的跨聊天平台通信桥接框架。**

它把「读消息 → 判要不要回 → 生成 → 串行发送 → 核验」拆成可替换的三个接口
（`MessageSource` / `Responder` / `Sender`），核心不绑定任何平台、昵称或模型。
换一个软件 = 写一个适配器，不用改核心。

> **v0.1.0 已提供通用核心和本地演示，微信、QQ 真实适配器尚未完成。**

```
软件适配器 MessageSource
           ↓ 标准 Message（平台 / 账号 / 会话 / 稳定原生事件 ID）
范围白名单 + 自身消息过滤
           ↓ SQLite 原子领取（claimed）
Responder（可接 DSH、其它模型，或纯规则）
           ↓ 生成校验 / 默认 dry-run
Sender（适配器负责串行化界面操作与目标核对）
           ↓ 明确回执
local_confirmed / failed / unknown / simulated
```

| 现在能用 | 还没有 |
|---|---|
标准消息与稳定事件键 | 真实聊天软件适配器（微信 / QQ / 飞书…）|
SQLite 台账：`claimed → sending → 回执` | DSH 模型连接器 |
范围白名单（平台 + 账号 + 会话）| 媒体、表情、引用消息 |
默认 dry-run，显式开启才发送 | 速率限制与节奏控制 |
崩溃恢复：不自动重发、不确定就标 `unknown` | 进程隔离与连接器超时取消 |
本地 JSONL 演示 + 12 个单元测试 | 生产级安装与长期运行验证 |

**当前可以运行的是本地 JSONL 演示，不是已经接通微信或 QQ 的机器人。**
没有防检测、绕过风控、注入客户端或破解协议功能。

## 我们不做什么（硬约束）

这四条是项目边界，**不接受违反它们的贡献**：

1. 不做**检测规避** —— 不研究怎么不被发现，不提供指纹伪装、多账号轮换、代理池
2. 不做**协议逆向** —— 不模拟官方客户端、不破解加密、不读其它进程内存、不注入
3. 不碰**未经授权的接入** —— 只接官方 API 与官方可访问性接口（UIA / AX / CDP / 扩展 API）
4. 不**代用户决定发送** —— 默认不发送，允许范围必须显式配置

理由不是姿态，是工程判断：对抗式方案的生命周期只有"到对方下一次更新为止"，
而且一旦被判定为绕过，处罚通常没有申诉入口。**能长期维护的只有被授权的那条路。**

## 已知限制（v0.1）

- **`local_confirmed` 目前由适配器自报**，核心不做独立核验 ——
  也就是说，适配器可以"自称发送成功"。0.2 会把核验改成核心驱动的三态探测
  （`present` / `absent` / `inconclusive`），适配器只能提供探测方法，不能直接给结论。
- 同一事件崩溃后**不会重发**（防重复优先），因此可能漏回，需要人工核对台账。
- 无速率限制/节奏控制（计划 0.2）。
- 只在本机 Windows + Python 3.12 实测；3.11 由 CI 覆盖，未在真机手工验证。
- 无真实平台适配器，`docs/ADAPTERS.md` 里的 `DesktopSender` 只是接口示例。

## 快速运行（Windows PowerShell，Python 3.11+）

无需安装依赖：

```powershell
$env:PYTHONPATH = 'src'
python -m fishbridge.cli --input examples/messages.jsonl --allow demo/local/friends
python -m fishbridge.cli --input examples/messages.jsonl --data .fishbridge-demo --allow demo/local/friends --emit-demo
python -m unittest discover -s tests -v
```

第一条仅 dry-run；第二条只写本地 outbox.jsonl，结果标为 simulated。
两个命令用不同数据库，避免已领取的 dry-run 事件被重新执行。
重复运行第二条显示 duplicate，不重复写出。清理测试数据请只操作你自己的演示目录。
也可 `python -m pip install -e .` 后使用 `fishbridge` 命令。

## 架构

```
软件适配器 MessageSource
           ↓ 标准 Message（平台/账号/会话/稳定事件ID）
范围白名单 + 自身消息过滤
           ↓ SQLite 原子领取
Responder（可替换为 DSH、其他模型或规则）
           ↓ 生成校验 / 默认 dry-run
Sender（适配器负责串行化界面操作与目标核对）
           ↓ 明确回执
local_confirmed / failed / unknown / simulated
```

核心不依赖微信昵称、QQ 协议或特定模型。MessageSource、Responder、Sender
是三个 Python Protocol，写适配器不需要改核心。消息只能作为数据，核心不执行聊天中的命令、代码或链接。

## 状态与恢复

- 每条事件由平台、账号、会话和原生事件ID构成稳定键。
- claimed 在调用模型前落盘；sending 在外部发送前落盘。
- 崩溃留下 claimed/sending，或异常进入 unknown，均不会自动重发。
- failed 同样不自动重试；操作者先核对原软件，再设计显式新操作。
- local_confirmed 只允许表示本机客户端可核验，不能表示对方手机收到或已读。
- 当前选择防重复优先，可能漏回；不承诺外部操作 exactly-once。
- SQLite 台账不保存正文、人格或密钥。演示 outbox 会保存演示正文，请勿输入真实隐私。

## 接入进度

| 适配器 | 当前状态 |
|---|---|
| 本地 JSONL | 已实现，可测试 |
| DSH 模型 | 接口已定义，尚未实现连接器 |
| 微信桌面 | 接口已定义，原项目能力尚未迁移 |
| QQ | 接口已定义，未实现、未在线验证 |
| 其他软件 | 可实现 MessageSource / Sender 接入 |

QQ 优先评估平台允许的机器人接入；桌面 UI 接入需要独立验证可访问性、目标身份、
发送回执以及平台使用要求。模拟键鼠也不保证不会触发限制。此仓库不声明任何平台官方授权。

参见 [适配器开发](docs/ADAPTERS.md)、[开发路线](docs/ROADMAP.md)、[安全边界](SECURITY.md)。

## 许可与发布

新代码采用 MIT。当前仅生成了本地项目，没有创建 GitHub 仓库或对外上传。
迁移原项目/第三方代码前须核对其许可证，不能因这个项目 MIT 就自动覆盖其他来源许可。
