import os
import json
import sqlite3
import Get_informations.Getpage as Getpage

# score.db 路径（固定为项目根目录，避免受启动 cwd 影响）
_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'score.db')


def _get_conn():
    """每次调用创建独立连接，保证多线程安全（原版模块级全局连接在子线程下会报 check_same_thread 错误）。"""
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL')
    return conn


def getScore(schoolId, provinceId, year):
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        # 检查表是否存在，如果不存在则创建
        cursor.execute('''CREATE TABLE IF NOT EXISTS score_data
                        (schoolId INTEGER,
                         provinceId INTEGER,
                         year INTEGER,
                         data TEXT,
                         PRIMARY KEY (schoolId, provinceId, year))''')

        # 先从数据库中查询
        cursor.execute('''SELECT data FROM score_data
                         WHERE schoolId = ? AND provinceId = ? AND year = ?''',
                       (schoolId, provinceId, year))
        result = cursor.fetchone()

        if result:
            # 如果在数据库中找到数据，直接返回（from_cache=True）
            return json.loads(result[0]), True

        # 从API获取数据
        page = 0
        data = []
        all_data = []
        while len(data) == 10 or page == 0:
            page += 1
            data = Getpage.getpage(page, schoolId, provinceId, year)
            all_data.extend(data)
        all_data = {"item": all_data}

        # 保存到数据库
        cursor.execute('''INSERT OR REPLACE INTO score_data
                        (schoolId, provinceId, year, data)
                        VALUES (?, ?, ?, ?)''',
                       (schoolId, provinceId, year, json.dumps(all_data, ensure_ascii=False)))
        conn.commit()

        return all_data, False
    finally:
        conn.close()
