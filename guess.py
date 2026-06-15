import numpy as np
from scipy import stats


def predict(history, want_year):
    """一元线性回归预测。

    history  : {年份: 分数/位次} 字典，如 {2021: 593, 2022: 591, 2023: 612}
    want_year: 希望预测的目标年份
    返回     : dict，含 slope/intercept/r/r_squared/predicted/equation_str/points/line
               points 为历史散点坐标，line 为覆盖 [min(年份), want_year] 的拟合直线两端点
               （供前端绘制散点 + 拟合线 + 预测点）
    """
    years = np.array(list(history.keys()), dtype=float)
    scores = np.array(list(history.values()), dtype=float)

    # 样本相关系数
    r = float(np.corrcoef(years, scores)[0, 1])

    # 一元线性回归
    slope, intercept, r_value, p_value, std_err = stats.linregress(years, scores)

    # 预测
    predicted = float(slope * want_year + intercept)

    # 历史散点
    points = [{"x": int(y), "y": float(s)} for y, s in zip(years, scores)]

    # 拟合直线（覆盖到目标年份，便于前端把预测点画在线上）
    x_min = float(min(np.min(years), want_year))
    x_max = float(max(np.max(years), want_year))
    line = [
        {"x": x_min, "y": float(slope * x_min + intercept)},
        {"x": x_max, "y": float(slope * x_max + intercept)},
    ]

    sign = "+" if intercept >= 0 else "-"
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r": r,
        "r_squared": r ** 2,
        "predicted": predicted,
        "equation_str": f"y = {slope:.4f}x {sign} {abs(intercept):.4f}",
        "points": points,
        "line": line,
    }


# 脚本式执行（保留原 CLI 用法）
if __name__ == "__main__":
    # 请注意 此处不限制填写的内容 但仍然建议填写排名，格式 年份:分数/排名
    num = {2021: 593, 2022: 591, 2023: 612}
    wantYear = 2024

    res = predict(num, wantYear)
    print("样本相关系数 r =", res["r"])
    print("一元线性方程：", res["equation_str"])
    print("预测", wantYear, "年的分数为：", res["predicted"])
