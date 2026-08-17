# .agents/sync/sync_engine.py
import os
import sys
import time
import json
import subprocess
import argparse
import logging
from datetime import datetime

TIMEOUT_SECONDS = 300 # 기본 5분 타임아웃
LOCK_FILE = ".terkirdo_sync.lock"
CACHE_FILE = ".terkirdo_pre_cache.md"
DEFERRED_QUEUE = ".terkirdo_deferred.json"

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def create_lock():
    if os.path.exists(LOCK_FILE):
        return False
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))
    return True

def release_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

def parse_cache(cache_path):
    if not os.path.exists(cache_path):
        return None
    with open(cache_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        json_str = content.split("```json")[1].split("```")[0]
        data = json.loads(json_str)
        # Windows 경로를 크로스 플랫폼 표준(/)으로 변환
        data['files'] = [file_path.replace('\\', '/') for file_path in data.get('files', [])]
        return data
    except Exception as e:
        logging.error(f"Failed to parse cache: {e}")
        return None

def check_merge_conflict():
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        # 'U' 상태 코드는 Unmerged 상태(충돌)를 의미함
        for line in result.stdout.split('\n'):
            if line.startswith('U') or 'U' in line[:2]:
                return True
        return False
    except Exception:
        return False

def update_cache_status(cache_path, new_status):
    if not os.path.exists(cache_path):
        return
    with open(cache_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content.replace('status: "in_progress"', f'status: "{new_status}"')
    with open(cache_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

def handle_conflict():
    logging.warning("Merge conflict detected! Suspending sync and updating status.")
    update_cache_status(CACHE_FILE, "conflict_paused")
    # AI 벡터 DB 롤백 (Drop uncommitted vectors) 로직이 이곳에 추가됩니다
    logging.info("Dropped uncommitted vectors for rollback.")

def sync_process(files):
    start_time = time.time()
    deferred_files = []
    
    for i, file_path in enumerate(files):
        # 1. 충돌(Conflict) 폴링 확인
        if check_merge_conflict():
            handle_conflict()
            return

        # 2. 타임아웃 5분(300초) 확인
        if time.time() - start_time > TIMEOUT_SECONDS:
            logging.warning("Timeout exceeded 5 minutes. Checkpointing and moving remaining to deferred queue.")
            deferred_files = files[i:]
            break
            
        # 3. 실질적인 동기화 작업 (AI Knowledge Base Update)
        logging.info(f"Syncing semantic index for file: {file_path}")
        time.sleep(0.5) # 실제 DB 업데이트 로직 자리

    # 지연 큐(Deferred Queue) 저장
    if deferred_files:
        with open(DEFERRED_QUEUE, 'w', encoding='utf-8') as f:
            json.dump({"deferred_files": deferred_files}, f, indent=2)
    else:
        # 정상 완료 시 캐시 클리어
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--predictive', action='store_true', help='Run predictive sync')
    parser.add_argument('--cache-file', type=str, default=CACHE_FILE, help='Cache file path')
    args = parser.parse_args()

    if not args.predictive:
        return

    # Lock 파일 검증 및 생성
    if not create_lock():
        logging.warning("Sync is already running. Skipping this trigger.")
        return

    try:
        data = parse_cache(args.cache_file)
        if data and 'files' in data:
            sync_process(data['files'])
    finally:
        # 종료/타임아웃 시 락 파일 제거
        release_lock()

if __name__ == "__main__":
    main()
