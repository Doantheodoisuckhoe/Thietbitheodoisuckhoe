// Gia lap toi thieu cua Arduino.h de chay Adafruit_GFX tren may tinh (chi de xem truoc man hinh).
#pragma once
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#ifndef ARDUINO
#define ARDUINO 100
#endif
#define PROGMEM
typedef bool boolean;
typedef uint8_t byte;
#define radians(d) ((d) * 0.017453292519943295)
class __FlashStringHelper;
class String {
public:
  String(const char* s = "") : p(s) {}
  const char* c_str() const { return p; }
  unsigned length() const { return strlen(p); }
private:
  const char* p;
};
#include "Print.h"
