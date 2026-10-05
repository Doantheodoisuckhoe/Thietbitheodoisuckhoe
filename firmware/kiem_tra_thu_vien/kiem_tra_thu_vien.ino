// Kiem tra thu vien: chi bien dich, chua can noi cam bien.
// Board: Seeed XIAO nRF52840 Sense (goi "Seeed nRF52 Boards").
// Bien dich thanh cong = da cai du thu vien va tuong thich voi loi nRF52.

#include <Wire.h>
#include <SPI.h>
#include "MAX30105.h"          // SparkFun MAX3010x (dung cho MAX30102)
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_GFX.h>
#include <Adafruit_GC9A01A.h>
#include "LSM6DS3.h"           // Seeed Arduino LSM6DS3 (IMU tren XIAO Sense)

#define CHAN_DS18B20 D2
#define TFT_CS  D7
#define TFT_DC  D6
#define TFT_RST -1

MAX30105 ppg;
OneWire oneWire(CHAN_DS18B20);
DallasTemperature nhietDo(&oneWire);
Adafruit_GC9A01A manHinh(TFT_CS, TFT_DC, TFT_RST);
LSM6DS3 imu(I2C_MODE, 0x6A);

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000) {}
  Serial.println("Kiem tra thu vien");
  Serial.println(ppg.begin(Wire, I2C_SPEED_FAST) ? "MAX30102: OK" : "MAX30102: khong thay");
  nhietDo.begin();
  Serial.print("DS18B20 tim thay: "); Serial.println(nhietDo.getDeviceCount());
  Serial.println(imu.begin() == 0 ? "IMU: OK" : "IMU: loi");
  manHinh.begin();
  manHinh.fillScreen(GC9A01A_BLACK);
}

void loop() {
  Serial.print("Gia toc Z (g): ");
  Serial.println(imu.readFloatAccelZ(), 3);
  delay(1000);
}
