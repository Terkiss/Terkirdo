#!/usr/bin/env python3
"""
Partition Validator for Agent Legion (Deterministic Python Check)
Ensures:
1. At most MAX_CONCURRENT_RALPH (4) ralph-orchestrator instances run concurrently per wave.
2. Disjointness of allowed_files across parallel partitions within the same wave.
"""

import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict

MAX_CONCURRENT_RALPH = 4

def validate_partitions(partition_data):
    """
    Validates that:
    - Each wave has at most MAX_CONCURRENT_RALPH (4) parallel ralph-orchestrator partitions.
    - All concurrent partitions within a wave have non-overlapping allowed_files.
    Returns (is_valid, errors, summary)
    """
    errors = []
    partitions = partition_data.get("partitions", [])

    if not partitions:
        return False, ["No partitions provided in partition data."], {}

    waves = defaultdict(list)
    for idx, p in enumerate(partitions):
        wave_id = p.get("wave", 1)
        waves[wave_id].append((idx, p))

    total_files = 0
    for wave_id, wave_items in sorted(waves.items(), key=lambda x: str(x[0])):
        if len(wave_items) > MAX_CONCURRENT_RALPH:
            errors.append(
                f"Concurrency limit exceeded in wave '{wave_id}': Legion Commander can operate at most "
                f"{MAX_CONCURRENT_RALPH} concurrent ralph-orchestrator instances simultaneously, "
                f"but {len(wave_items)} partitions were assigned to wave '{wave_id}'."
            )

        file_to_partition = {}
        for idx, p in wave_items:
            p_id = p.get("id", f"partition_{idx}")
            allowed = p.get("allowed_files", [])

            if not allowed:
                errors.append(f"Partition '{p_id}' (wave '{wave_id}') has empty allowed_files list.")
                continue

            for f in allowed:
                norm_f = str(Path(f)).replace('\\', '/').lower()
                if norm_f in file_to_partition:
                    existing_p = file_to_partition[norm_f]
                    errors.append(
                        f"Conflict detected in wave '{wave_id}': File '{f}' is claimed by both "
                        f"partition '{existing_p}' and '{p_id}'!"
                    )
                else:
                    file_to_partition[norm_f] = p_id
                    total_files += 1

    is_valid = len(errors) == 0
    summary = {
        "partition_count": len(partitions),
        "wave_count": len(waves),
        "max_concurrent_ralph_limit": MAX_CONCURRENT_RALPH,
        "total_files": total_files,
        "valid": is_valid
    }
    return is_valid, errors, summary

def main():
    parser = argparse.ArgumentParser(description="Validate disjoint file partitions and Quad-Ralph concurrency for Agent Legion.")
    parser.add_argument("partition_file", nargs="?", help="Path to JSON file containing partition definitions.")
    parser.add_argument("--json", action="store_true", help="Output results as JSON.")
    args = parser.parse_args()

    if args.partition_file:
        p_path = Path(args.partition_file)
        if not p_path.is_file():
            print(f"Error: File not found: {args.partition_file}", file=sys.stderr)
            sys.exit(2)
        try:
            with open(p_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error parsing JSON: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        try:
            data = json.load(sys.stdin)
        except Exception as e:
            print(f"Error reading JSON from stdin: {e}", file=sys.stderr)
            sys.exit(2)

    is_valid, errors, summary = validate_partitions(data)

    if args.json:
        result = {
            "status": "PASSED" if is_valid else "FAILED",
            "summary": summary,
            "errors": errors
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if is_valid:
            print(
                f"[Agent Legion] Partition Validation PASSED! "
                f"({summary['partition_count']} partitions across {summary['wave_count']} wave(s), "
                f"<= {MAX_CONCURRENT_RALPH} concurrent Ralph agents/wave, {summary['total_files']} non-conflicting files)"
            )
        else:
            print(f"[Agent Legion] Partition Validation FAILED with {len(errors)} error(s):", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)

    sys.exit(0 if is_valid else 1)

if __name__ == "__main__":
    main()
