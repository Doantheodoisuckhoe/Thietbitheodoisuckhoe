// fall_detect.cpp — xem fall_detect.h / algorithm/hwalgo/fall.py
#include "fall_detect.h"

#include <math.h>
#include <string.h>

void fall_default_params(FallParams* p, float fs) {
  p->fs = fs;
  p->impact_g = 2.8f;
  p->settle_s = 2.0f;
  p->still_s = 30.0f;
  p->block_s = 1.0f;
  p->block_std_g = 0.08f;
  p->max_active_blocks = 5;
  p->freefall_g = 0.6f;
  p->freefall_min_s = 0.06f;
  p->freefall_window_s = 1.0f;
  p->cooldown_s = 10.0f;
  p->activity_thr_g = 0.1f;
}

void fall_init(FallDetector* d, const FallParams* p) {
  d->fs = p->fs;
  d->impact_g = p->impact_g;
  d->settle_n = (int32_t)lroundf(p->settle_s * p->fs);
  d->block_n = (int32_t)lroundf(p->block_s * p->fs);
  d->n_blocks = (int32_t)lroundf(p->still_s / p->block_s);
  d->block_std_g = p->block_std_g;
  d->max_active_blocks = p->max_active_blocks;
  d->freefall_g = p->freefall_g;
  int32_t ffm = (int32_t)lroundf(p->freefall_min_s * p->fs);
  d->freefall_min_n = ffm < 1 ? 1 : ffm;
  d->freefall_window_n = (int32_t)lroundf(p->freefall_window_s * p->fs);
  d->cooldown_n = (int32_t)lroundf(p->cooldown_s * p->fs);
  d->activity_thr_g = p->activity_thr_g;
  d->g_alpha = 1.0f / p->fs;
  fall_reset(d);
}

void fall_reset(FallDetector* d) {
  d->state = FD_IDLE;
  d->n = d->state_n = d->ff_count = 0;
  d->last_ff_n = -1000000000;
  d->g_lp[0] = d->g_lp[1] = 0.0f;
  d->g_lp[2] = 1.0f;
  memcpy(d->pre_g, d->g_lp, sizeof(d->g_lp));
  d->g_init = false;
  d->peak_g = 0;
  d->had_ff = false;
  d->blk_cnt = d->blocks_done = d->active_blocks = d->post_cnt = 0;
  d->blk_sum = d->blk_sq = 0;
  d->post_sum[0] = d->post_sum[1] = d->post_sum[2] = 0;
  d->activity_count = 0;
  d->still_n = 0;
}

static void enter(FallDetector* d, uint8_t st) {
  d->state = st;
  d->state_n = 0;
}

static float angle_deg(const FallDetector* d) {
  if (d->post_cnt == 0) return 0.0f;
  double post[3] = {d->post_sum[0] / d->post_cnt, d->post_sum[1] / d->post_cnt, d->post_sum[2] / d->post_cnt};
  double dot = d->pre_g[0] * post[0] + d->pre_g[1] * post[1] + d->pre_g[2] * post[2];
  double na = sqrt((double)d->pre_g[0] * d->pre_g[0] + (double)d->pre_g[1] * d->pre_g[1] +
                   (double)d->pre_g[2] * d->pre_g[2]);
  double nb = sqrt(post[0] * post[0] + post[1] * post[1] + post[2] * post[2]);
  if (na < 1e-6 || nb < 1e-6) return 0.0f;
  double c = dot / (na * nb);
  if (c > 1) c = 1;
  if (c < -1) c = -1;
  return (float)(acos(c) * 180.0 / 3.14159265358979323846);
}

FallEvent fall_update(FallDetector* d, float ax, float ay, float az) {
  FallEvent ev = {FD_EV_NONE, 0, 0, false};
  float svm = sqrtf(ax * ax + ay * ay + az * az);
  d->n++;
  d->state_n++;

  if (fabsf(svm - 1.0f) > d->activity_thr_g) {
    d->activity_count++;
    d->still_n = 0;
  } else {
    d->still_n++;
  }

  if (svm < d->freefall_g) {
    d->ff_count++;
    if (d->ff_count >= d->freefall_min_n) d->last_ff_n = d->n;
  } else {
    d->ff_count = 0;
  }

  switch (d->state) {
    case FD_IDLE:
      if (!d->g_init) {
        d->g_lp[0] = ax; d->g_lp[1] = ay; d->g_lp[2] = az;
        d->g_init = true;
      } else {
        d->g_lp[0] += (ax - d->g_lp[0]) * d->g_alpha;
        d->g_lp[1] += (ay - d->g_lp[1]) * d->g_alpha;
        d->g_lp[2] += (az - d->g_lp[2]) * d->g_alpha;
      }
      if (svm >= d->impact_g) {
        memcpy(d->pre_g, d->g_lp, sizeof(d->g_lp));
        d->peak_g = svm;
        d->had_ff = (d->n - d->last_ff_n) <= d->freefall_window_n;
        enter(d, FD_SETTLE);
        ev.type = FD_EV_IMPACT;
        ev.peak_g = svm;
        ev.freefall = d->had_ff;
      }
      break;

    case FD_SETTLE:
      if (svm > d->peak_g) d->peak_g = svm;
      if (d->state_n >= d->settle_n) {
        enter(d, FD_CHECK);
        d->blk_cnt = d->blocks_done = d->active_blocks = d->post_cnt = 0;
        d->blk_sum = d->blk_sq = 0;
        d->post_sum[0] = d->post_sum[1] = d->post_sum[2] = 0;
      }
      break;

    case FD_CHECK:
      d->blk_cnt++;
      d->blk_sum += svm;
      d->blk_sq += (double)svm * svm;
      d->post_sum[0] += ax;
      d->post_sum[1] += ay;
      d->post_sum[2] += az;
      d->post_cnt++;
      if (d->blk_cnt >= d->block_n) {
        double mean = d->blk_sum / d->blk_cnt;
        double var = d->blk_sq / d->blk_cnt - mean * mean;
        if (var < 0) var = 0;
        if (sqrt(var) > d->block_std_g) d->active_blocks++;
        d->blocks_done++;
        d->blk_cnt = 0;
        d->blk_sum = d->blk_sq = 0;
        if (d->active_blocks > d->max_active_blocks) {
          enter(d, FD_IDLE);
        } else if (d->blocks_done >= d->n_blocks) {
          ev.type = FD_EV_FALL;
          ev.peak_g = d->peak_g;
          ev.angle_deg = angle_deg(d);
          ev.freefall = d->had_ff;
          enter(d, FD_COOLDOWN);
        }
      }
      break;

    case FD_COOLDOWN:
      if (d->state_n >= d->cooldown_n) enter(d, FD_IDLE);
      break;
  }
  return ev;
}

bool fall_cancel(FallDetector* d) {
  if (d->state == FD_SETTLE || d->state == FD_CHECK) {
    enter(d, FD_COOLDOWN);
    return true;
  }
  return false;
}

bool fall_is_checking(const FallDetector* d) { return d->state == FD_SETTLE || d->state == FD_CHECK; }

uint32_t fall_take_activity(FallDetector* d) {
  uint32_t c = d->activity_count;
  d->activity_count = 0;
  return c;
}

float fall_still_seconds(const FallDetector* d) { return (float)d->still_n / d->fs; }
