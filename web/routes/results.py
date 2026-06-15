from fastapi import APIRouter, HTTPException

from .. import results_repo

router = APIRouter(prefix='/results')


@router.get('')
def list_results():
    return results_repo.list_results()


@router.get('/{file:path}')
def get_result(file: str):
    try:
        return results_repo.read_result(file)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='结果文件不存在')
