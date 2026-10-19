// spo2.h — SpO2 theo tỉ số R. Port từ algorithm/hwalgo/spo2.py
#pragma once
#include <stdint.h>

enum Spo2Status { SPO2_OK = 0, SPO2_NO_CONTACT = 1, SPO2_LOW_QUALITY = 2, SPO2_MOTION = 3 };

struct Spo2Result {
  uint8_t status;
  float spo2;   // %
  float ratio;  // R
  uint8_t quality;
  int n_valid;
  int n_windows;
};

struct Spo2Coeffs {
  float a, b, c;  // SpO2 = a*R^2 + b*R + c
};

float spo2_from_ratio(float r, const Spo2Coeffs* k);

// red, ir: n mẫu thô (KHÔNG bị thay đổi). red_bp, ir_bp: bộ nhớ tạm n phần tử.
// ratios_scratch: bộ nhớ tạm >= số cửa sổ (n/(2s*fs) + 1), 2 mảng.
void spo2_compute(const float* red, const float* ir, int n, float fs, const Spo2Coeffs* k,
                  float* red_bp, float* ir_bp, float* ratios_scratch, float* corr_scratch,
                  int scratch_len, Spo2Result* out);
