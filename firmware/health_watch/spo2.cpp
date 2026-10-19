// spo2.cpp — xem spo2.h / algorithm/hwalgo/spo2.py
#include "spo2.h"

#include <math.h>
#include <string.h>

#include "dsp.h"

static const float WIN_S = 4.0f, HOP_S = 2.0f, SKIP_S = 2.0f;
static const float DC_MIN = 10000.0f, MIN_CORR = 0.8f, MIN_PI = 0.0005f;
static const float R_MIN = 0.2f, R_MAX = 2.0f;
static const int MIN_WINDOWS = 3;

float spo2_from_ratio(float r, const Spo2Coeffs* k) {
  float s = k->a * r * r + k->b * r + k->c;
  if (s > 100.0f) s = 100.0f;
  if (s < 70.0f) s = 70.0f;
  return s;
}

static double mean_of(const float* x, int n) {
  double s = 0;
  for (int i = 0; i < n; i++) s += x[i];
  return n > 0 ? s / n : 0.0;
}

void spo2_compute(const float* red, const float* ir, int n, float fs, const Spo2Coeffs* k,
                  float* red_bp, float* ir_bp, float* ratios, float* corrs, int scratch_len,
                  Spo2Result* out) {
  memset(out, 0, sizeof(*out));
  int win = (int)lroundf(WIN_S * fs);
  int hop = (int)lroundf(HOP_S * fs);
  int skip = (int)lroundf(SKIP_S * fs);
  if (n < skip + win) {
    out->status = SPO2_LOW_QUALITY;
    return;
  }
  if (mean_of(red + skip, n - skip) < DC_MIN || mean_of(ir + skip, n - skip) < DC_MIN) {
    out->status = SPO2_NO_CONTACT;
    return;
  }
  memcpy(red_bp, red, sizeof(float) * (size_t)n);
  memcpy(ir_bp, ir, sizeof(float) * (size_t)n);
  dsp_filtfilt_bandpass(red_bp, n, 0.5f, 5.0f, fs);
  dsp_filtfilt_bandpass(ir_bp, n, 0.5f, 5.0f, fs);

  int n_valid = 0, n_windows = 0;
  for (int s = skip; s + win <= n; s += hop) {
    n_windows++;
    double dc_r = mean_of(red + s, win);
    double dc_i = mean_of(ir + s, win);
    double m_r = mean_of(red_bp + s, win);
    double m_i = mean_of(ir_bp + s, win);
    double srr = 0, sii = 0, sri = 0;
    for (int j = s; j < s + win; j++) {
      double a = red_bp[j] - m_r, b = ir_bp[j] - m_i;
      srr += a * a;
      sii += b * b;
      sri += a * b;
    }
    double ac_r = sqrt(srr / win), ac_i = sqrt(sii / win);
    if (dc_r < DC_MIN || dc_i < DC_MIN || ac_i <= 0 || ac_r <= 0) continue;
    double corr = sri / (sqrt(srr * sii) + 1e-12);
    double pi_ir = ac_i / dc_i;
    double ratio = (ac_r / dc_r) / pi_ir;
    if (corr >= MIN_CORR && pi_ir >= MIN_PI && ratio >= R_MIN && ratio <= R_MAX && n_valid < scratch_len) {
      ratios[n_valid] = (float)ratio;
      corrs[n_valid] = (float)corr;
      n_valid++;
    }
  }
  out->n_valid = n_valid;
  out->n_windows = n_windows;
  if (n_valid < MIN_WINDOWS) {
    out->status = SPO2_LOW_QUALITY;
    out->quality = (uint8_t)(100 * n_valid / (n_windows > 0 ? n_windows : 1));
    return;
  }
  double corr_mean = mean_of(corrs, n_valid);
  float r_med = dsp_median_inplace(ratios, n_valid);
  out->status = SPO2_OK;
  out->ratio = r_med;
  out->spo2 = spo2_from_ratio(r_med, k);
  out->quality = (uint8_t)lround(100.0 * n_valid / n_windows * corr_mean);
}
