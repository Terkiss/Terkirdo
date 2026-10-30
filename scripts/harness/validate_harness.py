#!/usr/bin/env python3
import os
import sys
import re

VALID_MODELS = {"inherit", "pro", "flash", "flash_lite"}

WRITE_TOOLS = {"write_file", "edit_file", "notebook_edit"}
REQUIRED_WORKER_TOOLS = {"write_file", "edit_file", "run_command", "view_file"}
REQUIRED_SHELL_VERIFIER_TOOLS = {"run_command", "view_file"}
REQUIRED_ORCHESTRATOR_TOOLS = {"invoke_subagent", "manage_subagents", "view_file"}

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
        
        if ":" in line:
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
                
    if folded_mode and current_key:
        metadata[current_key] = "\n".join(folded_lines).strip()
    if list_mode and current_key:
        metadata[current_key] = list_items
        
    return metadata, body_text

def validate_harness(strict=False):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
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
