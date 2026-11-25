#!/usr/bin/env python3
"""
Hermes External Guest AI Bridge (Read-Only Zero-Tool Sandbox)

Bridges external frontier models (DeepSeek V4.1 Flash, Qwen 4 Max, GPT-6-Sol)
via Hermes CLI (`hermes chat -Q --ignore-rules -t "" --source tool --max-turns 1`)
for 8-Seat Grand Council debates in UltimateMake / multi-agent-conference.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

GUEST_SEATS = {
    "deepseek": {
        "provider": "alibaba-coding-plan",
        "model": "deepseek-v4.1-flash",
        "swarm_name": "guest-deepseek",
        "role": "Algorithmic Efficiency, Edge-Case & High-Density Systems Challenger",
    },
    "qwen": {
        "provider": "alibaba-coding-plan",
        "model": "qwen4-max",
        "swarm_name": "guest-qwen",
        "role": "Distributed Data, State Consistency & Enterprise Architecture Critic",
    },
    "gpt": {
        "provider": "openai-codex",
        "model": "gpt-6-sol",
        "swarm_name": "guest-gpt",
        "role": "Reproducibility-Driven Adversarial Red-Team & Non-Atomicity Auditor",
    },
}

DEFAULT_REASONING = "medium"
DEFAULT_RUN_BUDGET = 180
VALID_REASONING_LEVELS = ("none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra")
DEFAULT_SESSION_STORE_DIR = Path(tempfile.gettempdir()) / "terukirdo_hermes_guest_sessions"

# Strip CSI and OSC ANSI escape sequences without altering UTF-8 text.
ANSI_CSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
ANSI_OSC_RE = re.compile(r"\x1B\][^\x07\x1B]*(?:\x07|\x1B\\)")
SESSION_ID_RE = re.compile(r"session_id:\s*(\S+)")


def resolve_seat(
    seat: str | None,
    provider: str | None = None,
    model: str | None = None,
) -> tuple[str, str, str]:
    """Resolve (seat_label, provider, model) from a preset seat or explicit pair."""
    clean_provider = provider.strip() if isinstance(provider, str) else ""
    clean_model = model.strip() if isinstance(model, str) else ""

    if seat is not None and seat.strip():
        norm_seat = seat.strip().lower()
        if norm_seat not in GUEST_SEATS:
            raise ValueError(
                f"Unknown guest seat '{seat}'. Valid seats: {', '.join(sorted(GUEST_SEATS.keys()))}"
            )
        preset = GUEST_SEATS[norm_seat]
        resolved_provider = clean_provider or preset["provider"]
        resolved_model = clean_model or preset["model"]
        return norm_seat, resolved_provider, resolved_model

    if not clean_provider or not clean_model:
        raise ValueError("Either --seat or both --provider and --model must be provided.")

    return f"{clean_provider}/{clean_model}", clean_provider, clean_model


def strip_ansi(text: str) -> str:
    """Remove ANSI CSI and OSC escape sequences from text."""
    if not text:
        return ""
    cleaned = ANSI_OSC_RE.sub("", text)
    cleaned = ANSI_CSI_RE.sub("", cleaned)
    return cleaned


def _session_record_path(session_name: str, store_dir: Path) -> Path:
    """Return the per-thread session mapping file path outside the repository."""
    digest = hashlib.sha256(session_name.encode("utf-8")).hexdigest()
    return store_dir / f"{digest}.json"


def load_session_id(
    session_name: str,
    provider: str,
    model: str,
    store_dir: Path = DEFAULT_SESSION_STORE_DIR,
) -> str | None:
    """Load a persisted Hermes session_id only if provider and model match."""
    record_path = _session_record_path(session_name, store_dir)
    if not record_path.is_file():
        return None
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(record, dict):
        return None
    if record.get("provider") != provider or record.get("model") != model:
        return None
    sid = record.get("session_id")
    return sid.strip() if isinstance(sid, str) and sid.strip() else None


def save_session_id(
    session_name: str,
    seat_label: str,
    provider: str,
    model: str,
    session_id: str,
    store_dir: Path = DEFAULT_SESSION_STORE_DIR,
) -> None:
    """Atomically persist a named thread's Hermes session_id to store_dir."""
    store_dir.mkdir(parents=True, exist_ok=True)
    record_path = _session_record_path(session_name, store_dir)
    payload = {
        "session": session_name,
        "seat": seat_label,
        "provider": provider,
        "model": model,
        "session_id": session_id,
    }
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(store_dir),
            delete=False,
            suffix=".tmp",
        ) as tf:
            json.dump(payload, tf, indent=2, ensure_ascii=False)
            tmp_path = tf.name
        os.replace(tmp_path, record_path)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def build_hermes_cmd(
    query_file: str,
    provider: str,
    model: str,
    resume_session_id: str | None = None,
    reasoning: str = DEFAULT_REASONING,
    run_budget: int = DEFAULT_RUN_BUDGET,
    profile: str | None = None,
    hermes_bin: str = "hermes",
) -> list[str]:
    """Build the Hermes CLI invocation for fresh Round 1 create or Round 2~3 resume."""
    cmd: list[str] = [hermes_bin]
    if profile and profile.strip():
        cmd.extend(["-p", profile.strip()])

    if resume_session_id and resume_session_id.strip():
        cmd.extend([
            "chat",
            "--query-file",
            query_file,
            "-Q",
            "--resume",
            resume_session_id.strip(),
            "--no-restore-cwd",
        ])
        return cmd

    cmd.extend([
        "chat",
        "--query-file",
        query_file,
        "-Q",
        "--ignore-rules",
        "-t",
        "",
        "--source",
        "tool",
        "--max-turns",
        "1",
        "--run-budget",
        str(run_budget),
        "--provider",
        provider,
        "-m",
        model,
    ])

    if reasoning and reasoning.strip():
        cmd.extend(["--reasoning", reasoning.strip()])

    return cmd


def _extract_session_line(stderr_text: str) -> str:
    """Extract the session_id line from Hermes stderr if present."""
    if not stderr_text:
        return ""
    for line in strip_ansi(stderr_text).splitlines():
        if "session_id:" in line:
            return line.strip()
    return ""


def _summarize_error(stderr_text: str, stdout_text: str) -> str:
    """Extract a concise, secret-free single-line diagnostic summary."""
    combined = strip_ansi(stderr_text or "") + "\n" + strip_ansi(stdout_text or "")
    for line in combined.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:240]
    return "No diagnostic output returned."


def run_guest_query(
    seat_label: str,
    provider: str,
    model: str,
    prompt_text: str,
    session: str | None = None,
    resume_session_id: str | None = None,
    session_store_dir: Path | None = None,
    reasoning: str = DEFAULT_REASONING,
    run_budget: int = DEFAULT_RUN_BUDGET,
    profile: str | None = None,
    hermes_bin: str = "hermes",
    emit_session_id: bool = False,
) -> tuple[int, str, str]:
    """Execute a Read-Only guest AI query via Hermes CLI with guaranteed temp cleanup."""
    hermes_path = shutil.which(hermes_bin)
    if not hermes_path:
        return (
            2,
            "",
            f"[HERMES_GUEST_UNAVAILABLE: {seat_label}] Hermes CLI ('{hermes_bin}') not found on PATH.\n",
        )

    store_dir = session_store_dir or DEFAULT_SESSION_STORE_DIR
    clean_session = session.strip() if isinstance(session, str) and session.strip() else None
    target_resume_id = (
        resume_session_id.strip()
        if isinstance(resume_session_id, str) and resume_session_id.strip()
        else (load_session_id(clean_session, provider, model, store_dir) if clean_session else None)
    )

    temp_file: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            suffix=".txt",
        ) as tf:
            tf.write(prompt_text)
            temp_file = tf.name

        cmd = build_hermes_cmd(
            query_file=temp_file,
            provider=provider,
            model=model,
            resume_session_id=target_resume_id,
            reasoning=reasoning,
            run_budget=run_budget,
            profile=profile,
            hermes_bin=hermes_path,
        )

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=run_budget + 30,
        )
    except subprocess.TimeoutExpired:
        return (
            2,
            "",
            f"[HERMES_GUEST_UNAVAILABLE: {seat_label}] Hermes CLI timed out after {run_budget + 30}s.\n",
        )
    except OSError as exc:
        return (
            2,
            "",
            f"[HERMES_GUEST_UNAVAILABLE: {seat_label}] OS error invoking Hermes CLI: {exc}\n",
        )
    finally:
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except OSError:
                pass

    cleaned_stdout = strip_ansi(proc.stdout or "")
    cleaned_stderr = strip_ansi(proc.stderr or "")
    failure_markers = ("API call failed", "Connection error", "invalid_params")

    has_failure_marker = any(
        marker in cleaned_stderr or marker in cleaned_stdout for marker in failure_markers
    )
    if proc.returncode != 0 or (has_failure_marker and not cleaned_stdout.strip()):
        detail = _summarize_error(cleaned_stderr, cleaned_stdout)
        return (
            2,
            "",
            f"[HERMES_GUEST_UNAVAILABLE: {seat_label}] Hermes CLI exited with code {proc.returncode}: {detail}\n",
        )

    if has_failure_marker:
        detail = _summarize_error(cleaned_stderr, cleaned_stdout)
        return (
            2,
            "",
            f"[HERMES_GUEST_UNAVAILABLE: {seat_label}] Hermes CLI reported failure: {detail}\n",
        )

    sid_match = SESSION_ID_RE.search(cleaned_stderr)
    parsed_sid = sid_match.group(1).strip() if sid_match else ""
    if clean_session and parsed_sid and parsed_sid != target_resume_id:
        save_session_id(clean_session, seat_label, provider, model, parsed_sid, store_dir)

    session_line = _extract_session_line(cleaned_stderr) if emit_session_id else ""
    return (0, cleaned_stdout, session_line)


def _configure_utf8_streams() -> None:
    """Reconfigure stdout and stderr to UTF-8 with replacement on encoding errors."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def _read_prompt(args: argparse.Namespace) -> str:
    """Load prompt text from --prompt, --prompt-file, or stdin."""
    if args.prompt is not None:
        return args.prompt

    if args.prompt_file is not None:
        if args.prompt_file == "-":
            return sys.stdin.read()
        return Path(args.prompt_file).read_text(encoding="utf-8")

    if not sys.stdin.isatty():
        return sys.stdin.read()

    raise ValueError("No prompt provided. Use --prompt, --prompt-file, or pipe via stdin.")


def build_arg_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Bridge external frontier guest models via Hermes CLI in a zero-tool Read-Only sandbox."
    )
    parser.add_argument(
        "--seat",
        choices=sorted(GUEST_SEATS.keys()),
        help="Preset guest seat identifier.",
    )
    parser.add_argument("--provider", help="Override or specify Hermes provider.")
    parser.add_argument("--model", help="Override or specify Hermes model slug.")
    parser.add_argument("--profile", help="Optional Hermes profile (-p).")

    prompt_group = parser.add_mutually_exclusive_group()
    prompt_group.add_argument("--prompt", help="Inline prompt text.")
    prompt_group.add_argument(
        "--prompt-file",
        help="Path to UTF-8 prompt file (or '-' to read from stdin).",
    )

    session_group = parser.add_mutually_exclusive_group()
    session_group.add_argument(
        "--session",
        help="Named thread identifier mapped to a Hermes session_id for multi-round continuity.",
    )
    session_group.add_argument(
        "--resume",
        help="Explicit Hermes session_id to resume without creation override flags.",
    )
    parser.add_argument(
        "--reasoning",
        default=DEFAULT_REASONING,
        choices=VALID_REASONING_LEVELS,
        help=f"Reasoning effort level (default: {DEFAULT_REASONING}).",
    )
    parser.add_argument(
        "--run-budget",
        type=int,
        default=DEFAULT_RUN_BUDGET,
        help=f"Hermes run budget in seconds (minimum 10, default: {DEFAULT_RUN_BUDGET}).",
    )
    parser.add_argument(
        "--emit-session-id",
        action="store_true",
        help="Emit extracted session_id line to stderr on success.",
    )
    parser.add_argument(
        "--list-seats",
        action="store_true",
        help="Print preset GUEST_SEATS JSON and exit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    _configure_utf8_streams()
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.list_seats:
        sys.stdout.write(json.dumps(GUEST_SEATS, indent=2, ensure_ascii=False) + "\n")
        return 0

    if args.run_budget < 10:
        parser.error("--run-budget must be >= 10")

    try:
        seat_label, provider, model = resolve_seat(args.seat, args.provider, args.model)
        prompt_text = _read_prompt(args)
    except (ValueError, OSError) as exc:
        sys.stderr.write(f"[ERROR] {exc}\n")
        return 1

    if not prompt_text.strip():
        sys.stderr.write("[ERROR] Prompt text is empty.\n")
        return 1

    exit_code, stdout_text, extra = run_guest_query(
        seat_label=seat_label,
        provider=provider,
        model=model,
        prompt_text=prompt_text,
        session=args.session,
        resume_session_id=args.resume,
        reasoning=args.reasoning,
        run_budget=args.run_budget,
        profile=args.profile,
        emit_session_id=args.emit_session_id,
    )

    if exit_code != 0:
        sys.stderr.write(extra)
        return exit_code

    if stdout_text:
        sys.stdout.write(stdout_text)
        if not stdout_text.endswith("\n"):
            sys.stdout.write("\n")

    if extra:
        sys.stderr.write(extra + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
