import requests


class RateLimitError(Exception):
    """触发目标站点「请求过多」风控。由上层捕获后重试。"""
    pass


def getpage(page, schoolId, provinceId, year):
    params = {
        "local_province_id": provinceId,
        "page": page,
        "school_id": schoolId,
        "size": "10",
        "uri": "apidata/api/gk/score/special",
        "year": year,
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Baiduspider-render/2.0; +http://www.baidu.com/search/spider.html)"
        # "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"
    }
    response = requests.get("https://api.zjzw.cn/web/api/", params=params, headers=headers, timeout=15)

    # 风控：抛明确异常，由上层 process 的 except 捕获后进入重试等待
    # （原版此处 data 未定义直接 return 会抛 UnboundLocalError，行为相同但语义更清晰）
    if "请求过多，请稍后再试" in response.text:
        raise RateLimitError("请求过多，请稍后再试")

    data = response.json().get("data", {}).get("item", [])
    return data if data is not None else []
