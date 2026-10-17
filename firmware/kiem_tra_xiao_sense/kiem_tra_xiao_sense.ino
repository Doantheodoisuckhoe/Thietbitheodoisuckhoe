// Kiem tra phan cung tren board Seeed XIAO nRF52840 Sense (khong can noi them gi).
// Board: "Seeed XIAO nRF52840 Sense" (goi "Seeed nRF52 Boards"), toc do Serial 115200.
// Kiem tra: USB Serial, LED RGB, IMU LSM6DS3, micro PDM, dien ap pin, quang ba BLE.
// LED RGB tren XIAO sang khi xuat muc LOW.

#include <bluefruit.h>
#include <PDM.h>
#include "LSM6DS3.h"
#include "Wire.h"

LSM6DS3 imu(I2C_MODE, 0x6A);
bool imuOk = false;
bool micOk = false;

short mauAm[256];
volatile int soMau = 0;

void khiCoAmThanh() {
  int n = PDM.available();
  PDM.read(mauAm, n);
  soMau = n / 2;
}

void tatLed() {
  digitalWrite(LED_RED, HIGH);
  digitalWrite(LED_GREEN, HIGH);
  digitalWrite(LED_BLUE, HIGH);
}

void chayLed() {
  const int den[3] = {LED_RED, LED_GREEN, LED_BLUE};
  const char *ten[3] = {"DO", "XANH LA", "XANH DUONG"};
  for (int i = 0; i < 3; i++) {
    tatLed();
    digitalWrite(den[i], LOW);
    Serial.print("LED: "); Serial.println(ten[i]);
    delay(700);
  }
  tatLed();
}

float docPin() {
  // Cau phan ap 1M/510k tren P0.31, bat bang VBAT_ENABLE (P0.14) muc LOW.
  uint32_t tong = 0;
  for (int i = 0; i < 16; i++) tong += analogRead(PIN_VBAT);
  float raw = tong / 16.0;
  return raw * 3.6 / 4096.0 * (1510.0 / 510.0);
}

void batBle() {
  Bluefruit.begin();
  Bluefruit.setTxPower(4);
  Bluefruit.setName("DATN-XIAO-TEST");
  Bluefruit.Advertising.addFlags(BLE_GAP_ADV_FLAGS_LE_ONLY_GENERAL_DISC_MODE);
  Bluefruit.Advertising.addTxPower();
  Bluefruit.ScanResponse.addName();
  Bluefruit.Advertising.restartOnDisconnect(true);
  Bluefruit.Advertising.setInterval(160, 244);
  Bluefruit.Advertising.start(0);
}

void setup() {
  pinMode(LED_RED, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_BLUE, OUTPUT);
  tatLed();
  pinMode(VBAT_ENABLE, OUTPUT);
  digitalWrite(VBAT_ENABLE, LOW);
  analogReadResolution(12);

  Serial.begin(115200);
  while (!Serial && millis() < 5000) {}
  Serial.println("=== Kiem tra XIAO nRF52840 Sense ===");
  Serial.println("Serial: OK");

  chayLed();

  pinMode(PIN_LSM6DS3TR_C_POWER, OUTPUT);
  digitalWrite(PIN_LSM6DS3TR_C_POWER, HIGH);
  delay(50);
  imuOk = (imu.begin() == 0);
  Serial.println(imuOk ? "IMU: OK" : "IMU: LOI");

  PDM.onReceive(khiCoAmThanh);
  micOk = (PDM.begin(1, 16000) == 1);
  Serial.println(micOk ? "Micro: OK" : "Micro: LOI");

  batBle();
  Serial.println("BLE: dang quang ba ten DATN-XIAO-TEST");
}

void loop() {
  static uint32_t lanTruoc = 0;
  static bool sang = false;
  if (millis() - lanTruoc < 500) return;
  lanTruoc = millis();

  // Nhay xanh duong cham = chuong trinh dang chay.
  sang = !sang;
  digitalWrite(LED_BLUE, sang ? LOW : HIGH);

  if (imuOk) {
    Serial.print("IMU g x/y/z: ");
    Serial.print(imu.readFloatAccelX(), 2); Serial.print(" ");
    Serial.print(imu.readFloatAccelY(), 2); Serial.print(" ");
    Serial.print(imu.readFloatAccelZ(), 2);
    Serial.print(" | gyro z: "); Serial.print(imu.readFloatGyroZ(), 1);
  }
  if (micOk && soMau > 0) {
    float tong = 0;
    for (int i = 0; i < soMau; i++) tong += (float)mauAm[i] * mauAm[i];
    Serial.print(" | mic rms: "); Serial.print(sqrt(tong / soMau), 0);
  }
  Serial.print(" | pin V: "); Serial.print(docPin(), 2);
  Serial.print(" | BLE ket noi: "); Serial.println(Bluefruit.connected() ? "co" : "khong");
}
