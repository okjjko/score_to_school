# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

从「掌上高考」平台抓取全国高校在指定省份、年份、专业的录取分数数据，根据用户排名筛选匹配的学校，并以 JSON 格式输出排行结果。

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 运行主程序（从 config.json 读取配置）
python main.py

# 预测分数（修改 guess.py 中的历史数据后执行）
python guess.py
```

## 项目架构

```
main.py                    # 入口：读取 config.json，调用 process()
process.py                 # 核心编排：遍历所有学校，获取分数，过滤匹配，含断点续传
Get_informations/
  GetScore.py              # 获取单个学校在指定省份+年份的分数数据（带 SQLite 缓存）
  Getpage.py               # 底层 HTTP 请求封装（调用 api.zjzw.cn）
  Get_province_id.py       # 省份名称 → ID 解析
  Get_school_id.py         # 从 schoolid.json 加载学校列表
guess.py                   # 一元线性回归工具，根据历史年份数据预测下一年分数
```

### 数据流

1. `main.py` 读取 `config.json`（province_id, want, year, rank, thread_num 等）
2. `process.py` 将省份名转为数字 ID，加载全部学校列表（约 2000+ 所学校）
3. 跳过含「学院」「职业」的学校，顺序遍历剩余学校，调用 API 获取每个学校的专业录取数据
4. 对每个专业，匹配专业名称（包含 `want` 关键字）、排除专项计划（除非 `ethnic_minority=true`）、筛选排名与用户排名差距 <3000
5. 匹配结果按学校聚合，最终输出 JSON 文件

### 数据库

| 文件 | 用途 |
|------|------|
| `score.db` | 缓存 API 响应，按 (schoolId, provinceId, year) 去重，避免重复请求 |
| `progress.db` | 断点续传，记录已处理的学校列表和中间结果，中断后可恢复 |

### 反爬策略

- 每处理 10 所学校暂停 30 秒
- 每次请求间随机延迟 0.1-0.3 秒
- 请求异常时等待 10 分钟后重试（不更新进度，保持可恢复状态）
- User-Agent 伪装为百度爬虫

### API 依赖

项目依赖以下公开 API（详见 `apis.md`）：
- **专业分数 API**: `https://api.zjzw.cn/web/api/` (参数: uri=apidata/api/gk/score/special, school_id, year, local_province_id, page)
- **省份配置**: `https://static-data.gaokao.cn/www/2.0/config/81004.json`
- **学校代码**: `https://static-data.gaokao.cn/www/2.0/school/school_code.json`

### 输出格式

```json
[
  {
    "学校名称": [
      {"专业名称": {"min": "最低分", "min_section": "最低位次"}}
    ]
  }
]
```

## Web 界面（Vue 3 + FastAPI）

除命令行外，项目提供完整 Web 界面，设计风格遵循 Anthropic Claude 设计系统（暖奶油画布 `#faf9f5` + 珊瑚色主 CTA `#cc785c` + Cormorant Garamond/Noto Serif SC 衬线标题）。

### 启动

```bash
# 1) 后端（必须在项目根目录运行，单 worker）
python -m uvicorn web.app:app --port 8000
#    注意：用 `python -m uvicorn` 而非 `uvicorn`，确保用装了依赖的 Python 环境；
#    多 worker 会让任务状态分裂（任务字典在进程内）。

# 2) 前端（另开终端）
cd frontend
npm install
npm run dev   # http://localhost:5173 ，自动代理 /api -> :8000
```

### 架构

```
web/                        # FastAPI 后端，复用现有 Python 逻辑
  app.py                    # FastAPI 入口：CORS、路由注册、chdir 到项目根、单 worker 警告
  task_manager.py           # 任务字典 + 后台线程 + cancel_event + 暂停/取消状态机
  config_io.py              # config.json 读写
  progress_adapter.py       # progress.db 读写（断点续传列表/删除）
  results_repo.py           # 扫描 *_学校分数排行.json、读单文件（路径白名单防穿越）
  meta.py                   # 31 省 ID↔名称、学校数统计
  routes/                   # /api/config /api/task/* /api/resume /api/results /api/predict
frontend/                   # Vue 3 + Vite + Pinia + Vue Router + Tailwind + ECharts
  src/styles/{tokens,fonts,base}.css   # 设计 token → CSS 变量（样式唯一源头）
  src/components/ui/        # CButton/CCard/DarkSurface/CInput/CSelect/CBadge/CTabs/CProgress/CSwitch
  src/views/                # ConfigScrape（配置+实时进度）/ Results / Predict / History
```

### 任务模型

抓取单次可运行数小时（反爬限速 + 风控），HTTP 同步必超时。因此采用「任务后台化 + 轮询」：

- `POST /api/task/start` → 起后台线程跑改造后的 `process(on_progress, cancel_event)`，立即返回 `task_id`
- 前端每 2 秒轮询 `GET /api/task/{id}/progress`，含 `status`（任务级）、`phase`（子阶段 running/sleeping/retry）、processed/total、matched、当前学校、剩余秒
- 暂停：设 `cancel_event` → 线程在可中断 sleep 的下个检查点抛 `TaskCancelled` → 状态置 `paused`（progress.db 记录保留）
- 取消：同上但删除 progress.db 记录
- 恢复：`/history` 选续传项 → 写回 config.json → 配置页点「开始抓取」，`process` 自动读 progress.db 续传

### 对核心文件的改造（保留 CLI 向后兼容）

- `process.py`：`process()` 新增可选参数 `on_progress`（进度回调）、`cancel_event`（取消信号）、`output_dir`；新增 `_interruptible_sleep`（每秒检查取消，替代 30s/600s 的硬 sleep）；定义 `TaskCancelled` 异常。不传新参数时行为与原 CLI 完全一致。
- `guess.py`：抽出 `predict(history, want_year)` 函数，返回回归参数 + 散点/拟合线坐标，供 `/api/predict` 绘图；`__main__` 保留脚本式用法。
- `Get_informations/GetScore.py`：模块级全局 sqlite 连接改为函数内局部连接（多线程必需，否则子线程首调即报 `check_same_thread`）。
- `Get_informations/Getpage.py`：修复风控时 `data` 未定义的 `UnboundLocalError`，改为抛明确的 `RateLimitError`，由上层 `process` 的 except 捕获后重试。

