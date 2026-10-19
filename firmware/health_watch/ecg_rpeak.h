// ecg_rpeak.h — phát hiện đỉnh R (Pan-Tompkins rút gọn, offline trên bộ đệm).
// Port 1-1 từ algorithm/hwalgo/ecg_rpeak.py
#pragma once
#include <stdint.h>

// x   : n mẫu ECG; sau khi gọi, x bị THAY bằng tín hiệu band-pass 5–15 Hz.
// mwi : bộ nhớ tạm n phần tử.
// peaks: mảng kết quả (chỉ số mẫu đỉnh R), tối đa max_peaks.
// Trả về số đỉnh R tìm được.
int ecg_detect_r_peaks(float* x, int n, float fs, float* mwi, int32_t* peaks, int max_peaks);

// Trung vị RR (ms) và nhịp tim (bpm) từ danh sách đỉnh. Trả về bpm (0 nếu < 2 đỉnh).
float ecg_heart_rate(const int32_t* peaks, int n_peaks, float fs, float* rr_median_ms);
