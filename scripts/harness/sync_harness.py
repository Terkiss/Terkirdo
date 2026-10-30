#!/usr/bin/env python3
"""
Terukirdo v5.6 Deterministic Harness Synchronizer & Legacy Purger
- Mirrors core harness directories so files deleted in the master template are
  deterministically purged from older target projects.
- Purges stale root protocol files (e.g. Terukirdo_Protocol_v5.2~v5.5.md) and legacy paths.
- Preserves target project's .git, source code, README.md, MEMORY.md, docs/specs, and .agents/state.
"""

import os
import sys
import shutil
import filecmp
import argparse
import subprocess
from pathlib import Path

# Directories that are 100% owned by the harness and must be mirrored (including purging deleted files)
MIRROR_DIRS = [
    ".agents",
    "agents",
    "scripts/harness",
    "scripts/self-evolution",
    "tests/harness",
    "docs/harness",
    "docs/archive",
    "docs/v2_specs",
    "reference",
]

# Sub-paths inside MIRROR_DIRS that belong to the target project's runtime state and must NEVER be deleted
PRESERVED_SUBPATHS = {
    ".agents/state",
    ".agents/skills/self-evolution/scripts/skillopt-engine/venv",
}

# Individual harness files outside MIRROR_DIRS that must always be overwritten with the latest template version
OVERWRITE_FILES = [
    "AGENTS.md",
    "scripts/hermes_disasm.py",
    "docs/README.md",
    "docs/V2_Architecture_Spec.md",
    "docs/V2_Implementation_Plan.md",
]

# Directories where missing template files are seeded once, but existing target files are NEVER overwritten or deleted
SEED_ONLY_DIRS = [
    "docs/architecture",
    "docs/design",
    "docs/development",
    "docs/handoff",
    "docs/operations",
    "docs/product",
    "docs/project",
]

# Known legacy files from older Terukirdo versions (v5.1 ~ v5.5) that were deleted from the template
KNOWN_LEGACY_PATHS = [
    "IMPLEMENTATION_PROGRESS.md",
    "Documents/Implementation_Plan.md",
    "scripts/auto_evolve.py",
]

IGNORE_NAMES = {"__pycache__", ".pytest_cache", ".pyc"}


def should_ignore(name: str) -> bool:
    return name in IGNORE_NAMES or name.endswith(".pyc")


def is_preserved_subpath(rel_posix: str) -> bool:
    rel_norm = rel_posix.strip("/").lower()
    for p in PRESERVED_SUBPATHS:
        p_norm = p.strip("/").lower()
        if rel_norm == p_norm or rel_norm.startswith(p_norm + "/"):
            return True
    return False


def files_are_identical(src: Path, dst: Path) -> bool:
    if not dst.is_file():
        return False
    try:
        return filecmp.cmp(str(src), str(dst), shallow=False)
    except Exception:
        return False


def copy_file_tracked(src: Path, dst: Path, stats: dict, rel_label: str):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copy2(src, dst)
        stats["added"].append(rel_label)
    elif not files_are_identical(src, dst):
        shutil.copy2(src, dst)
        stats["updated"].append(rel_label)
    else:
        stats["unchanged"] += 1


def mirror_directory(source_root: Path, target_root: Path, rel_dir: str, stats: dict):
    src_dir = source_root / rel_dir
    dst_dir = target_root / rel_dir

    if not src_dir.is_dir() and not dst_dir.is_dir():
        return

    # 1. Purge items in dst_dir that no longer exist in src_dir (unless preserved)
    if dst_dir.is_dir():
        for root, dirs, files in os.walk(dst_dir, topdown=False):
            root_path = Path(root)
            rel_from_target = root_path.relative_to(target_root).as_posix()

            if is_preserved_subpath(rel_from_target):
                continue

            corresponding_src_root = source_root / rel_from_target

            for fname in files:
                dst_file = root_path / fname
                file_rel = dst_file.relative_to(target_root).as_posix()
                if is_preserved_subpath(file_rel):
                    continue
                src_file = corresponding_src_root / fname
                if should_ignore(fname) or not src_file.is_file():
                    try:
                        dst_file.unlink()
                        if not should_ignore(fname):
                            stats["deleted"].append(file_rel)
                    except Exception as e:
                        stats["errors"].append(f"Failed to delete file {file_rel}: {e}")

            for dname in dirs:
                dst_subdir = root_path / dname
                dir_rel = dst_subdir.relative_to(target_root).as_posix()
                if is_preserved_subpath(dir_rel):
                    continue
                src_subdir = corresponding_src_root / dname
                if should_ignore(dname) or not src_subdir.is_dir():
                    try:
                        shutil.rmtree(dst_subdir)
                        if not should_ignore(dname):
                            stats["deleted"].append(dir_rel + "/")
                    except Exception as e:
                        stats["errors"].append(f"Failed to delete directory {dir_rel}: {e}")

        if not src_dir.is_dir() and not is_preserved_subpath(rel_dir):
            try:
                if not any(dst_dir.iterdir()):
                    dst_dir.rmdir()
                    stats["deleted"].append(rel_dir + "/")
            except Exception as e:
                stats["errors"].append(f"Failed to delete directory {rel_dir}: {e}")
            return

    if not src_dir.is_dir():
        return

    dst_dir.mkdir(parents=True, exist_ok=True)

    # 2. Copy/update all items from src_dir to dst_dir
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if not should_ignore(d)]
        root_path = Path(root)
        rel_from_source = root_path.relative_to(source_root).as_posix()

        if is_preserved_subpath(rel_from_source):
            dirs[:] = []
            continue

        target_subdir = target_root / rel_from_source
        target_subdir.mkdir(parents=True, exist_ok=True)

        for fname in files:
            if should_ignore(fname):
                continue
            src_file = root_path / fname
            file_rel = src_file.relative_to(source_root).as_posix()
            if is_preserved_subpath(file_rel):
                continue
            dst_file = target_root / file_rel
            copy_file_tracked(src_file, dst_file, stats, file_rel)


def purge_legacy_root_files(source_root: Path, target_root: Path, stats: dict):
    # 1. Purge old Terukirdo_Protocol_*.md in root that no longer exist in source_root
    source_protocols = {p.name for p in source_root.glob("Terukirdo_Protocol_*.md")}
    for target_proto in target_root.glob("Terukirdo_Protocol_*.md"):
        if target_proto.name not in source_protocols:
            try:
                target_proto.unlink()
                stats["deleted"].append(target_proto.name)
            except Exception as e:
                stats["errors"].append(f"Failed to delete stale protocol {target_proto.name}: {e}")

    # 2. Purge known legacy paths
    for rel_legacy in KNOWN_LEGACY_PATHS:
        legacy_path = target_root / rel_legacy
        if legacy_path.is_file():
            try:
                legacy_path.unlink()
                stats["deleted"].append(rel_legacy)
            except Exception as e:
                stats["errors"].append(f"Failed to delete legacy file {rel_legacy}: {e}")
        elif legacy_path.is_dir():
            try:
                shutil.rmtree(legacy_path)
                stats["deleted"].append(rel_legacy + "/")
            except Exception as e:
                stats["errors"].append(f"Failed to delete legacy dir {rel_legacy}: {e}")


def seed_missing_docs(source_root: Path, target_root: Path, stats: dict):
    for rel_dir in SEED_ONLY_DIRS:
        src_dir = source_root / rel_dir
        if not src_dir.is_dir():
            continue
        for root, _, files in os.walk(src_dir):
            root_path = Path(root)
            for fname in files:
                if should_ignore(fname):
                    continue
                src_file = root_path / fname
                file_rel = src_file.relative_to(source_root).as_posix()
                dst_file = target_root / file_rel
                if not dst_file.exists():
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dst_file)
                    stats["seeded"].append(file_rel)
                else:
                    stats["preserved"].append(file_rel)


def sync_harness(source_root: Path, target_root: Path, run_verification: bool = True) -> tuple[bool, dict]:
    source_root = source_root.resolve()
    target_root = target_root.resolve()

    if source_root == target_root:
        raise ValueError("Source and target directories cannot be identical.")

    if not (source_root / ".agents" / "agents" / "agy-worker" / "agent.md").is_file():
        raise FileNotFoundError(f"Invalid master template directory: {source_root}")

    if not target_root.is_dir():
        raise FileNotFoundError(f"Target directory does not exist: {target_root}")

    stats = {
        "added": [],
        "updated": [],
        "deleted": [],
        "seeded": [],
        "preserved": [],
        "unchanged": 0,
        "errors": [],
    }

    # Step 1: Purge stale root protocol files and legacy paths
    purge_legacy_root_files(source_root, target_root, stats)

    # Step 2: Mirror harness-owned directories (adds new, updates changed, deletes removed)
    for rel_dir in MIRROR_DIRS:
        mirror_directory(source_root, target_root, rel_dir, stats)

    # Ensure .agents/state exists in target
    (target_root / ".agents" / "state").mkdir(parents=True, exist_ok=True)

    # Step 3: Overwrite root/core harness files (active protocol, AGENTS.md, hermes_disasm.py, etc.)
    for proto_file in source_root.glob("Terukirdo_Protocol_*.md"):
        copy_file_tracked(proto_file, target_root / proto_file.name, stats, proto_file.name)

    for rel_file in OVERWRITE_FILES:
        src_file = source_root / rel_file
        if src_file.is_file():
            copy_file_tracked(src_file, target_root / rel_file, stats, rel_file)

    # Step 4: Seed missing project docs & preserve existing README.md, MEMORY.md, Trajectory
    seed_missing_docs(source_root, target_root, stats)

    for preserved_file in ["README.md", "MEMORY.md"]:
        dst_p = target_root / preserved_file
        src_p = source_root / preserved_file
        if not dst_p.exists() and src_p.is_file():
            shutil.copy2(src_p, dst_p)
            stats["seeded"].append(preserved_file)
        elif dst_p.exists():
            stats["preserved"].append(preserved_file)

    traj_path = target_root / "docs" / "Terukirdo_Trajectory.txt"
    traj_path.parent.mkdir(parents=True, exist_ok=True)
    if not traj_path.exists():
        traj_path.write_text("", encoding="utf-8")
        stats["seeded"].append("docs/Terukirdo_Trajectory.txt")
    else:
        stats["preserved"].append("docs/Terukirdo_Trajectory.txt")

    # Step 5: Rebuild skill index and run validate_harness.py in target
    if run_verification:
        indexer_script = target_root / ".agents" / "skills" / "self-evolution" / "scripts" / "skill_indexer.py"
        if indexer_script.is_file():
            res_idx = subprocess.run(
                [sys.executable, str(indexer_script), "--build"],
                cwd=str(target_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if res_idx.returncode != 0:
                stats["errors"].append(f"skill_indexer.py failed: {res_idx.stderr}")

        validator_script = target_root / "scripts" / "harness" / "validate_harness.py"
        if validator_script.is_file():
            res_val = subprocess.run(
                [sys.executable, str(validator_script), "--strict"],
                cwd=str(target_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if res_val.returncode != 0:
                stats["errors"].append(f"validate_harness.py failed:\n{res_val.stderr}")

    success = len(stats["errors"]) == 0
    return success, stats


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Synchronize Terukirdo v5.6 harness to a target project.")
    parser.add_argument("--source", type=str, required=True, help="Master template root directory")
    parser.add_argument("--target", type=str, required=True, help="Target project root directory")
    parser.add_argument("--no-verify", action="store_true", help="Skip post-sync skill indexing and harness validation")
    args = parser.parse_args()

    try:
        success, stats = sync_harness(
            Path(args.source),
            Path(args.target),
            run_verification=not args.no_verify,
        )
    except Exception as e:
        print(f"[ERROR] Harness sync failed: {e}", file=sys.stderr)
        sys.exit(1)

    print("----------------------------------------------------------------------------")
    print(f"  [+] Added files     : {len(stats['added'])}")
    print(f"  [~] Updated files   : {len(stats['updated'])}")
    print(f"  [-] Purged old files: {len(stats['deleted'])}")
    if stats["deleted"]:
        for d in stats["deleted"][:15]:
            print(f"        purged: {d}")
        if len(stats["deleted"]) > 15:
            print(f"        ... and {len(stats['deleted']) - 15} more")
    print(f"  [*] Seeded defaults : {len(stats['seeded'])}")
    print(f"  [=] Unchanged files : {stats['unchanged']}")
    print("----------------------------------------------------------------------------")

    if not success:
        print("[FAILED] Errors occurred during synchronization:", file=sys.stderr)
        for err in stats["errors"]:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)

    print("[PASSED] Harness Validation & Skill Indexer verified in target project.")
    sys.exit(0)


if __name__ == "__main__":
    main()
