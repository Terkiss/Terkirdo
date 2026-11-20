import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "harness"))

from sync_harness import sync_harness  # noqa: E402
from validate_harness import (  # noqa: E402
    EXPECTED_AGENT_MODELS,
    EXPECTED_AGENTS,
    FORBIDDEN_SKILL_PATTERNS,
    GEMINI_CLI_CATALOG_MODELS,
    GEMINI_CLI_NEON_MODELS,
    GEMINI_CLI_ORCHESTRATOR_MODELS,
    GEMINI_CLI_V1512_CATALOG_MODELS,
    VALID_MODELS,
    parse_frontmatter,
    validate_harness,
    validate_skills_directory,
)

BASELINE_13_TEST_FILES = {
    "test_agent_discovery.py",
    "test_cli_v157_alignment.py",
    "test_contracts.py",
    "test_document_references.py",
    "test_hooks_config.py",
    "test_legion_radio.py",
    "test_partition_validator.py",
    "test_post_tool_hook.py",
    "test_pre_tool_hook.py",
    "test_skill_indexer.py",
    "test_skills_integrity.py",
    "test_stop_hook.py",
    "test_update_harness.py",
}


class TestCliV1512NeonAlignment(unittest.TestCase):
    def test_v1512_20_slug_catalog_and_v157_backward_compatibility(self):
        expected_14_v157 = {
            "gemini-4-carbon-low",
            "gemini-4-carbon-medium",
            "gemini-4-carbon-high",
            "gemini-4-argon-low",
            "gemini-4-argon-medium",
            "gemini-4-argon-high",
            "gemini-4-hydrogen-low",
            "gemini-4-hydrogen-medium",
            "gemini-4-hydrogen-high",
            "gemini-4-hydrogen-xhigh",
            "gemini-pro-orchestrator",
            "gemini-3.8-flash-low",
            "gemini-3.8-flash-medium",
            "gemini-3.8-flash-high",
        }
        expected_4_neon = {
            "gemini-4-neon-low",
            "gemini-4-neon-medium",
            "gemini-4-neon-high",
            "gemini-4-neon-xhigh",
        }
        expected_3_orchestrator = {
            "gemini-pro-orchestrator",
            "gemini-pro-orchestrator-neon",
            "gemini-pro-orchestrator-argon",
        }
        expected_20_v1512 = expected_14_v157 | expected_4_neon | expected_3_orchestrator

        self.assertEqual(len(GEMINI_CLI_CATALOG_MODELS), 14)
        self.assertEqual(GEMINI_CLI_CATALOG_MODELS, expected_14_v157)

        self.assertEqual(len(GEMINI_CLI_NEON_MODELS), 4)
        self.assertEqual(GEMINI_CLI_NEON_MODELS, expected_4_neon)

        self.assertEqual(len(GEMINI_CLI_ORCHESTRATOR_MODELS), 3)
        self.assertEqual(GEMINI_CLI_ORCHESTRATOR_MODELS, expected_3_orchestrator)

        self.assertEqual(len(GEMINI_CLI_V1512_CATALOG_MODELS), 20)
        self.assertEqual(GEMINI_CLI_V1512_CATALOG_MODELS, expected_20_v1512)
        self.assertTrue(GEMINI_CLI_CATALOG_MODELS.issubset(GEMINI_CLI_V1512_CATALOG_MODELS))
        self.assertEqual(VALID_MODELS, {"inherit", "pro", "flash", "flash_lite"})

    def test_live_agy_models_contains_all_20_v1512_gemini_slugs(self):
        agy_bin = shutil.which("agy")
        if not agy_bin:
            self.skipTest("agy CLI not found on PATH")

        try:
            res = subprocess.run(
                [agy_bin, "models"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            self.skipTest("agy models timed out in restricted/offline environment")

        if res.returncode != 0:
            combined_err = f"{res.stdout}\n{res.stderr}".lower()
            if any(k in combined_err for k in ("network", "offline", "unauthenticated", "connect", "dial tcp")):
                self.skipTest(f"agy models unavailable offline: {res.stderr.strip()}")
            self.fail(f"agy models exited with code {res.returncode}:\n{res.stdout}\n{res.stderr}")

        for slug in sorted(GEMINI_CLI_V1512_CATALOG_MODELS):
            self.assertIn(
                slug,
                res.stdout,
                f"Expected Antigravity CLI v1.5.12 Gemini slug '{slug}' missing from `agy models` output",
            )

    def test_raw_neon_model_rejected_in_agents_and_skills(self):
        self.assertIn("model: neon", FORBIDDEN_SKILL_PATTERNS)
        self.assertIn("model: gemini-4-neon", FORBIDDEN_SKILL_PATTERNS)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_base = Path(tmpdir)
            shutil.copytree(REPO_ROOT / ".agents" / "agents", tmp_base / ".agents" / "agents")
            shutil.copytree(REPO_ROOT / ".agents" / "rules", tmp_base / ".agents" / "rules")
            shutil.copytree(REPO_ROOT / ".agents" / "hooks", tmp_base / ".agents" / "hooks")
            shutil.copy2(REPO_ROOT / ".agents" / "hooks.json", tmp_base / ".agents" / "hooks.json")

            legion_skill_dst = tmp_base / ".agents" / "skills" / "agent-legion"
            shutil.copytree(REPO_ROOT / ".agents" / "skills" / "agent-legion", legion_skill_dst)

            # Inject raw Neon model names into custom agent frontmatter
            agy_worker_md = tmp_base / ".agents" / "agents" / "agy-worker" / "agent.md"
            agy_worker_md.write_text(
                agy_worker_md.read_text(encoding="utf-8").replace("model: inherit", "model: neon", 1),
                encoding="utf-8",
            )
            legion_worker_md = tmp_base / ".agents" / "agents" / "legion-worker" / "agent.md"
            legion_worker_md.write_text(
                legion_worker_md.read_text(encoding="utf-8").replace(
                    "model: inherit", "model: gemini-4-neon-high", 1
                ),
                encoding="utf-8",
            )

            agent_errs = "\n".join(validate_harness(strict=False, base_dir=tmp_base))
            self.assertIn(
                "Invalid or missing model 'neon' in .agents/agents/agy-worker/agent.md",
                agent_errs,
            )
            self.assertIn(
                "Invalid or missing model 'gemini-4-neon-high' in .agents/agents/legion-worker/agent.md",
                agent_errs,
            )

            # Inject forbidden raw Neon model lines into temp skills and verify strict skill validation rejects both
            bad_skill_a = tmp_base / ".agents" / "skills" / "bad-neon-tier"
            bad_skill_a.mkdir(parents=True, exist_ok=True)
            (bad_skill_a / "SKILL.md").write_text(
                "---\n"
                "name: bad-neon-tier\n"
                "description: Negative fixture testing raw neon tier rejection.\n"
                "model: neon\n"
                "---\n\n"
                "Invalid raw model tier in skill.\n",
                encoding="utf-8",
            )

            bad_skill_b = tmp_base / ".agents" / "skills" / "bad-neon-slug"
            bad_skill_b.mkdir(parents=True, exist_ok=True)
            (bad_skill_b / "SKILL.md").write_text(
                "---\n"
                "name: bad-neon-slug\n"
                "description: Negative fixture testing raw gemini-4-neon-xhigh slug rejection.\n"
                "---\n\n"
                "Configured with model: gemini-4-neon-xhigh directly.\n",
                encoding="utf-8",
            )

            skill_errs = "\n".join(validate_skills_directory(tmp_base, strict=True))
            self.assertIn("Forbidden pattern 'model: neon' found in .agents/skills/bad-neon-tier/SKILL.md", skill_errs)
            self.assertIn(
                "Forbidden pattern 'model: gemini-4-neon' found in .agents/skills/bad-neon-slug/SKILL.md",
                skill_errs,
            )

    def test_ssot_protocol_readme_and_reference_neon_v1512_alignment(self):
        required_tokens = (
            "v1.5.12",
            "Gemini 4 Neon",
            "gemini-4-neon-xhigh",
            "gemini-pro-orchestrator-neon",
            "gemini-pro-orchestrator-argon",
            "gemini-4-hydrogen-tiered-xhigh",
            "gemini-4-hydrogen-tiered-high",
            "gemini-3.5-flash-lite",
        )
        target_docs = (
            REPO_ROOT / "AGENTS.md",
            REPO_ROOT / "Terukirdo_Protocol_v5.7.md",
            REPO_ROOT / "README.md",
            REPO_ROOT / "reference" / "ai-performance-cards.md",
            REPO_ROOT / "reference" / "cross-ai-collaboration-guide.md",
        )

        for doc_path in target_docs:
            self.assertTrue(doc_path.is_file(), f"Missing required document: {doc_path}")
            raw = doc_path.read_bytes()
            self.assertFalse(raw.startswith(b"\xef\xbb\xbf"), f"UTF-8 BOM detected in {doc_path.name}")
            text = raw.decode("utf-8")
            for tok in required_tokens:
                self.assertIn(tok, text, f"Missing '{tok}' in {doc_path.relative_to(REPO_ROOT).as_posix()}")

        perf_card_text = (REPO_ROOT / "reference" / "ai-performance-cards.md").read_text(encoding="utf-8")
        verified_neon_figures = (
            "2026-11-18",
            "58.6",
            "65.2%",
            "65.4%",
            "39.0%",
            "84",
            "32%",
            "$3.00",
            "$15.00",
            "$0.15",
        )
        for fig in verified_neon_figures:
            self.assertIn(
                fig,
                perf_card_text,
                f"Missing verified Gemini 4 Neon figure '{fig}' in reference/ai-performance-cards.md",
            )

    def test_agents_and_skills_neon_alignment_and_loader_invariants(self):
        spine_and_judge_agents = {
            "legion-commander",
            "ralph-orchestrator",
            "agy-worker",
            "legion-worker",
            "tech-expert",
        }
        for agent in EXPECTED_AGENTS:
            agent_path = REPO_ROOT / ".agents" / "agents" / agent / "agent.md"
            self.assertTrue(agent_path.is_file(), f"Missing agent file: {agent_path}")
            raw = agent_path.read_bytes()
            self.assertFalse(raw.startswith(b"\xef\xbb\xbf"), f"UTF-8 BOM in {agent}/agent.md")
            text = raw.decode("utf-8")
            meta, body = parse_frontmatter(text)
            self.assertIsInstance(meta, dict)
            self.assertEqual(meta.get("model"), EXPECTED_AGENT_MODELS[agent])

            tools = set(meta.get("tools", []))
            self.assertIn("view_file", tools, f"{agent} missing view_file")
            self.assertNotIn("read_file", tools, f"{agent} must not co-declare read_file")
            self.assertIn("v1.5.12", body, f"{agent}/agent.md body missing v1.5.12 alignment")

            if agent in spine_and_judge_agents:
                self.assertIn("Gemini 4 Neon", body, f"{agent}/agent.md missing 'Gemini 4 Neon'")
                self.assertIn(
                    "gemini-pro-orchestrator-neon",
                    body,
                    f"{agent}/agent.md missing 'gemini-pro-orchestrator-neon'",
                )

        for skill_name in ("multi-agent-conference", "agent-legion"):
            skill_path = REPO_ROOT / ".agents" / "skills" / skill_name / "SKILL.md"
            self.assertTrue(skill_path.is_file())
            skill_text = skill_path.read_text(encoding="utf-8")
            self.assertIn("Gemini 4 Neon", skill_text, f"{skill_name}/SKILL.md missing 'Gemini 4 Neon'")
            self.assertIn(
                "gemini-pro-orchestrator-neon",
                skill_text,
                f"{skill_name}/SKILL.md missing 'gemini-pro-orchestrator-neon'",
            )
            for forbidden in FORBIDDEN_SKILL_PATTERNS:
                self.assertNotIn(forbidden, skill_text)

        self.assertEqual(validate_skills_directory(REPO_ROOT, strict=True), [])
        self.assertEqual(validate_harness(strict=True, base_dir=REPO_ROOT), [])

    def test_baseline_13_test_files_remain_unmodified_in_git_diff(self):
        if not (REPO_ROOT / ".git").exists():
            self.skipTest("Not running inside a Git repository")

        res = subprocess.run(
            ["git", "diff", "--name-only", "HEAD", "--", "tests/harness/"],
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(res.returncode, 0, f"git diff failed: {res.stderr}")
        changed_names = {
            Path(line.strip()).name
            for line in res.stdout.splitlines()
            if line.strip()
        }
        touched_baseline = sorted(changed_names & BASELINE_13_TEST_FILES)
        self.assertEqual(
            touched_baseline,
            [],
            f"Baseline test integrity violation — pre-existing test files modified: {touched_baseline}",
        )

    def test_sync_harness_propagates_v1512_neon_alignment_cleanly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_target = Path(tmpdir)
            success, stats = sync_harness(REPO_ROOT, tmp_target, run_verification=True)
            self.assertTrue(success, f"sync_harness failed with errors: {stats['errors']}")
            self.assertEqual(stats["errors"], [])

            mirrored_test = tmp_target / "tests" / "harness" / "test_cli_v1512_neon_alignment.py"
            self.assertTrue(mirrored_test.is_file(), "test_cli_v1512_neon_alignment.py was not mirrored to target")

            self.assertEqual(
                (tmp_target / "AGENTS.md").read_text(encoding="utf-8"),
                (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                (tmp_target / "reference" / "ai-performance-cards.md").read_text(encoding="utf-8"),
                (REPO_ROOT / "reference" / "ai-performance-cards.md").read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
