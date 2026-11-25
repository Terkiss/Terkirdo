import json
import os
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
    AGY_CLI_EXTERNAL_MODELS,
    AGY_CLI_V1516_CATALOG_MODELS,
    EXPECTED_AGENT_MODELS,
    EXPECTED_AGENTS,
    FORBIDDEN_AGENT_TOOLS,
    FORBIDDEN_SKILL_PATTERNS,
    GEMINI_CLI_CATALOG_MODELS,
    GEMINI_CLI_V1512_CATALOG_MODELS,
    VALID_MODELS,
    parse_frontmatter,
    validate_harness,
    validate_hooks_config,
    validate_skills_directory,
)

PRE_HOOK_PATH = str(REPO_ROOT / ".agents" / "hooks" / "pre_tool_use_policy.py")

UNTOUCHED_11_BASELINE_TEST_FILES = {
    "test_agent_discovery.py",
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
}


class TestCliV1516V58Alignment(unittest.TestCase):
    def _run_pre_hook(self, payload: dict, cwd: Path | None = None) -> tuple[dict, str]:
        res = subprocess.run(
            [sys.executable, PRE_HOOK_PATH],
            input=json.dumps(payload),
            cwd=str(cwd) if cwd is not None else str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(res.returncode, 0, f"PreToolUse hook exited {res.returncode}: {res.stderr}")
        return json.loads(res.stdout.strip()), res.stderr

    def test_v1516_27_slug_catalog_and_subagent_constants(self):
        expected_external_7 = {
            "claude-opus-5-5-low",
            "claude-opus-5-5-medium",
            "claude-opus-5-5-high",
            "claude-sonnet-5-5-low",
            "claude-sonnet-5-5-medium",
            "claude-sonnet-5-5-high",
            "gpt-oss-120b-medium",
        }
        self.assertEqual(len(GEMINI_CLI_CATALOG_MODELS), 14)
        self.assertEqual(len(GEMINI_CLI_V1512_CATALOG_MODELS), 20)
        self.assertEqual(len(AGY_CLI_EXTERNAL_MODELS), 7)
        self.assertEqual(AGY_CLI_EXTERNAL_MODELS, expected_external_7)

        self.assertEqual(len(AGY_CLI_V1516_CATALOG_MODELS), 27)
        self.assertEqual(
            AGY_CLI_V1516_CATALOG_MODELS,
            GEMINI_CLI_V1512_CATALOG_MODELS | AGY_CLI_EXTERNAL_MODELS,
        )
        self.assertEqual(FORBIDDEN_AGENT_TOOLS, {"run_workflow", "swarm"})
        self.assertEqual(VALID_MODELS, {"inherit", "pro", "flash", "flash_lite"})

        for forbidden_pat in ("model: claude-", "model: gpt-oss", "run_workflow("):
            self.assertIn(forbidden_pat, FORBIDDEN_SKILL_PATTERNS)

    def test_live_agy_models_matches_v1516_catalog(self):
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

        parsed_slugs = set()
        for line in res.stdout.splitlines():
            if "\t" in line:
                slug = line.split("\t", 1)[0].strip()
                if slug:
                    parsed_slugs.add(slug)

        for gemini_slug in sorted(GEMINI_CLI_V1512_CATALOG_MODELS):
            self.assertIn(
                gemini_slug,
                res.stdout,
                f"Expected Gemini slug '{gemini_slug}' missing from `agy models` output",
            )

        for full_slug in sorted(AGY_CLI_V1516_CATALOG_MODELS):
            self.assertIn(
                full_slug,
                res.stdout,
                f"Expected CLI v1.5.16 catalog slug '{full_slug}' missing from `agy models` output",
            )

        if parsed_slugs:
            self.assertTrue(
                AGY_CLI_V1516_CATALOG_MODELS.issubset(parsed_slugs),
                f"Catalog slugs missing in parsed output: {AGY_CLI_V1516_CATALOG_MODELS - parsed_slugs}",
            )

    def test_run_workflow_unconditional_permanent_deny_in_hook(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            transcript = Path(tmpdir) / "transcript.jsonl"
            transcript.write_text(
                json.dumps({"type": "USER_INPUT", "content": "/ultimate-make 결제 시스템 기획해줘"}) + "\n"
                + json.dumps(
                    {
                        "type": "PLANNER_RESPONSE",
                        "tool_calls": [
                            {"name": "read_file", "args": {"Path": ".agents/skills/ultimate-make/SKILL.md"}}
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            scenarios = [
                (
                    "워크플로우로 자동화해줘",
                    {"Script": "print('inline workflow')"},
                    None,
                ),
                (
                    "/swarm 병렬 실행해줘",
                    {"ScriptPath": "workflows/parallel.py"},
                    None,
                ),
                (
                    "/ultimate-make 결제 시스템 기획해줘",
                    {"Script": "import agent; agent.run()"},
                    str(transcript),
                ),
                (
                    "/agent-legion 8분대 병렬 구현",
                    {"ScriptPath": "scripts/run_legion.py"},
                    None,
                ),
            ]
            for user_prompt, wf_args, tx_path in scenarios:
                payload = {
                    "lastUserInput": user_prompt,
                    "toolCall": {"name": "run_workflow", "args": wf_args},
                }
                if tx_path:
                    payload["transcriptPath"] = tx_path
                dec, _ = self._run_pre_hook(payload)
                self.assertEqual(dec["decision"], "deny", f"Expected deny for prompt={user_prompt!r}")
                self.assertIn("run_workflow", dec["reason"])

    def test_validator_rejects_forbidden_tools_flags_hooks_and_skills(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_base = Path(tmpdir)
            shutil.copytree(REPO_ROOT / ".agents" / "agents", tmp_base / ".agents" / "agents")
            shutil.copytree(REPO_ROOT / ".agents" / "rules", tmp_base / ".agents" / "rules")
            shutil.copytree(REPO_ROOT / ".agents" / "hooks", tmp_base / ".agents" / "hooks")
            shutil.copy2(REPO_ROOT / ".agents" / "hooks.json", tmp_base / ".agents" / "hooks.json")
            shutil.copytree(
                REPO_ROOT / ".agents" / "skills" / "agent-legion",
                tmp_base / ".agents" / "skills" / "agent-legion",
            )

            # 1. Inject forbidden tools (run_workflow, swarm) & invalid subagent/mainAgent types/booleans
            agy_worker_md = tmp_base / ".agents" / "agents" / "agy-worker" / "agent.md"
            agy_worker_md.write_text(
                agy_worker_md.read_text(encoding="utf-8")
                .replace("  - view_file\n", "  - view_file\n  - run_workflow\n", 1)
                .replace("subagent: true\n", 'subagent: "true"\n', 1),
                encoding="utf-8",
            )

            ralph_md = tmp_base / ".agents" / "agents" / "ralph-orchestrator" / "agent.md"
            ralph_md.write_text(
                ralph_md.read_text(encoding="utf-8")
                .replace("  - view_file\n", "  - view_file\n  - swarm\n", 1)
                .replace("mainAgent: false\n", "mainAgent: true\n", 1),
                encoding="utf-8",
            )

            plan_md = tmp_base / ".agents" / "agents" / "terukirdo-plan" / "agent.md"
            plan_md.write_text(
                plan_md.read_text(encoding="utf-8")
                .replace("subagent: true\n", "", 1)
                .replace("mainAgent: false\n", 'mainAgent: "false"\n', 1),
                encoding="utf-8",
            )

            errs = "\n".join(validate_harness(strict=False, base_dir=tmp_base))
            self.assertIn("Agent 'agy-worker' must not declare forbidden tool(s) in frontmatter: ['run_workflow']", errs)
            self.assertIn("Invalid or missing 'subagent: true' boolean in .agents/agents/agy-worker/agent.md", errs)
            self.assertIn("Agent 'ralph-orchestrator' must not declare forbidden tool(s) in frontmatter: ['swarm']", errs)
            self.assertIn(
                "Invalid or missing 'mainAgent: false' boolean in .agents/agents/ralph-orchestrator/agent.md", errs
            )
            self.assertIn("Invalid or missing 'subagent: true' boolean in .agents/agents/terukirdo-plan/agent.md", errs)
            self.assertIn("Invalid or missing 'mainAgent: false' boolean in .agents/agents/terukirdo-plan/agent.md", errs)

            # 2. Hooks config missing run_workflow or swarm in PreToolUse matcher
            hooks_path = tmp_base / ".agents" / "hooks.json"
            hooks_data = json.loads(hooks_path.read_text(encoding="utf-8"))
            hooks_data["terukirdo-safety-policy"]["PreToolUse"][0]["matcher"] = (
                "run_command|write_file|edit_file|notebook_edit|invoke_subagent"
            )
            hooks_path.write_text(json.dumps(hooks_data), encoding="utf-8")
            hook_errs = "\n".join(validate_hooks_config(tmp_base))
            self.assertIn("run_workflow", hook_errs)
            self.assertIn("swarm", hook_errs)

            # 3. Skills containing run_workflow(, model: claude-opus-5-5-high, or model: gpt-oss-120b-medium
            bad_skills = {
                "bad-wf-skill": "Invoke run_workflow(Script='x') directly.\n",
                "bad-claude-skill": "Pinned frontmatter:\nmodel: claude-opus-5-5-high\n",
                "bad-gpt-skill": "Pinned frontmatter:\nmodel: gpt-oss-120b-medium\n",
            }
            for sname, sbody in bad_skills.items():
                sdir = tmp_base / ".agents" / "skills" / sname
                sdir.mkdir(parents=True, exist_ok=True)
                (sdir / "SKILL.md").write_text(
                    f"---\nname: {sname}\ndescription: Negative test fixture for {sname}.\n---\n\n{sbody}",
                    encoding="utf-8",
                )

            skill_errs = "\n".join(validate_skills_directory(tmp_base, strict=True))
            self.assertIn("Forbidden pattern 'run_workflow(' found in .agents/skills/bad-wf-skill/SKILL.md", skill_errs)
            self.assertIn(
                "Forbidden pattern 'model: claude-' found in .agents/skills/bad-claude-skill/SKILL.md", skill_errs
            )
            self.assertIn(
                "Forbidden pattern 'model: gpt-oss' found in .agents/skills/bad-gpt-skill/SKILL.md", skill_errs
            )

    def test_swarm_slash_lock_and_dual_anchored_ultimatemake_window(self):
        # 1. Conversational prompt -> deny
        dec_conv, _ = self._run_pre_hook(
            {
                "lastUserInput": "스웜으로 병렬 처리해줘",
                "toolCall": {"name": "swarm", "args": {"action": "add", "name": "scout-1"}},
            }
        )
        self.assertEqual(dec_conv["decision"], "deny")

        with tempfile.TemporaryDirectory() as tmpdir:
            # 2. LLM self-unlock forgery (model read ultimate-make/SKILL.md, but USER_INPUT never asked for it) -> deny
            forgery_tx = Path(tmpdir) / "forgery_transcript.jsonl"
            forgery_tx.write_text(
                json.dumps({"type": "USER_INPUT", "content": "결제 시스템 만들어줘"}) + "\n"
                + json.dumps(
                    {
                        "type": "PLANNER_RESPONSE",
                        "tool_calls": [
                            {"name": "read_file", "args": {"Path": ".agents/skills/ultimate-make/SKILL.md"}}
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            dec_forgery, _ = self._run_pre_hook(
                {
                    "lastUserInput": "결제 시스템 만들어줘",
                    "transcriptPath": str(forgery_tx),
                    "toolCall": {"name": "swarm", "args": {"action": "add", "name": "forged-worker"}},
                }
            )
            self.assertEqual(dec_forgery["decision"], "deny")

            # 3. Natural-language UltimateMake request WITHOUT ultimate-make/SKILL.md loaded yet -> deny
            nl_um_tx = Path(tmpdir) / "nl_um_transcript.jsonl"
            nl_um_tx.write_text(
                json.dumps({"type": "USER_INPUT", "content": "UltimateMake로 결제 기획해줘"}) + "\n",
                encoding="utf-8",
            )
            dec_no_skill, _ = self._run_pre_hook(
                {
                    "lastUserInput": "UltimateMake로 결제 기획해줘",
                    "transcriptPath": str(nl_um_tx),
                    "toolCall": {"name": "swarm", "args": {"action": "add", "name": "premature-scout"}},
                }
            )
            self.assertEqual(dec_no_skill["decision"], "deny")

            # 4. Explicit /swarm slash command -> allow; unused /swarm window closes on next non-/swarm turn
            dec_slash, _ = self._run_pre_hook(
                {
                    "lastUserInput": "/swarm 아키텍처 대안 비교해줘",
                    "toolCall": {"name": "swarm", "args": {"action": "add", "name": "arch-1"}},
                }
            )
            self.assertEqual(dec_slash["decision"], "allow")

            unused_swarm_tx = Path(tmpdir) / "unused_swarm.jsonl"
            unused_swarm_tx.write_text(
                json.dumps({"type": "USER_INPUT", "content": "/swarm 간단한 질문"}) + "\n"
                + json.dumps({"type": "PLANNER_RESPONSE", "content": "텍스트 답변만 수행"}) + "\n"
                + json.dumps({"type": "USER_INPUT", "content": "오타 수정해줘"}) + "\n",
                encoding="utf-8",
            )
            dec_closed_swarm, _ = self._run_pre_hook(
                {
                    "lastUserInput": "오타 수정해줘",
                    "transcriptPath": str(unused_swarm_tx),
                    "toolCall": {"name": "swarm", "args": {"action": "add", "name": "late-worker"}},
                }
            )
            self.assertEqual(dec_closed_swarm["decision"], "deny")

            # 5. Multi-turn UltimateMake session with malformed JSONL resilience + SKILL.md read output -> allow
            um_tx = Path(tmpdir) / "um_session.jsonl"
            um_tx.write_text(
                json.dumps({"type": "USER_INPUT", "content": "UltimateMake로 결제 기획해줘"}) + "\n"
                + "{malformed json line that must be tolerated\n"
                + json.dumps(
                    {
                        "type": "PLANNER_RESPONSE",
                        "thinking": "In Phase 4 we will run validate_spec_lock.py after swarm kill.",
                        "tool_calls": [
                            {
                                "name": "read_file",
                                "args": {"Path": str(REPO_ROOT / ".agents" / "skills" / "ultimate-make" / "SKILL.md")},
                            }
                        ],
                    }
                )
                + "\n"
                + json.dumps(
                    {
                        "type": "GENERIC",
                        "content": "Showing lines 1-111 of 111\n1: ---\n2: name: ultimate-make\n48: validate_spec_lock.py\n",
                    }
                )
                + "\n"
                + json.dumps({"type": "USER_INPUT", "content": "1번은 A, 다중 모델 모드로 해줘"}) + "\n",
                encoding="utf-8",
            )

            for action in ("add", "title", "status", "kill"):
                dec_um, _ = self._run_pre_hook(
                    {
                        "lastUserInput": "1번은 A, 다중 모델 모드로 해줘",
                        "transcriptPath": str(um_tx),
                        "toolCall": {"name": "swarm", "args": {"action": action, "name": "rfc-scout"}},
                    }
                )
                self.assertEqual(dec_um["decision"], "allow", f"Expected allow for UltimateMake action={action}")

            # 6. Post-Phase-4 window closure after validate_spec_lock.py executes:
            #    new swarm{action:"add"} is denied, while cleanup swarm{action:"kill"} remains allowed!
            with open(um_tx, "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "type": "PLANNER_RESPONSE",
                            "tool_calls": [{"name": "swarm", "args": {"action": "add", "name": "rfc-scout"}}],
                        }
                    )
                    + "\n"
                    + json.dumps(
                        {
                            "type": "PLANNER_RESPONSE",
                            "tool_calls": [
                                {
                                    "name": "run_command",
                                    "args": {
                                        "CommandLine": "python .agents/skills/ultimate-make/scripts/validate_spec_lock.py --spec docs/specs/pay.spec.md --research docs/research/pay_intelligence.md"
                                    },
                                }
                            ],
                        }
                    )
                    + "\n"
                    + json.dumps({"type": "USER_INPUT", "content": "승인"}) + "\n"
                )

            dec_post_p4_add, _ = self._run_pre_hook(
                {
                    "lastUserInput": "승인",
                    "transcriptPath": str(um_tx),
                    "toolCall": {"name": "swarm", "args": {"action": "add", "name": "rogue-phase6-swarm"}},
                }
            )
            self.assertEqual(dec_post_p4_add["decision"], "deny")

            dec_post_p4_kill, _ = self._run_pre_hook(
                {
                    "lastUserInput": "승인",
                    "transcriptPath": str(um_tx),
                    "toolCall": {"name": "swarm", "args": {"action": "kill", "id": "rfc-scout"}},
                }
            )
            self.assertEqual(dec_post_p4_kill["decision"], "allow")

    def test_outside_vcs_write_defense_and_workspace_paths_containment(self):
        # 1. UNC and NT device paths -> deny
        for bad_path in (r"\\evil\share\a.py", r"\\?\C:\Windows\win.ini"):
            dec_unc, _ = self._run_pre_hook(
                {
                    "toolCall": {
                        "name": "write_file",
                        "args": {"Path": bad_path, "Content": "x = 1\n"},
                    }
                }
            )
            self.assertEqual(dec_unc["decision"], "deny", f"Expected deny for UNC/device path {bad_path}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)

            # 2. External Git repository outside workspacePaths -> deny (neutralizes CLI v1.5.16 Auto outside-VCS write relaxation)
            ext_git_repo = tmp_root / "external_git_repo"
            ext_git_repo.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "init"],
                cwd=str(ext_git_repo),
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            dec_ext_vcs, _ = self._run_pre_hook(
                {
                    "cwd": str(REPO_ROOT),
                    "workspacePaths": [str(REPO_ROOT)],
                    "toolCall": {
                        "name": "write_file",
                        "args": {
                            "Path": str(ext_git_repo / "pwned.py"),
                            "Content": "print('outside workspace vcs')\n",
                        },
                    },
                }
            )
            self.assertEqual(dec_ext_vcs["decision"], "deny")

            # 3. Isolated subagent share/branch worktree passed via workspacePaths (with Windows drive-case mismatch)
            worktree_dir = tmp_root / "subagent_branch_worktree"
            worktree_dir.mkdir(parents=True, exist_ok=True)
            wt_str = str(worktree_dir)
            if os.name == "nt" and len(wt_str) >= 2 and wt_str[1] == ":":
                ws_param = wt_str[0].lower() + wt_str[1:]
                target_inside = (wt_str[0].upper() + wt_str[1:]) + os.sep + "src" + os.sep + "feature.py"
            else:
                ws_param = wt_str
                target_inside = str(worktree_dir / "src" / "feature.py")

            dec_wt_allow, _ = self._run_pre_hook(
                {
                    "cwd": wt_str,
                    "workspacePaths": [ws_param],
                    "toolCall": {
                        "name": "write_file",
                        "args": {
                            "Path": target_inside,
                            "Content": "def feature():\n    return True\n",
                        },
                    },
                }
            )
            self.assertEqual(dec_wt_allow["decision"], "allow")

            # When isolated to worktree_dir in workspacePaths, writing back to main REPO_ROOT is denied!
            dec_wt_escape_main, _ = self._run_pre_hook(
                {
                    "cwd": wt_str,
                    "workspacePaths": [ws_param],
                    "toolCall": {
                        "name": "edit_file",
                        "args": {
                            "Path": str(REPO_ROOT / "README.md"),
                            "Target": "Terukirdo",
                            "Replacement": "Escaped",
                        },
                    },
                }
            )
            self.assertEqual(dec_wt_escape_main["decision"], "deny")

    def test_live_agy_plugin_validate_strict_zero_errors_and_warnings(self):
        agy_bin = shutil.which("agy")
        if not agy_bin:
            self.skipTest("agy CLI not found on PATH")

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)
            (plugin_dir / "logo.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
                '<circle cx="32" cy="32" r="28" fill="#e91e63"/></svg>\n',
                encoding="utf-8",
            )
            (plugin_dir / "plugin.json").write_text(
                json.dumps(
                    {
                        "name": "terukirdo-v58-harness-fixture",
                        "version": "5.8.0",
                        "description": "Terukirdo Protocol v5.8 Antigravity CLI v1.5.16 strict validation fixture",
                        "logo": "logo.svg",
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            shutil.copytree(REPO_ROOT / ".agents" / "agents", plugin_dir / "agents")
            shutil.copytree(REPO_ROOT / ".agents" / "rules", plugin_dir / "rules")
            shutil.copytree(REPO_ROOT / ".agents" / "hooks", plugin_dir / "hooks")
            shutil.copy2(REPO_ROOT / ".agents" / "hooks.json", plugin_dir / "hooks.json")

            for skill_folder in sorted((REPO_ROOT / ".agents" / "skills").iterdir()):
                skill_md = skill_folder / "SKILL.md"
                if skill_folder.is_dir() and skill_md.is_file():
                    dest_skill_dir = plugin_dir / "skills" / skill_folder.name
                    dest_skill_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(skill_md, dest_skill_dir / "SKILL.md")

            res = subprocess.run(
                [agy_bin, "plugin", "validate", str(plugin_dir), "--strict", "--json"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(
                res.returncode,
                0,
                f"agy plugin validate --strict --json failed:\n{res.stdout}\n{res.stderr}",
            )
            report = json.loads(res.stdout)
            findings = report.get("findings", [])
            errors = [f for f in findings if f.get("severity") == "error"]
            warnings = [f for f in findings if f.get("severity") == "warning"]
            self.assertEqual(errors, [], f"Unexpected strict loader errors: {errors}")
            self.assertEqual(warnings, [], f"Unexpected strict loader warnings: {warnings}")

            components = report.get("components", {})
            self.assertEqual(components.get("agents"), 9)
            self.assertEqual(components.get("hooks"), 3)
            self.assertEqual(components.get("rules"), 4)
            self.assertEqual(components.get("skills"), 19)

    def test_protocol_v58_promotion_ultimatemake_contract_and_sync_purge(self):
        self.assertTrue((REPO_ROOT / "Terukirdo_Protocol_v5.8.md").is_file())
        self.assertFalse((REPO_ROOT / "Terukirdo_Protocol_v5.7.md").exists())
        self.assertTrue((REPO_ROOT / "docs" / "archive" / "Terukirdo_Protocol_v5.7.md").is_file())

        for agent in EXPECTED_AGENTS:
            agent_path = REPO_ROOT / ".agents" / "agents" / agent / "agent.md"
            meta, body = parse_frontmatter(agent_path.read_text(encoding="utf-8"))
            self.assertIsInstance(meta, dict)
            self.assertEqual(meta.get("model"), EXPECTED_AGENT_MODELS[agent])
            self.assertIs(meta.get("subagent"), True, f"{agent} missing subagent: true")
            self.assertIs(meta.get("mainAgent"), False, f"{agent} missing mainAgent: false")
            self.assertIn("v5.8", body, f"{agent}/agent.md body missing v5.8")
            self.assertIn("v1.5.16", body, f"{agent}/agent.md body missing v1.5.16")

        for skill_rel in (
            ".agents/skills/ultimate-make/SKILL.md",
            ".agents/skills/multi-agent-conference/SKILL.md",
        ):
            stext = (REPO_ROOT / skill_rel).read_text(encoding="utf-8")
            self.assertIn("swarm", stext, f"{skill_rel} missing swarm documentation")
            self.assertIn("read_board", stext, f"{skill_rel} missing Round 1 read_board rule")
            self.assertIn("narrator", stext, f"{skill_rel} missing narrator exclusion")
            self.assertIn("monitor", stext, f"{skill_rel} missing monitor exclusion")
            self.assertIn("kill", stext, f"{skill_rel} missing pre-Phase-4 kill teardown")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_target = Path(tmpdir)
            (tmp_target / "Terukirdo_Protocol_v5.7.md").write_text("stale root v5.7 protocol\n", encoding="utf-8")

            success, stats = sync_harness(REPO_ROOT, tmp_target, run_verification=True)
            self.assertTrue(success, f"sync_harness failed with errors: {stats['errors']}")
            self.assertEqual(stats["errors"], [])
            self.assertFalse((tmp_target / "Terukirdo_Protocol_v5.7.md").exists())
            self.assertTrue((tmp_target / "Terukirdo_Protocol_v5.8.md").is_file())
            self.assertTrue((tmp_target / "docs" / "archive" / "Terukirdo_Protocol_v5.7.md").is_file())

    def test_eleven_untouched_baseline_test_files_zero_diff(self):
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
        touched_untouched = sorted(changed_names & UNTOUCHED_11_BASELINE_TEST_FILES)
        self.assertEqual(
            touched_untouched,
            [],
            f"Baseline test integrity violation — untouched baseline test files modified: {touched_untouched}",
        )


if __name__ == "__main__":
    unittest.main()
