// host_test.cpp — chạy thuật toán C của firmware trên máy tính (không cần board).
// Được gọi bởi run_host_tests.py để so sánh với bản Python.
//
//   g++ -O2 -std=c++17 -I../health_watch host_test.cpp ../health_watch/{dsp,hr_ppg,spo2,ecg_rpeak,pat,fall_detect}.cpp -o host_test
//   ./host_test hr   <fs> <invert 0|1> <x.csv>
//   ./host_test spo2 <fs> <red_ir.csv>
//   ./host_test ecg  <fs> <x.csv>
//   ./host_test pat  <r_ms.csv> <ppg.csv> <t0_ms> <dt_ms>
//   ./host_test fall <fs> <acc.csv>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

#include "ecg_rpeak.h"
#include "fall_detect.h"
#include "hr_ppg.h"
#include "pat.h"
#include "spo2.h"

static std::vector<std::vector<float>> read_csv(const char* path) {
  std::vector<std::vector<float>> rows;
  FILE* f = fopen(path, "r");
  if (!f) { perror(path); exit(1); }
  char line[512];
  while (fgets(line, sizeof line, f)) {
    std::vector<float> r;
    char* p = line;
    while (*p) {
      char* end;
      float v = strtof(p, &end);
      if (end == p) break;
      r.push_back(v);
      p = end;
      while (*p == ',' || *p == ' ') p++;
    }
    if (!r.empty()) rows.push_back(r);
  }
  fclose(f);
  return rows;
}

int main(int argc, char** argv) {
  if (argc < 3) { fprintf(stderr, "thiếu tham số\n"); return 1; }
  std::string mode = argv[1];

  if (mode == "hr") {
    float fs = atof(argv[2]);
    bool inv = atoi(argv[3]);
    auto rows = read_csv(argv[4]);
    HrEstimator h;
    hr_init(&h, fs, inv, 0);
    int step = (int)(fs + 0.5f);
    for (size_t i = 0; i < rows.size(); i++) {
      hr_update(&h, rows[i][0]);
      if ((i + 1) % step == 0) {
        uint8_t q;
        float bpm = hr_get(&h, &q);
        printf("%.4f,%u\n", bpm, q);
      }
    }
  } else if (mode == "spo2") {
    float fs = atof(argv[2]);
    auto rows = read_csv(argv[3]);
    int n = rows.size();
    std::vector<float> red(n), ir(n), rb(n), ib(n), ra(64), co(64);
    for (int i = 0; i < n; i++) { red[i] = rows[i][0]; ir[i] = rows[i][1]; }
    Spo2Coeffs k = {-45.060f, 30.354f, 94.845f};
    Spo2Result r;
    spo2_compute(red.data(), ir.data(), n, fs, &k, rb.data(), ib.data(), ra.data(), co.data(), 64, &r);
    printf("%d,%.4f,%.5f,%d,%d,%d\n", r.status, r.spo2, r.ratio, r.quality, r.n_valid, r.n_windows);
  } else if (mode == "ecg") {
    float fs = atof(argv[2]);
    auto rows = read_csv(argv[3]);
    int n = rows.size();
    std::vector<float> x(n), mwi(n);
    for (int i = 0; i < n; i++) x[i] = rows[i][0];
    std::vector<int32_t> peaks(400);
    int c = ecg_detect_r_peaks(x.data(), n, fs, mwi.data(), peaks.data(), 400);
    for (int i = 0; i < c; i++) printf("%d\n", peaks[i]);
  } else if (mode == "pat") {
    auto r = read_csv(argv[2]);
    auto p = read_csv(argv[3]);
    double t0 = atof(argv[4]), dt = atof(argv[5]);
    std::vector<float> rt(r.size()), pp(p.size()), scratch(2 * r.size() + 2);
    for (size_t i = 0; i < r.size(); i++) rt[i] = r[i][0];
    for (size_t i = 0; i < p.size(); i++) pp[i] = p[i][0];
    PatResult res;
    pat_compute(rt.data(), rt.size(), pp.data(), pp.size(), t0, dt, true, scratch.data(), &res);
    printf("%d,%.4f,%.4f,%d,%d\n", res.status, res.pat_ms, res.iqr_ms, res.n_valid, res.n_beats);
  } else if (mode == "fall") {
    float fs = atof(argv[2]);
    auto rows = read_csv(argv[3]);
    FallParams prm;
    fall_default_params(&prm, fs);
    FallDetector d;
    fall_init(&d, &prm);
    for (size_t i = 0; i < rows.size(); i++) {
      FallEvent ev = fall_update(&d, rows[i][0], rows[i][1], rows[i][2]);
      if (ev.type != FD_EV_NONE)
        printf("%zu,%d,%.4f,%.3f,%d\n", i, ev.type, ev.peak_g, ev.angle_deg, ev.freefall ? 1 : 0);
    }
  } else {
    fprintf(stderr, "mode không hợp lệ\n");
    return 1;
  }
  return 0;
}
