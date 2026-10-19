// dsp.cpp — xem dsp.h
#include "dsp.h"

#include <math.h>
#include <stdlib.h>
#include <string.h>

void biquad_design(Biquad* q, BiquadKind kind, float f0, float fs) {
  // Tính bằng double cho khớp với Python, sau đó lưu float.
  const double Q = 0.70710678118654752;  // Butterworth
  double w0 = 2.0 * M_PI * (double)f0 / (double)fs;
  double cw = cos(w0), sw = sin(w0);
  double alpha = sw / (2.0 * Q);
  double b0, b1, b2;
  if (kind == BQ_LOWPASS) {
    b0 = (1 - cw) / 2; b1 = 1 - cw; b2 = (1 - cw) / 2;
  } else {
    b0 = (1 + cw) / 2; b1 = -(1 + cw); b2 = (1 + cw) / 2;
  }
  double a0 = 1 + alpha;
  q->b0 = (float)(b0 / a0);
  q->b1 = (float)(b1 / a0);
  q->b2 = (float)(b2 / a0);
  q->a1 = (float)(-2 * cw / a0);
  q->a2 = (float)((1 - alpha) / a0);
  q->z1 = q->z2 = 0.0f;
}

float biquad_process(Biquad* q, float x) {
  float y = q->b0 * x + q->z1;
  q->z1 = q->b1 * x - q->a1 * y + q->z2;
  q->z2 = q->b2 * x - q->a2 * y;
  return y;
}

float biquad_reset_to(Biquad* q, float u) {
  float gain = (q->b0 + q->b1 + q->b2) / (1.0f + q->a1 + q->a2);
  float y = gain * u;
  q->z2 = q->b2 * u - q->a2 * y;
  q->z1 = q->b1 * u - q->a1 * y + q->z2;
  return y;
}

void bandpass_design(BiquadChain* c, float f_lo, float f_hi, float fs) {
  biquad_design(&c->s[0], BQ_HIGHPASS, f_lo, fs);
  biquad_design(&c->s[1], BQ_LOWPASS, f_hi, fs);
  c->n = 2;
}

float chain_process(BiquadChain* c, float x) {
  for (int i = 0; i < c->n; i++) x = biquad_process(&c->s[i], x);
  return x;
}

void chain_reset_to(BiquadChain* c, float u) {
  for (int i = 0; i < c->n; i++) u = biquad_reset_to(&c->s[i], u);
}

void dsp_filtfilt_bandpass(float* x, int n, float f_lo, float f_hi, float fs) {
  if (n <= 0) return;
  BiquadChain c;
  bandpass_design(&c, f_lo, f_hi, fs);
  chain_reset_to(&c, x[0]);
  for (int i = 0; i < n; i++) x[i] = chain_process(&c, x[i]);
  bandpass_design(&c, f_lo, f_hi, fs);
  chain_reset_to(&c, x[n - 1]);
  for (int i = n - 1; i >= 0; i--) x[i] = chain_process(&c, x[i]);
}

static int cmp_float(const void* a, const void* b) {
  float fa = *(const float*)a, fb = *(const float*)b;
  return (fa > fb) - (fa < fb);
}

void dsp_sort(float* a, int n) {
  if (n <= 1) return;
  if (n <= 32) {  // insertion sort cho mảng nhỏ
    for (int i = 1; i < n; i++) {
      float v = a[i];
      int j = i - 1;
      while (j >= 0 && a[j] > v) { a[j + 1] = a[j]; j--; }
      a[j + 1] = v;
    }
  } else {
    qsort(a, (size_t)n, sizeof(float), cmp_float);
  }
}

float dsp_median_inplace(float* a, int n) {
  if (n <= 0) return 0.0f;
  dsp_sort(a, n);
  int m = n / 2;
  return (n % 2) ? a[m] : 0.5f * (a[m - 1] + a[m]);
}

float dsp_median_copy(const float* a, int n, float* scratch) {
  if (n <= 0) return 0.0f;
  memcpy(scratch, a, sizeof(float) * (size_t)n);
  return dsp_median_inplace(scratch, n);
}

float dsp_percentile_sorted(const float* s, int n, float q) {
  if (n <= 0) return 0.0f;
  if (n == 1) return s[0];
  float pos = q * (float)(n - 1);
  int lo = (int)floorf(pos);
  if (lo >= n - 1) return s[n - 1];
  float frac = pos - (float)lo;
  return s[lo] + (s[lo + 1] - s[lo]) * frac;
}
