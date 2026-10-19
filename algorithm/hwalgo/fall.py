"""Phát hiện té ngã bằng gia tốc kế cổ tay (LSM6DS3 trên XIAO Sense).

Quy tắc theo đề cương: "va chạm mạnh, sau đó bất động 30 giây".

Máy trạng thái (xử lý từng mẫu, fs mặc định 104 Hz, đơn vị g):

  IDLE    --(|a| >= impact_g)-->  SETTLE   (bỏ qua 2 s dao động sau va chạm)
  SETTLE  --(hết 2 s)---------->  CHECK    (theo dõi 30 s)
  CHECK   : chia thành các khối 1 s, khối "có cử động" nếu độ lệch chuẩn |a| > 0,08 g.
            > 5 khối cử động  -> người dùng đã cử động/đứng dậy -> về IDLE.
            hết 30 s          -> XÁC NHẬN TÉ NGÃ.
  Nút bấm ngắn trong lúc CHECK -> huỷ (người dùng báo "tôi không sao").
  Sau khi xác nhận/huỷ: COOLDOWN 10 s.

Thêm thông tin phụ đi kèm sự kiện: có rơi tự do trước va chạm không
(|a| < 0,6 g >= 60 ms), góc thay đổi tư thế cổ tay.

Đồng thời đếm "mẫu có hoạt động" (||a| - 1g| > 0,1 g) cho cảnh báo
"không cử động 3 giờ" và để biết người dùng có đang đứng yên (đo SpO2).

Bản C tương ứng: firmware/health_watch/fall_detect.cpp
"""
from __future__ import annotations

import math
from typing import Optional

IDLE, SETTLE, CHECK, COOLDOWN = 0, 1, 2, 3


class FallDetector:
    def __init__(
        self,
        fs: float = 104.0,
        impact_g: float = 2.8,
        settle_s: float = 2.0,
        still_s: float = 30.0,
        block_s: float = 1.0,
        block_std_g: float = 0.08,
        max_active_blocks: int = 5,
        freefall_g: float = 0.6,
        freefall_min_s: float = 0.06,
        freefall_window_s: float = 1.0,
        cooldown_s: float = 10.0,
        activity_thr_g: float = 0.1,
    ):
        self.fs = fs
        self.impact_g = impact_g
        self.settle_n = int(round(settle_s * fs))
        self.block_n = int(round(block_s * fs))
        self.n_blocks = int(round(still_s / block_s))
        self.block_std_g = block_std_g
        self.max_active_blocks = max_active_blocks
        self.freefall_g = freefall_g
        self.freefall_min_n = max(1, int(round(freefall_min_s * fs)))
        self.freefall_window_n = int(round(freefall_window_s * fs))
        self.cooldown_n = int(round(cooldown_s * fs))
        self.activity_thr_g = activity_thr_g
        self.g_alpha = 1.0 / fs  # hằng số thời gian 1 s
        self.reset()

    def reset(self) -> None:
        self.state = IDLE
        self.n = 0
        self.state_n = 0
        self.ff_count = 0
        self.last_ff_n = -10**9
        self.g_lp = [0.0, 0.0, 1.0]
        self.g_init = False
        self.pre_g = [0.0, 0.0, 1.0]
        self.peak_g = 0.0
        self.had_ff = False
        self.blk_cnt = 0
        self.blk_sum = 0.0
        self.blk_sq = 0.0
        self.blocks_done = 0
        self.active_blocks = 0
        self.post_sum = [0.0, 0.0, 0.0]
        self.post_cnt = 0
        self.activity_count = 0
        self.still_n = 0

    # ------------------------------------------------------------------
    def take_activity(self) -> int:
        """Lấy và xoá bộ đếm hoạt động (firmware gọi mỗi chu kỳ gửi dữ liệu)."""
        c = self.activity_count
        self.activity_count = 0
        return c

    def still_seconds(self) -> float:
        return self.still_n / self.fs

    def is_checking(self) -> bool:
        return self.state in (SETTLE, CHECK)

    def cancel(self) -> bool:
        """Người dùng bấm nút trong lúc đếm ngược -> huỷ. Trả về True nếu có huỷ."""
        if self.state in (SETTLE, CHECK):
            self._enter(COOLDOWN)
            return True
        return False

    def _enter(self, st: int) -> None:
        self.state = st
        self.state_n = 0

    # ------------------------------------------------------------------
    def update(self, ax: float, ay: float, az: float) -> Optional[dict]:
        """Đưa vào 1 mẫu (g). Trả về dict sự kiện hoặc None.

        Sự kiện: {"type": "impact"|"fall", "peak_g", "angle_deg", "freefall"}
        """
        svm = math.sqrt(ax * ax + ay * ay + az * az)
        self.n += 1
        self.state_n += 1
        event = None

        # đếm hoạt động / thời gian đứng yên
        if abs(svm - 1.0) > self.activity_thr_g:
            self.activity_count += 1
            self.still_n = 0
        else:
            self.still_n += 1

        # rơi tự do
        if svm < self.freefall_g:
            self.ff_count += 1
            if self.ff_count >= self.freefall_min_n:
                self.last_ff_n = self.n
        else:
            self.ff_count = 0

        if self.state == IDLE:
            if not self.g_init:
                self.g_lp = [ax, ay, az]
                self.g_init = True
            else:
                self.g_lp[0] += (ax - self.g_lp[0]) * self.g_alpha
                self.g_lp[1] += (ay - self.g_lp[1]) * self.g_alpha
                self.g_lp[2] += (az - self.g_lp[2]) * self.g_alpha
            if svm >= self.impact_g:
                self.pre_g = list(self.g_lp)
                self.peak_g = svm
                self.had_ff = (self.n - self.last_ff_n) <= self.freefall_window_n
                self._enter(SETTLE)
                event = {"type": "impact", "peak_g": svm, "angle_deg": 0.0, "freefall": self.had_ff}

        elif self.state == SETTLE:
            if svm > self.peak_g:
                self.peak_g = svm
            if self.state_n >= self.settle_n:
                self._enter(CHECK)
                self.blk_cnt = 0
                self.blk_sum = 0.0
                self.blk_sq = 0.0
                self.blocks_done = 0
                self.active_blocks = 0
                self.post_sum = [0.0, 0.0, 0.0]
                self.post_cnt = 0

        elif self.state == CHECK:
            self.blk_cnt += 1
            self.blk_sum += svm
            self.blk_sq += svm * svm
            self.post_sum[0] += ax
            self.post_sum[1] += ay
            self.post_sum[2] += az
            self.post_cnt += 1
            if self.blk_cnt >= self.block_n:
                mean = self.blk_sum / self.blk_cnt
                var = max(0.0, self.blk_sq / self.blk_cnt - mean * mean)
                if math.sqrt(var) > self.block_std_g:
                    self.active_blocks += 1
                self.blocks_done += 1
                self.blk_cnt = 0
                self.blk_sum = 0.0
                self.blk_sq = 0.0
                if self.active_blocks > self.max_active_blocks:
                    self._enter(IDLE)  # đã cử động lại -> không phải té ngã
                elif self.blocks_done >= self.n_blocks:
                    event = {
                        "type": "fall",
                        "peak_g": self.peak_g,
                        "angle_deg": self._angle(),
                        "freefall": self.had_ff,
                    }
                    self._enter(COOLDOWN)

        elif self.state == COOLDOWN:
            if self.state_n >= self.cooldown_n:
                self._enter(IDLE)

        return event

    def _angle(self) -> float:
        if self.post_cnt == 0:
            return 0.0
        post = [v / self.post_cnt for v in self.post_sum]
        a = self.pre_g
        dot = a[0] * post[0] + a[1] * post[1] + a[2] * post[2]
        na = math.sqrt(sum(v * v for v in a))
        nb = math.sqrt(sum(v * v for v in post))
        if na < 1e-6 or nb < 1e-6:
            return 0.0
        c = max(-1.0, min(1.0, dot / (na * nb)))
        return math.degrees(math.acos(c))
