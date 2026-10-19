// pat.cpp — xem pat.h / algorithm/hwalgo/pat.py
#include "pat.h"

#include <math.h>
#include <string.h>

#include "dsp.h"

static const float WIN_LO_MS = 100.0f, WIN_HI_MS = 500.0f;
static const float PAT_MIN_MS = 80.0f, PAT_MAX_MS = 600.0f;
static const int MIN_BEATS = 8;

// chỉ số đầu tiên j có t(j) >= v  (giống numpy.searchsorted side='left')
static int search_idx(double t0, double dt, int n, double v) {
  double f = (v - t0) / dt;
  int j = (int)ceil(f - 1e-9);
  if (j < 0) j = 0;
  if (j > n) j = n;
  return j;
}

void pat_compute(const float* r_times_ms, int n_r, float* p, int n, double t0, double dt, bool invert,
                 float* scratch, PatResult* out) {
  memset(out, 0, sizeof(*out));
  out->n_beats = n_r;
  out->status = PAT_LOW_QUALITY;
  if (n < 10 || n_r == 0) return;
  if (invert)
    for (int i = 0; i < n; i++) p[i] = -p[i];
  float fs = (float)(1000.0 / dt);
  dsp_filtfilt_bandpass(p, n, 0.5f, 8.0f, fs);

  float* pats = scratch;         // n_r
  float* tmp = scratch + n_r;    // n_r
  int m = 0;
  for (int b = 0; b < n_r; b++) {
    double tr = r_times_ms[b];
    int i0 = search_idx(t0, dt, n, tr + WIN_LO_MS);
    int i1 = search_idx(t0, dt, n, tr + WIN_HI_MS);
    if (i0 < 1 || i1 >= n || i1 - i0 < 3) continue;
    // điểm dốc nhất (đạo hàm có tâm theo thời gian)
    int k = i0;
    float dk = -1e30f;
    for (int j = i0; j < i1; j++) {
      float d = (j >= 1 && j < n - 1) ? (float)((p[j + 1] - p[j - 1]) / (2.0 * dt)) : 0.0f;
      if (d > dk) { dk = d; k = j; }
    }
    if (dk <= 0) continue;
    int j0 = search_idx(t0, dt, n, tr);
    float pmin = p[j0];
    for (int j = j0; j <= k; j++)
      if (p[j] < pmin) pmin = p[j];
    double tk = t0 + k * dt;
    double t_foot = tk - (p[k] - pmin) / dk;
    float pat = (float)(t_foot - tr);
    if (pat >= PAT_MIN_MS && pat <= PAT_MAX_MS) pats[m++] = pat;
  }
  out->n_valid = m;
  if (m < MIN_BEATS) return;

  float med = dsp_median_copy(pats, m, tmp);
  for (int i = 0; i < m; i++) tmp[i] = fabsf(pats[i] - med);
  float mad = dsp_median_inplace(tmp, m) * 1.4826f;
  float lim = 3.0f * mad > 5.0f ? 3.0f * mad : 5.0f;
  int kept = 0;
  for (int i = 0; i < m; i++)
    if (fabsf(pats[i] - med) <= lim) tmp[kept++] = pats[i];
  out->n_valid = kept;
  if (kept < MIN_BEATS) return;
  dsp_sort(tmp, kept);
  out->pat_ms = dsp_percentile_sorted(tmp, kept, 0.5f);
  out->iqr_ms = dsp_percentile_sorted(tmp, kept, 0.75f) - dsp_percentile_sorted(tmp, kept, 0.25f);
  out->status = PAT_OK;
}
