// ecg_rpeak.cpp — xem ecg_rpeak.h / algorithm/hwalgo/ecg_rpeak.py
#include "ecg_rpeak.h"

#include <math.h>

#include "dsp.h"

#define MAX_QRS 160
#define MAX_PENDING 64
#define MAX_RR 8

static inline float diff_at(const float* bp, int n, int i) {
  if (i < 2 || i >= n - 2) return 0.0f;
  return (-bp[i - 2] - 2.0f * bp[i - 1] + 2.0f * bp[i + 1] + bp[i + 2]) / 8.0f;
}

static float max_slope(const float* bp, int n, int i, int half) {
  int lo = i - half < 0 ? 0 : i - half;
  int hi = i + half + 1 > n ? n : i + half + 1;
  float m = 0;
  for (int k = lo; k < hi; k++) {
    float v = fabsf(diff_at(bp, n, k));
    if (v > m) m = v;
  }
  return m;
}

struct PtState {
  int32_t qrs[MAX_QRS];
  int n_qrs;
  int32_t rr[MAX_RR];
  int n_rr;
  int32_t pend_i[MAX_PENDING];
  float pend_v[MAX_PENDING];
  int n_pend;
  int refr;
  int max_rr;
};

static void accept(PtState* s, int32_t p) {
  if (s->n_qrs > 0) {
    int32_t interval = p - s->qrs[s->n_qrs - 1];
    if (interval >= s->refr && interval <= s->max_rr) {
      if (s->n_rr == MAX_RR) {
        for (int i = 1; i < MAX_RR; i++) s->rr[i - 1] = s->rr[i];
        s->n_rr--;
      }
      s->rr[s->n_rr++] = interval;
    }
  }
  if (s->n_qrs < MAX_QRS) s->qrs[s->n_qrs++] = p;
}

static void pend_push(PtState* s, int32_t i, float v) {
  if (s->n_pend == MAX_PENDING) {  // bỏ ứng viên cũ nhất
    for (int k = 1; k < MAX_PENDING; k++) {
      s->pend_i[k - 1] = s->pend_i[k];
      s->pend_v[k - 1] = s->pend_v[k];
    }
    s->n_pend--;
  }
  s->pend_i[s->n_pend] = i;
  s->pend_v[s->n_pend] = v;
  s->n_pend++;
}

int ecg_detect_r_peaks(float* x, int n, float fs, float* mwi, int32_t* peaks, int max_peaks) {
  if (n < (int)fs) return 0;
  static PtState st;  // static để không chiếm stack (~1,5 KB)
  PtState* s = &st;
  s->n_qrs = s->n_rr = s->n_pend = 0;

  float* bp = x;
  dsp_filtfilt_bandpass(bp, n, 5.0f, 15.0f, fs);

  // cực tính
  int edge = (int)(0.5f * fs);
  int r0 = 0, r1 = n;
  if (n > 4 * edge) { r0 = edge; r1 = n - edge; }
  float vmax = bp[r0], vmin = bp[r0];
  for (int i = r0; i < r1; i++) {
    if (bp[i] > vmax) vmax = bp[i];
    if (bp[i] < vmin) vmin = bp[i];
  }
  float sign = (vmax >= -vmin) ? 1.0f : -1.0f;

  // MWI = trung bình trượt có tâm của (đạo hàm)^2, độ rộng 150 ms
  int w = (int)lroundf(0.150f * fs);
  int half = w / 2;
  {
    double sum = 0;
    int lo = 0, hi = (half + 1 < n) ? half + 1 : n;
    for (int k = lo; k < hi; k++) { float d = diff_at(bp, n, k); sum += (double)d * d; }
    for (int i = 0; i < n; i++) {
      int nlo = i - half < 0 ? 0 : i - half;
      int nhi = i + half + 1 > n ? n : i + half + 1;
      while (hi < nhi) { float d = diff_at(bp, n, hi); sum += (double)d * d; hi++; }
      while (lo < nlo) { float d = diff_at(bp, n, lo); sum -= (double)d * d; lo++; }
      double v = sum / (double)(hi - lo);
      mwi[i] = (float)(v > 0 ? v : 0);
    }
  }

  s->refr = (int)lroundf(0.200f * fs);
  s->max_rr = (int)(3 * fs);
  int twin = (int)lroundf(0.360f * fs);

  int init = n < (int)(2 * fs) ? n : (int)(2 * fs);
  float mx = 0;
  double mean = 0;
  for (int i = 0; i < init; i++) {
    if (mwi[i] > mx) mx = mwi[i];
    mean += mwi[i];
  }
  mean /= init;
  float spki = 0.25f * mx;
  float npki = 0.5f * (float)mean;
  float thr = npki + 0.25f * (spki - npki);

  for (int p = 1; p < n - 1; p++) {
    if (!(mwi[p] > mwi[p - 1] && mwi[p] >= mwi[p + 1])) continue;
    float v = mwi[p];

    // searchback
    if (s->n_qrs > 0 && s->n_rr >= 2) {
      float rr_avg = 0;
      for (int k = 0; k < s->n_rr; k++) rr_avg += (float)s->rr[k];
      rr_avg /= (float)s->n_rr;
      int32_t last = s->qrs[s->n_qrs - 1];
      if ((float)(p - last) > 1.66f * rr_avg) {
        int best = -1;
        for (int k = 0; k < s->n_pend; k++) {
          if (s->pend_i[k] - last >= s->refr && s->pend_v[k] > 0.5f * thr &&
              (best < 0 || s->pend_v[k] > s->pend_v[best]))
            best = k;
        }
        if (best >= 0) {
          int32_t bi = s->pend_i[best];
          float bv = s->pend_v[best];
          accept(s, bi);
          spki = 0.25f * bv + 0.75f * spki;
          thr = npki + 0.25f * (spki - npki);
          int m = 0;
          for (int k = 0; k < s->n_pend; k++) {
            if (s->pend_i[k] > bi) {
              s->pend_i[m] = s->pend_i[k];
              s->pend_v[m] = s->pend_v[k];
              m++;
            }
          }
          s->n_pend = m;
        }
      }
    }

    // thời gian trơ
    if (s->n_qrs > 0 && p - s->qrs[s->n_qrs - 1] < s->refr) {
      if (v > mwi[s->qrs[s->n_qrs - 1]]) {
        s->qrs[s->n_qrs - 1] = p;
        if (s->n_qrs >= 2 && s->n_rr > 0) s->rr[s->n_rr - 1] = s->qrs[s->n_qrs - 1] - s->qrs[s->n_qrs - 2];
      }
      continue;
    }

    if (v > thr) {
      if (s->n_qrs > 0 && p - s->qrs[s->n_qrs - 1] < twin &&
          max_slope(bp, n, p, half) < 0.5f * max_slope(bp, n, s->qrs[s->n_qrs - 1], half)) {
        npki = 0.125f * v + 0.875f * npki;  // sóng T
        pend_push(s, p, v);
      } else {
        accept(s, p);
        spki = 0.125f * v + 0.875f * spki;
        s->n_pend = 0;
      }
    } else {
      npki = 0.125f * v + 0.875f * npki;
      pend_push(s, p, v);
    }
    thr = npki + 0.25f * (spki - npki);
  }

  // tinh chỉnh vị trí R
  int r_win = (int)lroundf(0.100f * fs);
  int count = 0;
  for (int k = 0; k < s->n_qrs; k++) {
    int q = s->qrs[k];
    int lo = q - r_win < 0 ? 0 : q - r_win;
    int hi = q + r_win + 1 > n ? n : q + r_win + 1;
    int best = lo;
    for (int i = lo; i < hi; i++)
      if (sign * bp[i] > sign * bp[best]) best = i;
    if ((count == 0 || best - peaks[count - 1] >= s->refr) && count < max_peaks) peaks[count++] = best;
  }
  return count;
}

float ecg_heart_rate(const int32_t* peaks, int n_peaks, float fs, float* rr_median_ms) {
  *rr_median_ms = 0;
  if (n_peaks < 2) return 0.0f;
  static float rr[MAX_QRS];
  int m = 0;
  for (int i = 1; i < n_peaks && m < MAX_QRS; i++) rr[m++] = (float)(peaks[i] - peaks[i - 1]) / fs;
  float med = dsp_median_inplace(rr, m);
  *rr_median_ms = med * 1000.0f;
  return 60.0f / med;
}
