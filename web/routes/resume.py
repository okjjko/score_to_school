from fastapi import APIRouter, HTTPException

from .. import progress_adapter

router = APIRouter(prefix='/resume')


@router.get('')
def list_resume():
    return progress_adapter.list_resumable()


@router.get('/{task_id}')
def get_resume(task_id: str):
    item = progress_adapter.get_resume(task_id)
    if not item:
        raise HTTPException(status_code=404, detail='无此续传记录')
    return item


@router.delete('/{task_id}')
def delete_resume(task_id: str):
    progress_adapter.delete_resume(task_id)
    return {'ok': True}
