import json
from .paths import SCHOOLID_PATH

# 31 个省/直辖市/自治区 ID ↔ 名称（来自 gaokao.cn config）
PROVINCES = [
    (11, '北京'), (12, '天津'), (13, '河北'), (14, '山西'), (15, '内蒙古'),
    (21, '辽宁'), (22, '吉林'), (23, '黑龙江'),
    (31, '上海'), (32, '江苏'), (33, '浙江'), (34, '安徽'), (35, '福建'),
    (36, '江西'), (37, '山东'),
    (41, '河南'), (42, '湖北'), (43, '湖南'), (44, '广东'), (45, '广西'), (46, '海南'),
    (50, '重庆'), (51, '四川'), (52, '贵州'), (53, '云南'), (54, '西藏'),
    (61, '陕西'), (62, '甘肃'), (63, '青海'), (64, '宁夏'), (65, '新疆'),
]


def list_provinces():
    return [{'id': pid, 'name': name} for pid, name in PROVINCES]


def schools_count():
    """学校总数与去「学院/职业」后可用数（与 process.py 跳过逻辑一致）。"""
    try:
        with open(SCHOOLID_PATH, encoding='utf-8') as f:
            schools = json.load(f).get('data', {}).get('school', [])
    except Exception:
        return {'total': 0, 'usable': 0}
    total = len(schools)
    usable = sum(1 for s in schools
                 if '学院' not in s.get('name', '') and '职业' not in s.get('name', ''))
    return {'total': total, 'usable': usable}
