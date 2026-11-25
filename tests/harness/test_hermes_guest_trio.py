#!/usr/bin/env python3
"""Unit and integration tests for SPEC-20261125-HERMES-GUEST-TRIO-SWARM."""

import ast
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
HARNESS_DIR = SCRIPTS_DIR / "harness"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(HARNESS_DIR))

import hermes_guest  # noqa: E402
import sync_harness  # noqa: E402
import validate_harness  # noqa: E402


class TestHermesGuestTrio(unittest.TestCase):
    """Verify Hermes Guest AI Trio bridge, v0.23.1 sandbox flags, sync/validation, and docs."""

    def test_seat_preset_resolution_and_overrides(self):
        self.assertEqual(set(hermes_guest.GUEST_SEATS.keys()), {"deepseek", "qwen", "gpt"})

        label, prov, model = hermes_guest.resolve_seat(" DeepSeek ")
        self.assertEqual(label, "deepseek")
        self.assertEqual(prov, "alibaba-coding-plan")
        self.assertEqual(model, "deepseek-v4.1-flash")

        label, prov, model = hermes_guest.resolve_seat("qwen", provider="custom-prov", model="qwen-next")
        self.assertEqual(label, "qwen")
        self.assertEqual(prov, "custom-prov")
        self.assertEqual(model, "qwen-next")

        label, prov, model = hermes_guest.resolve_seat(None, provider="openai-codex", model="gpt-6-sol")
        self.assertEqual(label, "openai-codex/gpt-6-sol")
        self.assertEqual(prov, "openai-codex")
        self.assertEqual(model, "gpt-6-sol")

        with self.assertRaises(ValueError):
            hermes_guest.resolve_seat("unknown-seat")
        with self.assertRaises(ValueError):
            hermes_guest.resolve_seat(None, provider="openai-codex", model=None)

    def test_build_hermes_cmd_enforces_zero_tool_readonly_sandbox_and_session(self):
        fresh_cmd = hermes_guest.build_hermes_cmd(
            query_file="prompt.txt",
            provider="openai-codex",
            model="gpt-6-sol",
            resume_session_id=None,
            reasoning="high",
            run_budget=120,
            profile="custom-prof",
            hermes_bin="/usr/bin/hermes",
        )
        self.assertEqual(fresh_cmd[0:4], ["/usr/bin/hermes", "-p", "custom-prof", "chat"])
        self.assertIn("-Q", fresh_cmd)
        self.assertIn("--ignore-rules", fresh_cmd)
        self.assertEqual(fresh_cmd[fresh_cmd.index("--source") + 1], "tool")
        self.assertEqual(fresh_cmd[fresh_cmd.index("--max-turns") + 1], "1")
        self.assertEqual(fresh_cmd[fresh_cmd.index("-t") + 1], "")
        self.assertEqual(fresh_cmd[fresh_cmd.index("--run-budget") + 1], "120")
        self.assertEqual(fresh_cmd[fresh_cmd.index("--provider") + 1], "openai-codex")
        self.assertEqual(fresh_cmd[fresh_cmd.index("-m") + 1], "gpt-6-sol")
        self.assertEqual(fresh_cmd[fresh_cmd.index("--reasoning") + 1], "high")
        self.assertNotIn("--resume", fresh_cmd)
        self.assertNotIn("--continue", fresh_cmd)

        resumed_cmd = hermes_guest.build_hermes_cmd(
            query_file="prompt2.txt",
            provider="openai-codex",
            model="gpt-6-sol",
            resume_session_id="local-abc123",
            reasoning="high",
            run_budget=120,
            profile="custom-prof",
            hermes_bin="/usr/bin/hermes",
        )
        self.assertEqual(
            resumed_cmd,
            [
                "/usr/bin/hermes",
                "-p",
                "custom-prof",
                "chat",
                "--query-file",
                "prompt2.txt",
                "-Q",
                "--resume",
                "local-abc123",
                "--no-restore-cwd",
            ],
        )
        for forbidden_flag in (
            "-m",
            "--provider",
            "--reasoning",
            "--max-turns",
            "--ignore-rules",
            "-t",
            "--run-budget",
            "--source",
        ):
            self.assertNotIn(forbidden_flag, resumed_cmd)

    def test_named_session_persists_round1_and_resumes_round2_without_cross_model_collision(self):
        captured_cmds: list[list[str]] = []

        def fake_run(cmd, **kwargs):
            captured_cmds.append(list(cmd))
            if "--resume" in cmd:
                return subprocess.CompletedProcess(
                    args=cmd,
                    returncode=0,
                    stdout="ROUND2_OK\n",
                    stderr="session_id: local-r1-sid\n",
                )
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout="ROUND1_OK\n",
                stderr="session_id: local-r1-sid\n",
            )

        with tempfile.TemporaryDirectory() as store_tmp:
            store_dir = Path(store_tmp)
            with mock.patch("hermes_guest.shutil.which", return_value="hermes"), \
                 mock.patch("hermes_guest.subprocess.run", side_effect=fake_run):
                c1, out1, _ = hermes_guest.run_guest_query(
                    "deepseek",
                    "alibaba-coding-plan",
                    "deepseek-v4.1-flash",
                    "Round 1",
                    session="um-auth-deepseek",
                    session_store_dir=store_dir,
                )
                c2, out2, _ = hermes_guest.run_guest_query(
                    "deepseek",
                    "alibaba-coding-plan",
                    "deepseek-v4.1-flash",
                    "Round 2",
                    session="um-auth-deepseek",
                    session_store_dir=store_dir,
                )
                c3, out3, _ = hermes_guest.run_guest_query(
                    "qwen",
                    "alibaba-coding-plan",
                    "qwen4-max",
                    "Different model",
                    session="um-auth-deepseek",
                    session_store_dir=store_dir,
                )

        self.assertEqual((c1, out1), (0, "ROUND1_OK\n"))
        self.assertEqual((c2, out2), (0, "ROUND2_OK\n"))
        self.assertEqual((c3, out3), (0, "ROUND1_OK\n"))

        self.assertNotIn("--resume", captured_cmds[0])
        self.assertIn("--ignore-rules", captured_cmds[0])
        self.assertIn("--resume", captured_cmds[1])
        self.assertEqual(captured_cmds[1][captured_cmds[1].index("--resume") + 1], "local-r1-sid")
        self.assertNotIn("-m", captured_cmds[1])
        self.assertNotIn("--provider", captured_cmds[1])
        self.assertNotIn("--ignore-rules", captured_cmds[1])
        self.assertNotIn("--resume", captured_cmds[2])
        self.assertEqual(captured_cmds[2][captured_cmds[2].index("-m") + 1], "qwen4-max")

    def test_run_guest_query_cleans_temp_file_on_success_and_failure(self):
        created_paths: list[str] = []
        orig_ntf = tempfile.NamedTemporaryFile

        def tracking_ntf(*args, **kwargs):
            tf = orig_ntf(*args, **kwargs)
            created_paths.append(tf.name)
            return tf

        success_proc = subprocess.CompletedProcess(
            args=["hermes"],
            returncode=0,
            stdout="\x1b[32mOK\x1b[0m 한글테스트\n",
            stderr="session_id: sess-123\n",
        )
        with mock.patch("hermes_guest.shutil.which", return_value="hermes"), \
             mock.patch("hermes_guest.tempfile.NamedTemporaryFile", side_effect=tracking_ntf), \
             mock.patch("hermes_guest.subprocess.run", return_value=success_proc):
            code, out, extra = hermes_guest.run_guest_query(
                "deepseek",
                "alibaba-coding-plan",
                "deepseek-v4.1-flash",
                "hello",
                emit_session_id=True,
            )

        self.assertEqual(code, 0)
        self.assertEqual(out, "OK 한글테스트\n")
        self.assertEqual(extra, "session_id: sess-123")
        self.assertEqual(len(created_paths), 1)
        self.assertFalse(os.path.exists(created_paths[0]))

        fail_proc = subprocess.CompletedProcess(
            args=["hermes"],
            returncode=1,
            stdout="",
            stderr="API call failed: upstream error",
        )
        with mock.patch("hermes_guest.shutil.which", return_value="hermes"), \
             mock.patch("hermes_guest.tempfile.NamedTemporaryFile", side_effect=tracking_ntf), \
             mock.patch("hermes_guest.subprocess.run", return_value=fail_proc):
            code, out, extra = hermes_guest.run_guest_query(
                "qwen",
                "alibaba-coding-plan",
                "qwen4-max",
                "hello",
            )

        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("[HERMES_GUEST_UNAVAILABLE: qwen]", extra)
        self.assertEqual(len(created_paths), 2)
        self.assertFalse(os.path.exists(created_paths[1]))

        with mock.patch("hermes_guest.shutil.which", return_value="hermes"), \
             mock.patch("hermes_guest.tempfile.NamedTemporaryFile", side_effect=tracking_ntf), \
             mock.patch("hermes_guest.subprocess.run", side_effect=subprocess.TimeoutExpired("hermes", 10)):
            code, out, extra = hermes_guest.run_guest_query(
                "gpt",
                "openai-codex",
                "gpt-6-sol",
                "hello",
                run_budget=10,
            )

        self.assertEqual(code, 2)
        self.assertIn("[HERMES_GUEST_UNAVAILABLE: gpt]", extra)
        self.assertEqual(len(created_paths), 3)
        self.assertFalse(os.path.exists(created_paths[2]))

    def test_run_guest_query_missing_hermes_binary_returns_exit_2(self):
        with mock.patch("hermes_guest.shutil.which", return_value=None):
            code, out, extra = hermes_guest.run_guest_query(
                "deepseek",
                "alibaba-coding-plan",
                "deepseek-v4.1-flash",
                "Reply OK",
                hermes_bin="hermes-nonexistent",
            )
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("[HERMES_GUEST_UNAVAILABLE: deepseek]", extra)

    def test_hermes_disasm_mode_a_uses_v023_empty_toolset_flag(self):
        disasm_path = SCRIPTS_DIR / "hermes_disasm.py"
        source = disasm_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(disasm_path))

        found_extra_flags: list[str] | None = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "hermes_extra_flags":
                        if isinstance(node.value, ast.List):
                            vals = [
                                elt.value
                                for elt in node.value.elts
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                            ]
                            if "--ignore-rules" in vals and "--max-turns" in vals:
                                found_extra_flags = vals
                                break

        self.assertIsNotNone(found_extra_flags, "Expected Mode A hermes_extra_flags assignment in hermes_disasm.py")
        t_idx = found_extra_flags.index("-t")
        self.assertEqual(found_extra_flags[t_idx + 1], "")

    def test_sync_harness_propagates_hermes_guest_and_strict_validator_enforces_it(self):
        self.assertIn("scripts/hermes_guest.py", sync_harness.OVERWRITE_FILES)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            for folder in (
                ".agents/agents",
                ".agents/hooks",
                ".agents/rules",
                ".agents/skills/agent-legion/scripts",
            ):
                (tmp_root / folder).mkdir(parents=True, exist_ok=True)
            (tmp_root / ".agents" / "skills" / "agent-legion" / "scripts" / "partition_validator.py").write_text("", encoding="utf-8")
            (tmp_root / ".agents" / "skills" / "agent-legion" / "scripts" / "legion_radio.py").write_text("", encoding="utf-8")

            errors = validate_harness.validate_harness(strict=True, base_dir=str(tmp_root))
            self.assertIn("Missing required harness script: scripts/hermes_guest.py", errors)

            (tmp_root / "scripts").mkdir(parents=True, exist_ok=True)
            (tmp_root / "scripts" / "hermes_guest.py").write_text("# stub\n", encoding="utf-8")
            errors_after = validate_harness.validate_harness(strict=True, base_dir=str(tmp_root))
            self.assertNotIn("Missing required harness script: scripts/hermes_guest.py", errors_after)

    def test_skills_and_docs_8seat_grand_council_contract(self):
        um_skill = (REPO_ROOT / ".agents" / "skills" / "ultimate-make" / "SKILL.md").read_text(encoding="utf-8")
        mac_skill = (REPO_ROOT / ".agents" / "skills" / "multi-agent-conference" / "SKILL.md").read_text(encoding="utf-8")
        safety_rule = (REPO_ROOT / ".agents" / "rules" / "safety.md").read_text(encoding="utf-8")

        for doc in (um_skill, mac_skill):
            self.assertIn("8-Seat Grand Council", doc)
            self.assertIn("scripts/hermes_guest.py", doc)
            self.assertIn("guest-deepseek", doc)
            self.assertIn("guest-qwen", doc)
            self.assertIn("guest-gpt", doc)
            self.assertIn("[guest-unavailable]", doc)

        self.assertIn("Mode 2B", um_skill)
        self.assertIn("scripts/hermes_guest.py", safety_rule)
        self.assertIn('-t ""', safety_rule)

    def test_cli_list_seats_subprocess(self):
        proc = subprocess.run(
            [sys.executable, "-X", "utf8", str(SCRIPTS_DIR / "hermes_guest.py"), "--list-seats"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(set(data.keys()), {"deepseek", "qwen", "gpt"})
        self.assertEqual(data["deepseek"]["model"], "deepseek-v4.1-flash")
        self.assertEqual(data["qwen"]["model"], "qwen4-max")
        self.assertEqual(data["gpt"]["model"], "gpt-6-sol")


if __name__ == "__main__":
    unittest.main()
