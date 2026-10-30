import tempfile
import unittest
from pathlib import Path

from fishbridge.adapters import DemoResponder, JsonlSender, JsonlSource
from fishbridge.core import Engine, Ledger, Message, Receipt


class BridgeTests(unittest.TestCase):
    def setUp(self):
        test_root = Path(__file__).resolve().parents[1] / '.test-tmp'
        test_root.mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=test_root)
        self.root = Path(self.tmp.name)
        self.ledger = Ledger(self.root / "ledger.db")
        self.message = Message("demo", "me", "room", "1", "friend", "hello", "2026-10-30")
        self.calls = 0
        outer = self
        class Send:
            def send(self, message, text, operation_id):
                outer.calls += 1
                return Receipt("local_confirmed")
        self.sender = Send()
        self.engine = Engine(self.ledger, DemoResponder(), self.sender,
                             {("demo", "me", "room")}, live=True)

    def tearDown(self):
        self.ledger.close()
        self.tmp.cleanup()

    def test_success_and_dedup(self):
        self.assertEqual(self.engine.process(self.message), "local_confirmed")
        self.assertEqual(self.engine.process(self.message), "duplicate")
        self.assertEqual(self.calls, 1)

    def test_default_dry_run(self):
        self.engine.live = False
        self.assertEqual(self.engine.process(self.message), "dry_run")
        self.assertEqual(self.calls, 0)

    def test_deny(self):
        self.engine.allowed = set()
        self.assertEqual(self.engine.process(self.message), "denied")
        self.assertEqual(self.calls, 0)

    def test_self(self):
        from dataclasses import replace
        self.assertEqual(self.engine.process(replace(self.message, is_self=True)), "ignored_self")

    def test_timeout_never_retried(self):
        def fail(*args):
            self.calls += 1
            raise TimeoutError()
        self.sender.send = fail
        self.assertEqual(self.engine.process(self.message), "unknown")
        self.assertEqual(self.engine.process(self.message), "duplicate")
        self.assertEqual(self.calls, 1)

    def test_restart_preserves_uncertainty(self):
        self.ledger.claim(self.message)
        self.ledger.update(self.message.key, "sending")
        self.ledger.close()
        self.ledger = Ledger(self.root / "ledger.db")
        self.engine.ledger = self.ledger
        self.assertEqual(self.engine.process(self.message), "duplicate")
        self.assertEqual(self.ledger.state(self.message.key), "sending")
        self.assertEqual(self.calls, 0)

    def test_generation_failure(self):
        self.engine.responder.reply = lambda message: ""
        self.assertEqual(self.engine.process(self.message), "generation_failed")
        self.assertEqual(self.calls, 0)

    def test_scoped_identity(self):
        from dataclasses import replace
        self.assertNotEqual(self.message.key, replace(self.message, account="other").key)
        self.assertNotEqual(self.message.key, replace(self.message, conversation="other").key)

    def test_missing_path(self):
        with self.assertRaises(FileNotFoundError):
            JsonlSource(self.root / "missing").poll()

    def test_simulated_is_not_delivered(self):
        self.engine.sender = JsonlSender(self.root / "out.jsonl")
        self.assertEqual(self.engine.process(self.message), "simulated")

    def test_invalid_receipt(self):
        self.sender.send = lambda *args: True
        self.assertEqual(self.engine.process(self.message), "unknown")

    def test_validation(self):
        with self.assertRaises(ValueError):
            Receipt("delivered")
        with self.assertRaises(ValueError):
            Message("", "me", "room", "1", "friend", "hi", "today")


if __name__ == "__main__":
    unittest.main()
