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
