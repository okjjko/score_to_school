import os
import sys
from contextlib import asynccontextmanager

# Windows 控制台默认 GBK，强制 stdout/stderr 用 utf-8，避免 print 中文/符号时 UnicodeEncodeError
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 计算项目根（本文件位于 web/app.py），加入 sys.path。
# 这样无论「python app.py」直接运行，还是「python -m uvicorn web.app:app」，都能 import web 包。
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 用绝对导入（web.xxx），兼容直接运行脚本（相对导入在 __main__ 下会失败）
from web.paths import PROJECT_ROOT

# 兜底：让 process.py 内部的相对路径（schoolid.json / progress.db）在任意 cwd 启动下都能工作
os.chdir(PROJECT_ROOT)

from web import task_manager
from web.routes import config as config_routes
from web.routes import task as task_routes
from web.routes import resume as resume_routes
from web.routes import predict as predict_routes
from web.routes import results as results_routes


@asynccontextmanager
async def lifespan(app):
    # 启动时把落盘的"曾运行"任务重建进进程内字典，标记为可恢复态
    try:
        task_manager.restore_on_startup()
    except Exception as e:
        print(f'[task_state] 启动重建异常（忽略）: {e}')
    yield


app = FastAPI(title='score_to_school API', version='1.0.0', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/api/health')
def health():
    return {'ok': True}


app.include_router(config_routes.router, prefix='/api')
app.include_router(task_routes.router, prefix='/api')
app.include_router(resume_routes.router, prefix='/api')
app.include_router(predict_routes.router, prefix='/api')
app.include_router(results_routes.router, prefix='/api')

print('=' * 64)
print('score_to_school API 已启动')
print('直接运行：python app.py      |   生产推荐：python -m uvicorn web.app:app --port 8000')
print('[注意] 务必单 worker：任务字典保存在进程内，多 worker 会状态分裂。')
print('=' * 64)


# 支持直接 `python app.py` 启动（开发用，不支持 --reload）
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
