// hr_ppg.h — ước lượng nhịp tim liên tục từ PPG xanh, xử lý từng mẫu.
// Port 1-1 từ algorithm/hwalgo/hr_ppg.py (đọc docstring ở đó để hiểu thuật toán).
#pragma once
#include <stdint.h>

#include "dsp.h"

#define HR_MAX_IBI 8

struct HrEstimator {
  // tham số
  float fs;
  bool invert;
  float amp_decay, thr_ratio;
  float refr_init, refr_min, refr_max, refr_ratio;  // đơn vị: mẫu
  float ibi_min, ibi_max;                          // giây
  float outlier_ratio;
  int max_outliers;
  float beat_timeout;  // mẫu
  int min_ibis;
  float dc_alpha, contact_dc_min;
  // trạng thái
  BiquadChain bp;
  bool started;
  int32_t n;
  float y1, y2, amp;
  int32_t last_peak;  // -1 = chưa có
  float ibis[HR_MAX_IBI];
  int n_ibis;
  int consec_outliers;
  float dc;
};

// contact_dc_min <= 0: không kiểm tra tiếp xúc.
void hr_init(HrEstimator* h, float fs, bool invert, float contact_dc_min);
void hr_reset(HrEstimator* h);
bool hr_update(HrEstimator* h, float x);         // true nếu vừa có nhịp
float hr_get(HrEstimator* h, uint8_t* quality);  // bpm (0 nếu không tin cậy)
bool hr_in_contact(const HrEstimator* h);
