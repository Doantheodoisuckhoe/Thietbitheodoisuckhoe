// max30101.h — driver cảm biến PPG MAX30101 (I2C 0x57).
#pragma once
#include <Arduino.h>
#include <Wire.h>

class Max30101 {
 public:
  enum Mode { MODE_OFF, MODE_HR_GREEN, MODE_SPO2, MODE_PAT_GREEN };

  bool begin(TwoWire& wire = Wire);
  bool setMode(Mode m);  // cấu hình lại + xoá FIFO
  Mode mode() const { return mode_; }
  int channels() const { return mode_ == MODE_SPO2 ? 2 : 1; }
  // Đọc toàn bộ mẫu đang có trong FIFO. out[i*channels()+c]. Trả về số mẫu.
  // overflow = true nếu FIFO đã tràn (mất mẫu) từ lần đọc trước.
  int readFifo(uint32_t* out, int max_samples, bool* overflow);
  bool present() const { return ok_; }

 private:
  bool write8(uint8_t reg, uint8_t val);
  uint8_t read8(uint8_t reg);
  bool readBytes(uint8_t reg, uint8_t* buf, int len);
  void clearFifo();

  TwoWire* wire_ = nullptr;
  Mode mode_ = MODE_OFF;
  bool ok_ = false;
};
