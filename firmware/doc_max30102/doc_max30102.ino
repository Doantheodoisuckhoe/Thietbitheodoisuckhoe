// Doc MAX30102 o 100 mau/giay, in du lieu tho ra Serial dang CSV de ve va phan tich bang Python.
// Board: Seeed XIAO nRF52840 Sense (goi "Seeed nRF52 Boards").
//
// Noi day (module MAX30102 -> XIAO):
//   VIN -> 3V3, GND -> GND, SDA -> D4, SCL -> D5
// Module khong tra loi I2C: xem muc "Loi da gap" trong firmware/README.md (dien tro keo len 1,8 V).
//
// Cach dung: Serial Monitor 115200, hoac luu thanh file CSV bang Serial Plotter / script Python.
// Cot t_ms tinh theo so thu tu mau (moi mau 10 ms), khong dung millis() vi mau doc ra theo tung dot.

#include <Wire.h>
#include "MAX30105.h"   // SparkFun MAX3010x (dung chung cho MAX30102 va MAX30101)

const uint8_t  DO_SANG_LED   = 0x1F;  // khoang 6,4 mA; tang len 0x3F neu tin hieu yeu
const uint8_t  TRUNG_BINH    = 4;     // cam bien lay trung binh 4 mau -> 400 / 4 = 100 mau/giay
const uint8_t  CHE_DO_LED    = 2;     // 2 = LED do + hong ngoai (can cho SpO2)
const int      TAN_SO_LAY    = 400;   // mau/giay truoc khi lay trung binh
const int      DO_RONG_XUNG  = 411;   // us, ung voi do phan giai 18 bit
const int      DAI_DO_ADC    = 4096;  // nA
const uint32_t CHU_KY_MAU_MS = 1000UL * TRUNG_BINH / TAN_SO_LAY;  // 10 ms

MAX30105 ppg;
uint32_t soMau = 0;

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000) {}

  if (!ppg.begin(Wire, I2C_SPEED_FAST)) {
    Serial.println("# Khong thay MAX30102: kiem tra day noi va dien tro keo len I2C");
    while (true) delay(1000);
  }
  ppg.setup(DO_SANG_LED, TRUNG_BINH, CHE_DO_LED, TAN_SO_LAY, DO_RONG_XUNG, DAI_DO_ADC);

  Serial.println("t_ms,red,ir");
}

void loop() {
  ppg.check();                    // chuyen cac mau moi tu FIFO cua cam bien vao bo dem
  while (ppg.available()) {
    Serial.print(soMau * CHU_KY_MAU_MS);
    Serial.print(',');
    Serial.print(ppg.getFIFORed());
    Serial.print(',');
    Serial.println(ppg.getFIFOIR());
    ppg.nextSample();
    soMau++;
  }
}
