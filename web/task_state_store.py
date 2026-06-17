"""任务级状态持久化层（task_state 表）。

与 progress 表（断点续传，process.py 每校写一次）职责分离：
task_state 只在 task_manager 的状态转移点写（start/pause/cancel/done/error），
存任务级 status + 完整 TaskConfig，用于服务端重启后识别"曾运行"的任务。

与 progress_adapter 一样建在同一个 progress.db 内，共享 WAL；本模块用独立的
模块级 `_lock`，且**不嵌套调用 progress_adapter**（后者有自己的 _lock），避免死锁。
"""
import json
import sqlite3
import threading
import time

from .paths import PROGRESS_DB

# 模块级锁，保护 task_state 的读-改-写。与 progress_adapter._lock 不交叉。
_lock = threading.Lock()


def _conn():
    conn = sqlite3.connect(PROGRESS_DB, check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL')
    return conn


def _ensure_table(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS task_state
        (task_id TEXT PRIMARY KEY,
         status TEXT NOT NULL,
         cfg TEXT NOT NULL,
         last_update REAL NOT NULL,
         created_at REAL NOT NULL)''')


def upsert(task_id, status, cfg_obj, now=None):
    """插入或覆盖一条任务状态。cfg_obj 为 TaskConfig 实例（或 dict）。"""
    now = time.time() if now is None else now
    cfg_json = json.dumps(_cfg_to_dict(cfg_obj), ensure_ascii=False)
    with _lock:
        conn = _conn()
        try:
            _ensure_table(conn)
            conn.execute(
                '''INSERT INTO task_state (task_id, status, cfg, last_update, created_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(task_id) DO UPDATE SET
                     status=excluded.status,
                     cfg=excluded.cfg,
                     last_update=excluded.last_update''',
                (task_id, status, cfg_json, now, now))
            conn.commit()
        finally:
            conn.close()


def update_status(task_id, status, now=None):
    """只更新 status 与 last_update（不重写 cfg）。"""
    now = time.time() if now is None else now
    with _lock:
        conn = _conn()
        try:
            _ensure_table(conn)
            conn.execute(
                'UPDATE task_state SET status=?, last_update=? WHERE task_id=?',
                (status, now, task_id))
            conn.commit()
        finally:
            conn.close()


def get(task_id):
    """返回 {task_id, status, cfg(dict), last_update, created_at} 或 None。"""
    with _lock:
        conn = _conn()
        try:
            _ensure_table(conn)
            cur = conn.execute(
                'SELECT task_id, status, cfg, last_update, created_at FROM task_state WHERE task_id=?',
                (task_id,))
            row = cur.fetchone()
        finally:
            conn.close()
    if not row:
        return None
    return _row_to_dict(row)


def list_all():
    """返回全部记录，按 last_update 倒序。"""
    with _lock:
        conn = _conn()
        try:
            _ensure_table(conn)
            cur = conn.execute(
                'SELECT task_id, status, cfg, last_update, created_at FROM task_state '
                'ORDER BY last_update DESC')
            rows = cur.fetchall()
        finally:
            conn.close()
    return [_row_to_dict(r) for r in rows]


def list_by_status(statuses):
    """按 status 集合过滤（用于启动重建）。"""
    with _lock:
        conn = _conn()
        try:
            _ensure_table(conn)
            placeholders = ','.join('?' * len(statuses))
            cur = conn.execute(
                f'SELECT task_id, status, cfg, last_update, created_at FROM task_state '
                f'WHERE status IN ({placeholders}) ORDER BY last_update DESC',
                list(statuses))
            rows = cur.fetchall()
        finally:
            conn.close()
    return [_row_to_dict(r) for r in rows]


def delete(task_id):
    with _lock:
        conn = _conn()
        try:
            _ensure_table(conn)
            conn.execute('DELETE FROM task_state WHERE task_id=?', (task_id,))
            conn.commit()
        finally:
            conn.close()


def cleanup_old(before_ts, statuses):
    """删除 last_update 早于 before_ts 且 status ∈ statuses 的记录（done/cancelled 7 天清理）。"""
    with _lock:
        conn = _conn()
        try:
            _ensure_table(conn)
            placeholders = ','.join('?' * len(statuses))
            conn.execute(
                f'DELETE FROM task_state WHERE last_update < ? AND status IN ({placeholders})',
                [before_ts, *statuses])
            conn.commit()
        finally:
            conn.close()


def _cfg_to_dict(cfg_obj):
    """兼容 pydantic v2 model_dump / v1 dict / 已是 dict 三种情况。"""
    if isinstance(cfg_obj, dict):
        return cfg_obj
    dump = getattr(cfg_obj, 'model_dump', None)
    if callable(dump):
        return dump()
    dump = getattr(cfg_obj, 'dict', None)
    if callable(dump):
        return dump()
    return cfg_obj


def _row_to_dict(row):
    task_id, status, cfg_json, last_update, created_at = row
    try:
        cfg = json.loads(cfg_json) if cfg_json else {}
    except (ValueError, TypeError):
        cfg = {}
    return {
        'task_id': task_id,
        'status': status,
        'cfg': cfg,
        'last_update': last_update,
        'created_at': created_at,
    }
