import argparse
import json
from pathlib import Path

from .adapters import DemoResponder, JsonlSender, JsonlSource
from .core import Engine, Ledger


def main():
    parser = argparse.ArgumentParser(description="FishBridge local demo; no desktop messages sent")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--data", type=Path, default=Path(".fishbridge"))
    parser.add_argument("--allow", action="append", default=[], metavar="PLATFORM/ACCOUNT/CONVERSATION")
    parser.add_argument("--emit-demo", action="store_true", help="Write simulated replies to local JSONL")
    args = parser.parse_args()
    allowed = set()
    for item in args.allow:
        parts = item.split("/")
        if len(parts) != 3 or not all(parts):
            parser.error("--allow requires PLATFORM/ACCOUNT/CONVERSATION")
        allowed.add(tuple(parts))
    try:
        messages = JsonlSource(args.input).poll()
    except (OSError, ValueError, TypeError) as error:
        parser.exit(2, f"Invalid input: {type(error).__name__}\n")
    args.data.mkdir(parents=True, exist_ok=True)
    ledger = Ledger(args.data / "ledger.sqlite3")
    try:
        engine = Engine(ledger, DemoResponder(), JsonlSender(args.data / "outbox.jsonl"),
                        allowed, live=args.emit_demo)
        for message in messages:
            print(json.dumps({"event_key": message.key, "state": engine.process(message)}))
    finally:
        ledger.close()


if __name__ == "__main__":
    main()
