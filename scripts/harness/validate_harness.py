#!/usr/bin/env python3
import os
import sys
import re
from pathlib import Path

VALID_MODELS = {"inherit", "pro", "flash", "flash_lite"}

WRITE_TOOLS = {"write_file", "edit_file", "notebook_edit"}
REQUIRED_WORKER_TOOLS = {"write_file", "edit_file", "run_command", "view_file"}
REQUIRED_SHELL_VERIFIER_TOOLS = {"run_command", "view_file"}
REQUIRED_ORCHESTRATOR_TOOLS = {"invoke_subagent", "manage_subagents", "view_file", "send_message", "run_command"}

EXPECTED_AGENTS = [
    "ralph-orchestrator",
    "terukirdo-plan",
    "agy-worker",
    "first-reviewer",
    "tech-expert",
    "universal-final-controller",
    "final-approach-control",
    "legion-commander",
    "legion-worker"
]

EXPECTED_AGENT_MODELS = {
    "legion-commander": "inherit",
    "ralph-orchestrator": "inherit",
    "terukirdo-plan": "pro",
    "agy-worker": "inherit",
    "legion-worker": "inherit",
    "first-reviewer": "pro",
    "tech-expert": "pro",
    "universal-final-controller": "flash",
    "final-approach-control": "flash",
}

FORBIDDEN_SKILL_PATTERNS = (
    "model: opus",
    "model: sonnet",
    "auto_evolve.py",
    "implementation-playbook.md",
    "undetected_chromedriver",
    ".agent/skills/",
    ".claude4net",
)

FENCE_RE = re.compile(r"^`{3,}")
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
MD_LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
SKILL_REL_PATH_RE = re.compile(r"\.agents/skills/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+")


def strip_code_blocks_and_inline(markdown_text):
    """Remove fenced code blocks and inline code spans before link extraction."""
    outside_fences = []
    in_fence = False
    fence_marker = None
    for line in markdown_text.splitlines():
        stripped = line.strip()
        m = FENCE_RE.match(stripped)
        if m:
            ticks = m.group(0)
            if not in_fence:
                in_fence = True
                fence_marker = ticks
            elif len(ticks) >= len(fence_marker):
                in_fence = False
                fence_marker = None
            continue
        if not in_fence:
            outside_fences.append(INLINE_CODE_RE.sub("", line))
    return "\n".join(outside_fences)


def parse_frontmatter(content):
    if not content.startswith("---"):
        return None, "File does not start with YAML frontmatter delimiter '---'"
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, "File does not contain closing YAML frontmatter delimiter '---'"
    
    frontmatter_text = parts[1]
    body_text = parts[2]
    
    metadata = {}
    lines = frontmatter_text.splitlines()
    current_key = None
    folded_mode = False
    folded_lines = []
    list_mode = False
    list_items = []
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith("#"):
            continue
        
        if list_mode:
            if line_stripped.startswith("- "):
                item = line_stripped[2:].strip().strip('"').strip("'")
                list_items.append(item)
                continue
            elif not line.startswith(" ") and not line.startswith("\t"):
                metadata[current_key] = list_items
                list_mode = False
                list_items = []
            else:
                continue

        if folded_mode:
            if ":" in line and not line.startswith(" ") and not line.startswith("\t"):
                metadata[current_key] = "\n".join(folded_lines).strip()
                folded_mode = False
                folded_lines = []
            else:
                folded_lines.append(line)
                continue
        
        if ":" in line and not line.startswith(" ") and not line.startswith("\t"):
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            
            if val in (">", "|", ">-", "|-"):
                folded_mode = True
                current_key = key
                folded_lines = []
            elif val == "":
                list_mode = True
                current_key = key
                list_items = []
            else:
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                metadata[key] = val
                current_key = key
        elif current_key and (line.startswith(" ") or line.startswith("\t")) and isinstance(metadata.get(current_key), str):
            metadata[current_key] = f"{metadata[current_key]} {line_stripped}".strip()
                
    if folded_mode and current_key:
        metadata[current_key] = "\n".join(folded_lines).strip()
    if list_mode and current_key:
        metadata[current_key] = list_items
        
    return metadata, body_text


def validate_skills_directory(base_dir, strict=False):
    skills_dir = Path(base_dir) / ".agents" / "skills"
    errors = []

    if not skills_dir.is_dir():
        errors.append(f"Directory not found: {skills_dir}")
        return errors

    skill_folders = sorted([d for d in skills_dir.iterdir() if d.is_dir()], key=lambda p: p.name)
    if not skill_folders:
        errors.append("No skill directories found in .agents/skills")
        return errors

    for folder in skill_folders:
        skill_md = folder / "SKILL.md"
        rel_skill = f".agents/skills/{folder.name}/SKILL.md"
        if not skill_md.is_file():
            errors.append(f"Missing skill definition file: {rel_skill}")
            continue

        try:
            content = skill_md.read_text(encoding="utf-8")
        except Exception as e:
            errors.append(f"Failed to read {rel_skill}: {e}")
            continue

        metadata, _ = parse_frontmatter(content)
        if not isinstance(metadata, dict):
            errors.append(f"Invalid frontmatter in {rel_skill}: {metadata}")
            continue

        name = metadata.get("name")
        if name != folder.name:
            errors.append(f"Skill name mismatch in {rel_skill}: frontmatter name '{name}' != folder name '{folder.name}'")

        description = metadata.get("description")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"Missing or empty description in {rel_skill} frontmatter")
        elif description.strip().endswith("implementa"):
            errors.append(f"Truncated description detected in {rel_skill}")

    if strict:
        for md_path in sorted(skills_dir.rglob("*.md")):
            if "skillopt-engine" in md_path.parts:
                continue
            rel_md = md_path.relative_to(base_dir).as_posix()
            try:
                text = md_path.read_text(encoding="utf-8")
            except Exception as e:
                errors.append(f"Failed to read {rel_md}: {e}")
                continue

            for forbidden in FORBIDDEN_SKILL_PATTERNS:
                if forbidden in text:
                    errors.append(f"Forbidden pattern '{forbidden}' found in {rel_md}")

            if rel_md == ".agents/skills/cluedoc/SKILL.md":
                for cluedoc_forbidden in ("<!-- cluedoc:start -->", "without being asked"):
                    if cluedoc_forbidden in text:
                        errors.append(f"Protocol-conflicting pattern '{cluedoc_forbidden}' found in {rel_md}")

            stripped = strip_code_blocks_and_inline(text)
            for match in MD_LINK_RE.finditer(stripped):
                raw_target = match.group(2).strip()
                target = raw_target.split("#", 1)[0].strip()
                if not target or target.startswith(("http://", "https://", "mailto:")):
                    continue
                resolved = (md_path.parent / target).resolve()
                if not resolved.exists():
                    errors.append(f"Broken relative markdown link '{raw_target}' in {rel_md}")

            for match in SKILL_REL_PATH_RE.finditer(stripped):
                ref_rel = match.group(0).rstrip(".,;:)")
                if not (Path(base_dir) / ref_rel).exists():
                    errors.append(f"Missing referenced skill path '{ref_rel}' in {rel_md}")

    return errors


def validate_harness(strict=False, base_dir=None):
    if base_dir is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    else:
        base_dir = os.path.abspath(str(base_dir))
    agents_dir = os.path.join(base_dir, ".agents", "agents")
    old_agents_dir = os.path.join(base_dir, "agents")
    errors = []
    
    if not os.path.isdir(agents_dir):
        errors.append(f"Directory not found: {agents_dir}")
        return errors

    found_agents = []
    for agent in EXPECTED_AGENTS:
        agent_path = os.path.join(agents_dir, agent, "agent.md")
        if not os.path.isfile(agent_path):
            errors.append(f"Missing agent file: .agents/agents/{agent}/agent.md")
            continue
        
        try:
            with open(agent_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            errors.append(f"Failed to read {agent_path}: {e}")
            continue
            
        metadata, _ = parse_frontmatter(content)
        if not isinstance(metadata, dict):
            errors.append(f"Invalid frontmatter in .agents/agents/{agent}/agent.md: {metadata}")
            continue
            
        name = metadata.get("name")
        if name != agent:
            errors.append(f"Name mismatch in .agents/agents/{agent}/agent.md: frontmatter name '{name}' != folder name '{agent}'")
            
        description = metadata.get("description")
        if not description:
            errors.append(f"Missing description in .agents/agents/{agent}/agent.md frontmatter")

        model = metadata.get("model")
        if not model or model not in VALID_MODELS:
            errors.append(f"Invalid or missing model '{model}' in .agents/agents/{agent}/agent.md: must be one of {sorted(VALID_MODELS)}")
        else:
            expected_model = EXPECTED_AGENT_MODELS.get(agent)
            if expected_model and model != expected_model:
                errors.append(f"Tri-Engine model mismatch in .agents/agents/{agent}/agent.md: got '{model}', expected '{expected_model}'")

        tools = metadata.get("tools")
        if not isinstance(tools, list) or not tools:
            errors.append(f"Missing or empty 'tools' list in .agents/agents/{agent}/agent.md frontmatter")
        else:
            tool_set = set(tools)
            if agent in ("agy-worker", "legion-worker"):
                missing_worker_tools = REQUIRED_WORKER_TOOLS - tool_set
                if missing_worker_tools:
                    errors.append(
                        f"agy-worker missing required write/execution tools in frontmatter: {sorted(missing_worker_tools)}"
                    )
            else:
                forbidden_write = tool_set & WRITE_TOOLS
                if forbidden_write:
                    errors.append(
                        f"Read-only agent '{agent}' must not declare write tools in frontmatter: {sorted(forbidden_write)}"
                    )
                if agent in ("universal-final-controller", "final-approach-control", "legion-commander"):
                    missing_verifier = REQUIRED_SHELL_VERIFIER_TOOLS - tool_set
                    if missing_verifier:
                        errors.append(
                            f"Verifier agent '{agent}' missing required execution tools: {sorted(missing_verifier)}"
                        )
                if agent in ("ralph-orchestrator", "legion-commander"):
                    missing_orch = REQUIRED_ORCHESTRATOR_TOOLS - tool_set
                    if missing_orch:
                        errors.append(
                            f"Orchestrator agent '{agent}' missing required dispatch tools: {sorted(missing_orch)}"
                        )

        found_agents.append(agent)

    for folder in os.listdir(agents_dir):
        folder_path = os.path.join(agents_dir, folder)
        if os.path.isdir(folder_path) and folder not in EXPECTED_AGENTS:
            errors.append(f"Unexpected custom agent folder found: .agents/agents/{folder}")

    if os.path.isdir(old_agents_dir):
        for f in os.listdir(old_agents_dir):
            if f not in ["README.md", ".gitkeep"] and f.endswith(".md"):
                errors.append(f"Stale duplicate agent file found in root agents/ directory: agents/{f}")

    required_legion_scripts = [
        os.path.join(".agents", "skills", "agent-legion", "scripts", "partition_validator.py"),
        os.path.join(".agents", "skills", "agent-legion", "scripts", "legion_radio.py"),
    ]
    for rel_script in required_legion_scripts:
        full_script = os.path.join(base_dir, rel_script)
        if not os.path.isfile(full_script):
            errors.append(f"Missing required Agent Legion script: {rel_script.replace(os.sep, '/')}")

    errors.extend(validate_skills_directory(base_dir, strict=strict))

    return errors

if __name__ == "__main__":
    strict = "--strict" in sys.argv
    errors = validate_harness(strict=strict)
    
    if errors:
        print("Harness Validation FAILED with following errors:", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        sys.exit(1)
    else:
        print("Harness Validation PASSED.")
        sys.exit(0)
