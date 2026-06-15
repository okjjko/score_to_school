import os
import json
import glob
from .paths import PROJECT_ROOT

SUFFIX = '_学校分数排行.json'


def list_results():
    items = []
    for path in glob.glob(os.path.join(PROJECT_ROOT, '*' + SUFFIX)):
        name = os.path.basename(path)
        st = os.stat(path)
        stem = name[:-len(SUFFIX)]  # 去掉后缀，形如 "2024_生物科学"
        parts = stem.split('_', 1)
        year = parts[0] if parts and parts[0].isdigit() else ''
        want = parts[1] if len(parts) > 1 else stem
        items.append({
            'file': name,
            'want': want,
            'year': year,
            'size_kb': round(st.st_size / 1024, 1),
            'mtime': int(st.st_mtime),
        })
    items.sort(key=lambda x: x['mtime'], reverse=True)
    return items


def read_result(name):
    safe = os.path.basename(name)  # 防穿越：只取纯文件名
    if not safe.endswith(SUFFIX):
        raise FileNotFoundError(name)
    path = os.path.join(PROJECT_ROOT, safe)
    if not os.path.isfile(path):
        raise FileNotFoundError(name)
    with open(path, encoding='utf-8') as f:
        return json.load(f)
