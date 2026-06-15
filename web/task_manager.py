import threading
import time

from . import progress_adapter
from .paths import PROJECT_ROOT
# process 内部用相对路径（schoolid.json / progress.db），依赖 cwd —— app.py 启动时已 chdir 到项目根
import process

# task_id -> 任务状态字典（进程内，单 worker 模型）
_tasks = {}
_lock = threading.Lock()


def _make_task_id(cfg):
    return f"{cfg.province_id}_{cfg.want}_{cfg.year}_{cfg.rank}"


def _run_task(task_id, cfg):
    cancel_event = _tasks.get(task_id, {}).get('cancel_event') or threading.Event()

    def on_progress(info):
        with _lock:
            cur = _tasks.get(task_id)
            if cur:
                cur['progress'] = info
                cur['last_update'] = time.time()

    try:
        result = process.process(
            province_id=cfg.province_id,
            want=cfg.want,
            year=cfg.year,
            thread_num=cfg.thread_num,
            ethnic_minority=cfg.ethnic_minority,
            output=True,
            rank=cfg.rank,
            on_progress=on_progress,
            cancel_event=cancel_event,
            output_dir=PROJECT_ROOT,
        )
        with _lock:
            cur = _tasks.get(task_id)
            if cur:
                cur['status'] = 'done'
                cur['message'] = result if isinstance(result, str) else None
                p = cur.get('progress') or {}
                p['status'] = 'done'
                cur['progress'] = p
                cur['last_update'] = time.time()
    except process.TaskCancelled:
        with _lock:
            cur = _tasks.get(task_id)
            if cur:
                if cur.get('cancel_intent') == 'cancel':
                    cur['status'] = 'cancelled'
                    # 线程已退出，安全删除续传记录（避免与 _persist_progress 竞争）
                    try:
                        progress_adapter.delete_resume(task_id)
                    except Exception:
                        pass
                else:
                    cur['status'] = 'paused'
                cur['last_update'] = time.time()
    except Exception as e:
        with _lock:
            cur = _tasks.get(task_id)
            if cur:
                cur['status'] = 'error'
                cur['error'] = str(e)
                cur['last_update'] = time.time()


def start_task(cfg):
    """启动（或恢复）一个抓取任务。process 内部会自动读 progress.db 续传。

    返回 (task_id, started)。started=False 表示同任务已在运行。
    """
    task_id = _make_task_id(cfg)
    with _lock:
        existing = _tasks.get(task_id)
        if existing and existing['status'] in ('running', 'pending', 'pausing', 'cancelling'):
            return task_id, False
        cancel_event = threading.Event()
        _tasks[task_id] = {
            'task_id': task_id,
            'status': 'running',
            'cfg': cfg,
            'cancel_event': cancel_event,
            'cancel_intent': None,
            'progress': {'status': 'pending', 'processed': 0, 'total': 0, 'matched': 0,
                         'school': None, 'remaining_sec': None},
            'message': None,
            'error': None,
            'last_update': time.time(),
        }
    thread = threading.Thread(target=_run_task, args=(task_id, cfg), daemon=True)
    with _lock:
        if task_id in _tasks:
            _tasks[task_id]['thread'] = thread
    thread.start()
    return task_id, True


def pause_task(task_id):
    with _lock:
        t = _tasks.get(task_id)
        if t and t['status'] == 'running':
            t['cancel_intent'] = 'pause'
            t['cancel_event'].set()
            t['status'] = 'pausing'
            return True
    return False


def cancel_task(task_id):
    with _lock:
        t = _tasks.get(task_id)
        if t and t['status'] in ('running', 'paused', 'pausing'):
            t['cancel_intent'] = 'cancel'
            t['cancel_event'].set()
            t['status'] = 'cancelling'
            return True
    return False


def get_progress(task_id):
    with _lock:
        t = _tasks.get(task_id)
        if not t:
            return None
        p = t.get('progress') or {}
        return {
            'task_id': task_id,
            'status': t['status'],
            'phase': p.get('status'),
            'processed': p.get('processed', 0),
            'total': p.get('total', 0),
            'matched': p.get('matched', 0),
            'school': p.get('school'),
            'remaining_sec': p.get('remaining_sec'),
            'message': t.get('message'),
            'error': t.get('error'),
            'last_update': t.get('last_update'),
        }


def list_tasks():
    with _lock:
        ids = list(_tasks.keys())
    return [get_progress(tid) for tid in ids]


def get_result(task_id):
    """done 时从结果文件读取（process output=True 已落盘 {year}_{want}_学校分数排行.json）。"""
    with _lock:
        t = _tasks.get(task_id)
        if not t:
            return None, 'not_found'
        status = t['status']
        cfg = t['cfg']
    if status != 'done':
        return None, status
    from .results_repo import read_result
    fname = f"{cfg.year}_{cfg.want}_学校分数排行.json"
    try:
        return read_result(fname), 'done'
    except FileNotFoundError:
        return [], 'done'
