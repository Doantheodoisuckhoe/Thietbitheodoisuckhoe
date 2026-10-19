// app.cpp — toàn bộ logic firmware (xem mô tả trong health_watch.ino)
#include <Arduino.h>
#include <Wire.h>
#include <bluefruit.h>

#include "ad8232.h"
#include "ble_link.h"
#include "config.h"
#include "ecg_rpeak.h"
#include "fall_detect.h"
#include "hr_ppg.h"
#include "max30101.h"
#include "pat.h"
#include "power_ui.h"
#include "protocol.h"
#include "sensors_misc.h"
#include "spo2.h"
#include "app.h"

#if defined(WIRE_INTERFACES_COUNT) && WIRE_INTERFACES_COUNT > 1
#define IMU_WIRE Wire1  // IMU trên XIAO Sense nằm ở bus I2C nội
#else
#define IMU_WIRE Wire
#endif

// -----------------------------------------------------------------------------
// Cảm biến & thuật toán
// -----------------------------------------------------------------------------
Max30101 ppg;
Tmp117 tmp;
Lsm6ds3 imu;
HrEstimator hrEst;
FallDetector fallDet;

// -----------------------------------------------------------------------------
// Bộ đệm dùng chung (các phiên ECG và SpO2 không chạy đồng thời) ~ 90 KB RAM
// -----------------------------------------------------------------------------
#define ECG_MAX_N ((int)(ECG_MAX_DURATION_S * ECG_FS + 64))
#define PAT_PPG_MAX_N ((int)(ECG_MAX_DURATION_S * PPG_PAT_FS + 64))
#define SPO2_N ((int)(SPO2_DURATION_S * PPG_SPO2_FS))
#define MAX_BEATS 200
static float bufA[ECG_MAX_N];        // ECG (ADC) -> band-pass | SpO2: đỏ, IR
static float bufB[ECG_MAX_N];        // MWI                  | SpO2: đỏ, IR đã lọc
static float bufPpg[PAT_PPG_MAX_N];  // PPG trong phiên ECG
static int32_t peaks[MAX_BEATS];
static float rTimes[MAX_BEATS];
static float patScratch[2 * MAX_BEATS];
static_assert(2 * SPO2_N <= ECG_MAX_N, "bufA không đủ cho SpO2");

// -----------------------------------------------------------------------------
// Trạng thái hệ thống
// -----------------------------------------------------------------------------
enum Mode { MODE_NORMAL, MODE_SPO2, MODE_ECG };
static Mode mode = MODE_NORMAL;

static uint32_t epochOffset = 0;  // epoch = uptime_s + epochOffset
static bool timeSynced = false;
static bool rawStream = RAW_STREAM_DEFAULT;
static uint8_t vitalsInterval = VITALS_INTERVAL_S;

static uint16_t vitalsSeq = 0, eventSeq = 0;
static float tempSum = 0;
static int tempCount = 0;
static float lastTemp = NAN;
static uint16_t batteryMv = 0;
static uint8_t batteryPct = 100;
static bool charging = false;
static bool lowBatteryNotified = false;
static bool worn = false;

static uint8_t pendingSpo2 = 0, pendingSpo2Q = 0;
static uint32_t nextSpo2Ms = 60000;  // lần đo SpO2 đầu tiên sau 1 phút

static uint32_t lastVitalsMs = 0, lastTempMs = 0, lastBattMs = 0, lastPpgReadMs = 0;
static uint32_t lastEventTryMs = 0;

static inline uint32_t uptimeS() { return millis() / 1000; }

// -----------------------------------------------------------------------------
// Hàng đợi gói VITALS và EVENT (giữ lại khi mất kết nối điện thoại)
// Gói lưu timestamp = uptime; đổi sang epoch lúc gửi nếu đã đồng bộ giờ.
// -----------------------------------------------------------------------------
template <typename T, int N>
struct Ring {
  T items[N];
  int head = 0, count = 0;
  void push(const T& v) {
    int idx = (head + count) % N;
    if (count == N) {  // đầy -> ghi đè gói cũ nhất
      items[head] = v;
      head = (head + 1) % N;
    } else {
      items[idx] = v;
      count++;
    }
  }
  T* front() { return count ? &items[head] : nullptr; }
  void pop() {
    if (count) {
      head = (head + 1) % N;
      count--;
    }
  }
};
static Ring<VitalsPacket, VITALS_QUEUE_LEN> vitalsQ;
static Ring<EventPacket, EVENT_QUEUE_LEN> eventQ;

template <typename P>
static void stampForSend(P& pkt) {
  if (timeSynced && !(pkt.flags & FLAG_TIME_SYNCED)) {
    pkt.timestamp += epochOffset;
    pkt.flags |= FLAG_TIME_SYNCED;
  }
}

static uint32_t stampNow(uint8_t* flags) {
  uint32_t ts = uptimeS();
  if (timeSynced) {
    ts += epochOffset;
    *flags |= FLAG_TIME_SYNCED;
  }
  return ts;
}

static void logf(const char* fmt, ...) {
  if (!Serial) return;
  char buf[160];
  va_list ap;
  va_start(ap, fmt);
  vsnprintf(buf, sizeof buf, fmt, ap);
  va_end(ap);
  Serial.print("# ");
  Serial.println(buf);
}

static void queueEvent(uint8_t type, int16_t v1, int16_t v2, uint16_t v3) {
  EventPacket e = {};
  e.version = PROTO_VERSION;
  e.type = type;
  e.seq = eventSeq++;
  e.timestamp = uptimeS();  // đổi sang epoch khi gửi
  e.value1 = v1;
  e.value2 = v2;
  e.value3 = v3;
  eventQ.push(e);
  lastEventTryMs = 0;  // gửi ngay
  logf("EVENT type=%u v1=%d v2=%d v3=%u", type, v1, v2, v3);
}

// =============================================================================
// SpO2 — phiên đo 30 s (đỏ + IR 100 Hz)
// =============================================================================
static int spo2N = 0;
static uint32_t spo2Activity = 0;

static void startSpo2() {
  if (mode != MODE_NORMAL || !ppg.present()) return;
  mode = MODE_SPO2;
  spo2N = 0;
  spo2Activity = 0;
  ppg.setMode(Max30101::MODE_SPO2);
  logf("SpO2: bắt đầu đo %d s", SPO2_DURATION_S);
}

static void finishSpo2() {
  float* red = bufA;
  float* ir = bufA + SPO2_N;
  static float ratios[32], corrs[32];
  Spo2Coeffs k = {SPO2_COEF_A, SPO2_COEF_B, SPO2_COEF_C};
  Spo2Result r;
  if (spo2Activity > SPO2_MOTION_MAX_ACTIVITY) {
    r = {};
    r.status = SPO2_MOTION;
  } else {
    spo2_compute(red, ir, spo2N, PPG_SPO2_FS, &k, bufB, bufB + SPO2_N, ratios, corrs, 32, &r);
  }
  logf("SPO2 status=%u spo2=%.1f R=%.4f q=%u win=%d/%d act=%lu", r.status, r.spo2, r.ratio, r.quality,
       r.n_valid, r.n_windows, (unsigned long)spo2Activity);
  bool recheck = true;
  if (r.status == SPO2_OK) {
    pendingSpo2 = (uint8_t)lroundf(r.spo2);
    pendingSpo2Q = r.quality;
    recheck = pendingSpo2 < SPO2_RECHECK_BELOW;  // thấp -> đo lại sớm để xác nhận
  }
  nextSpo2Ms = millis() + (recheck ? SPO2_RECHECK_MIN : SPO2_PERIOD_MIN) * 60000UL;
  ppg.setMode(Max30101::MODE_HR_GREEN);
  hr_reset(&hrEst);
  mode = MODE_NORMAL;
}

static void serviceSpo2() {
  static uint32_t samples[32 * 2];
  bool ovf;
  int n = ppg.readFifo(samples, 32, &ovf);
  for (int i = 0; i < n && spo2N < SPO2_N; i++) {
    bufA[spo2N] = (float)samples[2 * i];               // đỏ
    bufA[SPO2_N + spo2N] = (float)samples[2 * i + 1];  // IR
    if (rawStream && Serial) Serial.printf("S,%lu,%lu,%lu\n", millis(), samples[2 * i], samples[2 * i + 1]);
    spo2N++;
  }
  if (spo2N >= SPO2_N) finishSpo2();
}

// =============================================================================
// ECG + PAT — phiên đo theo yêu cầu
// =============================================================================
struct LinFit {  // hồi quy t = a + b*i để gán thời gian cho từng mẫu
  double sx = 0, sy = 0, sxx = 0, sxy = 0;
  int n = 0;
  void reset() { sx = sy = sxx = sxy = 0; n = 0; }
  void add(double x, double y) { sx += x; sy += y; sxx += x * x; sxy += x * y; n++; }
  bool solve(double* a, double* b, double nominal_dt) const {
    double den = n * sxx - sx * sx;
    if (n < 3 || fabs(den) < 1e-9) { *b = nominal_dt; *a = n ? (sy - *b * sx) / n : 0; return false; }
    *b = (n * sxy - sx * sy) / den;
    *a = (sy - *b * sx) / n;
    return true;
  }
};

static struct {
  bool waitingLeads;
  uint8_t session;
  uint8_t durationS;
  uint32_t waitStartMs, startMs;
  uint32_t t0Us;
  int nEcg, nPpg;
  uint16_t pktSeq;
  uint32_t leadOffSamples;
  bool leadOffNow;
  uint32_t lastLeadCheckMs, leadOnSinceMs;
  LinFit fitE, fitP;
  uint8_t pkt[6 + 2 * ECG_SAMPLES_PER_PACKET_MAX];
  int pktCount;
} es;

static void sendEcgResult(uint8_t status, uint8_t hr, uint8_t q, uint8_t nBeats, float pat, float iqr, uint8_t nPat,
                          uint16_t rrMs) {
  EcgResultPacket r = {};
  r.version = PROTO_VERSION;
  r.status = status;
  r.session = es.session;
  r.n_beats = nBeats;
  r.timestamp = stampNow(&r.flags);
  r.hr_bpm = hr;
  r.quality = q;
  r.pat_ms_x10 = (uint16_t)lroundf(pat * 10);
  r.pat_iqr_x10 = (uint16_t)lroundf(iqr * 10);
  r.n_pat = nPat;
  r.fs_hz = (uint16_t)ECG_FS;
  r.n_samples = (uint16_t)es.nEcg;
  r.rr_ms = rrMs;
  BleLink::sendEcgResult(r);
  logf("ECG_RESULT status=%u hr=%u q=%u beats=%u PAT=%.1f iqr=%.1f nPat=%u", status, hr, q, nBeats, pat, iqr, nPat);
}

static void startEcg(uint8_t durationS) {
  es.session++;
  if (mode != MODE_NORMAL) { sendEcgResult(ECG_ST_BUSY, 0, 0, 0, 0, 0, 0, 0); return; }
  if (charging) { sendEcgResult(ECG_ST_CHARGING, 0, 0, 0, 0, 0, 0, 0); return; }  // AN TOÀN ĐIỆN
  if (durationS == 0 || durationS > ECG_MAX_DURATION_S) durationS = ECG_DURATION_S;
  mode = MODE_ECG;
  es.durationS = durationS;
  es.waitingLeads = true;
  es.waitStartMs = millis();
  es.nEcg = es.nPpg = 0;
  es.pktSeq = 0;
  es.pktCount = 0;
  es.leadOffSamples = 0;
  es.leadOffNow = true;
  es.lastLeadCheckMs = 0;
  es.leadOnSinceMs = 0;
  es.fitE.reset();
  es.fitP.reset();
  Ad8232::start();
  logf("ECG: đặt ngón tay lên điện cực trên mặt đồng hồ...");
}

static void stopEcgHardware() {
  Ad8232::stop();
  ppg.setMode(Max30101::MODE_HR_GREEN);
  hr_reset(&hrEst);
  mode = MODE_NORMAL;
}

static void abortEcg(uint8_t status) {
  stopEcgHardware();
  sendEcgResult(status, 0, 0, 0, 0, 0, 0, 0);
}

static void flushEcgPacket() {
  if (es.pktCount == 0) return;
  EcgDataHeader h = {es.session, (uint8_t)(es.leadOffNow ? ECG_FLAG_LEAD_OFF : 0), es.pktSeq++,
                     (uint8_t)es.pktCount, 0};
  memcpy(es.pkt, &h, sizeof h);
  BleLink::sendEcgData(es.pkt, sizeof h + 2 * es.pktCount);  // mất gói thì chỉ ảnh hưởng hiển thị
  es.pktCount = 0;
}

static void finishEcg() {
  stopEcgHardware();
  double aE, bE, aP, bP;
  es.fitE.solve(&aE, &bE, 1000.0 / ECG_FS);
  es.fitP.solve(&aP, &bP, 1000.0 / PPG_PAT_FS);
  float leadOffFrac = es.nEcg ? (float)es.leadOffSamples / es.nEcg : 1.0f;

  int nPeaks = ecg_detect_r_peaks(bufA, es.nEcg, ECG_FS, bufB, peaks, MAX_BEATS);
  float rrMs = 0;
  float hr = ecg_heart_rate(peaks, nPeaks, ECG_FS, &rrMs);
  for (int i = 0; i < nPeaks; i++) rTimes[i] = (float)(aE + bE * peaks[i]);

  PatResult pr = {};
  if (es.nPpg > 100) pat_compute(rTimes, nPeaks, bufPpg, es.nPpg, aP, bP, true, patScratch, &pr);

  uint8_t status = ECG_ST_OK;
  if (leadOffFrac > 0.2f) status = ECG_ST_LEAD_OFF;
  else if (nPeaks < (int)(0.6f * es.durationS)) status = ECG_ST_LOW_QUALITY;
  uint8_t q = (uint8_t)(100.0f * (1.0f - leadOffFrac));
  float pat = pr.status == PAT_OK ? pr.pat_ms : 0.0f;
  float iqr = pr.status == PAT_OK ? pr.iqr_ms : 0.0f;
  logf("ECG fs_eff=%.2f Hz (mất %lu mẫu), PPG fs_eff=%.2f Hz", 1000.0 / bE, (unsigned long)Ad8232::dropped(),
       1000.0 / bP);
  sendEcgResult(status, (uint8_t)lroundf(hr), q, (uint8_t)min(nPeaks, 255), pat, iqr, (uint8_t)pr.n_valid,
                (uint16_t)lroundf(rrMs));
}

static void serviceEcg() {
  uint32_t now = millis();
  if (charging) { abortEcg(ECG_ST_CHARGING); return; }  // cắm sạc giữa chừng -> dừng ngay

  if (es.lastLeadCheckMs == 0 || now - es.lastLeadCheckMs >= 100) {
    es.lastLeadCheckMs = now;
    es.leadOffNow = Ad8232::leadOffNow();
  }

  static uint16_t eb[64];
  static bool lo[64];
  bool ovf;
  int ne = Ad8232::read(eb, lo, 64);
  double tE = (micros() - es.t0Us) / 1000.0;  // mốc thời gian ngay sau khi lấy mẫu ECG ra

  if (es.waitingLeads) {
    if (es.leadOffNow) {
      es.leadOnSinceMs = 0;
    } else if (es.leadOnSinceMs == 0) {
      es.leadOnSinceMs = now;
    }
    if (es.leadOnSinceMs && now - es.leadOnSinceMs >= 1000) {  // chạm ổn định 1 s -> bắt đầu ghi
      es.waitingLeads = false;
      es.startMs = now;
      es.t0Us = micros();
      ppg.setMode(Max30101::MODE_PAT_GREEN);
      Ad8232::start();  // xoá bộ đệm để mốc thời gian bắt đầu sạch
      sendEcgResult(ECG_ST_STARTED, 0, 0, 0, 0, 0, 0, 0);
      logf("ECG: bắt đầu ghi %u s", es.durationS);
    } else if (now - es.waitStartMs > ECG_LEAD_ON_TIMEOUT_S * 1000UL) {
      abortEcg(ECG_ST_LEAD_OFF);
    }
    return;
  }

  int maxEcg = (int)(es.durationS * ECG_FS);
  uint16_t perPkt = (BleLink::mtu() - 3 - sizeof(EcgDataHeader)) / 2;
  if (perPkt > ECG_SAMPLES_PER_PACKET_MAX) perPkt = ECG_SAMPLES_PER_PACKET_MAX;

  for (int i = 0; i < ne && es.nEcg < maxEcg; i++) {
    bufA[es.nEcg] = (float)eb[i];
    if (lo[i]) es.leadOffSamples++;
    int16_t s16 = (int16_t)eb[i] - ECG_ADC_MID;
    memcpy(&es.pkt[sizeof(EcgDataHeader) + 2 * es.pktCount], &s16, 2);
    if (++es.pktCount >= perPkt) flushEcgPacket();
    if (rawStream && Serial) Serial.printf("E,%.2f,%u\n", tE - (ne - 1 - i) * 1000.0 / ECG_FS, eb[i]);
    es.nEcg++;
  }
  if (ne > 0) es.fitE.add(es.nEcg - 1, tE);

  static uint32_t pb[32];
  int np = ppg.readFifo(pb, 32, &ovf);
  double tP = (micros() - es.t0Us) / 1000.0;  // mốc thời gian ngay sau khi đọc FIFO PPG
  for (int i = 0; i < np && es.nPpg < PAT_PPG_MAX_N; i++) {
    bufPpg[es.nPpg++] = (float)pb[i];
    if (rawStream && Serial)
      Serial.printf("P,%.2f,%lu\n", tP - (np - 1 - i) * 1000.0 / PPG_PAT_FS, (unsigned long)pb[i]);
  }
  if (np > 0) es.fitP.add(es.nPpg - 1, tP);

  if (es.nEcg >= maxEcg) {
    flushEcgPacket();
    finishEcg();
  }
}

// =============================================================================
// Chế độ thường: nhịp tim PPG xanh
// =============================================================================
static void serviceHr() {
  uint32_t now = millis();
  if (now - lastPpgReadMs < 100) return;
  lastPpgReadMs = now;
  static uint32_t samples[32];
  bool ovf;
  int n = ppg.readFifo(samples, 32, &ovf);
  for (int i = 0; i < n; i++) {
    hr_update(&hrEst, (float)samples[i]);
    if (rawStream && Serial) Serial.printf("G,%lu,%lu\n", now - (n - 1 - i) * 20, (unsigned long)samples[i]);
  }
  worn = hr_in_contact(&hrEst);
}

// =============================================================================
// IMU — té ngã, hoạt động
// =============================================================================
static void serviceImu() {
  float ax, ay, az;
  for (int k = 0; k < 4 && imu.read(&ax, &ay, &az); k++) {
    FallEvent ev = fall_update(&fallDet, ax, ay, az);
    if (mode == MODE_SPO2 && fallDet.still_n == 0) spo2Activity++;
    if (rawStream && Serial)
      Serial.printf("A,%lu,%d,%d,%d\n", millis(), (int)(ax * 1000), (int)(ay * 1000), (int)(az * 1000));
    if (ev.type == FD_EV_IMPACT) {
      Vibe::pattern(Vibe::PATTERN_IMPACT);  // báo người dùng: bấm nút nếu không sao
      queueEvent(EV_IMPACT, (int16_t)(ev.peak_g * 100), 0, ev.freefall ? 1 : 0);
    } else if (ev.type == FD_EV_FALL) {
      Vibe::pattern(Vibe::PATTERN_ALERT_SENT);
      queueEvent(EV_FALL, (int16_t)(ev.peak_g * 100), (int16_t)ev.angle_deg, ev.freefall ? 1 : 0);
    }
  }
}

static void serviceButton() {
  Button::Event b = Button::update();
  if (b == Button::LONG_HOLD) {
    Vibe::pattern(Vibe::PATTERN_ALERT_SENT);
    queueEvent(EV_SOS, 0, 0, 0);
  } else if (b == Button::SHORT_PRESS) {
    if (fall_cancel(&fallDet)) {
      Vibe::pattern(Vibe::PATTERN_CANCEL);
      queueEvent(EV_FALL_CANCELLED, 0, 0, 0);
    }
  }
}

// =============================================================================
// Nhiệt độ, pin, gói VITALS
// =============================================================================
static void serviceTempBattery() {
  uint32_t now = millis();
  if (now - lastTempMs >= TEMP_READ_INTERVAL_MS) {
    lastTempMs = now;
    float t;
    if (tmp.read(&t)) {
      lastTemp = t;
      tempSum += t;
      tempCount++;
      if (rawStream && Serial) Serial.printf("T,%lu,%.3f\n", now, t);
    }
  }
  // Không đọc pin khi đang đo ECG: ADC đang được ngắt TIMER4 dùng.
  if (mode != MODE_ECG && (lastBattMs == 0 || now - lastBattMs >= BATTERY_READ_INTERVAL_MS)) {
    lastBattMs = now;
    batteryMv = Power::readBatteryMv();
    batteryPct = Power::percentFromMv(batteryMv);
    BleLink::setBattery(batteryPct);
    if (!charging && batteryPct <= LOW_BATTERY_PCT && !lowBatteryNotified) {
      lowBatteryNotified = true;
      queueEvent(EV_LOW_BATTERY, batteryPct, 0, 0);
    }
    if (charging || batteryPct > LOW_BATTERY_PCT + 5) lowBatteryNotified = false;
  }
  charging = Power::usbPowered();
}

static void buildVitals() {
  VitalsPacket p = {};
  p.version = PROTO_VERSION;
  p.seq = vitalsSeq++;
  p.timestamp = uptimeS();  // đổi sang epoch khi gửi
  uint8_t q = 0;
  float hr = (mode == MODE_NORMAL && worn) ? hr_get(&hrEst, &q) : 0.0f;
  p.hr_bpm = (uint8_t)constrain(lroundf(hr), 0, 255);
  p.hr_quality = p.hr_bpm ? q : 0;
  p.spo2 = pendingSpo2;
  p.spo2_quality = pendingSpo2Q;
  pendingSpo2 = pendingSpo2Q = 0;
  p.skin_temp_c100 = tempCount ? (int16_t)lroundf(tempSum / tempCount * 100) : TEMP_NONE;
  tempSum = 0;
  tempCount = 0;
  uint32_t act = fall_take_activity(&fallDet);
  p.activity = act > 65535 ? 65535 : act;
  p.battery_pct = batteryPct;
  p.interval_s = vitalsInterval;
  p.battery_mv = batteryMv;
  if (worn) p.flags |= FLAG_WORN;
  if (charging) p.flags |= FLAG_CHARGING;
  if (fall_still_seconds(&fallDet) >= SPO2_STILL_REQUIRED_S) p.flags |= FLAG_STILL;
  if (batteryPct <= LOW_BATTERY_PCT) p.flags |= FLAG_LOW_BATTERY;
  vitalsQ.push(p);
  logf("VITALS hr=%u(q%u) spo2=%u temp=%.2f act=%u bat=%u%% worn=%d chg=%d", p.hr_bpm, p.hr_quality, p.spo2,
       p.skin_temp_c100 / 100.0f, p.activity, p.battery_pct, worn, charging);
}

static void serviceSending() {
  if (!BleLink::connected()) return;
  // chờ điện thoại đồng bộ giờ (tối đa 3 s sau khi kết nối)
  if (!timeSynced && millis() - BleLink::connectedSinceMs() < 3000) return;

  for (int k = 0; k < 4; k++) {
    VitalsPacket* p = vitalsQ.front();
    if (!p) break;
    VitalsPacket out = *p;
    stampForSend(out);
    if (!BleLink::sendVitals(out)) break;
    vitalsQ.pop();
  }
  EventPacket* e = eventQ.front();
  if (e && millis() - lastEventTryMs >= 1000) {
    lastEventTryMs = millis();
    EventPacket out = *e;
    stampForSend(out);
    if (BleLink::sendEvent(out)) eventQ.pop();  // chỉ xoá khi điện thoại đã xác nhận
  }
}

// =============================================================================
// Lệnh từ điện thoại (BLE) và từ cổng USB
// =============================================================================
static void handleCommand(const uint8_t* d, uint8_t len) {
  switch (d[0]) {
    case CMD_START_ECG: startEcg(len >= 2 ? d[1] : ECG_DURATION_S); break;
    case CMD_STOP_ECG:
      if (mode == MODE_ECG) abortEcg(ECG_ST_ABORTED);
      break;
    case CMD_START_SPO2: startSpo2(); break;
    case CMD_SET_TIME:
      if (len >= 5) {
        uint32_t epoch;
        memcpy(&epoch, d + 1, 4);
        epochOffset = epoch - uptimeS();
        timeSynced = true;
        logf("Đồng bộ giờ: %lu", (unsigned long)epoch);
      }
      break;
    case CMD_SET_INTERVAL:
      if (len >= 2 && d[1] >= 2) vitalsInterval = d[1];
      break;
    case CMD_SET_FALL:
      if (len >= 3) {
        FallParams p;
        fall_default_params(&p, IMU_FS);
        p.impact_g = d[1] / 10.0f;
        p.still_s = d[2];
        fall_init(&fallDet, &p);
        logf("Tham số té ngã: impact=%.1f g, still=%.0f s", p.impact_g, p.still_s);
      }
      break;
    case CMD_VIBRATE:
      if (len >= 3) {
        uint16_t ms;
        memcpy(&ms, d + 1, 2);
        Vibe::pulse(ms);
      }
      break;
    case CMD_ALERT_ACKED: Vibe::pattern(Vibe::PATTERN_ACK); break;
  }
}

static void serviceUsbCommands() {
  static char line[48];
  static int n = 0;
  while (Serial && Serial.available()) {
    char c = Serial.read();
    if (c == '\r') continue;
    if (c != '\n' && n < (int)sizeof(line) - 1) { line[n++] = c; continue; }
    line[n] = 0;
    n = 0;
    if (!strcmp(line, "ecg")) { uint8_t cmd[] = {CMD_START_ECG, ECG_DURATION_S}; handleCommand(cmd, 2); }
    else if (!strcmp(line, "spo2")) startSpo2();
    else if (!strcmp(line, "raw on")) rawStream = true;
    else if (!strcmp(line, "raw off")) rawStream = false;
    else if (!strcmp(line, "sos")) queueEvent(EV_SOS, 0, 0, 0);
    else if (!strncmp(line, "time ", 5)) {
      uint8_t cmd[5] = {CMD_SET_TIME};
      uint32_t ep = strtoul(line + 5, nullptr, 10);
      memcpy(cmd + 1, &ep, 4);
      handleCommand(cmd, 5);
    } else if (!strcmp(line, "status")) {
      logf("FW %s | mode=%d | BLE=%d mtu=%u | MAX30101=%d TMP117=%d IMU=%d | AD8232 tuột điện cực=%d", FW_VERSION,
           mode, BleLink::connected(), BleLink::mtu(), ppg.present(), tmp.present(), imu.present(),
           Ad8232::leadOffNow());
      logf("pin %u mV (%u%%) sạc=%d | worn=%d | nhiệt độ %.2f | hàng đợi vitals=%d event=%d", batteryMv,
           batteryPct, charging, worn, lastTemp, vitalsQ.count, eventQ.count);
    } else {
      logf("Lệnh: status | ecg | spo2 | raw on | raw off | sos | time <epoch>");
    }
  }
}

// =============================================================================
static void startWatchdog() {
#if USE_WATCHDOG
  NRF_WDT->CONFIG = (WDT_CONFIG_HALT_Pause << WDT_CONFIG_HALT_Pos) | (WDT_CONFIG_SLEEP_Run << WDT_CONFIG_SLEEP_Pos);
  NRF_WDT->CRV = 8 * 32768;  // 8 s
  NRF_WDT->RREN = WDT_RREN_RR0_Msk;
  NRF_WDT->TASKS_START = 1;
#endif
}

static inline void feedWatchdog() {
#if USE_WATCHDOG
  NRF_WDT->RR[0] = WDT_RR_RR_Reload;
#endif
}

void app_setup() {
  Serial.begin(115200);
  uint32_t t0 = millis();
  while (!Serial && millis() - t0 < 1500) delay(10);  // chờ USB ngắn (không bắt buộc)

#ifdef LED_RED
  pinMode(LED_RED, OUTPUT); digitalWrite(LED_RED, HIGH);  // LED tích cực mức thấp -> tắt
  pinMode(LED_GREEN, OUTPUT); digitalWrite(LED_GREEN, HIGH);
  pinMode(LED_BLUE, OUTPUT); digitalWrite(LED_BLUE, HIGH);
#endif

  Power::begin();
  Vibe::begin();
  Button::begin();
  Ad8232::begin();

  Wire.begin();
  Wire.setClock(400000);
  bool okPpg = ppg.begin(Wire);
  bool okTmp = tmp.begin(Wire);
  bool okImu = imu.begin(IMU_WIRE);

  hr_init(&hrEst, PPG_HR_FS, true, PPG_CONTACT_DC_MIN);
  FallParams fp;
  fall_default_params(&fp, IMU_FS);
  fp.impact_g = FALL_IMPACT_G;
  fp.still_s = FALL_STILL_S;
  fall_init(&fallDet, &fp);

  // Tên BLE: HealthWatch-XXXX (4 số hex cuối của địa chỉ chip)
  char name[24];
  snprintf(name, sizeof name, "%s-%04X", DEVICE_NAME_PREFIX, (unsigned)(NRF_FICR->DEVICEADDR[0] & 0xFFFF));
  BleLink::begin(name);

  charging = Power::usbPowered();
  logf("%s FW %s | MAX30101=%d TMP117=%d IMU=%d", name, FW_VERSION, okPpg, okTmp, okImu);
  Vibe::pulse(150);
  startWatchdog();
}

void app_loop() {
  feedWatchdog();
  uint32_t now = millis();

  serviceImu();
  serviceButton();
  serviceTempBattery();

  switch (mode) {
    case MODE_NORMAL:
      serviceHr();
      if ((int32_t)(now - nextSpo2Ms) >= 0) {
        if (worn && fall_still_seconds(&fallDet) >= SPO2_STILL_REQUIRED_S && !fall_is_checking(&fallDet))
          startSpo2();
        else
          nextSpo2Ms = now + 30000;  // chưa đứng yên -> thử lại sau 30 s
      }
      break;
    case MODE_SPO2: serviceSpo2(); break;
    case MODE_ECG: serviceEcg(); break;
  }

  if (now - lastVitalsMs >= vitalsInterval * 1000UL) {
    lastVitalsMs = now;
    buildVitals();
  }

  uint8_t cmd[20], len;
  while (BleLink::popCommand(cmd, &len)) handleCommand(cmd, len);
  serviceUsbCommands();
  serviceSending();
  Vibe::update();

  delay(mode == MODE_NORMAL ? 4 : 2);  // FreeRTOS cho CPU ngủ giữa các vòng
}
