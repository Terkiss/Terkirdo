#!/usr/bin/env python3
import json
import os
import re
import shlex
import sys
from pathlib import Path

VALID_MODELS = {"inherit", "pro", "flash", "flash_lite"}

VALID_RULE_TRIGGERS = {"always_on", "model_decision", "glob", "manual"}

MAX_RULE_FILE_BYTES = 24000

GEMINI_CLI_CATALOG_MODELS = {
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

GROUPED_HOOK_EVENTS = {"PreToolUse", "PostToolUse"}
FLAT_HOOK_EVENTS = {"Stop", "SessionStart", "PreInvocation", "PostInvocation"}

WRITE_TOOLS = {"write_file", "edit_file", "notebook_edit"}
REQUIRED_AGENT_TOOLS = {"view_file"}
REQUIRED_WORKER_TOOLS = {"write_file", "edit_file", "run_command", "view_file"}
REQUIRED_SHELL_VERIFIER_TOOLS = {"run_command", "view_file"}
REQUIRED_ORCHESTRATOR_TOOLS = {"invoke_subagent", "manage_subagents", "view_file", "send_message", "run_command"}

TOOL_ALIAS_CONFLICTS = [
    (
        {"view_file", "read_file"},
        "view_file and read_file both resolve to read_file in Antigravity CLI v1.5.7 and crash subagent executor construction",
    ),
    (
        {"write_file", "write_to_file"},
        "write_file and write_to_file conflict as duplicate file-write tool aliases in subagent executor construction",
    ),
    (
        {"edit_file", "replace_file_content"},
        "edit_file and replace_file_content conflict as duplicate file-edit tool aliases in subagent executor construction",
    ),
]

EXPECTED_AGENTS = [
    "ralph-orchestrator",
    "terukirdo-plan",
    "agy-worker",
    "first-reviewer",
    "tech-expert",
    "universal-final-controller",
    "final-approach-control",
    "legion-commander",
    "legion-worker",
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


def validate_rules_directory(base_dir):
    rules_dir = Path(base_dir) / ".agents" / "rules"
    errors = []

    if not rules_dir.is_dir():
        errors.append(f"Directory not found: {rules_dir}")
        return errors

    rule_files = sorted(
        [p for p in rules_dir.glob("*.md") if p.name.lower() != "readme.md"],
        key=lambda p: p.name,
    )
    if not rule_files:
        errors.append("No rule markdown files found in .agents/rules")
        return errors

    for rule_path in rule_files:
        rel_rule = f".agents/rules/{rule_path.name}"
        try:
            raw_bytes = rule_path.read_bytes()
        except Exception as e:
            errors.append(f"Failed to read {rel_rule}: {e}")
            continue

        if raw_bytes.startswith(b"\xef\xbb\xbf"):
            errors.append(f"UTF-8 BOM detected in {rel_rule} (Antigravity CLI rule loader requires UTF-8 without BOM)")
            raw_bytes = raw_bytes[3:]

        if len(raw_bytes) > MAX_RULE_FILE_BYTES:
            errors.append(
                f"Rule file size {len(raw_bytes)} bytes exceeds {MAX_RULE_FILE_BYTES}-byte CLI limit in {rel_rule}"
            )

        try:
            content = raw_bytes.decode("utf-8")
        except Exception as e:
            errors.append(f"Invalid UTF-8 encoding in {rel_rule}: {e}")
            continue

        metadata, body = parse_frontmatter(content)
        if not isinstance(metadata, dict):
            errors.append(f"Invalid frontmatter in {rel_rule}: {metadata}")
            continue

        trigger = metadata.get("trigger")
        if not trigger or trigger not in VALID_RULE_TRIGGERS:
            errors.append(
                f"Invalid or missing trigger '{trigger}' in {rel_rule}: must be one of {sorted(VALID_RULE_TRIGGERS)}"
            )
        else:
            if trigger == "model_decision":
                desc = metadata.get("description")
                if not isinstance(desc, str) or not desc.strip():
                    errors.append(f"Missing required 'description' for trigger 'model_decision' in {rel_rule}")
            elif trigger == "glob":
                globs = metadata.get("globs")
                has_globs = (isinstance(globs, str) and bool(globs.strip())) or (
                    isinstance(globs, list) and len(globs) > 0
                )
                if not has_globs:
                    errors.append(f"Missing required 'globs' for trigger 'glob' in {rel_rule}")

        if not body.strip():
            errors.append(f"Empty rule body in {rel_rule}")

    return errors


def _validate_hook_handler(handler, ctx_label, agents_root, errors):
    if not isinstance(handler, dict):
        errors.append(f"Hook handler in {ctx_label} must be a JSON object")
        return

    h_type = handler.get("type")
    if h_type != "command":
        errors.append(f"Hook handler in {ctx_label} must specify type 'command' (got '{h_type}')")

    cmd = handler.get("command")
    if not isinstance(cmd, str) or not cmd.strip():
        errors.append(f"Hook handler in {ctx_label} missing non-empty 'command'")
        return

    try:
        tokens = shlex.split(cmd, posix=True)
    except Exception:
        tokens = cmd.split()

    if tokens and os.path.basename(tokens[0]).lower() in ("python", "python3", "py", "python.exe", "python3.exe"):
        script_arg = None
        i = 1
        while i < len(tokens):
            tok = tokens[i]
            if tok == "-X" and i + 1 < len(tokens):
                i += 2
                continue
            if tok.startswith("-"):
                i += 1
                continue
            script_arg = tok
            break

        if script_arg:
            resolved_script = agents_root / script_arg
            if not resolved_script.is_file():
                errors.append(
                    f"Hook command script '{script_arg}' in {ctx_label} does not exist relative to .agents/ "
                    f"(expected {resolved_script.as_posix()})"
                )


def validate_hooks_config(base_dir):
    agents_root = Path(base_dir) / ".agents"
    hooks_json_path = agents_root / "hooks.json"
    errors = []

    if not hooks_json_path.is_file():
        errors.append("Missing hooks configuration file: .agents/hooks.json")
        return errors

    try:
        raw_bytes = hooks_json_path.read_bytes()
    except Exception as e:
        errors.append(f"Failed to read .agents/hooks.json: {e}")
        return errors

    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        errors.append("UTF-8 BOM detected in .agents/hooks.json")
        raw_bytes = raw_bytes[3:]

    try:
        data = json.loads(raw_bytes.decode("utf-8"))
    except Exception as e:
        errors.append(f"Invalid JSON in .agents/hooks.json: {e}")
        return errors

    if not isinstance(data, dict):
        errors.append(".agents/hooks.json root must be a JSON object")
        return errors

    if "hooks" in data:
        errors.append(".agents/hooks.json must not wrap root definitions inside a top-level 'hooks' key")
        return errors

    for policy_name, policy_cfg in data.items():
        if not isinstance(policy_cfg, dict):
            errors.append(f"Hook policy '{policy_name}' in .agents/hooks.json must be an object")
            continue

        for key, val in policy_cfg.items():
            if key == "enabled":
                if not isinstance(val, bool):
                    errors.append(f"Hook policy '{policy_name}.enabled' must be a boolean")
            elif key in GROUPED_HOOK_EVENTS:
                if not isinstance(val, list) or not val:
                    errors.append(f"Grouped hook event '{policy_name}.{key}' must be a non-empty list")
                    continue
                for idx, group in enumerate(val):
                    ctx = f"{policy_name}.{key}[{idx}]"
                    if not isinstance(group, dict):
                        errors.append(f"{ctx} must be an object with 'matcher' and 'hooks'")
                        continue
                    matcher = group.get("matcher")
                    if not isinstance(matcher, str) or not matcher.strip():
                        errors.append(f"{ctx} missing non-empty 'matcher'")
                    else:
                        matcher_tokens = {tok.strip() for tok in matcher.split("|") if tok.strip()}
                        for req_tool in ("write_file", "edit_file"):
                            if req_tool not in matcher_tokens:
                                errors.append(
                                    f"{ctx} matcher must include CLI v1.5.7 tool '{req_tool}' (got '{matcher}')"
                                )
                    nested_hooks = group.get("hooks")
                    if not isinstance(nested_hooks, list) or not nested_hooks:
                        errors.append(f"{ctx} missing non-empty 'hooks' handler list")
                        continue
                    for h_idx, handler in enumerate(nested_hooks):
                        _validate_hook_handler(handler, f"{ctx}.hooks[{h_idx}]", agents_root, errors)
            elif key in FLAT_HOOK_EVENTS:
                if not isinstance(val, list) or not val:
                    errors.append(f"Flat hook event '{policy_name}.{key}' must be a non-empty list of handlers")
                    continue
                for idx, handler in enumerate(val):
                    ctx = f"{policy_name}.{key}[{idx}]"
                    if isinstance(handler, dict) and "hooks" in handler:
                        errors.append(
                            f"Flat hook event '{ctx}' must NOT wrap handlers inside a nested 'hooks' key "
                            "(Antigravity CLI v1.5.7 requires flat handler objects for Stop/SessionStart/PreInvocation/PostInvocation)"
                        )
                        continue
                    _validate_hook_handler(handler, ctx, agents_root, errors)
            else:
                errors.append(f"Unsupported hook event or field '{key}' in '{policy_name}' (.agents/hooks.json)")

    return errors


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
            raw_bytes = skill_md.read_bytes()
            if raw_bytes.startswith(b"\xef\xbb\xbf"):
                errors.append(f"UTF-8 BOM detected in {rel_skill}")
                raw_bytes = raw_bytes[3:]
            content = raw_bytes.decode("utf-8")
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
            raw_bytes = Path(agent_path).read_bytes()
            if raw_bytes.startswith(b"\xef\xbb\xbf"):
                errors.append(f"UTF-8 BOM detected in .agents/agents/{agent}/agent.md")
                raw_bytes = raw_bytes[3:]
            content = raw_bytes.decode("utf-8")
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
            missing_agent_tools = REQUIRED_AGENT_TOOLS - tool_set
            if missing_agent_tools:
                errors.append(
                    f"Agent '{agent}' missing required file-read tool in frontmatter: {sorted(missing_agent_tools)}"
                )
            for conflict_pair, conflict_reason in TOOL_ALIAS_CONFLICTS:
                if conflict_pair.issubset(tool_set):
                    errors.append(
                        f"Tool alias collision in .agents/agents/{agent}/agent.md: {sorted(conflict_pair)} ({conflict_reason})"
                    )
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

    errors.extend(validate_rules_directory(base_dir))
    errors.extend(validate_hooks_config(base_dir))
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
