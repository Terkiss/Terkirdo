#!/usr/bin/env python3
import sys
import re
import json
import shlex
import os
import subprocess
from pathlib import Path
from common import load_input, respond_json, log_stderr, normalize_path, find_repo_root, check_secret_in_content

FILE_WRITE_TOOLS = {
    "write_file",
    "edit_file",
    "notebook_edit",
    "write_to_file",
    "replace_file_content",
    "multi_replace_file_content",
}

# Absolute Deny Command list
DENY_CMD_REGEX = [
    (r"\brm\s+-[^;\n]*r[^;\n]*f\s+/\b", "destructive root deletion (rm -rf /)"),
    (r"\bterraform\s+destroy\b", "destructive infrastructure destroy (terraform destroy)"),
    (r"(?i)\bFormat-Volume\b", "destructive disk formatting (Format-Volume)"),
    (r"\bdotnet\s+ef\s+database\s+drop\b", "destructive database drop (dotnet ef database drop)"),
    (r"(?i)\bDrop-Database\b", "destructive database drop (Drop-Database)"),
]

# Force Ask Command list
FORCE_ASK_CMD_REGEX = [
    (r"\bterraform\s+apply\b", "Terraform infrastructure mutation"),
    (r"\bkubectl\s+(apply|delete|rollout|scale)\b", "Kubernetes production-impacting operation"),
    (r"\bfirebase\s+deploy\b", "Firebase production deploy"),
    (r"\bgcloud\s+app\s+deploy\b", "Google Cloud production deploy"),
    (r"\bfastlane\s+(deliver|supply|pilot|deploy)\b", "Fastlane mobile release action"),
    (r"\b(npm|yarn|pnpm)\s+install\b", "package dependency installation"),
    (r"\bpip\s+install\b", "python package installation"),
    (r"\bflutter\s+pub\s+(add|get)\b", "Flutter package dependency action"),
]

SLASH_TRIGGER_PATTERN = re.compile(r"(?:^|\s|\[|\"|\'|>)(/agent-legion|/legion)(?=$|\s|\]|\"|\'|:|<)")

BRAIN_APP_VARIANTS = ("antigravity-cli", "antigravity", "antigravity-ide")


def _is_safe_conversation_id(conv_id: object) -> bool:
    if not isinstance(conv_id, str) or not conv_id.strip():
        return False
    return "/" not in conv_id and "\\" not in conv_id and ".." not in conv_id


def resolve_repo_root(payload: dict) -> Path:
    cwd_val = payload.get("cwd")
    if isinstance(cwd_val, str) and cwd_val.strip():
        cwd_path = Path(cwd_val)
        if cwd_path.is_dir():
            try:
                out = subprocess.check_output(
                    ["git", "rev-parse", "--show-toplevel"],
                    cwd=cwd_path,
                    stderr=subprocess.DEVNULL,
                    text=True,
                ).strip()
                if out:
                    return Path(out)
            except Exception:
                pass
    root = find_repo_root()
    if root.name == ".agents":
        return root.parent
    return root


def _resolve_transcript_path(payload: dict) -> Path | None:
    tp = payload.get("transcriptPath")
    if isinstance(tp, str) and tp.strip():
        candidate = Path(tp)
        if candidate.is_file():
            return candidate

    conversation_id = payload.get("conversationId")
    if _is_safe_conversation_id(conversation_id):
        home_gemini = Path.home() / ".gemini"
        for variant in BRAIN_APP_VARIANTS:
            fallback = (
                home_gemini
                / variant
                / "brain"
                / conversation_id.strip()
                / ".system_generated"
                / "logs"
                / "transcript.jsonl"
            )
            if fallback.is_file():
                return fallback
    return None


def check_subagent_invocation(args: dict, payload: dict) -> tuple[str, str]:
    type_name = (args.get("TypeName") or "").strip().lower()
    if type_name != "legion-commander":
        return "allow", ""

    prompt = args.get("Prompt") or ""
    if not SLASH_TRIGGER_PATTERN.search(prompt):
        return (
            "deny",
            "Slash-Command-Only Policy Violation: 'legion-commander' CANNOT be triggered via natural language conversation. "
            "It may ONLY be invoked when the user explicitly enters the '/agent-legion' or '/legion' slash command.",
        )

    last_user_input = payload.get("lastUserInput")
    if isinstance(last_user_input, str) and last_user_input.strip():
        if not SLASH_TRIGGER_PATTERN.search(last_user_input):
            return (
                "deny",
                "Slash-Command-Only Policy Violation: Latest user input (lastUserInput) does not contain "
                "explicit '/agent-legion' or '/legion' slash command. Conversational auto-trigger is strictly blocked.",
            )

    transcript_path = _resolve_transcript_path(payload)
    if transcript_path is not None and transcript_path.is_file():
        try:
            last_user_text = None
            with open(transcript_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    if obj.get("type") == "USER_INPUT":
                        last_user_text = obj.get("content", "")
            if last_user_text is not None and not SLASH_TRIGGER_PATTERN.search(str(last_user_text)):
                return (
                    "deny",
                    "Slash-Command-Only Policy Violation: Latest user input in conversation transcript does not contain "
                    "explicit '/agent-legion' or '/legion' slash command. Conversational auto-trigger is strictly blocked.",
                )
        except Exception:
            pass

    return "allow", ""


def check_command_line(cmd: str, repo_root_str: str) -> tuple[str, str]:
    for pattern, description in DENY_CMD_REGEX:
        if re.search(pattern, cmd):
            return "deny", f"Destructive command detected: {description}"

    try:
        tokens = shlex.split(cmd)
    except Exception:
        tokens = cmd.split()

    if not tokens:
        return "allow", ""

    main_cmd = os.path.basename(tokens[0]).lower()

    if main_cmd == "git":
        git_args = [t.lower() for t in tokens[1:]]
        if "reset" in git_args and "--hard" in git_args:
            return "deny", "Destructive git operation: git reset --hard is strictly denied."
        if "clean" in git_args:
            if "-n" in git_args or "--dry-run" in git_args:
                return "allow", ""
            if "-f" in git_args or "-fd" in git_args or "-fdx" in git_args or "-fx" in git_args:
                return "deny", "Destructive git operation: git clean with force (-f) is strictly denied."
        if "checkout" in git_args and "--" in git_args:
            return "deny", "Destructive git operation: git checkout -- can discard uncommitted user changes and is denied."
        if "commit" in git_args:
            return "force_ask", "Commit operation requires user review and approval."

    if main_cmd == "rm" or main_cmd == "remove-item":
        for token in tokens[1:]:
            if token.startswith("-"):
                continue
            normalized_target = normalize_path(token)
            if normalized_target in ["/", "c:/", "d:/"]:
                return "deny", "Attempted root filesystem deletion."
            if normalized_target == normalize_path(repo_root_str):
                return "deny", "Attempted deletion of the repository root directory."
            if ".git" in normalized_target.split("/"):
                return "deny", "Attempted deletion or modification of the .git system directory."

    if "supabase" in tokens and "db" in tokens and any(x in tokens for x in ["reset", "push"]):
        return "force_ask", "Database mutation (supabase db reset/push) requires user approval."

    for pattern, description in FORCE_ASK_CMD_REGEX:
        if re.search(pattern, cmd):
            return "force_ask", f"Production-impacting command: {description} requires explicit confirmation."

    return "allow", ""


def _extract_written_content(args: dict) -> str:
    parts = []
    for key in ("Content", "Replacement", "NewSource", "CodeContent", "ReplacementContent"):
        val = args.get(key)
        if isinstance(val, str) and val:
            parts.append(val)

    chunks = args.get("ReplacementChunks")
    if isinstance(chunks, list):
        for chunk in chunks:
            if isinstance(chunk, dict):
                for ckey in ("ReplacementContent", "Replacement", "Content"):
                    cval = chunk.get(ckey)
                    if isinstance(cval, str) and cval:
                        parts.append(cval)

    for list_key in ("Cells", "Edits"):
        items = args.get(list_key)
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    for ikey in ("NewSource", "Source", "Content", "Replacement"):
                        ival = item.get(ikey)
                        if isinstance(ival, str) and ival:
                            parts.append(ival)

    return "\n".join(parts)


def _is_within_prefix(normalized_target: str, prefix: str) -> bool:
    if not prefix:
        return False
    clean_prefix = prefix.rstrip("/")
    if not clean_prefix:
        return normalized_target.startswith("/")
    return normalized_target == clean_prefix or normalized_target.startswith(clean_prefix + "/")


def check_file_write(tool_name: str, args: dict, repo_root_str: str, allowed_prefixes: list) -> tuple[str, str]:
    target_file = (
        args.get("Path")
        or args.get("TargetFile")
        or args.get("AbsolutePath")
        or args.get("NotebookPath")
    )
    if not target_file:
        return "allow", ""

    target_path = Path(target_file)
    if not target_path.is_absolute():
        target_path = Path(repo_root_str) / target_path
    normalized_target = normalize_path(str(target_path))

    if ".git" in normalized_target.split("/"):
        return "deny", "Direct modification of .git internals is strictly denied."

    is_allowed_path = any(_is_within_prefix(normalized_target, prefix) for prefix in allowed_prefixes)
    if not is_allowed_path:
        return "deny", f"Workspace escape blocked. Path {target_file} is outside authorized directories."

    file_name = os.path.basename(normalized_target).lower()
    content = _extract_written_content(args)

    if file_name in [".env", "secrets", "credentials"]:
        if check_secret_in_content(content):
            return "deny", f"Writing literal secrets directly to {file_name} is strictly denied."
        return "force_ask", f"Writing/modifying sensitive file {file_name} requires explicit user approval."

    if not normalized_target.lower().endswith(".md"):
        reason = check_secret_in_content(content)
        if reason:
            return "deny", f"Literal secret detected in code content: {reason}."

    return "allow", ""


def build_allowed_prefixes(payload: dict, repo_root_str: str) -> list[str]:
    allowed_prefixes = [repo_root_str]

    workspace_paths = payload.get("workspacePaths", [])
    if isinstance(workspace_paths, list):
        for path in workspace_paths:
            if isinstance(path, str) and path.strip():
                allowed_prefixes.append(normalize_path(path))

    artifact_dir = payload.get("artifactDirectoryPath")
    if isinstance(artifact_dir, str) and artifact_dir.strip():
        allowed_prefixes.append(normalize_path(artifact_dir))

    conversation_id = payload.get("conversationId")
    if _is_safe_conversation_id(conversation_id):
        home_gemini = Path.home() / ".gemini"
        for variant in BRAIN_APP_VARIANTS:
            allowed_prefixes.append(
                normalize_path(str(home_gemini / variant / "brain" / conversation_id.strip()))
            )

    return allowed_prefixes


def main() -> int:
    try:
        payload = load_input()
    except Exception as e:
        respond_json({"decision": "force_ask", "reason": f"Harness internal parse error: {e}"})
        return 0

    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name")
    args = tool_call.get("args", {}) if isinstance(tool_call, dict) else {}
    if not isinstance(args, dict):
        args = {}

    repo_root = resolve_repo_root(payload)
    repo_root_str = normalize_path(str(repo_root))
    allowed_prefixes = build_allowed_prefixes(payload, repo_root_str)

    log_stderr(f"Evaluating tool call '{tool_name}'")

    try:
        if tool_name == "run_command":
            cmd = args.get("CommandLine", "")
            decision, reason = check_command_line(cmd, repo_root_str)
            respond_json({"decision": decision, "reason": reason})
        elif tool_name in FILE_WRITE_TOOLS:
            decision, reason = check_file_write(tool_name, args, repo_root_str, allowed_prefixes)
            respond_json({"decision": decision, "reason": reason})
        elif tool_name == "invoke_subagent":
            decision, reason = check_subagent_invocation(args, payload)
            respond_json({"decision": decision, "reason": reason})
        else:
            respond_json({"decision": "allow", "reason": ""})
    except Exception as exc:
        log_stderr(f"Error evaluating hook: {exc}")
        if tool_name in ({"run_command", "invoke_subagent"} | FILE_WRITE_TOOLS):
            respond_json({"decision": "deny", "reason": f"Harness check exception: {exc}."})
        else:
            respond_json({"decision": "force_ask", "reason": f"Harness check exception: {exc}."})

    return 0


if __name__ == "__main__":
    main()
