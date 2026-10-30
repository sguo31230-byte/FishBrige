from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, Protocol


@dataclass(frozen=True)
class Message:
    platform: str
    account: str
    conversation: str
    event_id: str  # Stable native ID, never a freshly generated polling ID.
    sender: str
    text: str
    timestamp: str
    is_self: bool = False

    def __post_init__(self):
        for key in ("platform", "account", "conversation", "event_id", "sender", "timestamp"):
            if not isinstance(getattr(self, key), str) or not getattr(self, key).strip():
                raise ValueError(f"{key} must be a nonempty string")
        if not isinstance(self.text, str) or type(self.is_self) is not bool:
            raise ValueError("invalid text or is_self")
        if len(self.text) > 16000:
            raise ValueError("message too long")

    @property
    def key(self) -> str:
        parts = [self.platform, self.account, self.conversation, self.event_id]
        return hashlib.sha256(json.dumps(parts, ensure_ascii=False).encode()).hexdigest()


@dataclass(frozen=True)
class Receipt:
    status: Literal["local_confirmed", "failed", "unknown", "simulated"]
    detail: str = ""

    def __post_init__(self):
        if self.status not in {"local_confirmed", "failed", "unknown", "simulated"}:
            raise ValueError("invalid receipt")


class MessageSource(Protocol):
    def poll(self) -> list[Message]: ...


class Responder(Protocol):
    def reply(self, message: Message) -> str: ...


class Sender(Protocol):
    def send(self, message: Message, text: str, operation_id: str) -> Receipt: ...


class Ledger:
    """SQLite claim happens before model/UI side effects. Never auto-retry unknowns."""

    def __init__(self, path: str | Path):
        self.db = sqlite3.connect(path, timeout=10)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("""CREATE TABLE IF NOT EXISTS operations (
            id TEXT PRIMARY KEY, platform TEXT NOT NULL, state TEXT NOT NULL,
            detail TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL
            DEFAULT CURRENT_TIMESTAMP)""")
        self.db.commit()

    def claim(self, message: Message) -> bool:
        with self.db:
            return self.db.execute(
                "INSERT OR IGNORE INTO operations(id,platform,state) VALUES (?,?,'claimed')",
                (message.key, message.platform)).rowcount == 1

    def update(self, key: str, state: str, detail: str = ""):
        with self.db:
            self.db.execute("UPDATE operations SET state=?,detail=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                            (state, detail, key))

    def state(self, key: str) -> str | None:
        row = self.db.execute("SELECT state FROM operations WHERE id=?", (key,)).fetchone()
        return row[0] if row else None

    def close(self):
        self.db.close()


class Engine:
    def __init__(self, ledger: Ledger, responder: Responder, sender: Sender,
                 allowed: set[tuple[str, str, str]], *, live: bool = False):
        self.ledger, self.responder, self.sender = ledger, responder, sender
        self.allowed, self.live = allowed, live

    def process(self, message: Message) -> str:
        if message.is_self:
            return "ignored_self"
        if (message.platform, message.account, message.conversation) not in self.allowed:
            return "denied"
        if not self.ledger.claim(message):
            return "duplicate"
        try:
            text = self.responder.reply(message)
            if not isinstance(text, str) or not text.strip() or len(text) > 4000:
                raise ValueError("invalid reply")
        except Exception as error:
            self.ledger.update(message.key, "generation_failed", type(error).__name__)
            return "generation_failed"
        if not self.live:
            self.ledger.update(message.key, "dry_run")
            return "dry_run"
        # Crash after this durable marker => uncertain, operator must reconcile.
        self.ledger.update(message.key, "sending")
        try:
            receipt = self.sender.send(message, text, message.key)
            if not isinstance(receipt, Receipt):
                raise TypeError("sender returned no receipt")
        except Exception as error:
            self.ledger.update(message.key, "unknown", type(error).__name__)
            return "unknown"
        self.ledger.update(message.key, receipt.status)
        return receipt.status
