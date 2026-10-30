import subprocess
import sys
import json
import unittest
from pathlib import Path

HOOK_PATH = str(Path(__file__).parent.parent.parent / ".agents" / "hooks" / "pre_tool_use_policy.py")

class TestPreToolHook(unittest.TestCase):
    def run_pre_hook(self, payload_dict, env=None):
        res = subprocess.run(
            [sys.executable, HOOK_PATH],
            input=json.dumps(payload_dict),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        try:
            decision = json.loads(res.stdout.strip())
        except Exception as e:
            raise ValueError(f"Stdout was not valid JSON: {res.stdout}. Stderr: {res.stderr}") from e
        return decision, res.stderr

    def test_pre_hook_allow_commands(self):
        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "npm test"}
            }
        }
        decision, _ = self.run_pre_hook(payload)
        self.assertEqual(decision["decision"], "allow")

        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git status --short"}
            }
        }
        decision, _ = self.run_pre_hook(payload)
        self.assertEqual(decision["decision"], "allow")

        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git clean -n"}
            }
        }
        decision, _ = self.run_pre_hook(payload)
        self.assertEqual(decision["decision"], "allow")

    def test_pre_hook_deny_commands(self):
        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "rm -rf /"}
            }
        }
        decision, _ = self.run_pre_hook(payload)
        self.assertEqual(decision["decision"], "deny")

        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git reset --hard"}
            }
        }
        decision, _ = self.run_pre_hook(payload)
        self.assertEqual(decision["decision"], "deny")

    def test_pre_hook_force_ask_commands(self):
        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "terraform apply"}
            }
        }
        decision, _ = self.run_pre_hook(payload)
        self.assertEqual(decision["decision"], "force_ask")

        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "firebase deploy"}
            }
        }
        decision, _ = self.run_pre_hook(payload)
        self.assertEqual(decision["decision"], "force_ask")

    def test_pre_hook_write_sensitive(self):
        payload = {
            "toolCall": {
                "name": "write_to_file",
                "args": {
                    "TargetFile": ".env",
                    "CodeContent": "AWS_SECRET_ACCESS_KEY=\"AIzaFakeSecretKey1234567890\""
                }
            }
        }
        decision, _ = self.run_pre_hook(payload)
        self.assertEqual(decision["decision"], "deny")

        payload = {
            "toolCall": {
                "name": "write_to_file",
                "args": {
                    "TargetFile": ".env",
                    "CodeContent": "PORT=8080"
                }
            }
        }
        decision, _ = self.run_pre_hook(payload)
        self.assertEqual(decision["decision"], "force_ask")

    def test_pre_hook_false_positive(self):
        payload = {
            "toolCall": {
                "name": "write_to_file",
                "args": {
                    "TargetFile": "docs/security.md",
                    "CodeContent": "To use this, specify your key as `sk-abcdefg1234567` in config."
                }
            }
        }
        decision, _ = self.run_pre_hook(payload)
        self.assertEqual(decision["decision"], "allow")

    def test_pre_hook_legion_commander_conversational_denied(self):
        payload = {
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "TypeName": "legion-commander",
                    "Role": "Legion Commander",
                    "Prompt": "에이전트 군단을 가동해서 이 대규모 작업을 병렬로 구현해줘"
                }
            }
        }
        decision, _ = self.run_pre_hook(payload)
        self.assertEqual(decision["decision"], "deny")
        self.assertIn("Slash-Command-Only", decision["reason"])

    def test_pre_hook_legion_commander_slash_command_allowed(self):
        payload = {
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "TypeName": "legion-commander",
                    "Role": "Legion Commander",
                    "Prompt": "[SLASH_TRIGGER: /agent-legion] 대규모 멀티 모듈 병렬 구현 수행"
                }
            }
        }
        decision, _ = self.run_pre_hook(payload)
        self.assertEqual(decision["decision"], "allow")

        payload_short = {
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "TypeName": "legion-commander",
                    "Role": "Legion Commander",
                    "Prompt": "/legion 대규모 리팩터링 병렬 수행"
                }
            }
        }
        decision_short, _ = self.run_pre_hook(payload_short)
        self.assertEqual(decision_short["decision"], "allow")

if __name__ == "__main__":
    unittest.main()
