#!/usr/bin/env python3
import sys
import os
import json
import subprocess
from pathlib import Path
from common import load_input, respond_json, log_stderr, find_repo_root

MAX_ATTEMPTS = 2
BYPASS_TERMINATION_REASONS = {"USER_CANCELED", "ERROR", "TERMINAL_CUSTOM_HOOK"}


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


def get_state_file(root: Path) -> Path:
    return root / ".agents" / "state" / "stop_gate_state.json"


def get_git_status_porcelain(root: Path) -> list:
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return [line.strip() for line in out.splitlines() if line.strip()]
    except Exception:
        return []


def run_git_diff_check(root: Path) -> bool:
    try:
        res1 = subprocess.run(["git", "diff", "--check"], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        res2 = subprocess.run(["git", "diff", "--cached", "--check"], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res1.returncode != 0 or res2.returncode != 0:
            log_stderr(f"Git diff check failed: {res1.stderr.decode(errors='replace')} {res2.stderr.decode(errors='replace')}")
            return False
        return True
    except Exception as e:
        log_stderr(f"Failed to run git diff --check: {e}")
        return True


def run_harness_validator(root: Path) -> bool:
    try:
        res = subprocess.run(
            [sys.executable, "scripts/harness/validate_harness.py", "--strict"],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if res.returncode != 0:
            log_stderr(f"validate_harness.py failed:\n{res.stderr}")
            return False
        return True
    except Exception as e:
        log_stderr(f"Failed to run validate_harness.py: {e}")
        return False


def load_stop_state(state_file: Path) -> dict:
    if state_file.is_file():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"attempt": 0}


def save_stop_state(state_file: Path, state: dict) -> None:
    try:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception as e:
        log_stderr(f"Failed to save stop gate state: {e}")


def main() -> int:
    try:
        payload = load_input()
    except Exception as e:
        log_stderr(f"Stop Hook input parse exception: {e}")
        respond_json({"decision": "allow", "status": "failed", "reason": f"Input parse error: {e}"})
        return 0

    root = resolve_repo_root(payload)
    state_file = get_state_file(root)

    termination_reason = payload.get("terminationReason")
    if termination_reason in BYPASS_TERMINATION_REASONS:
        log_stderr(f"Bypassing stop gate due to terminationReason={termination_reason}")
        if state_file.is_file():
            save_stop_state(state_file, {"attempt": 0})
        respond_json({
            "decision": "allow",
            "status": "passed",
            "reason": f"Stop gate bypassed due to terminationReason={termination_reason}.",
        })
        return 0

    continuation_active = payload.get("continuationActive") is True

    # 1. Check if workspace has meaningful modifications
    status_lines = get_git_status_porcelain(root)
    code_modified = False
    meaningful_work = False
    memory_synced = False

    for line in status_lines:
        parts = line.split(None, 1)
        if len(parts) < 2:
            continue
        path_str = parts[1].strip()
        p_lower = path_str.replace("\\", "/").lower()

        if p_lower in [
            ".agents/state/stop_gate_state.json",
            ".terkirdo_pre_cache.md",
            ".agents/skills/self-evolution/scripts/index/skills_meta.json",
        ] or p_lower.startswith(".agents/state/legion_radio.db"):
            continue

        if p_lower in ["memory.md", "docs/terukirdo_trajectory.txt"]:
            memory_synced = True
            continue

        meaningful_work = True

        # Harness files prefixes
        is_harness = any(p_lower.startswith(pref) for pref in [
            ".agents/", "scripts/", "tests/", "docs/", "agents/", "reference/",
            "terukirdo_protocol_", "agents.md", "readme.md", "테르키르도.zip", ".gitignore"
        ])
        if not is_harness and not path_str.endswith(".md"):
            code_modified = True

    if not meaningful_work and not memory_synced:
        log_stderr("No files modified. Tier 0/1 chat/query bypass active.")
        respond_json({"decision": "allow", "status": "passed", "reason": "No modifications detected."})
        return 0

    # 2. Track attempts to prevent infinite loop
    state = load_stop_state(state_file)
    state["attempt"] = int(state.get("attempt", 0)) + 1
    save_stop_state(state_file, state)

    log_stderr(f"Evaluating Stop Gate (Attempt {state['attempt']}/{MAX_ATTEMPTS}, continuationActive={continuation_active})")

    failures = []

    # Check 1: validate_harness.py
    if not run_harness_validator(root):
        failures.append("Harness structural validation failed (validate_harness.py)")

    # Check 2: Git diff --check
    if not run_git_diff_check(root):
        failures.append("Git diff whitespace or conflict checks failed (git diff --check)")

    # Check 3: Deterministic Memory Sync
    if meaningful_work and not memory_synced:
        failures.append("Turn-End Memory Sync required: You have modified files but didn't update MEMORY.md or docs/Terukirdo_Trajectory.txt.")

    if failures:
        reason = "; ".join(failures)
        if continuation_active:
            log_stderr(f"Continuation already active; allowing stop to prevent loop: {reason}")
            save_stop_state(state_file, {"attempt": 0})
            respond_json({
                "decision": "allow",
                "status": "blocked",
                "reason": f"Gate blocked while continuationActive=true: {reason}",
            })
        elif state["attempt"] >= MAX_ATTEMPTS:
            log_stderr(f"Max attempts exceeded. Stop Hook BLOCKED: {reason}")
            save_stop_state(state_file, {"attempt": 0})
            respond_json({
                "decision": "allow",
                "status": "blocked",
                "reason": f"Gate blocked after repeated failure: {reason}",
            })
        else:
            log_stderr(f"Stop Hook CONTINUE requested: {reason}")
            respond_json({
                "decision": "continue",
                "status": "continue",
                "reason": f"Quality gate checks failed. Please resolve: {reason}",
            })
    else:
        log_stderr("Stop Hook PASSED.")
        save_stop_state(state_file, {"attempt": 0})
        respond_json({
            "decision": "allow",
            "status": "passed",
            "reason": "All checks passed successfully.",
        })

    return 0


if __name__ == "__main__":
    main()
