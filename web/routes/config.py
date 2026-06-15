from fastapi import APIRouter

from .. import config_io, meta
from ..schemas import TaskConfig

router = APIRouter()


@router.get('/config')
def get_config():
    return config_io.read_config()


@router.put('/config')
def put_config(cfg: TaskConfig):
    return config_io.write_config(cfg.model_dump())


@router.get('/meta/provinces')
def get_provinces():
    return meta.list_provinces()


@router.get('/meta/schools-count')
def get_schools_count():
    return meta.schools_count()
