#!/usr/bin/env python3
"""
Peer Tactical Radio & Shared Bulletin Board CLI Engine for Agent Legion (Octa-Ralph).

Zero external dependencies (Python standard library only).
Provides lock-free cross-process tactical coordination for Commander and Ralph-1..Ralph-8
backed by SQLite WAL + busy_timeout=5000 + BEGIN IMMEDIATE transactions + jitter retry.
"""

import argparse
import datetime
import json
import os
import pathlib
import random
import sqlite3
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DEFAULT_DB_PATH = REPO_ROOT / ".agents" / "state" / "legion_radio.db"

VALID_SQUADS = (
    "Commander",
    "Ralph-1",
    "Ralph-2",
    "Ralph-3",
    "Ralph-4",
    "Ralph-5",
    "Ralph-6",
    "Ralph-7",
    "Ralph-8",
)
VALID_RECIPIENTS = ("ALL",) + VALID_SQUADS
VALID_TAGS = ("INTERFACE", "SCHEMA", "DECISION", "BLOCKER", "DONE")
MAX_MSG_LENGTH = 2000

SQUAD_ORDER = {name: idx for idx, name in enumerate(VALID_SQUADS)}

SCHEMA_SQL = (
    """
    CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS roster (
        squad TEXT PRIMARY KEY,
        conv_id TEXT NOT NULL,
        partition TEXT NOT NULL DEFAULT '',
        scope TEXT NOT NULL DEFAULT '',
        registered_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS messages (
        seq INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        recipient TEXT NOT NULL DEFAULT 'ALL',
        tag TEXT NOT NULL DEFAULT 'INTERFACE',
        body TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_messages_recipient_seq
    ON messages (recipient, seq);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_messages_tag_seq
    ON messages (tag, seq);
    """,
)


class RadioArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(f"[RADIO ERROR] {message}", file=sys.stderr)
        sys.exit(1)


def utc_now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds")


def resolve_db_path(cli_db=None) -> pathlib.Path:
    if cli_db:
        return pathlib.Path(cli_db).resolve()
    env_db = os.environ.get("LEGION_RADIO_DB", "").strip()
    if env_db:
        return pathlib.Path(env_db).resolve()
    return DEFAULT_DB_PATH


def fail(message: str, code: int = 1):
    print(f"[RADIO ERROR] {message}", file=sys.stderr)
    sys.exit(code)


def _open_connection(db_path: pathlib.Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=30.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000;")
    mode_row = conn.execute("PRAGMA journal_mode;").fetchone()
    current_mode = str(mode_row[0]).lower() if mode_row and mode_row[0] else ""
    if current_mode != "wal":
        conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn


def _tables_ready(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name IN ('meta', 'roster', 'messages');"
    ).fetchone()
    return bool(row and row[0] == 3)


def _ensure_schema_in_tx(conn: sqlite3.Connection):
    for stmt in SCHEMA_SQL:
        conn.execute(stmt)


def _ensure_ready(conn: sqlite3.Connection):
    if _tables_ready(conn):
        return
    conn.execute("BEGIN IMMEDIATE;")
    try:
        _ensure_schema_in_tx(conn)
        conn.execute("COMMIT;")
    except Exception:
        if conn.in_transaction:
            conn.execute("ROLLBACK;")
        raise


def _is_transient_lock_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return any(tok in msg for tok in ("locked", "busy", "protocol", "unable to open"))


def run_db_operation(db_path: pathlib.Path, operation, max_retries: int = 25):
    for attempt in range(max_retries + 1):
        conn = None
        try:
            conn = _open_connection(db_path)
            return operation(conn)
        except sqlite3.OperationalError as exc:
            if conn is not None:
                try:
                    if conn.in_transaction:
                        conn.execute("ROLLBACK;")
                except Exception:
                    pass
            if attempt < max_retries and _is_transient_lock_error(exc):
                backoff = random.uniform(0.015, 0.085) * min(attempt + 1, 6)
                time.sleep(backoff)
                continue
            raise
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass


def _get_mission(conn: sqlite3.Connection) -> str:
    row = conn.execute("SELECT value FROM meta WHERE key = 'mission';").fetchone()
    return str(row["value"]) if row else ""


def cmd_init(args, db_path: pathlib.Path):
    mission = (args.mission or "").strip()
    if not mission:
        fail("--mission must not be empty.")

    now_iso = utc_now_iso()

    def _op(conn: sqlite3.Connection):
        conn.execute("BEGIN IMMEDIATE;")
        try:
            _ensure_schema_in_tx(conn)
            if args.reset:
                conn.execute("DELETE FROM messages;")
                conn.execute("DELETE FROM roster;")
                conn.execute("DELETE FROM meta;")
                seq_tbl = conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'sqlite_sequence';"
                ).fetchone()
                if seq_tbl:
                    conn.execute("DELETE FROM sqlite_sequence WHERE name = 'messages';")

            conn.execute(
                """
                INSERT INTO meta (key, value) VALUES ('mission', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value;
                """,
                (mission,),
            )
            conn.execute(
                """
                INSERT INTO meta (key, value) VALUES ('initialized_at', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value;
                """,
                (now_iso,),
            )
            conn.execute("COMMIT;")
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK;")
            raise

        jmode_row = conn.execute("PRAGMA journal_mode;").fetchone()
        return str(jmode_row[0]).lower() if jmode_row else ""

    journal_mode = run_db_operation(db_path, _op)

    payload = {
        "status": "OK",
        "action": "init",
        "mission": mission,
        "reset": bool(args.reset),
        "journal_mode": journal_mode,
        "initialized_at": now_iso,
        "db": str(db_path),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            f"[RADIO INIT] Mission=\"{mission}\" "
            f"(reset={bool(args.reset)}, journal_mode={journal_mode}, db={db_path})"
        )


def cmd_roster_set(args, db_path: pathlib.Path):
    squad = (args.squad or "").strip()
    conv_id = (args.conv_id or "").strip()
    partition = (args.partition or "").strip()
    scope = (args.scope or "").strip()

    if squad not in VALID_SQUADS:
        fail(f"Invalid --squad '{squad}'. Valid squads: {', '.join(VALID_SQUADS)}")
    if not conv_id:
        fail("--conv-id must not be empty.")

    now_iso = utc_now_iso()

    def _op(conn: sqlite3.Connection):
        conn.execute("BEGIN IMMEDIATE;")
        try:
            if not _tables_ready(conn):
                _ensure_schema_in_tx(conn)
            conn.execute(
                """
                INSERT INTO roster (squad, conv_id, partition, scope, registered_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(squad) DO UPDATE SET
                    conv_id = excluded.conv_id,
                    partition = excluded.partition,
                    scope = excluded.scope,
                    registered_at = excluded.registered_at;
                """,
                (squad, conv_id, partition, scope, now_iso),
            )
            conn.execute("COMMIT;")
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK;")
            raise

    run_db_operation(db_path, _op)

    entry = {
        "status": "OK",
        "squad": squad,
        "conv_id": conv_id,
        "partition": partition,
        "scope": scope,
        "registered_at": now_iso,
    }
    if args.json:
        print(json.dumps(entry, ensure_ascii=False, indent=2))
    else:
        part_str = f" [{partition}]" if partition else ""
        scope_str = f" — {scope}" if scope else ""
        print(f"[RADIO ROSTER-SET] {squad}{part_str} -> conv_id={conv_id}{scope_str}")


def cmd_roster(args, db_path: pathlib.Path):
    def _op(conn: sqlite3.Connection):
        _ensure_ready(conn)
        mission = _get_mission(conn)
        rows = conn.execute(
            "SELECT squad, conv_id, partition, scope, registered_at FROM roster;"
        ).fetchall()
        items = [
            {
                "squad": r["squad"],
                "conv_id": r["conv_id"],
                "partition": r["partition"],
                "scope": r["scope"],
                "registered_at": r["registered_at"],
            }
            for r in rows
        ]
        items.sort(key=lambda x: (SQUAD_ORDER.get(x["squad"], 999), x["squad"]))
        return mission, items

    mission, items = run_db_operation(db_path, _op)

    if args.json:
        print(
            json.dumps(
                {"mission": mission, "count": len(items), "roster": items},
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    header_mission = f" (Mission: {mission})" if mission else ""
    print(f"[RADIO ROSTER]{header_mission} — {len(items)} active callsign(s):")
    if not items:
        print("  (no squads registered)")
        return
    for item in items:
        part_str = f" | partition={item['partition']}" if item["partition"] else ""
        scope_str = f" | scope={item['scope']}" if item["scope"] else ""
        print(
            f"  - {item['squad']}: conv_id={item['conv_id']}{part_str}{scope_str} "
            f"(at {item['registered_at']})"
        )


def cmd_post(args, db_path: pathlib.Path):
    sender = (args.sender or "").strip()
    recipient = (args.recipient or "ALL").strip()
    tag = (args.tag or "INTERFACE").strip()
    msg = args.msg if args.msg is not None else ""

    if sender not in VALID_SQUADS:
        fail(f"Invalid --from '{sender}'. Valid squads: {', '.join(VALID_SQUADS)}")
    if recipient not in VALID_RECIPIENTS:
        fail(f"Invalid --to '{recipient}'. Valid recipients: {', '.join(VALID_RECIPIENTS)}")
    if tag not in VALID_TAGS:
        fail(f"Invalid --tag '{tag}'. Valid tags: {', '.join(VALID_TAGS)}")
    if not msg.strip():
        fail("--msg must not be empty or whitespace-only.")
    if len(msg) > MAX_MSG_LENGTH:
        fail(
            f"Message length ({len(msg)} chars) exceeds MAX_MSG_LENGTH ({MAX_MSG_LENGTH} chars). "
            "Do NOT paste full source code into tactical radio; post concise interface signatures, "
            "schema summaries, decisions, and file paths only."
        )

    now_iso = utc_now_iso()

    def _op(conn: sqlite3.Connection):
        conn.execute("BEGIN IMMEDIATE;")
        try:
            if not _tables_ready(conn):
                _ensure_schema_in_tx(conn)
            cur = conn.execute(
                """
                INSERT INTO messages (sender, recipient, tag, body, created_at)
                VALUES (?, ?, ?, ?, ?);
                """,
                (sender, recipient, tag, msg, now_iso),
            )
            seq_id = int(cur.lastrowid)
            conn.execute("COMMIT;")
            return seq_id
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK;")
            raise

    seq = run_db_operation(db_path, _op)

    record = {
        "status": "OK",
        "seq": seq,
        "ref": f"#{seq}",
        "from": sender,
        "to": recipient,
        "tag": tag,
        "msg": msg,
        "created_at": now_iso,
    }
    if args.json:
        print(json.dumps(record, ensure_ascii=False, indent=2))
    else:
        print(f"[RADIO #{seq}] [{tag}] {sender} -> {recipient}: {msg}")


def cmd_read(args, db_path: pathlib.Path):
    since = args.since if args.since is not None else 0
    if since < 0:
        fail(f"--since must be >= 0 (got {since}).")

    recipient = args.recipient.strip() if args.recipient is not None else None
    if recipient is not None and recipient not in VALID_RECIPIENTS:
        fail(f"Invalid --to '{recipient}'. Valid recipients: {', '.join(VALID_RECIPIENTS)}")

    tag = args.tag.strip() if args.tag is not None else None
    if tag is not None and tag not in VALID_TAGS:
        fail(f"Invalid --tag '{tag}'. Valid tags: {', '.join(VALID_TAGS)}")

    limit = args.limit
    if limit is not None and limit <= 0:
        fail(f"--limit must be a positive integer > 0 (got {limit}).")

    def _op(conn: sqlite3.Connection):
        _ensure_ready(conn)
        mission = _get_mission(conn)

        clauses = ["seq > ?"]
        params = [since]

        if recipient is not None:
            if recipient == "ALL":
                clauses.append("recipient = 'ALL'")
            else:
                clauses.append("recipient IN (?, 'ALL')")
                params.append(recipient)

        if tag is not None:
            clauses.append("tag = ?")
            params.append(tag)

        where_sql = " AND ".join(clauses)
        limit_sql = ""
        if limit is not None:
            limit_sql = " LIMIT ?"
            params.append(limit)

        sql = (
            "SELECT seq, sender, recipient, tag, body, created_at "
            f"FROM messages WHERE {where_sql} ORDER BY seq ASC{limit_sql};"
        )
        rows = conn.execute(sql, params).fetchall()
        messages = [
            {
                "seq": int(r["seq"]),
                "ref": f"#{int(r['seq'])}",
                "from": r["sender"],
                "to": r["recipient"],
                "tag": r["tag"],
                "msg": r["body"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]
        return mission, messages

    mission, messages = run_db_operation(db_path, _op)
    last_seq = messages[-1]["seq"] if messages else since

    if args.json:
        print(
            json.dumps(
                {
                    "mission": mission,
                    "since": since,
                    "last_seq": last_seq,
                    "count": len(messages),
                    "messages": messages,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if not messages:
        print(f"[RADIO READ] No messages found (since #{since}).")
        return

    for m in messages:
        print(f"#{m['seq']} [{m['created_at']}] [{m['tag']}] {m['from']} -> {m['to']}: {m['msg']}")


def build_parser() -> RadioArgumentParser:
    common_sub = RadioArgumentParser(add_help=False)
    common_sub.add_argument(
        "--db",
        default=argparse.SUPPRESS,
        help="Override SQLite DB file path (default: .agents/state/legion_radio.db).",
    )
    common_sub.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Emit structured JSON output.",
    )

    parser = RadioArgumentParser(
        prog="legion_radio.py",
        description="Peer Tactical Radio & Shared Bulletin Board CLI for Octa-Ralph Agent Legion.",
    )
    parser.add_argument(
        "--db",
        default=None,
        help="Override SQLite DB file path (default: .agents/state/legion_radio.db).",
    )

    subparsers = parser.add_subparsers(dest="subcommand")

    p_init = subparsers.add_parser(
        "init",
        parents=[common_sub],
        help="Initialize tactical radio net and mission metadata.",
    )
    p_init.add_argument("--mission", required=True, help="Mission name / title.")
    p_init.add_argument(
        "--reset",
        action="store_true",
        help="Clear existing roster and messages and reset sequence to #1.",
    )

    p_roster_set = subparsers.add_parser(
        "roster-set",
        parents=[common_sub],
        help="Register or update an active squad callsign and conversationId.",
    )
    p_roster_set.add_argument(
        "--squad",
        required=True,
        help=f"Squad callsign ({', '.join(VALID_SQUADS)}).",
    )
    p_roster_set.add_argument(
        "--conv-id",
        required=True,
        dest="conv_id",
        help="Active subagent conversationId.",
    )
    p_roster_set.add_argument(
        "--partition",
        default="",
        help="Assigned partition ID (optional).",
    )
    p_roster_set.add_argument(
        "--scope",
        default="",
        help="Brief summary of owned files / responsibility (optional).",
    )

    subparsers.add_parser(
        "roster",
        parents=[common_sub],
        help="List registered active squad callsigns and conversationIds.",
    )

    p_post = subparsers.add_parser(
        "post",
        parents=[common_sub],
        help="Post a tactical message to the shared radio board and get atomic #seq.",
    )
    p_post.add_argument(
        "--from",
        required=True,
        dest="sender",
        help=f"Sender squad callsign ({', '.join(VALID_SQUADS)}).",
    )
    p_post.add_argument(
        "--to",
        default="ALL",
        dest="recipient",
        help=f"Recipient callsign ({', '.join(VALID_RECIPIENTS)}; default: ALL).",
    )
    p_post.add_argument(
        "--tag",
        default="INTERFACE",
        help=f"Message tag ({', '.join(VALID_TAGS)}; default: INTERFACE).",
    )
    p_post.add_argument(
        "--msg",
        required=True,
        help=f"Message body (max {MAX_MSG_LENGTH} chars; no full source code dumps).",
    )

    p_read = subparsers.add_parser(
        "read",
        parents=[common_sub],
        help="Read tactical messages incrementally by sequence, recipient, or tag.",
    )
    p_read.add_argument(
        "--since",
        type=int,
        default=0,
        help="Return messages with seq > since (default: 0).",
    )
    p_read.add_argument(
        "--to",
        default=None,
        dest="recipient",
        help="Filter for recipient (includes 'ALL' broadcasts when a squad is specified).",
    )
    p_read.add_argument(
        "--tag",
        default=None,
        help=f"Filter by tag ({', '.join(VALID_TAGS)}).",
    )
    p_read.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of messages to return.",
    )

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help(sys.stderr)
        sys.exit(1)

    db_path = resolve_db_path(getattr(args, "db", None))

    try:
        if args.subcommand == "init":
            cmd_init(args, db_path)
        elif args.subcommand == "roster-set":
            cmd_roster_set(args, db_path)
        elif args.subcommand == "roster":
            cmd_roster(args, db_path)
        elif args.subcommand == "post":
            cmd_post(args, db_path)
        elif args.subcommand == "read":
            cmd_read(args, db_path)
        else:
            fail(f"Unknown subcommand: {args.subcommand}")
    except sqlite3.Error as exc:
        fail(f"SQLite error on {db_path}: {exc}")


if __name__ == "__main__":
    main()
