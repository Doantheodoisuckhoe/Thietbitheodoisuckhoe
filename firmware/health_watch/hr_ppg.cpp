// hr_ppg.cpp — xem hr_ppg.h / algorithm/hwalgo/hr_ppg.py
#include "hr_ppg.h"

#include <math.h>

static float median_ibis(const HrEstimator* h) {
  float tmp[HR_MAX_IBI];
  return dsp_median_copy(h->ibis, h->n_ibis, tmp);
}

void hr_init(HrEstimator* h, float fs, bool invert, float contact_dc_min) {
  h->fs = fs;
  h->invert = invert;
  h->amp_decay = expf(-1.0f / (2.5f * fs));
  h->thr_ratio = 0.4f;
  h->refr_init = 0.30f * fs;
  h->refr_min = 0.25f * fs;
  h->refr_max = 1.2f * fs;
  h->refr_ratio = 0.6f;
  h->ibi_min = 0.3f;
  h->ibi_max = 2.0f;
  h->outlier_ratio = 0.3f;
  h->max_outliers = 3;
  h->beat_timeout = 3.0f * fs;
  h->min_ibis = 4;
  h->dc_alpha = 1.0f / (2.0f * fs);
  h->contact_dc_min = contact_dc_min;
  bandpass_design(&h->bp, 0.5f, 4.0f, fs);
  hr_reset(h);
}

void hr_reset(HrEstimator* h) {
  bandpass_design(&h->bp, 0.5f, 4.0f, h->fs);
  h->started = false;
  h->n = 0;
  h->y1 = h->y2 = 0.0f;
  h->amp = 0.0f;
  h->last_peak = -1;
  h->n_ibis = 0;
  h->consec_outliers = 0;
  h->dc = 0.0f;
}

static void add_ibi(HrEstimator* h, float ibi) {
  if (ibi < h->ibi_min || ibi > h->ibi_max) return;
  if (h->n_ibis >= 3) {
    float med = median_ibis(h);
    if (fabsf(ibi - med) > h->outlier_ratio * med) {
      h->consec_outliers++;
      if (h->consec_outliers >= h->max_outliers) {
        h->ibis[0] = ibi;
        h->n_ibis = 1;
        h->consec_outliers = 0;
      }
      return;
    }
  }
  if (h->n_ibis < HR_MAX_IBI) {
    h->ibis[h->n_ibis++] = ibi;
  } else {  // bỏ phần tử cũ nhất
    for (int i = 1; i < HR_MAX_IBI; i++) h->ibis[i - 1] = h->ibis[i];
    h->ibis[HR_MAX_IBI - 1] = ibi;
  }
  h->consec_outliers = 0;
}

bool hr_update(HrEstimator* h, float x) {
  float s = h->invert ? -x : x;
  if (!h->started) {
    chain_reset_to(&h->bp, s);
    h->dc = x;
    h->started = true;
  }
  h->dc += (x - h->dc) * h->dc_alpha;
  float y = chain_process(&h->bp, s);
  h->amp *= h->amp_decay;

  bool beat = false;
  if (h->y1 > h->y2 && h->y1 >= y && h->y1 > 0.0f) {
    int32_t p = h->n - 1;
    float refr;
    if (h->n_ibis >= 2) {
      refr = h->refr_ratio * median_ibis(h) * h->fs;
      if (refr < h->refr_min) refr = h->refr_min;
      if (refr > h->refr_max) refr = h->refr_max;
    } else {
      refr = h->refr_init;
    }
    if (h->last_peak < 0 || (float)(p - h->last_peak) >= refr) {
      if (h->y1 >= h->thr_ratio * h->amp) {
        beat = true;
        if (h->y1 > h->amp) h->amp = h->y1;
        if (h->last_peak >= 0) add_ibi(h, (float)(p - h->last_peak) / h->fs);
        h->last_peak = p;
      }
    }
  }
  h->y2 = h->y1;
  h->y1 = y;
  h->n++;
  return beat;
}

bool hr_in_contact(const HrEstimator* h) {
  return h->contact_dc_min <= 0.0f || h->dc >= h->contact_dc_min;
}

float hr_get(HrEstimator* h, uint8_t* quality) {
  *quality = 0;
  if (!hr_in_contact(h)) return 0.0f;
  if (h->last_peak < 0 || (float)(h->n - h->last_peak) > h->beat_timeout) return 0.0f;
  if (h->n_ibis < h->min_ibis) return 0.0f;
  float med = median_ibis(h);
  float dev[HR_MAX_IBI], tmp[HR_MAX_IBI];
  for (int i = 0; i < h->n_ibis; i++) dev[i] = fabsf(h->ibis[i] - med);
  float mad = dsp_median_copy(dev, h->n_ibis, tmp);
  float q = 100.0f * (1.0f - (mad / med) / 0.15f) - 20.0f * (float)h->consec_outliers;
  if (q < 0) q = 0;
  if (q > 100) q = 100;
  *quality = (uint8_t)q;  // cắt phần thập phân như int() trong Python
  return 60.0f / med;
}
