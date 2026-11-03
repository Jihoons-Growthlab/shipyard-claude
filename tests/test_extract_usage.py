"""Small stdlib-only smoke test for extract_usage.py."""
import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from extract_usage import aggregate


class UsageTests(unittest.TestCase):
    def test_deduplicates_message_snapshots_and_sums_caches(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "session.jsonl"
            ev1 = {
                "type": "assistant", "sessionId": "a",
                "message": {"id": "m1", "usage": {
                    "input_tokens": 2, "cache_creation_input_tokens": 3,
                    "cache_read_input_tokens": 4, "output_tokens": 5,
                }}
            }
            ev2 = {
                "type": "assistant", "sessionId": "a",
                "message": {"id": "m2", "usage": {
                    "input_tokens": 10, "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 0, "output_tokens": 8,
                }}
            }
            file.write_text("\n".join(json.dumps(o) for o in [ev1, ev1, ev2]) + "\n")
            result = aggregate(file)
            self.assertEqual(result["usage_messages"], 2)
            self.assertEqual(result["totals"]["prompt_total"], 19)
            self.assertEqual(result["totals"]["observed_total"], 32)


if __name__ == "__main__":
    unittest.main()
