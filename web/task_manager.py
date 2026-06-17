import threading
import time

from . import progress_adapter
from . import task_state_store
from .paths import PROJECT_ROOT
# process 内部用相对路径（schoolid.json / progress.db），依赖 cwd —— app.py 启动时已 chdir 到项目根
import process

# task_id -> 任务状态字典（进程内，单 worker 模型）
_tasks = {}
_lock = threading.Lock()

# 运行类状态：重启后这些状态背后的线程已死，需重建为 interrupted
_RUNNING_LIKE = ('running', 'pausing', 'cancelling')
# 终态：进入后不再变化，前端不自动接管
_TERMINAL = ('done', 'cancelled', 'error')
# 可续传态：前端可显示"恢复"按钮
_RESUMABLE = ('paused', 'interrupted')
# done/cancelled 记录保留 7 天后清理
_RETENTION_SEC = 7 * 24 * 3600


def _make_task_id(cfg):
    return f"{cfg.province_id}_{cfg.want}_{cfg.year}_{cfg.rank}"


# ---------------------------------------------------------------------------
# 持久化辅助
# ---------------------------------------------------------------------------

def _persist_state(task_id, status=None):
    """把当前任务状态落盘到 task_state 表。

    status 为 None 时用 _tasks 内当前 status。失败仅打印，不影响任务运行。
    """
    try:
        with _lock:
            t = _tasks.get(task_id)
            if not t:
                return
            s = status or t['status']
            cfg = t['cfg']
        task_state_store.upsert(task_id, s, cfg)
    except Exception as e:
        print(f"[task_state] 落盘失败（忽略，不影响运行）: {e}")


def restore_on_startup():
    """服务启动时重建 _tasks：把曾运行的任务识别为可恢复态。

    由 app.py 的 lifespan startup 调用（不放在 import 时，避免 --reload 重复执行）。
    任何异常都只打印警告，绝不阻塞启动。
    """
    restored = 0
    try:
        # 1) 清理过期终态记录
        try:
            task_state_store.cleanup_old(time.time() - _RETENTION_SEC, ('done', 'cancelled'))
        except Exception as e:
            print(f"[task_state] 清理过期记录失败（忽略）: {e}")

        # 2) 重建：running 类 → interrupted；paused 保留；终态跳过
        all_states = task_state_store.list_all()
        for rec in all_states:
            task_id = rec['task_id']
            status = rec['status']
            cfg_dict = rec.get('cfg') or {}
            if status in _RUNNING_LIKE:
                new_status = 'interrupted'
            elif status == 'paused':
                new_status = 'paused'
            else:
                # 终态：不进 _tasks（历史/结果页处理）
                continue
            try:
                cfg = _cfg_from_dict(cfg_dict)
            except Exception as e:
                print(f"[task_state] 跳过 {task_id}：cfg 反序列化失败 {e}")
                continue
            # 落盘回写为最终态
            try:
                task_state_store.update_status(task_id, new_status)
            except Exception as e:
                print(f"[task_state] 回写 {task_id} 状态失败（忽略）: {e}")
            with _lock:
                _tasks[task_id] = {
                    'task_id': task_id,
                    'status': new_status,
                    'cfg': cfg,
                    'cancel_event': threading.Event(),
                    'cancel_intent': None,
                    'progress': None,  # interrupted/paused 态无实时进度，get_progress 时从 progress 表补
                    'message': None,
                    'error': None,
                    'last_update': rec.get('last_update') or time.time(),
                }
            restored += 1
    except Exception as e:
        print(f"[task_state] 启动重建失败（忽略，将无法恢复历史任务）: {e}")
    if restored:
        print(f"[task_state] 已恢复 {restored} 个可续传任务（请在 Web 界面点「恢复」继续）")
    return restored


def _cfg_from_dict(cfg_dict):
    """从落盘 dict 还原 TaskConfig 实例。"""
    from .schemas import TaskConfig
    return TaskConfig(**cfg_dict)


# ---------------------------------------------------------------------------
# 任务执行
# ---------------------------------------------------------------------------

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
        _persist_state(task_id, 'done')
    except process.TaskCancelled:
        final_status = None
        with _lock:
            cur = _tasks.get(task_id)
            if cur:
                if cur.get('cancel_intent') == 'cancel':
                    cur['status'] = 'cancelled'
                    final_status = 'cancelled'
                    # 线程已退出，安全删除续传记录（避免与 _persist_progress 竞争）
                    try:
                        progress_adapter.delete_resume(task_id)
                    except Exception:
                        pass
                else:
                    cur['status'] = 'paused'
                    final_status = 'paused'
                cur['last_update'] = time.time()
        # 落盘：paused 保留记录（可续传）；cancelled 删除 task_state（与 progress 表双删对称）
        if final_status == 'paused':
            _persist_state(task_id, 'paused')
        elif final_status == 'cancelled':
            try:
                task_state_store.delete(task_id)
            except Exception as e:
                print(f"[task_state] 删除 cancelled 记录失败（忽略）: {e}")
    except Exception as e:
        with _lock:
            cur = _tasks.get(task_id)
            if cur:
                cur['status'] = 'error'
                cur['error'] = str(e)
                cur['last_update'] = time.time()
        _persist_state(task_id, 'error')


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
    # 起线程前先落盘 running，确保崩溃窗口内也能识别
    _persist_state(task_id, 'running')
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
            t['last_update'] = time.time()
        else:
            return False
    # 落盘 pausing：覆盖"已 set event 但线程尚未退出"的崩溃窗口
    _persist_state(task_id, 'pausing')
    return True


def cancel_task(task_id):
    with _lock:
        t = _tasks.get(task_id)
        if t and t['status'] in ('running', 'paused', 'pausing'):
            t['cancel_intent'] = 'cancel'
            t['cancel_event'].set()
            t['status'] = 'cancelling'
            t['last_update'] = time.time()
        else:
            return False
    _persist_state(task_id, 'cancelling')
    return True


def get_progress(task_id):
    with _lock:
        t = _tasks.get(task_id)
        if not t:
            return None
        status = t['status']
        cfg = t['cfg']
        p = t.get('progress') or {}
        last_update = t.get('last_update')
        message = t.get('message')
        error = t.get('error')

    # interrupted/paused 重建态无实时 progress，从 progress 表补 processed
    if p or status not in _RESUMABLE:
        processed = p.get('processed', 0)
        total = p.get('total', 0)
        matched = p.get('matched', 0)
        school = p.get('school')
        remaining_sec = p.get('remaining_sec')
        phase = p.get('status')
    else:
        processed = total = matched = 0
        school = None
        remaining_sec = None
        phase = status
        try:
            resume = progress_adapter.get_resume(task_id)
            if resume:
                processed = resume.get('processed_count', 0)
                matched = resume.get('results_count', 0)
        except Exception:
            pass

    return {
        'task_id': task_id,
        'status': status,
        'phase': phase,
        'processed': processed,
        'total': total,
        'matched': matched,
        'school': school,
        'remaining_sec': remaining_sec,
        'message': message,
        'error': error,
        'cfg': _cfg_to_plain(cfg),
        'is_resumable': status in _RESUMABLE,
        'last_update': last_update,
    }


def list_tasks(include_finished=False):
    """列出进程内任务（含 interrupted/paused）。

    include_finished=True 时额外合并 task_state 表里的 done/error 历史记录。
    每项含 cfg + is_resumable + last_update，前端据此自动接管或显示恢复按钮。
    """
    with _lock:
        ids = list(_tasks.keys())
    items = [p for p in (get_progress(tid) for tid in ids) if p]
    if include_finished:
        try:
            for rec in task_state_store.list_all():
                tid = rec['task_id']
                if tid in ids:
                    continue
                items.append({
                    'task_id': tid,
                    'status': rec['status'],
                    'phase': rec['status'],
                    'processed': 0,
                    'total': 0,
                    'matched': 0,
                    'school': None,
                    'remaining_sec': None,
                    'message': None,
                    'error': None,
                    'cfg': rec.get('cfg') or {},
                    'is_resumable': rec['status'] in _RESUMABLE,
                    'last_update': rec.get('last_update'),
                })
        except Exception as e:
            print(f"[task_state] 合并历史记录失败（忽略）: {e}")
    # 按最后更新时间倒序
    items.sort(key=lambda x: x.get('last_update') or 0, reverse=True)
    return items


def _cfg_to_plain(cfg):
    """TaskConfig → dict（用于响应体）。"""
    if isinstance(cfg, dict):
        return cfg
    dump = getattr(cfg, 'model_dump', None)
    if callable(dump):
        return dump()
    dump = getattr(cfg, 'dict', None)
    if callable(dump):
        return dump()
    return cfg


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
