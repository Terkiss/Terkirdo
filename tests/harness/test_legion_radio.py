import concurrent.futures
import contextlib
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from collections import Counter
from pathlib import Path


class TestLegionRadio(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[2]
        self.script_path = (
            self.repo_root
            / ".agents"
            / "skills"
            / "agent-legion"
            / "scripts"
            / "legion_radio.py"
        )
        self.assertTrue(self.script_path.is_file(), f"Missing script: {self.script_path}")

    def _load_module(self):
        spec = importlib.util.spec_from_file_location("legion_radio", self.script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def run_cli(self, db_path: Path, args: list, db_after_subcommand: bool = False):
        if db_after_subcommand:
            cmd = [sys.executable, str(self.script_path)] + list(args) + ["--db", str(db_path)]
        else:
            cmd = [sys.executable, str(self.script_path), "--db", str(db_path)] + list(args)
        return subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def test_default_db_path_resolution(self):
        module = self._load_module()
        old_env = os.environ.pop("LEGION_RADIO_DB", None)
        try:
            resolved = module.resolve_db_path(None)
            expected = (self.repo_root / ".agents" / "state" / "legion_radio.db").resolve()
            self.assertEqual(resolved, expected)

            with tempfile.TemporaryDirectory() as tmpdir:
                env_target = Path(tmpdir) / "env_override.db"
                os.environ["LEGION_RADIO_DB"] = str(env_target)
                self.assertEqual(module.resolve_db_path(None), env_target.resolve())

                cli_target = Path(tmpdir) / "cli_override.db"
                self.assertEqual(module.resolve_db_path(str(cli_target)), cli_target.resolve())
        finally:
            if old_env is not None:
                os.environ["LEGION_RADIO_DB"] = old_env
            else:
                os.environ.pop("LEGION_RADIO_DB", None)

    def test_init_wal_mode_and_reset_sequence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "radio_init.db"

            res_init = self.run_cli(
                db_path,
                ["init", "--mission", "Operation Octa Storm", "--json"],
            )
            self.assertEqual(res_init.returncode, 0, res_init.stderr)
            init_data = json.loads(res_init.stdout)
            self.assertEqual(init_data["status"], "OK")
            self.assertEqual(init_data["mission"], "Operation Octa Storm")
            self.assertEqual(init_data["journal_mode"], "wal")

            with contextlib.closing(sqlite3.connect(str(db_path))) as conn:
                jmode = conn.execute("PRAGMA journal_mode;").fetchone()[0].lower()
                self.assertEqual(jmode, "wal")

            p1 = self.run_cli(
                db_path,
                ["post", "--from", "Commander", "--tag", "DECISION", "--msg", "First msg", "--json"],
                db_after_subcommand=True,
            )
            self.assertEqual(p1.returncode, 0, p1.stderr)
            self.assertEqual(json.loads(p1.stdout)["seq"], 1)

            p2 = self.run_cli(
                db_path,
                ["post", "--from", "Ralph-1", "--tag", "INTERFACE", "--msg", "Second msg", "--json"],
            )
            self.assertEqual(p2.returncode, 0, p2.stderr)
            self.assertEqual(json.loads(p2.stdout)["seq"], 2)

            self.assertEqual(
                self.run_cli(
                    db_path,
                    ["roster-set", "--squad", "Ralph-1", "--conv-id", "conv-r1"],
                ).returncode,
                0,
            )

            # Reset must wipe roster + messages and restart sequence from #1
            res_reset = self.run_cli(
                db_path,
                ["init", "--mission", "Operation Reboot", "--reset", "--json"],
            )
            self.assertEqual(res_reset.returncode, 0, res_reset.stderr)
            self.assertTrue(json.loads(res_reset.stdout)["reset"])

            roster_after = json.loads(
                self.run_cli(db_path, ["roster", "--json"]).stdout
            )
            self.assertEqual(roster_after["mission"], "Operation Reboot")
            self.assertEqual(roster_after["roster"], [])

            p_after_reset = self.run_cli(
                db_path,
                ["post", "--from", "Commander", "--tag", "DECISION", "--msg", "Fresh #1", "--json"],
            )
            self.assertEqual(p_after_reset.returncode, 0, p_after_reset.stderr)
            self.assertEqual(json.loads(p_after_reset.stdout)["seq"], 1)
            self.assertEqual(json.loads(p_after_reset.stdout)["ref"], "#1")

    def test_roster_set_upsert_and_octa_callsign_order(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "radio_roster.db"
            self.assertEqual(
                self.run_cli(db_path, ["init", "--mission", "Octa Roster Test"]).returncode,
                0,
            )

            # Register in reverse order to verify deterministic logical sorting
            squads_reverse = [f"Ralph-{i}" for i in range(8, 0, -1)] + ["Commander"]
            for sq in squads_reverse:
                res = self.run_cli(
                    db_path,
                    [
                        "roster-set",
                        "--squad",
                        sq,
                        "--conv-id",
                        f"conv-{sq.lower()}",
                        "--partition",
                        f"part-{sq.lower()}",
                        "--scope",
                        f"Scope for {sq}",
                    ],
                )
                self.assertEqual(res.returncode, 0, res.stderr)

            # UPSERT Ralph-8 with updated conv-id and scope
            res_upsert = self.run_cli(
                db_path,
                [
                    "roster-set",
                    "--squad",
                    "Ralph-8",
                    "--conv-id",
                    "conv-ralph-8-updated",
                    "--partition",
                    "P8-v2",
                    "--scope",
                    "Updated Scope R8",
                    "--json",
                ],
            )
            self.assertEqual(res_upsert.returncode, 0, res_upsert.stderr)

            res_json = self.run_cli(db_path, ["roster", "--json"])
            self.assertEqual(res_json.returncode, 0, res_json.stderr)
            payload = json.loads(res_json.stdout)
            expected_order = ["Commander"] + [f"Ralph-{i}" for i in range(1, 9)]
            self.assertEqual([r["squad"] for r in payload["roster"]], expected_order)

            r8 = [r for r in payload["roster"] if r["squad"] == "Ralph-8"][0]
            self.assertEqual(r8["conv_id"], "conv-ralph-8-updated")
            self.assertEqual(r8["partition"], "P8-v2")
            self.assertEqual(r8["scope"], "Updated Scope R8")

            res_text = self.run_cli(db_path, ["roster"])
            self.assertEqual(res_text.returncode, 0, res_text.stderr)
            self.assertIn("conv-ralph-8-updated", res_text.stdout)
            self.assertIn("Commander", res_text.stdout)

    def test_post_and_read_filters_incremental_and_direct_vs_broadcast(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "radio_read.db"
            self.run_cli(db_path, ["init", "--mission", "Filter Verification", "--reset"])

            posts = [
                ("Commander", "ALL", "DECISION", "Global architecture rule"),
                ("Ralph-1", "ALL", "INTERFACE", "AuthToken verify(token: str) -> Claims"),
                ("Ralph-1", "Ralph-2", "SCHEMA", "Direct packet header v2 for Ralph-2"),
                ("Ralph-3", "Ralph-4", "BLOCKER", "Private blocker only for Ralph-4"),
                ("Ralph-8", "Commander", "DONE", "Partition 8 verified"),
            ]
            for sender, to, tag, msg in posts:
                res = self.run_cli(
                    db_path,
                    ["post", "--from", sender, "--to", to, "--tag", tag, "--msg", msg],
                )
                self.assertEqual(res.returncode, 0, res.stderr)
                self.assertIn("[RADIO #", res.stdout)

            # 1. Incremental --since 2 returns #3, #4, #5
            inc = json.loads(self.run_cli(db_path, ["read", "--since", "2", "--json"]).stdout)
            self.assertEqual([m["seq"] for m in inc["messages"]], [3, 4, 5])
            self.assertEqual(inc["last_seq"], 5)

            # 2. --to Ralph-2 returns ALL broadcasts (#1, #2) + direct to Ralph-2 (#3), excluding #4 and #5
            r2_inbox = json.loads(
                self.run_cli(db_path, ["read", "--to", "Ralph-2", "--json"]).stdout
            )
            self.assertEqual([m["seq"] for m in r2_inbox["messages"]], [1, 2, 3])

            # 3. --to ALL returns strictly recipient == 'ALL' (#1, #2)
            all_only = json.loads(
                self.run_cli(db_path, ["read", "--to", "ALL", "--json"]).stdout
            )
            self.assertEqual([m["seq"] for m in all_only["messages"]], [1, 2])

            # 4. --tag SCHEMA returns #3 only
            schema_only = json.loads(
                self.run_cli(db_path, ["read", "--tag", "SCHEMA", "--json"]).stdout
            )
            self.assertEqual([m["seq"] for m in schema_only["messages"]], [3])

            # 5. --limit 2 returns #1, #2
            limited = json.loads(
                self.run_cli(db_path, ["read", "--limit", "2", "--json"]).stdout
            )
            self.assertEqual([m["seq"] for m in limited["messages"]], [1, 2])

            # 6. Plain text output includes #<seq>
            txt = self.run_cli(db_path, ["read", "--since", "4"])
            self.assertEqual(txt.returncode, 0)
            self.assertIn("#5", txt.stdout)
            self.assertIn("Partition 8 verified", txt.stdout)

    def test_validation_guards_and_2000_char_limit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "radio_guard.db"
            self.run_cli(db_path, ["init", "--mission", "Guard Test", "--reset"])

            # Exact 2,000 characters -> MUST PASS
            exact_2000 = "A" * 2000
            res_ok = self.run_cli(
                db_path,
                ["post", "--from", "Ralph-5", "--tag", "INTERFACE", "--msg", exact_2000, "--json"],
            )
            self.assertEqual(res_ok.returncode, 0, res_ok.stderr)
            self.assertEqual(json.loads(res_ok.stdout)["seq"], 1)

            # 2,001 characters -> MUST FAIL with exit code 1 and NOT write to DB
            over_2001 = "B" * 2001
            res_over = self.run_cli(
                db_path,
                ["post", "--from", "Ralph-5", "--tag", "INTERFACE", "--msg", over_2001],
            )
            self.assertEqual(res_over.returncode, 1)
            self.assertIn("2000", res_over.stderr)

            # Invalid squad (Ralph-9), invalid tag, empty msg, empty conv-id, invalid limit
            invalid_cases = [
                ["post", "--from", "Ralph-9", "--msg", "out of range squad"],
                ["post", "--from", "Ralph-1", "--to", "Ralph-9", "--msg", "bad recipient"],
                ["post", "--from", "Ralph-1", "--tag", "SPAM", "--msg", "bad tag"],
                ["post", "--from", "Ralph-1", "--msg", "   "],
                ["roster-set", "--squad", "Ralph-0", "--conv-id", "abc"],
                ["roster-set", "--squad", "Ralph-1", "--conv-id", "   "],
                ["read", "--limit", "0"],
                ["read", "--since", "-1"],
                ["read", "--to", "UnknownSquad"],
                ["read", "--tag", "INVALID_TAG"],
            ]
            for bad_args in invalid_cases:
                res_bad = self.run_cli(db_path, bad_args)
                self.assertEqual(
                    res_bad.returncode,
                    1,
                    f"Expected exit code 1 for {bad_args}, got {res_bad.returncode}",
                )

            # Verify DB still has ONLY message #1 (2,001-char and invalid posts never persisted)
            read_check = json.loads(self.run_cli(db_path, ["read", "--json"]).stdout)
            self.assertEqual(read_check["count"], 1)
            self.assertEqual(read_check["messages"][0]["seq"], 1)

    def test_octa_ralph_8_process_concurrent_stress_200_posts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "radio_stress_octa.db"
            init_res = self.run_cli(
                db_path,
                ["init", "--mission", "Octa-Ralph 8x25 Concurrency Stress", "--reset"],
            )
            self.assertEqual(init_res.returncode, 0, init_res.stderr)

            num_squads = 8
            posts_per_squad = 25
            total_expected = num_squads * posts_per_squad  # 200 OS subprocess calls
            barrier = threading.Barrier(num_squads)

            def squad_worker(squad_idx: int):
                squad_name = f"Ralph-{squad_idx}"
                results = []
                barrier.wait(timeout=30.0)
                for i in range(posts_per_squad):
                    tag = ("INTERFACE", "SCHEMA", "DECISION", "BLOCKER", "DONE")[i % 5]
                    res = subprocess.run(
                        [
                            sys.executable,
                            str(self.script_path),
                            "--db",
                            str(db_path),
                            "post",
                            "--from",
                            squad_name,
                            "--to",
                            "ALL",
                            "--tag",
                            tag,
                            "--msg",
                            f"[{squad_name}] msg #{i + 1}: packet contract v{i + 1}",
                            "--json",
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                    )
                    results.append((squad_name, i, res.returncode, res.stdout, res.stderr))
                return results

            all_results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_squads) as pool:
                futures = [pool.submit(squad_worker, idx) for idx in range(1, num_squads + 1)]
                for fut in concurrent.futures.as_completed(futures):
                    all_results.extend(fut.result())

            self.assertEqual(len(all_results), total_expected)

            failures = [r for r in all_results if r[2] != 0]
            self.assertEqual(
                len(failures),
                0,
                f"Expected 0 subprocess failures, got {len(failures)}: {failures[:3]}",
            )

            lock_stderrs = [
                r[4]
                for r in all_results
                if "locked" in r[4].lower() or "busy" in r[4].lower()
            ]
            self.assertEqual(
                len(lock_stderrs),
                0,
                f"Unexpected SQLite lock/busy stderr outputs: {lock_stderrs[:3]}",
            )

            read_res = self.run_cli(db_path, ["read", "--json"])
            self.assertEqual(read_res.returncode, 0, read_res.stderr)
            board = json.loads(read_res.stdout)

            self.assertEqual(board["count"], total_expected)
            self.assertEqual(len(board["messages"]), total_expected)

            seqs = [m["seq"] for m in board["messages"]]
            self.assertEqual(seqs, list(range(1, total_expected + 1)))

            sender_counts = Counter(m["from"] for m in board["messages"])
            for idx in range(1, num_squads + 1):
                sq = f"Ralph-{idx}"
                self.assertEqual(
                    sender_counts[sq],
                    posts_per_squad,
                    f"{sq} expected {posts_per_squad} messages, got {sender_counts[sq]}",
                )


if __name__ == "__main__":
    unittest.main()
