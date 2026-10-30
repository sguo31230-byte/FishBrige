# 适配器契约

1. `poll()` 返回标准 Message 列表。每条消息必须保留稳定原生事件ID，读取水位由适配器管理。
   无稳定ID的软件需要先设计可靠身份策略，不可每次轮询生成新ID。
2. `Responder.reply(message)` 返回非空、最多4000字符正文。模型调用必须在连接器中设置网络超时、
   输出预算和取消机制；核心不会开启循环，也不会执行模型返回的工具指令。
3. `Sender.send(message, text, operation_id)` 接收确定的目标与幂等操作ID。
   一个桌面账号只能有一个发送工作者；多进程UI互斥由适配器实现。
4. 发送前核验账号、会话稳定身份、窗口状态和输入框。不能仅凭重名昵称选择目标。
5. 超时或点击之后无法确认时返回 unknown；确定未发送才可 failed。
   入队成功、粘贴成功、点击成功都不是 local_confirmed。
6. local_confirmed 需要本地消息回查，关联目标、内容与时间；保留证据引用但不要默认记录聊天正文。
7. 图片、表情与引用消息尚未纳入 v0.1 契约；不要把图片占位文本冒称视觉理解。

最小示例（仅展示接口，不能直接发送）：

```python
from fishbridge.core import Receipt

class DesktopSender:
    def send(self, message, text, operation_id):
        # 实现账号锁、目标校验、UI操作和独立消息回查之后再开放。
        return Receipt('failed', 'adapter_not_implemented')
```

验收必须覆盖错误会话、同名联系人、窗口关闭、附件未就绪、重复轮询、
点击后崩溃、回执超时。先使用测试账号和用户指定的单一会话。
