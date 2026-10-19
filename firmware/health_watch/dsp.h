// dsp.h — bộ lọc biquad, lọc pha-không, trung vị, phân vị.
// Port 1-1 từ algorithm/hwalgo/filters.py. Không phụ thuộc Arduino (biên dịch
// được trên máy tính để kiểm thử: firmware/tests).
#pragma once
#include <stdint.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

enum BiquadKind { BQ_LOWPASS = 0, BQ_HIGHPASS = 1 };

struct Biquad {
  float b0, b1, b2, a1, a2;  // a0 = 1
  float z1, z2;              // trạng thái DF2T
};

struct BiquadChain {
  Biquad s[2];
  int n;
};

void biquad_design(Biquad* q, BiquadKind kind, float f0, float fs);
float biquad_process(Biquad* q, float x);
float biquad_reset_to(Biquad* q, float u);  // trạng thái xác lập với đầu vào hằng u

void bandpass_design(BiquadChain* c, float f_lo, float f_hi, float fs);  // HP(f_lo) + LP(f_hi)
float chain_process(BiquadChain* c, float x);
void chain_reset_to(BiquadChain* c, float u);

// Lọc band-pass xuôi-ngược tại chỗ (giống filtfilt_ss trong Python).
void dsp_filtfilt_bandpass(float* x, int n, float f_lo, float f_hi, float fs);

// Sắp xếp tăng dần tại chỗ.
void dsp_sort(float* a, int n);
// Trung vị (sắp xếp mảng a tại chỗ). n chẵn: trung bình 2 phần tử giữa.
float dsp_median_inplace(float* a, int n);
// Trung vị không làm đổi mảng gốc (copy sang scratch, cần >= n phần tử).
float dsp_median_copy(const float* a, int n, float* scratch);
// Phân vị q (0..1), nội suy tuyến tính như numpy.percentile. Mảng đã sắp xếp.
float dsp_percentile_sorted(const float* sorted, int n, float q);
