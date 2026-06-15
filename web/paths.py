import os

# 项目根目录（web/ 的上一级）。process.py 内部用相对路径读 schoolid.json / 写 progress.db，
# 因此 uvicorn 必须在项目根目录启动 —— app.py 启动时会 os.chdir 到这里兜底。
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'config.json')
SCHOOLID_PATH = os.path.join(PROJECT_ROOT, 'schoolid.json')
PROGRESS_DB = os.path.join(PROJECT_ROOT, 'progress.db')
SCORE_DB = os.path.join(PROJECT_ROOT, 'score.db')
