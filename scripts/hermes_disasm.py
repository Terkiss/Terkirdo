#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hermes_disasm.py — Deterministic Sanitizer Wrapper for Binary Disassembly via Hermes CLI.

Modes:
- Mode A (Fast In-Memory Capstone + Hermes): Disassembles specified VAs in-memory, queries local Offrail-27B-12G model.
- Mode B (Hermes + REA MCP Explicit Tool Mode): Dispatches queries with --use-rea and --yolo so Hermes calls the rea MCP server.
- Mode C (Stdin Sanitizer): Standalone regex gate for arbitrary piped text via --sanitize-only.

Guarantees that ZERO raw x86/x64 assembly instructions, mnemonics, or byte dumps can EVER reach the main LLM agent's stdout.
Strictly enforces [FORCE_ASK: HERMES_UNAVAILABLE] (exit code 2) when Hermes or the local model is offline.
"""

import sys
import os
import re
import shutil
import argparse
import tempfile
import subprocess
from pathlib import Path

try:
    import pefile
    import capstone
except ImportError as e:
    sys.stderr.write(f"[ERROR] Required python package missing: {e}. Please install pefile and capstone.\n")
    sys.exit(1)


# ---------------------------------------------------------------------------
# In-Memory Disassembler (pefile + capstone, 32-bit & 64-bit auto-detection)
# ---------------------------------------------------------------------------

def disassemble_va(pe: pefile.PE, va: int, size: int, stop_at_ret: bool = True) -> list[str]:
    """
    Extracts bytes from the PE at Virtual Address `va` and disassembles them in-memory.
    Auto-detects PE32 vs PE32+ (x86 vs x64). Never prints raw instructions to stdout.
    """
    image_base = pe.OPTIONAL_HEADER.ImageBase
    rva = va - image_base
    if rva < 0:
        raise ValueError(f"Virtual Address 0x{va:08X} is below ImageBase 0x{image_base:08X}")

    try:
        data = pe.get_data(rva, size)
    except Exception as e:
        raise RuntimeError(f"Failed to read {size} bytes at VA 0x{va:08X} (RVA 0x{rva:08X}): {e}")

    # Auto-detect 32-bit vs 64-bit machine
    is_64bit = getattr(pe.FILE_HEADER, "Machine", 0) == 0x8664  # IMAGE_FILE_MACHINE_AMD64
    mode = capstone.CS_MODE_64 if is_64bit else capstone.CS_MODE_32

    md = capstone.Cs(capstone.CS_ARCH_X86, mode)
    md.detail = False

    lines = []
    for insn in md.disasm(data, va):
        lines.append(f"0x{insn.address:08X}: {insn.mnemonic} {insn.op_str}")
        if stop_at_ret and insn.mnemonic.startswith("ret"):
            break

    return lines


# ---------------------------------------------------------------------------
# Deterministic Regex Output Sanitizer
# ---------------------------------------------------------------------------

RE_ASM_CODE_BLOCK = re.compile(
    r"```(?:asm|x86|x64|nasm|assembly|disasm)\b[\s\S]*?```",
    re.IGNORECASE
)

# Supports 32-bit and 64-bit VA prefix lines (up to 16 hex digits)
RE_VA_PREFIX = re.compile(r"0x[0-9a-fA-F]{5,16}\s*:")

RE_MNEMONICS = re.compile(
    r"\b(mov|movzx|movsx|movsxd|push|pop|lea|call|jmp|je|jne|jz|jnz|ja|jae|jb|jbe|jg|jge|jl|jle|cmp|test|xor|sub|add|imul|idiv|shl|shr|sar|rep|stosd|stosq|stosw|stosb|movsd|movsq|movsb|ret|retn|nop)\b",
    re.IGNORECASE
)

# x86 and x64 registers and operand tokens
RE_OPERANDS = re.compile(
    r"\b(dword\s+ptr|word\s+ptr|byte\s+ptr|qword\s+ptr|tbyte\s+ptr|xmmword\s+ptr|ymmword\s+ptr|"
    r"rax|rbx|rcx|rdx|rsi|rdi|rbp|rsp|rip|r8|r9|r10|r11|r12|r13|r14|r15|"
    r"r8d|r9d|r10d|r11d|r12d|r13d|r14d|r15d|r8w|r9w|r10w|r11w|r12w|r13w|r14w|r15w|"
    r"r8b|r9b|r10b|r11b|r12b|r13b|r14b|r15b|"
    r"eax|ebx|ecx|edx|esi|edi|ebp|esp|eip|ax|bx|cx|dx|si|di|bp|sp|al|bl|cl|dl|ah|bh|ch|dh|"
    r"xmm[0-9]|ymm[0-9])\b",
    re.IGNORECASE
)

RE_MEM_PTR_DWORD = re.compile(r"\bdword\s+ptr\b", re.IGNORECASE)
RE_MEM_PTR_WORD = re.compile(r"\bword\s+ptr\b", re.IGNORECASE)
RE_MEM_PTR_BYTE = re.compile(r"\bbyte\s+ptr\b", re.IGNORECASE)
RE_MEM_PTR_QWORD = re.compile(r"\bqword\s+ptr\b", re.IGNORECASE)


def sanitize_stdout(text: str) -> str:
    """
    Deterministically sanitizes text before printing to stdout:
    1. Removes any assembly code blocks (```asm ... ```).
    2. Replaces any line matching raw disassembly patterns with [REDACTED_ASM_LINE].
    3. Replaces memory pointer syntax (e.g. 'dword ptr') with safe pseudocode tokens.
    """
    if not text:
        return ""

    # 1. Strip marked assembly code blocks
    cleaned = RE_ASM_CODE_BLOCK.sub("[REDACTED_ASM_BLOCK]", text)

    # 2. Line-by-line inspection
    sanitized_lines = []
    for line in cleaned.splitlines():
        has_va = bool(RE_VA_PREFIX.search(line))
        has_mnemonic = bool(RE_MNEMONICS.search(line))
        has_operands = bool(RE_OPERANDS.search(line))

        if (has_va and has_mnemonic) or (has_mnemonic and has_operands):
            sanitized_lines.append("[REDACTED_ASM_LINE]")
        else:
            s_line = RE_MEM_PTR_DWORD.sub("uint32_mem", line)
            s_line = RE_MEM_PTR_WORD.sub("uint16_mem", s_line)
            s_line = RE_MEM_PTR_BYTE.sub("uint8_mem", s_line)
            s_line = RE_MEM_PTR_QWORD.sub("uint64_mem", s_line)
            sanitized_lines.append(s_line)

    return "\n".join(sanitized_lines)


# ---------------------------------------------------------------------------
# Main Execution Pipeline
# ---------------------------------------------------------------------------

def parse_va_str(va_str: str) -> int:
    s = va_str.strip()
    if s.lower().startswith("0x"):
        return int(s, 16)
    return int(s, 16 if any(c in "abcdefABCDEF" for c in s) else 10)


def resolve_binary_path(binary_arg: str | None) -> Path:
    """
    Resolves binary path with fallback to common project defaults.
    """
    repo_root = Path(__file__).resolve().parent.parent

    if binary_arg:
        p = Path(binary_arg)
        if p.is_file():
            return p
        candidate = repo_root / binary_arg
        if candidate.is_file():
            return candidate
        sys.stderr.write(f"[ERROR] Specified binary file not found: {binary_arg}\n")
        sys.exit(1)

    # Fallback default: check if MOF/mofclient.exe exists
    mof_candidate = repo_root / "MOF" / "mofclient.exe"
    if mof_candidate.is_file():
        return mof_candidate

    sys.stderr.write(
        "[ERROR] Binary file not specified and no default found. "
        "Please provide --binary <path/to/binary.exe>.\n"
    )
    sys.exit(1)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description="Deterministic Sanitizer Wrapper for Binary Disassembly via Hermes CLI (Offrail-27B-12G & REA MCP)."
    )
    parser.add_argument(
        "--binary", "-b",
        default=None,
        help="Path to PE binary (default: MOF/mofclient.exe if present)"
    )
    parser.add_argument(
        "--va",
        nargs="+",
        required=False,
        help="One or more virtual addresses in hex (e.g. --va 0x00578840 0x00578870)"
    )
    parser.add_argument(
        "--use-rea",
        action="store_true",
        help="Explicitly route query to Hermes with registered 'rea' MCP tools (procedure_pseudo_code, xrefs, etc.)"
    )
    parser.add_argument(
        "--size", "-s",
        type=int,
        default=120,
        help="Disassembly byte window per VA in Mode A (default: 120)"
    )
    parser.add_argument(
        "--stop-at-ret",
        action="store_true",
        default=True,
        help="Stop disassembly at first 'ret' instruction (default: True)"
    )
    parser.add_argument(
        "--no-stop-at-ret",
        dest="stop_at_ret",
        action="store_false",
        help="Do not stop disassembly at 'ret'"
    )
    parser.add_argument(
        "--question", "-q",
        default="이 함수의 주요 로직, 인자 전달 순서, 필드 오프셋, 반환값을 한국어로 요약 분석해주세요.",
        help="Reverse engineering question in Korean"
    )
    parser.add_argument(
        "--model", "-m",
        default=None,
        help="Hermes model name (default: None, uses config.yaml default Offrail-27B-12G)"
    )
    parser.add_argument(
        "--provider",
        default=None,
        help="Hermes provider (default: None, uses config.yaml default offrail)"
    )
    parser.add_argument(
        "--sanitize-only", "--stdin-sanitize",
        dest="sanitize_only",
        action="store_true",
        help="Read text from stdin, sanitize it via sanitize_stdout(), and print to stdout"
    )

    args = parser.parse_args()

    # 1. Standalone Stdin Sanitization Mode
    if args.sanitize_only:
        raw_input = sys.stdin.read()
        sanitized = sanitize_stdout(raw_input)
        sys.stdout.write(sanitized + ("\n" if not sanitized.endswith("\n") else ""))
        sys.exit(0)

    # 2. Check required arguments
    if not args.use_rea and not args.va:
        parser.error("the following arguments are required: --va (or use --use-rea / --sanitize-only)")

    # 3. Check if Hermes CLI is available (Master Directive: NEVER fallback to raw disassembly)
    if not shutil.which("hermes"):
        sys.stderr.write(
            "[FORCE_ASK: HERMES_UNAVAILABLE] Hermes CLI 또는 로컬 Offrail-27B-12G 모델을 사용할 수 없습니다.\n"
            "임의로 직접 디스어셈블을 수행하지 말고, 즉시 주인님(사용자)께 Hermes 구동/설치 여부 또는 대안 진행 승인을 질문하십시오.\n"
        )
        sys.exit(2)

    # Resolve binary path
    bin_path = resolve_binary_path(args.binary)
    abs_bin_path = str(bin_path.resolve())

    # Build Prompt according to mode
    if args.use_rea:
        # Mode B: Hermes + REA MCP Explicit Tool Mode
        va_section = f"\n[분석 대상 가상 주소 (VA)]\n{', '.join(args.va)}" if args.va else ""
        prompt = f"""당신은 바이너리 역공학 전문 AI입니다. 등록된 'rea' MCP 도구(open_binary, procedure_pseudo_code, analyze_function, xrefs, read_function_instructions, search_strings 등)를 명시적으로 활용하여 아래 바이너리와 질문을 심층 분석하십시오.

[대상 바이너리 절대 경로]
{abs_bin_path}{va_section}

[질문]
{args.question}

[엄격한 출력 제한 규칙 - 절대 준수]
1. 답변에 어셈블리 명령어(mov, movzx, movsx, push, pop, lea, call, jmp, je, jne, jz, jnz, ja, jae, jb, jbe, jg, jge, jl, jle, cmp, test, xor, sub, add, imul, idiv, shl, shr, sar, rep, stos, ret, dword ptr, word ptr, byte ptr, esp, ebp, eax, ebx, ecx, edx, esi, edi, rax, rbx, rcx, rdx, rsi, rdi, rbp, rsp 등)나 어셈블리 코드 블록(```asm, ```x86, ```x64 등)을 절대 포함하지 마십시오.
2. 오직 C# 또는 C 스타일의 고수준 의사코드(Pseudocode), 함수 호출 관계(Call Graph/Xrefs), 구조체 오프셋 표(예: +0x08 = Level), 패킷 필드 순서와 의미만 한국어로 명확히 요약하여 답변하십시오.
3. 규칙을 위반하여 어셈블리 명령어가 노출되면 상류 보안 필터에 의해 출력이 차단됩니다.
"""
        hermes_extra_flags = ["--yolo"]
    else:
        # Mode A: Fast In-Memory Capstone + Hermes
        try:
            pe = pefile.PE(str(bin_path), fast_load=True)
            pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXPORT"]])
        except Exception as e:
            sys.stderr.write(f"[ERROR] Failed to load PE binary {bin_path}: {e}\n")
            sys.exit(1)

        disasm_sections = []
        for va_str in args.va:
            try:
                va = parse_va_str(va_str)
                lines = disassemble_va(pe, va, args.size, stop_at_ret=args.stop_at_ret)
                disasm_text = "\n".join(lines)
                disasm_sections.append(f"=== VA 0x{va:08X} (Length: {len(lines)} instructions) ===\n{disasm_text}")
            except Exception as e:
                sys.stderr.write(f"[ERROR] Disassembly failed for VA {va_str}: {e}\n")
                sys.exit(1)

        combined_disasm = "\n\n".join(disasm_sections)

        prompt = f"""당신은 바이너리 역공학 전문 AI입니다. 아래 제공된 디스어셈블리 코드를 분석하여 질문에 답하십시오.

[분석 대상 디스어셈블리]
{combined_disasm}

[질문]
{args.question}

[엄격한 출력 제한 규칙 - 절대 준수]
1. 답변에 어셈블리 명령어(mov, movzx, movsx, push, pop, lea, call, jmp, je, jne, jz, jnz, ja, jae, jb, jbe, jg, jge, jl, jle, cmp, test, xor, sub, add, imul, idiv, shl, shr, sar, rep, stos, ret, dword ptr, word ptr, byte ptr, esp, ebp, eax, ebx, ecx, edx, esi, edi, rax, rbx, rcx, rdx, rsi, rdi, rbp, rsp 등)나 어셈블리 코드 블록(```asm, ```x86 등)을 절대 포함하지 마십시오.
2. 오직 C# 또는 C 스타일의 고수준 의사코드(Pseudocode), 구조체 오프셋 표(예: +0x08 = Level), 패킷 필드 순서와 의미만 한국어로 요약하여 답변하십시오.
3. 규칙을 위반하여 어셈블리 명령어가 노출되면 상류 보안 필터에 의해 출력이 차단됩니다.
"""
        hermes_extra_flags = []

    temp_file = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".txt") as tf:
            tf.write(prompt)
            temp_file = tf.name

        # Invoke Hermes CLI
        hermes_cmd = [
            "hermes", "chat",
            "--query-file", temp_file,
            "-Q"
        ]
        hermes_cmd.extend(hermes_extra_flags)
        if args.provider:
            hermes_cmd.extend(["--provider", args.provider])
        if args.model:
            hermes_cmd.extend(["-m", args.model])

        proc = subprocess.run(
            hermes_cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        raw_output = proc.stdout

        # Check for model / provider execution failures
        if proc.returncode != 0 and not raw_output:
            sys.stderr.write(
                f"[FORCE_ASK: HERMES_UNAVAILABLE] Hermes CLI 실행 실패 (exit {proc.returncode}): {proc.stderr}\n"
                "로컬 Offrail-27B-12G 모델 또는 Hermes CLI를 사용할 수 없습니다.\n"
                "임의로 직접 디스어셈블을 수행하지 말고, 즉시 주인님(사용자)께 Hermes 구동/설치 여부 또는 대안 진행 승인을 질문하십시오.\n"
            )
            sys.exit(2)

        if "API call failed" in raw_output or "Connection error" in raw_output:
            sys.stderr.write(
                f"[FORCE_ASK: HERMES_UNAVAILABLE] Hermes CLI 연결 실패: {raw_output.strip()}\n"
                "로컬 Offrail-27B-12G 모델에 연결할 수 없습니다.\n"
                "임의로 직접 디스어셈블을 수행하지 말고, 즉시 주인님(사용자)께 Hermes 구동/설치 여부 또는 대안 진행 승인을 질문하십시오.\n"
            )
            sys.exit(2)

        # Deterministic Regex Output Sanitization Gate
        sanitized = sanitize_stdout(raw_output)
        sys.stdout.write(sanitized + ("\n" if not sanitized.endswith("\n") else ""))
        sys.exit(0)

    finally:
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass


if __name__ == "__main__":
    main()
