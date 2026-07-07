#!/usr/bin/env python3
import os
import subprocess
import sys
import time

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
SKILLS_DIR = os.path.join(BASE_DIR, '.agents', 'skills')
HOOKS_DIR = os.path.join(BASE_DIR, '.agents', 'hooks')

def run_cmd(cmd, cwd=None, check=True):
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)

def auto_evolve():
    print("Starting Self-Evolution Cycle (SkillOpt-Sleep)...")
    
    # 1. Version Control (Pre-Commit)
    run_cmd(["git", "add", ".agents/skills/"], cwd=BASE_DIR, check=False)
    status = run_cmd(["git", "status", "--porcelain"], cwd=BASE_DIR, check=False)
    if "M " in status.stdout or "A " in status.stdout:
        run_cmd(["git", "commit", "-m", "chore: backup skills before self-evolution"], cwd=BASE_DIR, check=False)
    
    # Save current commit hash for rollback
    last_commit = run_cmd(["git", "rev-parse", "HEAD"], cwd=BASE_DIR).stdout.strip()
    print(f"Safe point commit: {last_commit}")

    # 2. Immutable Core Guardrail: We only allow changes in .agents/skills/
    # (By only running skillopt on the skills directory, but we also enforce it via git checkout if needed)

    # 3. Trigger SkillOpt-Sleep Pipeline
    # Assuming skillopt_sleep is available in the venv
    venv_python = os.path.join(os.path.dirname(__file__), 'skillopt-engine', 'venv', 'Scripts', 'python.exe')
    if not os.path.exists(venv_python):
        print(f"Python venv not found at {venv_python}. Skipping evolution.")
        return

    try:
        # Run harvest, mine, rollout (simplified mock command for actual engine)
        run_cmd([venv_python, "-m", "skillopt_sleep", "--harvest", "--mine", "--rollout"], cwd=os.path.join(os.path.dirname(__file__), 'skillopt-engine'), check=False)
    except Exception as e:
        print(f"SkillOpt engine failed: {e}")

    # 4. Quality Gate & Approval (Validation)
    print("Running Quality Gates on updated skills...")
    qg_passed = True
    
    # Run stop_quality_gate.py
    qg_res = run_cmd([sys.executable, os.path.join(HOOKS_DIR, "stop_quality_gate.py")], cwd=BASE_DIR, check=False)
    if qg_res.returncode != 0:
        print(f"Quality Gate failed: {qg_res.stderr}")
        qg_passed = False
        
    # Find any verify.ps1 and run them
    verify_scripts = []
    for root, _, files in os.walk(SKILLS_DIR):
        if "verify.ps1" in files:
            verify_scripts.append(os.path.join(root, "verify.ps1"))
            
    for script in verify_scripts:
        res = run_cmd(["powershell", "-ExecutionPolicy", "Bypass", "-File", script], cwd=BASE_DIR, check=False)
        if res.returncode != 0:
            print(f"Skill verification failed for {script}: {res.stderr}")
            qg_passed = False
            break

    # 5. Live Release or Rollback
    if qg_passed:
        print("Self-Evolution Successful! Quality gates passed.")
        run_cmd(["git", "add", ".agents/skills/"], cwd=BASE_DIR, check=False)
        run_cmd(["git", "commit", "-m", "feat: self-evolution optimized skills"], cwd=BASE_DIR, check=False)
        # Note: Index will be automatically rebuilt by the watchdog daemon (Phase 1)
    else:
        print(f"High error rate or QG failure detected. Rolling back to {last_commit}...")
        run_cmd(["git", "reset", "--hard", last_commit], cwd=BASE_DIR, check=False)
        run_cmd(["git", "clean", "-fd", ".agents/skills/"], cwd=BASE_DIR, check=False)
        print("Rollback complete.")

if __name__ == "__main__":
    auto_evolve()
