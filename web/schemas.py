from typing import List, Optional
from pydantic import BaseModel, Field


class TaskConfig(BaseModel):
    """任务参数 —— 与 config.json 字段一一对应。"""
    province_id: int = Field(..., description="省份ID")
    rank: int = Field(..., ge=0, description="用户高考位次")
    want: str = Field(..., description="专业关键字（模糊匹配 spname）")
    year: int = Field(..., description="目标年份")
    ethnic_minority: bool = False
    output: str = "json"
    subject: List[str] = Field(default_factory=list)
    thread_num: int = 2


class PredictReq(BaseModel):
    history: dict = Field(..., description="{年份: 分数/位次}")
    target_year: int = Field(..., description="预测目标年份")


class Province(BaseModel):
    id: int
    name: str


class SchoolsCount(BaseModel):
    total: int
    usable: int


class ResultFile(BaseModel):
    file: str
    want: str
    year: str
    size_kb: float
    mtime: int


class ResumeItem(BaseModel):
    task_id: str
    province_id: str
    want: str
    year: int
    rank: int
    processed_count: int
    results_count: int


class TaskSummary(BaseModel):
    """任务摘要 —— GET /api/task 返回项（也复用于 progress 响应）。"""
    task_id: str
    status: str
    phase: Optional[str] = None
    processed: int = 0
    total: int = 0
    matched: int = 0
    school: Optional[str] = None
    remaining_sec: Optional[float] = None
    message: Optional[str] = None
    error: Optional[str] = None
    cfg: Optional[TaskConfig] = None
    is_resumable: bool = False
    last_update: Optional[float] = None
