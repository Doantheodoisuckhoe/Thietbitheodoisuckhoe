// max30101.cpp — xem max30101.h. Thanh ghi theo datasheet MAX30101 (Maxim).
#include "max30101.h"

#include "config.h"

namespace {
const uint8_t ADDR = 0x57;
const uint8_t REG_INT_STATUS1 = 0x00;
const uint8_t REG_INT_STATUS2 = 0x01;
const uint8_t REG_FIFO_WR_PTR = 0x04;
const uint8_t REG_OVF_COUNTER = 0x05;
const uint8_t REG_FIFO_RD_PTR = 0x06;
const uint8_t REG_FIFO_DATA = 0x07;
const uint8_t REG_FIFO_CONFIG = 0x08;
const uint8_t REG_MODE_CONFIG = 0x09;
const uint8_t REG_SPO2_CONFIG = 0x0A;
const uint8_t REG_LED1_PA = 0x0C;  // đỏ
const uint8_t REG_LED2_PA = 0x0D;  // hồng ngoại
const uint8_t REG_LED3_PA = 0x0E;  // xanh lá
const uint8_t REG_LED4_PA = 0x0F;  // xanh lá
const uint8_t REG_MULTI_LED1 = 0x11;
const uint8_t REG_MULTI_LED2 = 0x12;
const uint8_t REG_PART_ID = 0xFF;  // = 0x15

const uint8_t MODE_SHDN = 0x80;
const uint8_t MODE_RESET = 0x40;
const uint8_t MODE_SPO2_BITS = 0x03;   // đỏ + IR
const uint8_t MODE_MULTI_BITS = 0x07;  // multi-LED (dùng để chạy LED xanh)
const uint8_t SLOT_GREEN = 0x03;
const uint8_t SLOT_IR = 0x02;
// LED cho nhịp tim/PAT: xanh lá (LED3+LED4) hoặc hồng ngoại (LED2) — xem PPG_HR_USE_IR
#if PPG_HR_USE_IR
const uint8_t HR_SLOT = SLOT_IR, HR_IR_PA = PPG_IR_PA, HR_GREEN_PA = 0;
#else
const uint8_t HR_SLOT = SLOT_GREEN, HR_IR_PA = 0, HR_GREEN_PA = PPG_GREEN_PA;
#endif

// SPO2_CONFIG: [6:5] dải ADC, [4:2] tốc độ mẫu, [1:0] độ rộng xung
const uint8_t ADC_16384NA = 0x60;
const uint8_t SR_100 = 0x04;
const uint8_t SR_200 = 0x08;
const uint8_t PW_411US = 0x03;  // 18 bit
const uint8_t PW_215US = 0x02;  // 17 bit
// FIFO_CONFIG: [7:5] trung bình mẫu, bit4 rollover, [3:0] ngưỡng gần đầy
const uint8_t AVG_1 = 0x00;
const uint8_t AVG_2 = 0x20;
const uint8_t ROLLOVER = 0x10;
}  // namespace

bool Max30101::write8(uint8_t reg, uint8_t val) {
  wire_->beginTransmission(ADDR);
  wire_->write(reg);
  wire_->write(val);
  return wire_->endTransmission() == 0;
}

uint8_t Max30101::read8(uint8_t reg) {
  uint8_t v = 0;
  readBytes(reg, &v, 1);
  return v;
}

bool Max30101::readBytes(uint8_t reg, uint8_t* buf, int len) {
  wire_->beginTransmission(ADDR);
  wire_->write(reg);
  if (wire_->endTransmission(false) != 0) return false;
  int got = wire_->requestFrom((int)ADDR, len);
  for (int i = 0; i < got; i++) buf[i] = wire_->read();
  return got == len;
}

bool Max30101::begin(TwoWire& wire) {
  wire_ = &wire;
  ok_ = (read8(REG_PART_ID) == 0x15);
  if (!ok_) return false;
  write8(REG_MODE_CONFIG, MODE_RESET);
  uint32_t t0 = millis();
  while ((read8(REG_MODE_CONFIG) & MODE_RESET) && millis() - t0 < 100) delay(1);
  read8(REG_INT_STATUS1);  // xoá cờ PWR_RDY
  read8(REG_INT_STATUS2);
  return setMode(MODE_HR_GREEN);
}

void Max30101::clearFifo() {
  write8(REG_FIFO_WR_PTR, 0);
  write8(REG_OVF_COUNTER, 0);
  write8(REG_FIFO_RD_PTR, 0);
}

bool Max30101::setMode(Mode m) {
  if (!ok_) return false;
  bool r = true;
  switch (m) {
    case MODE_OFF:
      r &= write8(REG_MODE_CONFIG, MODE_SHDN);
      break;
    case MODE_HR_GREEN:  // 100 sps, trung bình 2 -> 50 Hz
      r &= write8(REG_MODE_CONFIG, MODE_SHDN);
      r &= write8(REG_FIFO_CONFIG, AVG_2 | ROLLOVER | 0x0F);
      r &= write8(REG_SPO2_CONFIG, ADC_16384NA | SR_100 | PW_411US);
      r &= write8(REG_LED1_PA, 0);
      r &= write8(REG_LED2_PA, HR_IR_PA);
      r &= write8(REG_LED3_PA, HR_GREEN_PA);
      r &= write8(REG_LED4_PA, HR_GREEN_PA);
      r &= write8(REG_MULTI_LED1, HR_SLOT);
      r &= write8(REG_MULTI_LED2, 0);
      clearFifo();
      r &= write8(REG_MODE_CONFIG, MODE_MULTI_BITS);
      break;
    case MODE_SPO2:  // đỏ + IR 100 Hz
      r &= write8(REG_MODE_CONFIG, MODE_SHDN);
      r &= write8(REG_FIFO_CONFIG, AVG_1 | ROLLOVER | 0x0F);
      r &= write8(REG_SPO2_CONFIG, ADC_16384NA | SR_100 | PW_411US);
      r &= write8(REG_LED1_PA, PPG_RED_PA);
      r &= write8(REG_LED2_PA, PPG_IR_PA);
      r &= write8(REG_LED3_PA, 0);
      r &= write8(REG_LED4_PA, 0);
      clearFifo();
      r &= write8(REG_MODE_CONFIG, MODE_SPO2_BITS);
      break;
    case MODE_PAT_GREEN:  // xanh 200 Hz cho PAT
      r &= write8(REG_MODE_CONFIG, MODE_SHDN);
      r &= write8(REG_FIFO_CONFIG, AVG_1 | ROLLOVER | 0x0F);
      r &= write8(REG_SPO2_CONFIG, ADC_16384NA | SR_200 | PW_215US);
      r &= write8(REG_LED1_PA, 0);
      r &= write8(REG_LED2_PA, HR_IR_PA);
      r &= write8(REG_LED3_PA, HR_GREEN_PA);
      r &= write8(REG_LED4_PA, HR_GREEN_PA);
      r &= write8(REG_MULTI_LED1, HR_SLOT);
      r &= write8(REG_MULTI_LED2, 0);
      clearFifo();
      r &= write8(REG_MODE_CONFIG, MODE_MULTI_BITS);
      break;
  }
  mode_ = m;
  return r;
}

int Max30101::readFifo(uint32_t* out, int max_samples, bool* overflow) {
  *overflow = false;
  if (!ok_ || mode_ == MODE_OFF) return 0;
  uint8_t ptr[3];
  if (!readBytes(REG_FIFO_WR_PTR, ptr, 3)) return 0;  // WR_PTR, OVF_COUNTER, RD_PTR
  int count = (ptr[0] - ptr[2]) & 0x1F;
  if (ptr[1] > 0) {
    *overflow = true;
    if (count == 0) count = 32;
  }
  if (count > max_samples) count = max_samples;
  const int ch = channels();
  const int bytes_per_sample = 3 * ch;
  const int samples_per_chunk = 30 / bytes_per_sample;  // giới hạn bộ đệm Wire (32 byte)
  uint8_t buf[30];
  int done = 0;
  while (done < count) {
    int n = count - done;
    if (n > samples_per_chunk) n = samples_per_chunk;
    if (!readBytes(REG_FIFO_DATA, buf, n * bytes_per_sample)) break;
    for (int i = 0; i < n; i++) {
      for (int c = 0; c < ch; c++) {
        const uint8_t* b = &buf[(i * ch + c) * 3];
        out[(done + i) * ch + c] = (((uint32_t)b[0] << 16) | ((uint32_t)b[1] << 8) | b[2]) & 0x3FFFF;
      }
    }
    done += n;
  }
  return done;
}
