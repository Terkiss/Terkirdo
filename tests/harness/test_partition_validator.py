import unittest
import sys
import json
import subprocess
from pathlib import Path

class TestPartitionValidator(unittest.TestCase):
    def setUp(self):
        self.base_dir = Path(__file__).parent.parent.parent
        self.script_path = self.base_dir / ".agents" / "skills" / "agent-legion" / "scripts" / "partition_validator.py"
        self.assertTrue(self.script_path.is_file(), f"Validator not found: {self.script_path}")

    def run_validator(self, data):
        res = subprocess.run(
            [sys.executable, str(self.script_path), "--json"],
            input=json.dumps(data),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return res.returncode, json.loads(res.stdout)

    def test_disjoint_up_to_8_ralph_partitions_pass(self):
        data = {
            "partitions": [
                {"id": "ralph_1", "allowed_files": ["lib/core/auth.dart", "lib/core/token.dart"]},
                {"id": "ralph_2", "allowed_files": ["lib/features/cart/cart_page.dart"]},
                {"id": "ralph_3", "allowed_files": ["lib/features/profile/profile_view.dart"]},
                {"id": "ralph_4", "allowed_files": ["lib/features/orders/order_service.dart"]},
                {"id": "ralph_5", "allowed_files": ["lib/features/billing/billing_repo.dart"]},
                {"id": "ralph_6", "allowed_files": ["lib/features/notify/push_gateway.dart"]},
                {"id": "ralph_7", "allowed_files": ["lib/features/search/search_index.dart"]},
                {"id": "ralph_8", "allowed_files": ["lib/features/audit/audit_logger.dart"]},
            ]
        }
        code, out = self.run_validator(data)
        self.assertEqual(code, 0)
        self.assertEqual(out["status"], "PASSED")
        self.assertEqual(out["summary"]["partition_count"], 8)
        self.assertEqual(out["summary"]["max_concurrent_ralph_limit"], 8)
        self.assertEqual(out["summary"]["total_files"], 9)

    def test_exceeding_max_8_concurrent_ralph_fails(self):
        data = {
            "partitions": [
                {"id": "ralph_1", "allowed_files": ["a.py"]},
                {"id": "ralph_2", "allowed_files": ["b.py"]},
                {"id": "ralph_3", "allowed_files": ["c.py"]},
                {"id": "ralph_4", "allowed_files": ["d.py"]},
                {"id": "ralph_5", "allowed_files": ["e.py"]},
                {"id": "ralph_6", "allowed_files": ["f.py"]},
                {"id": "ralph_7", "allowed_files": ["g.py"]},
                {"id": "ralph_8", "allowed_files": ["h.py"]},
                {"id": "ralph_9", "allowed_files": ["i.py"]},
            ]
        }
        code, out = self.run_validator(data)
        self.assertEqual(code, 1)
        self.assertEqual(out["status"], "FAILED")
        self.assertTrue(any("at most 8 concurrent ralph-orchestrator" in err for err in out["errors"]))

    def test_multi_wave_up_to_8_per_wave_passes(self):
        data = {
            "partitions": [
                {"id": "w1_ralph_1", "wave": 1, "allowed_files": ["a.py"]},
                {"id": "w1_ralph_2", "wave": 1, "allowed_files": ["b.py"]},
                {"id": "w1_ralph_3", "wave": 1, "allowed_files": ["c.py"]},
                {"id": "w1_ralph_4", "wave": 1, "allowed_files": ["d.py"]},
                {"id": "w1_ralph_5", "wave": 1, "allowed_files": ["e.py"]},
                {"id": "w1_ralph_6", "wave": 1, "allowed_files": ["f.py"]},
                {"id": "w1_ralph_7", "wave": 1, "allowed_files": ["g.py"]},
                {"id": "w1_ralph_8", "wave": 1, "allowed_files": ["h.py"]},
                {"id": "w2_ralph_1", "wave": 2, "allowed_files": ["i.py"]},
                {"id": "w2_ralph_2", "wave": 2, "allowed_files": ["j.py"]},
                {"id": "w2_ralph_3", "wave": 2, "allowed_files": ["k.py"]},
                {"id": "w2_ralph_4", "wave": 2, "allowed_files": ["l.py"]},
            ]
        }
        code, out = self.run_validator(data)
        self.assertEqual(code, 0)
        self.assertEqual(out["status"], "PASSED")
        self.assertEqual(out["summary"]["wave_count"], 2)
        self.assertEqual(out["summary"]["partition_count"], 12)

    def test_conflicting_partitions_fail(self):
        data = {
            "partitions": [
                {"id": "ralph_1", "allowed_files": ["lib/core/auth.dart", "lib/common/utils.dart"]},
                {"id": "ralph_2", "allowed_files": ["lib/common/utils.dart", "lib/features/home/home.dart"]},
            ]
        }
        code, out = self.run_validator(data)
        self.assertEqual(code, 1)
        self.assertEqual(out["status"], "FAILED")
        self.assertTrue(any("lib/common/utils.dart" in err for err in out["errors"]))

    def test_empty_allowed_files_fail(self):
        data = {
            "partitions": [
                {"id": "part_empty", "allowed_files": []}
            ]
        }
        code, out = self.run_validator(data)
        self.assertEqual(code, 1)
        self.assertEqual(out["status"], "FAILED")

if __name__ == "__main__":
    unittest.main()
