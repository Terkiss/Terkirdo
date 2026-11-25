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
SWARM_SLASH_PATTERN = re.compile(r"(?:^|\s|\[|\"|\'|>)(/swarm)(?=$|\s|\]|\"|\'|:|<|,|\.|!|\?)")
ULTIMATE_MAKE_SLASH_PATTERN = re.compile(r"(?:^|\s|\[|\"|\'|>)(/ultimate-make)(?=$|\s|\]|\"|\'|:|<|,|\.|!|\?)")
ULTIMATE_MAKE_USER_PATTERN = re.compile(
    r"(?i)(?:(?<![a-z0-9_./-])/ultimate-make(?![a-z0-9_./-])|(?<![a-z0-9_./-])ultimate[\s_-]?make(?![a-z0-9_./-])|얼티밋\s*메이크)"
)

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


def _record_is_swarm_call(obj: dict, stripped: str) -> bool:
    if (
        '"name":"swarm"' in stripped
        or '"name": "swarm"' in stripped
        or obj.get("name") == "swarm"
        or obj.get("toolName") == "swarm"
        or (isinstance(obj.get("toolCall"), dict) and obj["toolCall"].get("name") == "swarm")
    ):
        return True
    tool_calls = obj.get("tool_calls")
    if isinstance(tool_calls, list):
        for tc in tool_calls:
            if isinstance(tc, dict) and tc.get("name") == "swarm":
                return True
    return False


def _record_executes_spec_lock(obj: dict, norm_line: str) -> bool:
    if "validate_spec_lock.py" not in norm_line:
        return False
    if "ultimate-make/skill.md" in norm_line:
        return False
    rec_type = str(obj.get("type", "")).upper()
    content_str = str(obj.get("content", ""))
    if rec_type == "GENERIC" and (
        "Showing lines " in content_str or "Partial read (lines " in content_str
    ):
        return False
    if rec_type == "PLANNER_RESPONSE":
        tool_calls = obj.get("tool_calls")
        if not isinstance(tool_calls, list):
            return False
        for tc in tool_calls:
            if isinstance(tc, dict) and tc.get("name") == "run_command":
                tc_norm = re.sub(r"[\\/]+", "/", json.dumps(tc, ensure_ascii=False)).lower()
                if "validate_spec_lock.py" in tc_norm:
                    return True
        return False
    tool_name = str(
        obj.get("name")
        or obj.get("toolName")
        or (obj.get("toolCall", {}).get("name") if isinstance(obj.get("toolCall"), dict) else "")
        or ""
    ).lower()
    if tool_name in {"read_file", "view_file", "update_steps"}:
        return False
    return True


def _parse_transcript_signals(transcript_path: Path) -> dict:
    user_inputs: list[str] = []
    ultimate_make_skill_loaded = False
    had_prior_swarm_call = False
    um_window_open = False
    swarm_window_open = False
    swarm_called_in_window = False
    any_um_user_trigger = False
    any_swarm_slash_trigger = False

    try:
        with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
            for raw_line in f:
                stripped = raw_line.strip()
                if not stripped:
                    continue
                try:
                    obj = json.loads(stripped)
                except (json.JSONDecodeError, TypeError, ValueError):
                    continue
                if not isinstance(obj, dict):
                    continue

                if obj.get("type") == "USER_INPUT":
                    content = str(obj.get("content", ""))
                    user_inputs.append(content)
                    if ULTIMATE_MAKE_USER_PATTERN.search(content):
                        um_window_open = True
                        any_um_user_trigger = True
                    if SWARM_SLASH_PATTERN.search(content):
                        swarm_window_open = True
                        swarm_called_in_window = False
                        any_swarm_slash_trigger = True
                    elif swarm_window_open and not swarm_called_in_window:
                        swarm_window_open = False
                else:
                    norm_line = re.sub(r"[\\/]+", "/", stripped).lower()
                    if "ultimate-make/skill.md" in norm_line:
                        ultimate_make_skill_loaded = True
                    if _record_is_swarm_call(obj, stripped):
                        had_prior_swarm_call = True
                        if swarm_window_open:
                            swarm_called_in_window = True
                    if _record_executes_spec_lock(obj, norm_line):
                        um_window_open = False
    except OSError:
        pass

    return {
        "user_inputs": user_inputs,
        "ultimate_make_skill_loaded": ultimate_make_skill_loaded,
        "had_prior_swarm_call": had_prior_swarm_call,
        "um_window_open": um_window_open,
        "swarm_window_open": swarm_window_open,
        "swarm_called_in_window": swarm_called_in_window,
        "any_um_user_trigger": any_um_user_trigger,
        "any_swarm_slash_trigger": any_swarm_slash_trigger,
    }


def check_run_workflow_invocation(args: dict, payload: dict) -> tuple[str, str]:
    return (
        "deny",
        "Strictly Prohibited Tool: 'run_workflow' is permanently disabled and blocked by Terukirdo Protocol v5.8 safety policy.",
    )


def check_swarm_invocation(args: dict, payload: dict) -> tuple[str, str]:
    raw_last_input = payload.get("lastUserInput")
    has_last_input = isinstance(raw_last_input, str) and bool(raw_last_input.strip())
    last_user_input = raw_last_input if has_last_input else ""

    transcript_path = _resolve_transcript_path(payload)
    if transcript_path is not None and transcript_path.is_file():
        signals = _parse_transcript_signals(transcript_path)
    else:
        signals = {
            "user_inputs": [],
            "ultimate_make_skill_loaded": False,
            "had_prior_swarm_call": False,
            "um_window_open": False,
            "swarm_window_open": False,
            "swarm_called_in_window": False,
            "any_um_user_trigger": False,
            "any_swarm_slash_trigger": False,
        }

    user_inputs = signals["user_inputs"]
    ultimate_make_skill_loaded = signals["ultimate_make_skill_loaded"]
    had_prior_swarm_call = signals["had_prior_swarm_call"]
    um_window_open = signals["um_window_open"]
    swarm_window_open = signals["swarm_window_open"]
    swarm_called_in_window = signals["swarm_called_in_window"]
    any_um_user_trigger = signals["any_um_user_trigger"]
    any_swarm_slash_trigger = signals["any_swarm_slash_trigger"]

    if has_last_input:
        if SWARM_SLASH_PATTERN.search(last_user_input):
            swarm_window_open = True
            any_swarm_slash_trigger = True
        elif (not user_inputs or last_user_input != user_inputs[-1]) and swarm_window_open and not swarm_called_in_window:
            swarm_window_open = False
        if ULTIMATE_MAKE_USER_PATTERN.search(last_user_input):
            any_um_user_trigger = True

    current_turn_is_swarm_slash = (
        bool(SWARM_SLASH_PATTERN.search(last_user_input))
        if has_last_input
        else (bool(user_inputs) and bool(SWARM_SLASH_PATTERN.search(user_inputs[-1])))
    )
    if current_turn_is_swarm_slash:
        return "allow", ""

    active_multi_turn_swarm = swarm_window_open and had_prior_swarm_call
    if active_multi_turn_swarm:
        return "allow", ""

    has_um_user_trigger = (
        (has_last_input and bool(ULTIMATE_MAKE_USER_PATTERN.search(last_user_input)))
        or um_window_open
    )
    current_turn_is_um_slash = (
        bool(ULTIMATE_MAKE_SLASH_PATTERN.search(last_user_input))
        if has_last_input
        else (bool(user_inputs) and bool(ULTIMATE_MAKE_SLASH_PATTERN.search(user_inputs[-1])))
    )
    has_um_skill_anchor = current_turn_is_um_slash or ultimate_make_skill_loaded

    if has_um_user_trigger and has_um_skill_anchor:
        return "allow", ""

    action = str(args.get("action", "")).strip().lower()
    if action in {"kill", "status"} and had_prior_swarm_call and (
        any_swarm_slash_trigger or any_um_user_trigger
    ):
        return "allow", ""

    return (
        "deny",
        "Swarm Policy Violation: 'swarm' is strictly restricted to explicit '/swarm' slash commands "
        "or active 'UltimateMake' sessions (with UltimateMake user trigger and ultimate-make/SKILL.md loaded).",
    )


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
        signals = _parse_transcript_signals(transcript_path)
        user_inputs = signals["user_inputs"]
        if user_inputs and not SLASH_TRIGGER_PATTERN.search(user_inputs[-1]):
            return (
                "deny",
                "Slash-Command-Only Policy Violation: Latest user input in conversation transcript does not contain "
                "explicit '/agent-legion' or '/legion' slash command. Conversational auto-trigger is strictly blocked.",
            )

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


def _clean_resolved_path(path_obj: Path) -> str:
    try:
        resolved = str(path_obj.resolve(strict=False))
    except Exception:
        resolved = os.path.abspath(str(path_obj))
    if resolved.startswith("\\\\?\\UNC\\"):
        resolved = "\\\\" + resolved[8:]
    elif resolved.startswith("\\\\?\\"):
        resolved = resolved[4:]
    return normalize_path(resolved)


def _is_unc_or_device_path(raw_path: str) -> bool:
    s = raw_path.strip()
    if s.startswith(("\\\\?\\", "\\\\.\\", "\\??\\", "//?/", "//./", "/??/")):
        return True
    if s.startswith("\\\\") or s.startswith("//"):
        return True
    return False


def _extract_workspace_path_str(entry: object) -> str:
    raw = ""
    if isinstance(entry, str):
        raw = entry.strip()
    elif isinstance(entry, dict):
        val = entry.get("path") or entry.get("uri") or ""
        if isinstance(val, str):
            raw = val.strip()
    if not raw:
        return ""
    if raw.lower().startswith("file:///"):
        stripped = raw[8:]
        if len(stripped) >= 2 and stripped[1] == ":":
            raw = stripped
        else:
            raw = "/" + stripped
    elif raw.lower().startswith("file://"):
        raw = raw[7:]
    return raw.strip()


def _append_unique_prefix(prefixes: list[str], candidate: str) -> None:
    if not candidate:
        return
    cmp_val = candidate.lower() if os.name == "nt" else candidate
    existing = {p.lower() if os.name == "nt" else p for p in prefixes}
    if cmp_val not in existing:
        prefixes.append(candidate)


def _is_within_prefix(normalized_target: str, prefix: str) -> bool:
    if not prefix:
        return False
    target_cmp = normalized_target.lower() if os.name == "nt" else normalized_target
    clean_prefix = (prefix.lower() if os.name == "nt" else prefix).rstrip("/")
    if not clean_prefix:
        return target_cmp.startswith("/")
    return target_cmp == clean_prefix or target_cmp.startswith(clean_prefix + "/")


def check_file_write(
    tool_name: str,
    args: dict,
    repo_root_str: str,
    allowed_prefixes: list,
    payload: dict | None = None,
) -> tuple[str, str]:
    target_file = (
        args.get("Path")
        or args.get("TargetFile")
        or args.get("AbsolutePath")
        or args.get("NotebookPath")
        or args.get("path")
        or args.get("file_path")
        or args.get("target_file")
    )
    if not isinstance(target_file, str) or not target_file.strip():
        return "allow", ""

    raw_target = target_file.strip()

    if _is_unc_or_device_path(raw_target):
        explicit_unc_prefixes: list[str] = []
        if isinstance(payload, dict) and isinstance(payload.get("workspacePaths"), list):
            for entry in payload["workspacePaths"]:
                wp_str = _extract_workspace_path_str(entry)
                if wp_str and _is_unc_or_device_path(wp_str):
                    explicit_unc_prefixes.append(normalize_path(wp_str))
        norm_unc = normalize_path(raw_target)
        if not explicit_unc_prefixes or not any(
            _is_within_prefix(norm_unc, up) for up in explicit_unc_prefixes
        ):
            return "deny", f"UNC or NT device path blocked. Path {target_file} is outside authorized workspace paths."

    target_path = Path(raw_target)
    if not target_path.is_absolute():
        base_dir = Path(repo_root_str)
        if isinstance(payload, dict):
            cwd_val = payload.get("cwd")
            if isinstance(cwd_val, str) and cwd_val.strip():
                norm_cwd = normalize_path(os.path.abspath(cwd_val.strip()))
                if any(_is_within_prefix(norm_cwd, prefix) for prefix in allowed_prefixes):
                    base_dir = Path(cwd_val.strip())
            elif not any(_is_within_prefix(normalize_path(repo_root_str), prefix) for prefix in allowed_prefixes):
                ws_list = payload.get("workspacePaths", [])
                if isinstance(ws_list, list):
                    for entry in ws_list:
                        wp_str = _extract_workspace_path_str(entry)
                        if wp_str:
                            base_dir = Path(wp_str)
                            break
        target_path = base_dir / target_path

    if _is_unc_or_device_path(raw_target):
        lexical_target = normalize_path(raw_target)
    else:
        lexical_target = normalize_path(os.path.abspath(str(target_path)))
    resolved_target = _clean_resolved_path(target_path)

    if ".git" in [seg.lower() for seg in lexical_target.split("/")] or ".git" in [
        seg.lower() for seg in resolved_target.split("/")
    ]:
        return "deny", "Direct modification of .git internals is strictly denied."

    is_lexical_allowed = any(_is_within_prefix(lexical_target, prefix) for prefix in allowed_prefixes)
    is_resolved_allowed = any(_is_within_prefix(resolved_target, prefix) for prefix in allowed_prefixes)
    if not (is_lexical_allowed and is_resolved_allowed):
        return "deny", f"Workspace escape blocked. Path {target_file} is outside authorized directories."

    file_name = os.path.basename(lexical_target).lower()
    content = _extract_written_content(args)

    if file_name in [".env", "secrets", "credentials"]:
        if check_secret_in_content(content):
            return "deny", f"Writing literal secrets directly to {file_name} is strictly denied."
        return "force_ask", f"Writing/modifying sensitive file {file_name} requires explicit user approval."

    if not lexical_target.lower().endswith(".md"):
        reason = check_secret_in_content(content)
        if reason:
            return "deny", f"Literal secret detected in code content: {reason}."

    return "allow", ""


def build_allowed_prefixes(payload: dict, repo_root_str: str) -> list[str]:
    allowed_prefixes: list[str] = []
    ws_prefixes: list[str] = []

    workspace_paths = payload.get("workspacePaths", [])
    if isinstance(workspace_paths, list):
        for entry in workspace_paths:
            wp_str = _extract_workspace_path_str(entry)
            if wp_str:
                if _is_unc_or_device_path(wp_str):
                    _append_unique_prefix(ws_prefixes, normalize_path(wp_str))
                else:
                    _append_unique_prefix(ws_prefixes, normalize_path(os.path.abspath(wp_str)))
                _append_unique_prefix(ws_prefixes, _clean_resolved_path(Path(wp_str)))

    norm_repo_root = normalize_path(repo_root_str)
    resolved_repo_root = _clean_resolved_path(Path(repo_root_str))

    if not ws_prefixes:
        _append_unique_prefix(allowed_prefixes, norm_repo_root)
        _append_unique_prefix(allowed_prefixes, resolved_repo_root)
    else:
        for wp in ws_prefixes:
            _append_unique_prefix(allowed_prefixes, wp)
        if any(
            _is_within_prefix(norm_repo_root, wp) or _is_within_prefix(resolved_repo_root, wp)
            for wp in ws_prefixes
        ):
            _append_unique_prefix(allowed_prefixes, norm_repo_root)
            _append_unique_prefix(allowed_prefixes, resolved_repo_root)

    artifact_dir = payload.get("artifactDirectoryPath")
    if isinstance(artifact_dir, str) and artifact_dir.strip():
        _append_unique_prefix(allowed_prefixes, normalize_path(os.path.abspath(artifact_dir.strip())))
        _append_unique_prefix(allowed_prefixes, _clean_resolved_path(Path(artifact_dir.strip())))

    conversation_id = payload.get("conversationId")
    if _is_safe_conversation_id(conversation_id):
        home_gemini = Path.home() / ".gemini"
        for variant in BRAIN_APP_VARIANTS:
            brain_dir = home_gemini / variant / "brain" / conversation_id.strip()
            _append_unique_prefix(allowed_prefixes, normalize_path(str(brain_dir)))
            _append_unique_prefix(allowed_prefixes, _clean_resolved_path(brain_dir))

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
        if tool_name == "run_workflow":
            decision, reason = check_run_workflow_invocation(args, payload)
            respond_json({"decision": decision, "reason": reason})
        elif tool_name == "swarm":
            decision, reason = check_swarm_invocation(args, payload)
            respond_json({"decision": decision, "reason": reason})
        elif tool_name == "run_command":
            cmd = args.get("CommandLine", "")
            decision, reason = check_command_line(cmd, repo_root_str)
            respond_json({"decision": decision, "reason": reason})
        elif tool_name in FILE_WRITE_TOOLS:
            decision, reason = check_file_write(tool_name, args, repo_root_str, allowed_prefixes, payload=payload)
            respond_json({"decision": decision, "reason": reason})
        elif tool_name == "invoke_subagent":
            decision, reason = check_subagent_invocation(args, payload)
            respond_json({"decision": decision, "reason": reason})
        else:
            respond_json({"decision": "allow", "reason": ""})
    except Exception as exc:
        log_stderr(f"Error evaluating hook: {exc}")
        if tool_name in ({"run_command", "invoke_subagent", "run_workflow", "swarm"} | FILE_WRITE_TOOLS):
            respond_json({"decision": "deny", "reason": f"Harness check exception: {exc}."})
        else:
            respond_json({"decision": "force_ask", "reason": f"Harness check exception: {exc}."})

    return 0


if __name__ == "__main__":
    main()
