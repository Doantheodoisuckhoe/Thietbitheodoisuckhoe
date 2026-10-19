// pat.h — Pulse Arrival Time từ đỉnh R (ECG) và PPG. Port từ algorithm/hwalgo/pat.py
#pragma once
#include <stdint.h>

enum PatStatus { PAT_OK = 0, PAT_LOW_QUALITY = 3 };

struct PatResult {
  uint8_t status;
  float pat_ms;  // trung vị PAT (ms)
  float iqr_ms;
  int n_valid;
  int n_beats;
};

// r_times_ms: thời điểm các đỉnh R (ms, cùng gốc thời gian với PPG).
// ppg: n_p mẫu PPG thô — bị THAY bằng tín hiệu đã lọc. Thời điểm mẫu j: t0_ms + j*dt_ms.
// scratch: bộ nhớ tạm >= 2*n_r phần tử.
void pat_compute(const float* r_times_ms, int n_r, float* ppg, int n_p, double t0_ms, double dt_ms,
                 bool invert, float* scratch, PatResult* out);
