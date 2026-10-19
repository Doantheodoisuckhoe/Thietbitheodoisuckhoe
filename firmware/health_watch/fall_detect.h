// fall_detect.h — phát hiện té ngã "va chạm mạnh rồi bất động 30 s".
// Port 1-1 từ algorithm/hwalgo/fall.py (đọc docstring ở đó).
#pragma once
#include <stdint.h>

enum FallState { FD_IDLE = 0, FD_SETTLE = 1, FD_CHECK = 2, FD_COOLDOWN = 3 };
enum FallEventType { FD_EV_NONE = 0, FD_EV_IMPACT = 1, FD_EV_FALL = 2 };

struct FallEvent {
  uint8_t type;
  float peak_g;
  float angle_deg;
  bool freefall;
};

struct FallParams {
  float fs;
  float impact_g;
  float settle_s;
  float still_s;
  float block_s;
  float block_std_g;
  int max_active_blocks;
  float freefall_g;
  float freefall_min_s;
  float freefall_window_s;
  float cooldown_s;
  float activity_thr_g;
};

struct FallDetector {
  // tham số (đã đổi sang số mẫu)
  float fs, impact_g, block_std_g, freefall_g, activity_thr_g, g_alpha;
  int32_t settle_n, block_n, n_blocks, max_active_blocks, freefall_min_n, freefall_window_n, cooldown_n;
  // trạng thái
  uint8_t state;
  int32_t n, state_n, ff_count, last_ff_n;
  float g_lp[3], pre_g[3];
  bool g_init;
  float peak_g;
  bool had_ff;
  int32_t blk_cnt, blocks_done, active_blocks, post_cnt;
  double blk_sum, blk_sq;
  double post_sum[3];
  uint32_t activity_count;
  uint32_t still_n;
};

void fall_default_params(FallParams* p, float fs);
void fall_init(FallDetector* d, const FallParams* p);
void fall_reset(FallDetector* d);
FallEvent fall_update(FallDetector* d, float ax, float ay, float az);  // đơn vị g
bool fall_cancel(FallDetector* d);       // nút bấm huỷ trong lúc đếm ngược
bool fall_is_checking(const FallDetector* d);
uint32_t fall_take_activity(FallDetector* d);
float fall_still_seconds(const FallDetector* d);
