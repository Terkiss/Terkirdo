import os
import sys
import stat
import unittest
import tempfile
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "harness"))

from sync_harness import sync_harness


class TestUpdateHarness(unittest.TestCase):
    def test_sync_harness_purges_deleted_and_preserves_project_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # 1. Plant obsolete/deleted files from older Terukirdo versions (v5.2 ~ v5.5)
            zombie_files = [
                "Terukirdo_Protocol_v5.2.md",
                "Terukirdo_Protocol_v5.3.md",
                "Terukirdo_Protocol_v5.5.md",
                "IMPLEMENTATION_PROGRESS.md",
                "Documents/Implementation_Plan.md",
                "scripts/auto_evolve.py",
                "agents/agy-worker.md",
                "agents/ralph-orchestrator.md",
                "agents/Final_Approach_Control.md",
                ".agents/skills/flutter-expert/SKILL.md",
                ".agents/skills/self-evolution/scripts/auto_evolve.py",
                ".agents/agents/obsolete-agent/agent.md",
                ".agents/hooks/deprecated_hook.py",
                "docs/harness/obsolete_routing.md",
            ]
            for rel in zombie_files:
                p = target / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("stale zombie content", encoding="utf-8")

            # 2. Plant outdated core harness files that must be overwritten
            (target / "AGENTS.md").write_text("old AGENTS.md v5.2", encoding="utf-8")
            (target / "Terukirdo_Protocol_v5.6.md").write_text("outdated draft", encoding="utf-8")

            # 3. Plant project-owned files that MUST be preserved
            preserved_files = {
                "README.md": "# Custom Target Project README\n",
                "MEMORY.md": "# Custom Target Project Memory\n",
                "docs/Terukirdo_Trajectory.txt": "[2026-10-31] Custom trajectory entry\n",
                ".agents/state/stop_gate_state.json": '{"custom_state": 123}\n',
                "docs/specs/my_feature.spec.md": "# Custom Feature Frozen Spec\n",
                "docs/development/commands.md": "# Custom Project Build Commands\n",
                "src/app.py": "print('target app code')\n",
            }
            for rel, content in preserved_files.items():
                p = target / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")

            # 4. Run sync_harness with full verification (skill_indexer + validate_harness --strict)
            success, stats = sync_harness(REPO_ROOT, target, run_verification=True)
            self.assertTrue(success, f"sync_harness failed with errors: {stats['errors']}")

            # 5. Verify all zombie files and obsolete directories were purged
            for rel in zombie_files:
                self.assertFalse(
                    (target / rel).exists(),
                    f"Zombie file was not purged: {rel}",
                )
            self.assertFalse((target / ".agents/skills/flutter-expert").exists())
            self.assertFalse((target / ".agents/agents/obsolete-agent").exists())

            # 6. Verify core harness files were updated to match the master template
            self.assertEqual(
                (target / "AGENTS.md").read_text(encoding="utf-8"),
                (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                (target / "Terukirdo_Protocol_v5.6.md").read_text(encoding="utf-8"),
                (REPO_ROOT / "Terukirdo_Protocol_v5.6.md").read_text(encoding="utf-8"),
            )
            self.assertTrue((target / ".agents/agents/legion-commander/agent.md").is_file())
            self.assertTrue((target / ".agents/skills/agent-legion/SKILL.md").is_file())
            self.assertTrue((target / "agents/README.md").is_file())

            # 7. Verify all project-owned files were strictly preserved
            for rel, expected_content in preserved_files.items():
                self.assertTrue((target / rel).is_file(), f"Preserved file missing: {rel}")
                self.assertEqual(
                    (target / rel).read_text(encoding="utf-8"),
                    expected_content,
                    f"Preserved file was modified: {rel}",
                )

    def test_update_harness_bat_cli_execution(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            # Plant a zombie file to ensure the .bat script invokes the purge engine
            zombie = target / "Terukirdo_Protocol_v5.4.md"
            zombie.write_text("old v5.4 protocol", encoding="utf-8")

            bat_path = REPO_ROOT / "update_harness.bat"
            res = subprocess.run(
                ["cmd.exe", "/c", str(bat_path), str(target), "--no-pause"],
                cwd=str(REPO_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(res.returncode, 0, f"update_harness.bat failed:\n{res.stdout}\n{res.stderr}")
            self.assertFalse(zombie.exists(), "update_harness.bat did not purge Terukirdo_Protocol_v5.4.md")
            self.assertTrue((target / "update_harness.bat").is_file(), "update_harness.bat was not copied to target")

    def test_sync_harness_ignores_nested_git_and_purges_readonly_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)

            # 1. Place a read-only packfile inside target/reference/zombie_dir/.git/objects/pack/test.idx
            zombie_pack = target / "reference" / "zombie_dir" / ".git" / "objects" / "pack" / "test.idx"
            zombie_pack.parent.mkdir(parents=True, exist_ok=True)
            zombie_pack.write_bytes(b"\xff\x74\x4f\x63\x00\x00\x00\x02")
            os.chmod(zombie_pack, stat.S_IREAD)

            # 2. Place a zombie read-only file target/.agents/readonly_zombie.txt
            readonly_zombie = target / ".agents" / "readonly_zombie.txt"
            readonly_zombie.parent.mkdir(parents=True, exist_ok=True)
            readonly_zombie.write_text("read-only zombie file", encoding="utf-8")
            os.chmod(readonly_zombie, stat.S_IREAD)

            # 3. Run sync_harness from REPO_ROOT to target with run_verification=False
            success, stats = sync_harness(REPO_ROOT, target, run_verification=False)
            self.assertTrue(success, f"sync_harness failed with errors: {stats['errors']}")
            self.assertEqual(stats["errors"], [], f"Errors occurred during sync: {stats['errors']}")

            # 4. Assertions:
            # - (target / "reference" / "dual-brain" / ".git").exists() is False (nested .git is never copied)
            self.assertFalse(
                (target / "reference" / "dual-brain" / ".git").exists(),
                "Nested .git repository was unexpectedly copied to target!",
            )

            # - Read-only zombie files and directories were cleanly purged
            self.assertFalse(
                (target / "reference" / "zombie_dir").exists(),
                "Read-only zombie directory was not purged!",
            )
            self.assertFalse(
                (target / ".agents" / "readonly_zombie.txt").exists(),
                "Read-only zombie file was not purged!",
            )


if __name__ == "__main__":
    unittest.main()
