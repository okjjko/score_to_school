from fastapi import APIRouter, HTTPException

import guess
from ..schemas import PredictReq

router = APIRouter(prefix='/predict')


@router.post('')
def predict(req: PredictReq):
    try:
        # JSON 对象的键为字符串，这里转为 {年份(int): 数值(float)}
        history = {int(k): float(v) for k, v in req.history.items()}
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail='history 的键须为年份、值须为数字')
    if len(history) < 2:
        raise HTTPException(status_code=400, detail='至少需要 2 个历史数据点')
    return guess.predict(history, req.target_year)
