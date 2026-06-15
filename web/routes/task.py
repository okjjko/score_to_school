from fastapi import APIRouter, HTTPException

from .. import task_manager
from ..schemas import TaskConfig

router = APIRouter(prefix='/task')


@router.post('/start')
def start(cfg: TaskConfig):
    task_id, started = task_manager.start_task(cfg)
    if not started:
        raise HTTPException(status_code=409, detail='同名任务正在运行')
    return {'task_id': task_id, 'status': 'running'}


@router.get('/{task_id}/progress')
def progress(task_id: str):
    p = task_manager.get_progress(task_id)
    if not p:
        raise HTTPException(status_code=404, detail='任务不存在（进程可能已重启，请到「历史」页恢复）')
    return p


@router.post('/{task_id}/pause')
def pause(task_id: str):
    return {'ok': task_manager.pause_task(task_id)}


@router.post('/{task_id}/cancel')
def cancel(task_id: str):
    return {'ok': task_manager.cancel_task(task_id)}


@router.get('/{task_id}/result')
def result(task_id: str):
    data, status = task_manager.get_result(task_id)
    if status == 'not_found':
        raise HTTPException(status_code=404, detail='任务不存在')
    if status != 'done':
        raise HTTPException(status_code=409, detail=f'任务尚未完成，当前状态：{status}')
    return data
