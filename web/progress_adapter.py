import sqlite3
import json
import threading
from .paths import PROGRESS_DB

# 保护 progress.db 的读-改-写复合操作（后台抓取线程与 resume 查询并发）
_lock = threading.Lock()


def _conn():
    conn = sqlite3.connect(PROGRESS_DB, check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL')
    return conn


def _ensure_table(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS progress
        (task_id TEXT PRIMARY KEY, province_id TEXT, want TEXT, year INTEGER,
         rank INTEGER, processed_schools TEXT, results TEXT)''')


def list_resumable():
    with _lock:
        conn = _conn()
        try:
            _ensure_table(conn)
            cur = conn.execute(
                'SELECT task_id, province_id, want, year, rank, processed_schools, results FROM progress')
            rows = cur.fetchall()
        finally:
            conn.close()
    items = []
    for task_id, prov, want, year, rank, ps, res in rows:
        processed = json.loads(ps) if ps else []
        results = json.loads(res) if res else []
        items.append({
            'task_id': task_id,
            'province_id': prov,
            'want': want,
            'year': year,
            'rank': rank,
            'processed_count': len(processed),
            'results_count': len(results),
        })
    return items


def get_resume(task_id):
    with _lock:
        conn = _conn()
        try:
            _ensure_table(conn)
            cur = conn.execute(
                'SELECT task_id, province_id, want, year, rank, processed_schools, results '
                'FROM progress WHERE task_id = ?', (task_id,))
            row = cur.fetchone()
        finally:
            conn.close()
    if not row:
        return None
    task_id, prov, want, year, rank, ps, res = row
    processed = json.loads(ps) if ps else []
    results = json.loads(res) if res else []
    return {
        'task_id': task_id,
        'province_id': prov,
        'want': want,
        'year': year,
        'rank': rank,
        'processed_count': len(processed),
        'results_count': len(results),
    }


def delete_resume(task_id):
    with _lock:
        conn = _conn()
        try:
            _ensure_table(conn)
            conn.execute('DELETE FROM progress WHERE task_id = ?', (task_id,))
            conn.commit()
        finally:
            conn.close()
