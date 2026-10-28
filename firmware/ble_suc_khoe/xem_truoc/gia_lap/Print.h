#pragma once
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
class Print {
public:
  virtual ~Print() {}
  virtual size_t write(uint8_t) = 0;
  virtual size_t write(const uint8_t* b, size_t n) { size_t k = 0; while (n--) k += write(*b++); return k; }
  size_t write(const char* s) { size_t k = 0; while (*s) k += write((uint8_t)*s++); return k; }
  size_t print(const char* s) { return write(s); }
  size_t print(int v) { char b[16]; snprintf(b, sizeof b, "%d", v); return write(b); }
};
