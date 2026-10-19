"""Phát hiện đỉnh R trên ECG 1 chuyển đạo (AD8232) — Pan-Tompkins rút gọn.

Xử lý OFFLINE trên bộ đệm 30 s (thiết bị ghi xong mới xử lý), nên dùng
bộ lọc pha-không và đạo hàm/tích phân có tâm -> vị trí R không bị trễ.

Các bước:
 1. Band-pass 5–15 Hz (HP + LP biquad, lọc xuôi-ngược).
 2. Xác định cực tính (điện cực có thể bị đảo).
 3. Đạo hàm 5 điểm -> bình phương -> trung bình trượt 150 ms (MWI).
 4. Ngưỡng thích nghi SPKI/NPKI trên các cực đại của MWI, thời gian trơ 200 ms,
    phân biệt sóng T (< 360 ms và độ dốc < 50% QRS trước), tìm lại (searchback)
    khi quá 1,66 x RR trung bình mà chưa thấy nhịp.
 5. Tinh chỉnh vị trí R = cực đại của tín hiệu band-pass trong ±100 ms.

Mục tiêu đề cương: phát hiện đúng >= 95% đỉnh R (Se và +P trên MIT-BIH).
Bản C tương ứng: firmware/health_watch/ecg_rpeak.cpp
"""
from __future__ import annotations

from typing import List, Tuple

import numpy as np

from .filters import bandpass_sections, centered_diff, centered_moving_average, filtfilt_ss


def detect_r_peaks(ecg, fs: float, return_debug: bool = False):
    x = np.asarray(ecg, dtype=float)
    n = len(x)
    if n < int(fs):
        empty = np.zeros(0, dtype=int)
        return (empty, {}) if return_debug else empty

    bp = filtfilt_ss(bandpass_sections(5.0, 15.0, fs), x)

    edge = int(0.5 * fs)
    region = bp[edge:n - edge] if n > 4 * edge else bp
    sign = 1.0 if region.max() >= -region.min() else -1.0

    d = centered_diff(bp)
    sq = d * d
    w = int(round(0.150 * fs))
    mwi = centered_moving_average(sq, w)

    refr = int(round(0.200 * fs))
    twin = int(round(0.360 * fs))
    half = w // 2

    init = min(n, int(2 * fs))
    spki = 0.25 * float(mwi[:init].max())
    npki = 0.5 * float(mwi[:init].mean())
    thr = npki + 0.25 * (spki - npki)

    def max_slope(i: int) -> float:
        lo, hi = max(0, i - half), min(n, i + half + 1)
        return float(np.max(np.abs(d[lo:hi])))

    qrs: List[int] = []
    rr: List[int] = []
    pending: List[Tuple[int, float]] = []

    def accept(p: int) -> None:
        if qrs:
            interval = p - qrs[-1]
            if refr <= interval <= int(3 * fs):
                rr.append(interval)
                if len(rr) > 8:
                    rr.pop(0)
        qrs.append(p)

    # cực đại cục bộ của MWI
    cand = np.where((mwi[1:-1] > mwi[:-2]) & (mwi[1:-1] >= mwi[2:]))[0] + 1

    for p in cand:
        p = int(p)
        v = float(mwi[p])

        # --- searchback: quá lâu chưa có nhịp -> lấy ứng viên lớn nhất đã bỏ qua
        if qrs and len(rr) >= 2:
            rr_avg = sum(rr) / len(rr)
            if p - qrs[-1] > 1.66 * rr_avg:
                best = None
                for i2, v2 in pending:
                    if i2 - qrs[-1] >= refr and v2 > 0.5 * thr and (best is None or v2 > best[1]):
                        best = (i2, v2)
                if best is not None:
                    accept(best[0])
                    spki = 0.25 * best[1] + 0.75 * spki
                    thr = npki + 0.25 * (spki - npki)
                    pending = [it for it in pending if it[0] > best[0]]

        # --- thời gian trơ: giữ cực đại lớn hơn trong cùng 1 phức bộ
        if qrs and p - qrs[-1] < refr:
            if v > mwi[qrs[-1]]:
                qrs[-1] = p
                if len(qrs) >= 2 and rr:
                    rr[-1] = qrs[-1] - qrs[-2]
            continue

        if v > thr:
            if qrs and p - qrs[-1] < twin and max_slope(p) < 0.5 * max_slope(qrs[-1]):
                npki = 0.125 * v + 0.875 * npki  # sóng T
                pending.append((p, v))
            else:
                accept(p)
                spki = 0.125 * v + 0.875 * spki
                pending = []
        else:
            npki = 0.125 * v + 0.875 * npki
            pending.append((p, v))
        thr = npki + 0.25 * (spki - npki)

    # --- tinh chỉnh vị trí R
    r_win = int(round(0.100 * fs))
    peaks: List[int] = []
    for q in qrs:
        lo, hi = max(0, q - r_win), min(n, q + r_win + 1)
        r = lo + int(np.argmax(sign * bp[lo:hi]))
        if not peaks or r - peaks[-1] >= refr:
            peaks.append(r)
    out = np.asarray(peaks, dtype=int)
    if return_debug:
        return out, {"bp": bp, "mwi": mwi, "sign": sign}
    return out


def heart_rate_from_peaks(peaks, fs: float) -> float:
    if len(peaks) < 2:
        return 0.0
    rr = np.diff(peaks) / fs
    return float(60.0 / np.median(rr))


def match_beats(detected, reference, tol_samples: int) -> Tuple[int, int, int]:
    """So khớp nhịp phát hiện với nhịp chú thích (chuẩn ANSI/AAMI EC57, cửa sổ 150 ms).

    Trả về (TP, FP, FN).
    """
    det = np.sort(np.asarray(detected, dtype=int))
    ref = np.sort(np.asarray(reference, dtype=int))
    i = j = tp = 0
    used = np.zeros(len(det), dtype=bool)
    for r in ref:
        while i < len(det) and det[i] < r - tol_samples:
            i += 1
        k = i
        best = -1
        while k < len(det) and det[k] <= r + tol_samples:
            if not used[k] and (best < 0 or abs(det[k] - r) < abs(det[best] - r)):
                best = k
            k += 1
        if best >= 0:
            used[best] = True
            tp += 1
    fn = len(ref) - tp
    fp = int(len(det) - used.sum())
    return tp, fp, fn
