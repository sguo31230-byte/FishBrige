"""Bundled adapters are local demonstrations; no private platform protocols."""
import json
from pathlib import Path

from .core import Message, Receipt


class JsonlSource:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def poll(self) -> list[Message]:
        # Fully validate before any side effect; bounded input.
        if self.path.stat().st_size > 1024 * 1024:
            raise ValueError("input exceeds 1 MiB")
        return [Message(**json.loads(line)) for line in
                self.path.read_text(encoding="utf-8").splitlines() if line.strip()]


class DemoResponder:
    def reply(self, message: Message) -> str:
        return "已收到：" + message.text[:200]


class JsonlSender:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def send(self, message: Message, text: str, operation_id: str) -> Receipt:
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"operation_id": operation_id,
                "platform": message.platform, "account": message.account,
                "conversation": message.conversation, "text": text,
                "receipt": "simulated"}, ensure_ascii=False) + "\n")
        return Receipt("simulated", "local JSONL output only")
