import json
import os
import random
import time
import sqlite3
import Get_informations.GetScore as GetScore
import Get_informations.Get_province_id as Get_Province_Id
import Get_informations.Get_school_id as Get_School_Id


class TaskCancelled(Exception):
    """任务被外部取消（cancel_event 被设置）时抛出。"""
    pass


def _interruptible_sleep(seconds, cancel_event=None, tick=None):
    """可中断的 sleep。

    每秒检查一次 cancel_event，若已设置则抛出 TaskCancelled。
    tick(remaining_sec) 在每个检查周期被调用一次，用于向调用方报告剩余秒数。
    """
    remaining = float(seconds)
    while remaining > 0:
        if cancel_event is not None and cancel_event.is_set():
            raise TaskCancelled("任务被取消")
        step = min(1.0, remaining)
        if tick is not None:
            tick(round(remaining))
        time.sleep(step)
        remaining -= step


# 创建或连接到进度数据库
def init_progress_db():
    conn = sqlite3.connect('progress.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS progress
                     (task_id TEXT PRIMARY KEY,
                      province_id TEXT,
                      want TEXT,
                      year INTEGER,
                      rank INTEGER,
                      processed_schools TEXT,
                      results TEXT)''')
    conn.commit()
    return conn


def _persist_progress(progress_cursor, progress_conn, task_id, province_id, want, year, rank,
                      processed_schools, results):
    """将当前进度落盘（每处理一所学校后调用）。"""
    progress_cursor.execute('''INSERT OR REPLACE INTO progress
                            (task_id, province_id, want, year, rank, processed_schools, results)
                            VALUES (?, ?, ?, ?, ?, ?, ?)''',
                            (task_id, province_id, want, year, rank,
                             json.dumps(list(processed_schools), ensure_ascii=False),
                             json.dumps(results, ensure_ascii=False)))
    progress_conn.commit()


# 主处理函数
# 新增可选参数（向后兼容，CLI 调用不传时行为与原版完全一致）：
#   on_progress   : 进度回调 Callable[[dict], None]，每轮循环/sleep 时被调用
#   cancel_event  : threading.Event，被设置时在下一个检查点抛出 TaskCancelled
#   output_dir    : 结果文件输出目录，默认 os.getcwd()
def process(province_id, want, year, thread_num, ethnic_minority, output, rank,
            on_progress=None, cancel_event=None, output_dir=None):
    # 初始化进度数据库
    progress_conn = init_progress_db()
    progress_cursor = progress_conn.cursor()

    # 创建任务ID
    task_id = f"{province_id}_{want}_{year}_{rank}"

    # 检查是否有之前的进度
    progress_cursor.execute('''SELECT processed_schools, results FROM progress WHERE task_id = ?''', (task_id,))
    result = progress_cursor.fetchone()

    if result:
        processed_schools = set(json.loads(result[0]))
        existing_results = json.loads(result[1])
        print(f"发现之前进度，已处理 {len(processed_schools)} 所学校")
    else:
        processed_schools = set()
        existing_results = []

    # 获取省份ID和学校列表
    province_id = str(province_id)
    province_id = Get_Province_Id.get_province_id(province_id)
    all_school_id = Get_School_Id.get_school_ids()
    total = len(all_school_id)

    results = existing_results

    # 统一的进度报告闭包：始终携带 processed/total/matched 三个核心计数
    def _emit(status, school=None, remaining_sec=None):
        if on_progress is not None:
            on_progress({
                "status": status,
                "school": school,
                "processed": len(processed_schools),
                "total": total,
                "matched": len(results),
                "remaining_sec": remaining_sec,
            })

    # 过滤掉已处理的学校
    schools_to_process = {k: v for k, v in all_school_id.items() if k not in processed_schools}

    if not schools_to_process:
        print("所有学校已处理完成")
        # 删除进度记录
        progress_cursor.execute('''DELETE FROM progress WHERE task_id = ?''', (task_id,))
        progress_conn.commit()
        progress_conn.close()

        _emit("done")

        if output:
            # 保存最终结果
            base = output_dir if output_dir else os.getcwd()
            output_file = os.path.join(base, f"{year}_{want}_学校分数排行.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(existing_results, f, ensure_ascii=False, indent=4)
            return f"所有学校已处理完成，结果已保存到 {output_file}"
        else:
            return existing_results

    times = 0

    print(f"开始处理 {len(schools_to_process)} 所学校...")

    # 顺序处理每个学校
    for school_name, school_id in list(schools_to_process.items()):
        # 每轮循环开头检查取消
        if cancel_event is not None and cancel_event.is_set():
            raise TaskCancelled("任务被取消")

        try:
            _emit("running", school=school_name)
            print(f"正在处理 {school_name}")

            # 跳过特定类型的学校
            if "学院" in school_name or "职业" in school_name:
                processed_schools.add(school_name)
                # 更新进度
                _persist_progress(progress_cursor, progress_conn, task_id, province_id,
                                  want, year, rank, processed_schools, results)
                continue

            # 获取学校数据
            all_score = GetScore.getScore(schoolId=school_id, provinceId=province_id, year=year)
            majors = all_score.get("item", [])

            # 处理专业数据
            school_results = []
            for major in majors:
                # 确保min_section是数字
                min_section = major.get("min_section", 0)
                if isinstance(min_section, str):
                    try:
                        min_section = int(min_section)
                    except ValueError:
                        continue

                # 检查专业条件
                if (want in major["spname"] and
                    ("专项" in major["spname"] or not ethnic_minority) and
                    abs(min_section - rank) < 3000):
                    school_results.append({major["spname"]: {"min": major["min"], "min_section": major["min_section"]}})

            # 如果有匹配的专业，添加到结果中
            if school_results:
                results.append({school_name: school_results})
                print(f"找到匹配专业: {school_name}")

            # 更新进度
            processed_schools.add(school_name)
            _persist_progress(progress_cursor, progress_conn, task_id, province_id,
                              want, year, rank, processed_schools, results)

            _emit("running", school=school_name)

            # 控制请求频率
            times += 1
            if times % 10 == 0:
                print("处理了10所学校，暂停30秒...")
                _emit("sleeping", school=school_name, remaining_sec=30)
                _interruptible_sleep(30, cancel_event,
                                     tick=lambda r: _emit("sleeping", school=school_name, remaining_sec=r))
            else:
                time.sleep(random.uniform(0.1, 0.3))

        except TaskCancelled:
            # 取消时不更新进度（当前状态已落盘），直接向上抛出
            raise
        except Exception as e:
            print(f"处理学校 {school_name} 时出错: {e}")
            print("暂停10分钟后再继续...")

            _emit("retry", school=school_name, remaining_sec=600)

            # 等待10分钟（可中断）
            _interruptible_sleep(600, cancel_event,
                                 tick=lambda r: _emit("retry", school=school_name, remaining_sec=r))

            print("继续处理...")
            schools_to_process[school_name] = school_id

    # 任务完成，删除进度记录
    progress_cursor.execute('''DELETE FROM progress WHERE task_id = ?''', (task_id,))
    progress_conn.commit()
    progress_conn.close()

    _emit("done")

    if output:
        # 保存结果
        base = output_dir if output_dir else os.getcwd()
        output_file = os.path.join(base, f"{year}_{want}_学校分数排行.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        return f"已将结果保存到 {output_file}，共处理 {len(results)} 所学校"
    else:
        return results
