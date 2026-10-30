# 变更记录

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.1.0] · 2026-10-30

首个预览版。**只包含本地演示适配器，尚未接通任何真实聊天软件。**

### 新增

- 标准消息对象：`platform / account / conversation / event_id / sender / text / timestamp`
  —— 稳定键由**原生事件 id** 派生，不依赖轮询序号
- 三个 `Protocol` 接口：`MessageSource` / `Responder` / `Sender`
- SQLite 台账：`claimed → sending → local_confirmed / failed / unknown`
  —— `claimed` 在调模型之前落盘，`sending` 在发送之前落盘
- 范围白名单（平台 + 账号 + 会话三元组），默认不匹配即拒绝
- 默认 **dry-run**，必须显式开启才写出
- 保守恢复：`unknown` / `failed` **不自动重试**；崩溃留下的 `sending` 不重放
- 本地 JSONL 演示适配器 + 演示响应器
- 12 个单元测试，覆盖重复事件、越权会话、自身消息、发送超时、
  重启后不确定状态保留、空正文、非法回执、文件缺失

### 明确未做

- 未接通微信、QQ 或任何真实平台
- 未实现 DSH 模型连接器
- 未做媒体/表情/引用消息
- 未做进程隔离、连接器超时取消
- 未做速率限制与节奏控制（计划 0.2）

### 已知限制

- `local_confirmed` 目前由**适配器自报**，核心不做独立核验。
  也就是说：适配器可以"自称发送成功"。0.2 会把核验改成核心驱动的三态探测
  （`present` / `absent` / `inconclusive`），届时适配器只能提供探测方法，
  不能直接给出结论。
- 同一事件崩溃后不会重发（防重复优先），因此**可能漏回**，需要人工核对台账。
- 只在本机 Windows + Python 3.12 环境验证过；3.11 未实测。

### 不做

见 README「我们不做什么」。本版本不含任何防检测、协议逆向、客户端注入实现，
也不计划加入。
