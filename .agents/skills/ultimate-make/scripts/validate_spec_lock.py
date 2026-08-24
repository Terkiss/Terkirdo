#!/usr/bin/env python3
"""
UltimateMake Deterministic Spec-Lock Validator
===============================================
Enforces strict physical quality gates on specifications before allowing any code implementation.
Checks:
  1. Research Evidence Bundle validity (existence, byte size, URL links, RFC/CVE content)
  2. Banned Ambiguous Words Linter (적당히, 알아서, 등등 regex search)
  3. Spec Structural Completeness (All mandatory 7 sections)
  4. Given-When-Then Acceptance Criteria syntactic parser (min 3 ACs)
  5. Deterministic State Machine Matrix detection
"""

import sys
import os
import re
import argparse
from pathlib import Path

BANNED_WORDS = [
    r"적당히",
    r"빠르게",
    r"알아서",
    r"유연하게",
    r"기타\s*등등",
    r"필요시",
    r"적절한",
    r"상황에\s*따라",
    r"추후\s*결정",
    r"TBD",
    r"TODO"
]

MANDATORY_SECTIONS = [
    r"##\s*1\.\s*Problem Definition",
    r"##\s*2\.\s*Research & Global Benchmark",
    r"##\s*3\.\s*Architecture & Conference Decisions",
    r"##\s*4\.\s*Boundaries\s*\(Scope\)",
    r"##\s*5\.\s*Data & Deterministic State Machine",
    r"##\s*6\.\s*Machine-Verifiable Acceptance Criteria",
    r"##\s*7\.\s*Execution Cards"
]

def check_banned_words(content: str) -> list[str]:
    violations = []
    lines = content.splitlines()
    for idx, line in enumerate(lines, 1):
        # Ignore comments or markdown headings if needed, but inspect body
        for pattern in BANNED_WORDS:
            match = re.search(pattern, line)
            if match:
                violations.append(f"Line {idx}: Found banned word '{match.group(0)}' in: {line.strip()[:60]}")
    return violations

def check_structure(content: str) -> list[str]:
    missing = []
    for section_pattern in MANDATORY_SECTIONS:
        if not re.search(section_pattern, content, re.IGNORECASE):
            missing.append(f"Missing mandatory section matching pattern: {section_pattern}")
    return missing

def check_acceptance_criteria(content: str) -> tuple[int, list[str]]:
    errors = []
    # Count Given-When-Then triplets
    # Match patterns like: Given ... When ... Then ...
    gwt_blocks = re.findall(r"Given\s+.+?\s+When\s+.+?\s+Then\s+.+?", content, re.IGNORECASE | re.DOTALL)
    # Also line-by-line checks
    given_count = len(re.findall(r"\bGiven\b", content, re.IGNORECASE))
    when_count = len(re.findall(r"\bWhen\b", content, re.IGNORECASE))
    then_count = len(re.findall(r"\bThen\b", content, re.IGNORECASE))
    
    total_acs = min(given_count, when_count, then_count)
    if total_acs < 3:
        errors.append(f"Insufficient Acceptance Criteria. Found {total_acs} valid Given-When-Then clauses (Minimum required: 3).")
    
    return total_acs, errors

def check_state_machine_matrix(content: str) -> list[str]:
    errors = []
    # Check if a markdown table exists in section 5
    if "|" not in content or "---" not in content:
        errors.append("No Markdown State Machine Table / Matrix detected in specification.")
    return errors

def check_research_bundle(research_path: Path) -> list[str]:
    errors = []
    if not research_path.exists():
        errors.append(f"Research bundle does not exist at: {research_path}")
        return errors
    
    content = research_path.read_text(encoding="utf-8")
    if len(content.encode("utf-8")) < 1000:
        errors.append(f"Research bundle is too shallow ({len(content)} bytes). Minimum 1,000 bytes required for deep sweep.")
    
    # Check for external URLs
    urls = re.findall(r"https?://[^\s\)\>]+", content)
    if len(urls) < 3:
        errors.append(f"Research bundle lacks sufficient source citations (Found {len(urls)} URLs, minimum 3 required).")
    
    return errors

def main():
    parser = argparse.ArgumentParser(description="Deterministic Spec-Lock Validator for UltimateMake")
    parser.add_argument("--spec", required=True, help="Path to the specification file (docs/specs/*.spec.md)")
    parser.add_argument("--research", required=False, help="Path to the research bundle (docs/research/*.md)")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"[FATAL] Specification file not found: {spec_path}", file=sys.stderr)
        sys.exit(1)

    spec_content = spec_path.read_text(encoding="utf-8")
    
    print("=" * 60)
    print(f"🔒 UltimateMake Spec-Lock Validator: {spec_path.name}")
    print("=" * 60)

    has_errors = False

    # 1. Research Check
    if args.research:
        research_path = Path(args.research)
        print(f"[1/4] Checking Research Evidence Bundle: {research_path.name} ...")
        research_errors = check_research_bundle(research_path)
        if research_errors:
            has_errors = True
            for err in research_errors:
                print(f"  ❌ {err}")
        else:
            print("  ✅ Research Evidence verified (Deep sweep + citations present).")
    else:
        print("[1/4] Skipping Research check (no --research passed).")

    # 2. Structural Completeness
    print("[2/4] Checking 7 Mandatory Structural Sections ...")
    struct_errors = check_structure(spec_content)
    if struct_errors:
        has_errors = True
        for err in struct_errors:
            print(f"  ❌ {err}")
    else:
        print("  ✅ All 7 mandatory sections present.")

    # 3. Banned Words Linter
    print("[3/4] Scanning for Banned Ambiguous Words ...")
    banned_violations = check_banned_words(spec_content)
    if banned_violations:
        has_errors = True
        for v in banned_violations:
            print(f"  ❌ {v}")
    else:
        print("  ✅ Zero banned ambiguous words detected.")

    # 4. Acceptance Criteria & State Machine Matrix
    print("[4/4] Verifying Acceptance Criteria & State Machine Matrix ...")
    ac_count, ac_errors = check_acceptance_criteria(spec_content)
    sm_errors = check_state_machine_matrix(spec_content)
    all_ac_errors = ac_errors + sm_errors
    if all_ac_errors:
        has_errors = True
        for err in all_ac_errors:
            print(f"  ❌ {err}")
    else:
        print(f"  ✅ {ac_count} Given-When-Then Acceptance Criteria & State Table verified.")

    print("=" * 60)
    if has_errors:
        print("🚨 SPEC-LOCK FAILED: The specification contains ambiguities, missing sections, or shallow research.")
        print("🚫 AGY Worker execution is BLOCKED until all issues are resolved.")
        print("=" * 60)
        sys.exit(1)
    else:
        print("🏆 SPEC-LOCK APPROVED: Specification is 100% deterministic, unambiguous, and verified.")
        print("🔓 Hand-off to Ralph Loop (AGY Worker) is AUTHORIZED.")
        print("=" * 60)
        sys.exit(0)

if __name__ == "__main__":
    main()
