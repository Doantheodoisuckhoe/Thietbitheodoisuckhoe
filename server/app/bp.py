"""Ước lượng huyết áp từ PAT với hiệu chuẩn cá nhân.

Bản sao của algorithm/hwalgo/bp.py (giữ hai file giống nhau).
    SBP = a_s + b_s / PAT      DBP = a_d + b_d / PAT      (PAT: giây)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

DEFAULT_B_SBP = 50.0
DEFAULT_B_DBP = 25.0
B_SBP_RANGE = (10.0, 150.0)
B_DBP_RANGE = (5.0, 100.0)


@dataclass
class BpModel:
    a_sbp: float
    b_sbp: float
    a_dbp: float
    b_dbp: float
    n_points: int
    method: str  # offset | regression

    def estimate(self, pat_ms: float) -> Tuple[float, float]:
        x = 1000.0 / pat_ms
        return self.a_sbp + self.b_sbp * x, self.a_dbp + self.b_dbp * x


def _mean(v):
    return sum(v) / len(v)


def _slope(x, y):
    mx, my = _mean(x), _mean(y)
    sxx = sum((a - mx) ** 2 for a in x)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / sxx


def _fit_one(x, y, b_default, b_range, regression):
    if regression:
        b = min(max(_slope(x, y), b_range[0]), b_range[1])
    else:
        b = b_default
    a = _mean([yy - b * xx for xx, yy in zip(x, y)])
    return a, b


def fit_model(points: Sequence[Tuple[float, float, float]]) -> Optional[BpModel]:
    """points: [(pat_ms, sbp_ref, dbp_ref), ...]"""
    pts = [p for p in points if p[0] and p[0] > 0]
    if not pts:
        return None
    x = [1000.0 / p[0] for p in pts]
    sbp = [p[1] for p in pts]
    dbp = [p[2] for p in pts]
    mx = _mean(x)
    std_x = (sum((a - mx) ** 2 for a in x) / len(x)) ** 0.5
    regression = len(pts) >= 3 and (max(sbp) - min(sbp)) >= 10.0 and std_x > 1e-3
    a_s, b_s = _fit_one(x, sbp, DEFAULT_B_SBP, B_SBP_RANGE, regression)
    a_d, b_d = _fit_one(x, dbp, DEFAULT_B_DBP, B_DBP_RANGE, regression)
    return BpModel(a_s, b_s, a_d, b_d, len(pts), "regression" if regression else "offset")
