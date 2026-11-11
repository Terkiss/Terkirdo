import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "harness"))

from validate_harness import (  # noqa: E402
    parse_frontmatter,
    strip_code_blocks_and_inline,
    validate_skills_directory,
)

FENCE_LINE_RE = re.compile(r"^`{3,}")
HEADER_LINE_RE = re.compile(r"^#{1,3}\s+")
TEMPLATE_PLACEHOLDER_RE = re.compile(r"\{[a-zA-Z_][a-zA-Z0-9_]*\}")
MD_LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
CONCRETE_SKILL_PATH_RE = re.compile(r"\.agents/skills/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+")


class TestSkillsIntegrity(unittest.TestCase):
    def setUp(self):
        self.base_dir = REPO_ROOT
        self.skills_dir = self.base_dir / ".agents" / "skills"
        self.skill_folders = sorted(
            [d for d in self.skills_dir.iterdir() if d.is_dir()],
            key=lambda p: p.name,
        )
        self.all_skill_md_files = sorted(
            [
                p
                for p in self.skills_dir.rglob("*.md")
                if "skillopt-engine" not in p.parts
            ]
        )

    def test_all_19_skills_have_valid_frontmatter_and_no_truncation(self):
        self.assertEqual(
            len(self.skill_folders),
            19,
            f"Expected 19 skill directories under .agents/skills, found {len(self.skill_folders)}",
        )
        for folder in self.skill_folders:
            skill_md = folder / "SKILL.md"
            self.assertTrue(skill_md.is_file(), f"Missing SKILL.md in {folder.name}")
            content = skill_md.read_text(encoding="utf-8")
            metadata, body = parse_frontmatter(content)
            self.assertIsInstance(
                metadata,
                dict,
                f"Failed to parse YAML frontmatter in {skill_md.relative_to(self.base_dir)}",
            )
            self.assertEqual(
                metadata.get("name"),
                folder.name,
                f"Frontmatter name '{metadata.get('name')}' != folder '{folder.name}'",
            )
            desc = metadata.get("description", "")
            self.assertIsInstance(desc, str)
            self.assertGreaterEqual(
                len(desc.strip()),
                20,
                f"Description too short or empty in {folder.name}/SKILL.md: {desc!r}",
            )
            self.assertIsNone(
                re.search(r"\bimplementa\b", content),
                f"Truncated word 'implementa' found in {folder.name}/SKILL.md",
            )
            self.assertNotIn(
                "You push for explicit error hand\n",
                content,
                f"Truncated sentence artifact found in {folder.name}/SKILL.md",
            )
            self.assertTrue(body.strip(), f"Empty body in {folder.name}/SKILL.md")

    def test_markdown_links_and_skill_paths_resolve_without_ghost_references(self):
        forbidden_ghost_refs = (
            ".agent/skills/",
            "auto_evolve.py",
            "implementation-playbook.md",
        )
        for md_path in self.all_skill_md_files:
            rel_label = md_path.relative_to(self.base_dir).as_posix()
            raw_text = md_path.read_text(encoding="utf-8")

            for ghost in forbidden_ghost_refs:
                self.assertNotIn(
                    ghost,
                    raw_text,
                    f"Ghost/deleted reference '{ghost}' found in {rel_label}",
                )

            stripped = strip_code_blocks_and_inline(raw_text)

            for match in MD_LINK_RE.finditer(stripped):
                raw_target = match.group(2).strip()
                target = raw_target.split("#", 1)[0].strip()
                if not target or target.startswith(("http://", "https://", "mailto:")):
                    continue
                resolved = (md_path.parent / target).resolve()
                self.assertTrue(
                    resolved.exists(),
                    f"Broken relative markdown link '{raw_target}' in {rel_label} -> {resolved}",
                )

            for match in CONCRETE_SKILL_PATH_RE.finditer(raw_text):
                ref_rel = match.group(0).rstrip(".,;:)")
                self.assertTrue(
                    (self.base_dir / ref_rel).exists(),
                    f"Missing .agents/skills path '{ref_rel}' referenced in {rel_label}",
                )

    def test_even_code_fences_no_stubs_and_no_orphan_trailing_headers(self):
        for md_path in self.all_skill_md_files:
            rel_label = md_path.relative_to(self.base_dir).as_posix()
            text = md_path.read_text(encoding="utf-8")
            lines = text.splitlines()

            self.assertGreater(
                len(lines),
                2,
                f"Stub markdown file (<= 2 lines) detected: {rel_label}",
            )
            non_empty_lines = [ln for ln in lines if ln.strip()]
            self.assertGreaterEqual(
                len(non_empty_lines),
                2,
                f"Stub markdown file (< 2 non-empty lines) detected: {rel_label}",
            )

            fence_lines = [ln for ln in lines if FENCE_LINE_RE.match(ln.strip())]
            self.assertEqual(
                len(fence_lines) % 2,
                0,
                f"Unclosed/odd markdown code fences ({len(fence_lines)}) in {rel_label}",
            )

            last_line = non_empty_lines[-1].strip()
            if HEADER_LINE_RE.match(last_line):
                is_asset_template_footer = (
                    "assets" in md_path.parts and bool(TEMPLATE_PLACEHOLDER_RE.search(last_line))
                )
                self.assertTrue(
                    is_asset_template_footer,
                    f"Orphan trailing markdown header '{last_line}' at end of {rel_label}",
                )

    def test_zero_legacy_unsafe_or_protocol_conflicting_patterns(self):
        global_forbidden = (
            "model: opus",
            "model: sonnet",
            "Opus 5.5",
            "Sonnet 5.5",
            ".claude4net",
            "undetected_chromedriver",
            "fake_useragent",
        )
        for md_path in self.all_skill_md_files:
            rel_label = md_path.relative_to(self.base_dir).as_posix()
            text = md_path.read_text(encoding="utf-8")
            for pat in global_forbidden:
                self.assertNotIn(
                    pat,
                    text,
                    f"Forbidden legacy/unsafe pattern '{pat}' found in {rel_label}",
                )

        cluedoc_text = (self.skills_dir / "cluedoc" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("<!-- cluedoc:start -->", cluedoc_text)
        self.assertNotIn("without being asked", cluedoc_text)
        self.assertIn("auto_sync: false", cluedoc_text)

        conf_text = (self.skills_dir / "multi-agent-conference" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Gemini 4 Carbon", conf_text)
        self.assertIn("Gemini 4 Argon", conf_text)
        self.assertIn("Gemini 3.8 Flash", conf_text)
        self.assertIn("send_message", conf_text)
        self.assertIn("Zero Finding Quota", conf_text)
        self.assertIn("legion_radio.py", conf_text)

        crawler_text = (self.skills_dir / "universal-crawler" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("robots.txt", crawler_text)
        self.assertIn("Retry-After", crawler_text)
        self.assertIn("playwright.sync_api", crawler_text)

    def test_validate_skills_directory_strict_catches_defects(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_base = Path(tmpdir)
            bad_skill = tmp_base / ".agents" / "skills" / "demo-skill"
            bad_skill.mkdir(parents=True, exist_ok=True)
            (bad_skill / "SKILL.md").write_text(
                "---\n"
                "name: wrong-name\n"
                "description: Demo skill with broken link and model: opus\n"
                "---\n\n"
                "See [Missing](./sub-skills/missing.md) and `auto_evolve.py`.\n",
                encoding="utf-8",
            )
            errs = validate_skills_directory(tmp_base, strict=True)
            joined = "\n".join(errs)
            self.assertIn("Skill name mismatch", joined)
            self.assertIn("model: opus", joined)
            self.assertIn("auto_evolve.py", joined)
            self.assertIn("Broken relative markdown link", joined)


if __name__ == "__main__":
    unittest.main()
