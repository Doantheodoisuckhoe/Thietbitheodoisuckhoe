// sensors_misc.cpp — xem sensors_misc.h
#include "sensors_misc.h"

#include "config.h"

// ============================================================================
// TMP117 — datasheet TI. Thanh ghi 16 bit, MSB trước.
// ============================================================================
namespace {
const uint8_t TMP_REG_TEMP = 0x00;
const uint8_t TMP_REG_CONFIG = 0x01;
const uint8_t TMP_REG_ID = 0x0F;
// Liên tục, chu kỳ 1 s (CONV=100), trung bình 8 mẫu (AVG=01)
const uint16_t TMP_CONFIG = (0b00 << 10) | (0b100 << 7) | (0b01 << 5);
}  // namespace

bool Tmp117::write16(uint8_t reg, uint16_t v) {
  wire_->beginTransmission(addr_);
  wire_->write(reg);
  wire_->write((uint8_t)(v >> 8));
  wire_->write((uint8_t)v);
  return wire_->endTransmission() == 0;
}

bool Tmp117::read16(uint8_t reg, uint16_t* v) {
  wire_->beginTransmission(addr_);
  wire_->write(reg);
  if (wire_->endTransmission(false) != 0) return false;
  if (wire_->requestFrom((int)addr_, 2) != 2) return false;
  *v = ((uint16_t)wire_->read() << 8) | wire_->read();
  return true;
}

bool Tmp117::begin(TwoWire& wire, uint8_t addr) {
  wire_ = &wire;
  addr_ = addr;
  uint16_t id = 0;
  ok_ = read16(TMP_REG_ID, &id) && ((id & 0x0FFF) == 0x0117);
  if (ok_) ok_ = write16(TMP_REG_CONFIG, TMP_CONFIG);
  return ok_;
}

bool Tmp117::read(float* temp_c) {
  if (!ok_) return false;
  uint16_t raw;
  if (!read16(TMP_REG_TEMP, &raw)) return false;
  if (raw == 0x8000) return false;  // giá trị reset, chưa có kết quả
  *temp_c = (int16_t)raw * 0.0078125f;
  return true;
}

// ============================================================================
// LSM6DS3TR-C — datasheet ST.
// ============================================================================
namespace {
const uint8_t IMU_ADDR = 0x6A;
const uint8_t IMU_WHO_AM_I = 0x0F;  // 0x6A (LSM6DS3TR-C) hoặc 0x69 (LSM6DS3)
const uint8_t IMU_CTRL1_XL = 0x10;
const uint8_t IMU_CTRL2_G = 0x11;
const uint8_t IMU_CTRL3_C = 0x12;
const uint8_t IMU_STATUS = 0x1E;
const uint8_t IMU_OUTX_L_XL = 0x28;
const uint8_t XL_104HZ_16G = 0x44;  // ODR 104 Hz, ±16 g (va chạm khi ngã có thể > 8 g)
const float XL_SENS_16G = 0.000488f;  // g/LSB
}  // namespace

bool Lsm6ds3::write8(uint8_t reg, uint8_t v) {
  wire_->beginTransmission(IMU_ADDR);
  wire_->write(reg);
  wire_->write(v);
  return wire_->endTransmission() == 0;
}

bool Lsm6ds3::readBytes(uint8_t reg, uint8_t* buf, int len) {
  wire_->beginTransmission(IMU_ADDR);
  wire_->write(reg);
  if (wire_->endTransmission(false) != 0) return false;
  int got = wire_->requestFrom((int)IMU_ADDR, len);
  for (int i = 0; i < got; i++) buf[i] = wire_->read();
  return got == len;
}

bool Lsm6ds3::begin(TwoWire& wire) {
  wire_ = &wire;
#ifdef PIN_LSM6DS3TR_C_POWER
  pinMode(PIN_LSM6DS3TR_C_POWER, OUTPUT);
  digitalWrite(PIN_LSM6DS3TR_C_POWER, HIGH);  // cấp nguồn IMU trên XIAO Sense
  delay(20);
#endif
  wire_->begin();
  uint8_t who = 0;
  readBytes(IMU_WHO_AM_I, &who, 1);
  ok_ = (who == 0x6A || who == 0x69);
  if (!ok_) return false;
  write8(IMU_CTRL3_C, 0x01);  // SW_RESET
  delay(20);
  write8(IMU_CTRL3_C, 0x44);  // BDU + IF_INC
  write8(IMU_CTRL1_XL, XL_104HZ_16G);
  write8(IMU_CTRL2_G, 0x00);  // tắt con quay (tiết kiệm ~0,9 mA)
  return true;
}

bool Lsm6ds3::read(float* ax, float* ay, float* az) {
  if (!ok_) return false;
  uint8_t st = 0;
  if (!readBytes(IMU_STATUS, &st, 1) || !(st & 0x01)) return false;  // XLDA
  uint8_t b[6];
  if (!readBytes(IMU_OUTX_L_XL, b, 6)) return false;
  *ax = (int16_t)(b[0] | (b[1] << 8)) * XL_SENS_16G;
  *ay = (int16_t)(b[2] | (b[3] << 8)) * XL_SENS_16G;
  *az = (int16_t)(b[4] | (b[5] << 8)) * XL_SENS_16G;
  return true;
}
