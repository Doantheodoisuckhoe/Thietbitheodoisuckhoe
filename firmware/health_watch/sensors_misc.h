// sensors_misc.h — TMP117 (nhiệt độ da) và LSM6DS3TR-C (gia tốc kế trên XIAO Sense).
#pragma once
#include <Arduino.h>
#include <Wire.h>

class Tmp117 {
 public:
  bool begin(TwoWire& wire = Wire, uint8_t addr = 0x48);
  bool read(float* temp_c);  // đọc kết quả mới nhất
  bool present() const { return ok_; }

 private:
  bool write16(uint8_t reg, uint16_t v);
  bool read16(uint8_t reg, uint16_t* v);
  TwoWire* wire_ = nullptr;
  uint8_t addr_ = 0x48;
  bool ok_ = false;
};

class Lsm6ds3 {
 public:
  bool begin(TwoWire& wire);
  // true nếu có mẫu mới; đơn vị g
  bool read(float* ax, float* ay, float* az);
  bool present() const { return ok_; }

 private:
  bool write8(uint8_t reg, uint8_t v);
  bool readBytes(uint8_t reg, uint8_t* buf, int len);
  TwoWire* wire_ = nullptr;
  bool ok_ = false;
};
