// Test tat ca module da co tren breadboard, cung luc, bang mot sketch.
// Board: "Seeed XIAO nRF52840 Sense" (goi "Seeed nRF52 Boards"), Serial Monitor 115200.
// Huong dan cam day: firmware/test_breadboard/README.md
//
// Noi day (giu dung so chan cua mach in hardware/pcb_module):
//   Tat ca VCC/VIN/3.3V -> 3V3 cua XIAO, tat ca GND -> GND (KHONG noi vao 5V)
//   MAX30102 : SDA -> D4, SCL -> D5                    (I2C 0x57)
//   MAX30205 : SDA -> D4, SCL -> D5, A0/A1/A2 -> GND   (I2C 0x48), OS de trong
//   AD8232   : OUTPUT -> D0 (A0), LO+ -> D1, LO- va SDN de trong (D3 la den nen man hinh)
//   Man GC9A01: SCL -> D8, SDA -> D10, CS -> D7, DC -> D6, BLK -> D3, RES -> 3V3 (sketch nay khong ve man hinh)
//   Nut SOS  : D9 -> GND (chua co nut thi cham dau day tu D9 vao GND)
//   Dong co rung: KHONG noi vao chan D nao (dong qua lon), chi thu bang 3V3/GND, xem README.
//
// Moi 0,5 giay in 1 dong trang thai. Cac dong bat dau bang '#' la thong bao.

#include <Adafruit_TinyUSB.h>   // Serial qua USB tren goi Seeed nRF52
#include <Wire.h>
#include "MAX30105.h"           // SparkFun MAX3010x, dung duoc cho MAX30102
#include "LSM6DS3.h"            // Seeed Arduino LSM6DS3 (IMU tren XIAO Sense)

const uint8_t CHAN_ECG   = A0;  // D0
const uint8_t CHAN_LO_DUONG = D1;  // mach in: LO+ va LO- gop vao D1 qua 2 diode
const uint8_t CHAN_SOS   = D9;

const uint8_t DIA_CHI_MAX30102 = 0x57;

MAX30105 ppg;
LSM6DS3 imu(I2C_MODE, 0x6A);

bool coPpg = false;
bool coImu = false;
uint8_t diaChiNhietDo = 0;      // 0 = chua tim thay MAX30205

bool coThietBi(uint8_t diaChi) {
  Wire.beginTransmission(diaChi);
  return Wire.endTransmission() == 0;
}

void quetI2C() {
  Serial.print("# Quet I2C (D4/D5), tim thay:");
  uint8_t dem = 0;
  for (uint8_t a = 1; a < 127; a++) {
    if (coThietBi(a)) {
      Serial.print(" 0x");
      if (a < 16) Serial.print('0');
      Serial.print(a, HEX);
      dem++;
    }
  }
  if (dem == 0) Serial.print(" KHONG CO GI -> kiem tra day SDA/SCL, 3V3, GND");
  Serial.println();
}

// MAX30205: thanh ghi 0x00 la nhiet do, 16 bit, moi don vi = 1/256 do C.
// Sau khi cap dien no tu do lien tuc, khong can cai dat gi.
bool docNhietDo(float &doC) {
  Wire.beginTransmission(diaChiNhietDo);
  Wire.write(0x00);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(diaChiNhietDo, (uint8_t)2) != 2) return false;
  int16_t tho = (int16_t)((Wire.read() << 8) | Wire.read());
  doC = tho * 0.00390625f;
  return true;
}

void setup() {
  pinMode(CHAN_LO_DUONG, INPUT);
  pinMode(CHAN_SOS, INPUT_PULLUP);
  analogReadResolution(12);

  Serial.begin(115200);
  while (!Serial && millis() < 5000) {}
  Serial.println("# ===== Test breadboard =====");

  Wire.begin();
  Wire.setClock(100000);
  quetI2C();

  coPpg = coThietBi(DIA_CHI_MAX30102) && ppg.begin(Wire, I2C_SPEED_STANDARD);
  if (coPpg) {
    // Dong LED vua phai, du de doc qua ngon tay.
    ppg.setup(0x1F, 4, 2, 100, 411, 4096);   // do sang, trung binh 4, che do Red+IR, 100 Hz
    Serial.println("# MAX30102 (0x57): OK");
  } else {
    Serial.println("# MAX30102 (0x57): KHONG THAY -> xem muc 'Loi thuong gap' trong README");
  }

  for (uint8_t a = 0x48; a <= 0x4F; a++) {
    if (coThietBi(a)) { diaChiNhietDo = a; break; }
  }
  if (diaChiNhietDo) {
    Serial.print("# MAX30205: OK o dia chi 0x");
    Serial.println(diaChiNhietDo, HEX);
    if (diaChiNhietDo != 0x48) Serial.println("# (mach in dung 0x48: noi A0, A1, A2 xuong GND)");
  } else {
    Serial.println("# MAX30205 (0x48): KHONG THAY -> kiem tra VCC = 3V3, SDA/SCL");
  }

  pinMode(PIN_LSM6DS3TR_C_POWER, OUTPUT);
  digitalWrite(PIN_LSM6DS3TR_C_POWER, HIGH);
  delay(50);
  coImu = (imu.begin() == 0);
  Serial.println(coImu ? "# IMU: OK" : "# IMU: LOI");

  Serial.println("# Cot: IR (dat ngon tay len MAX30102) | nhiet do | gia toc Z | ECG | dien cuc | nut SOS");
}

void loop() {
  static uint32_t lanIn = 0;
  if (millis() - lanIn < 500) return;
  lanIn = millis();

  Serial.print("IR=");
  if (coPpg) {
    uint32_t ir = ppg.getIR();
    Serial.print(ir);
    Serial.print(ir > 50000 ? " (co ngon tay)" : " (chua co ngon tay)");
  } else {
    Serial.print("--");
  }

  Serial.print(" | T=");
  float doC;
  if (diaChiNhietDo && docNhietDo(doC)) {
    Serial.print(doC, 2);
    Serial.print(" C");
  } else {
    Serial.print("--");
  }

  Serial.print(" | Z=");
  if (coImu) {
    Serial.print(imu.readFloatAccelZ(), 2);
    Serial.print(" g");
  } else {
    Serial.print("--");
  }

  Serial.print(" | ECG=");
  Serial.print(analogRead(CHAN_ECG));
  bool tuot = digitalRead(CHAN_LO_DUONG);
  Serial.print(tuot ? " | dien cuc: TUOT" : " | dien cuc: OK");

  Serial.println(digitalRead(CHAN_SOS) == LOW ? " | SOS: BAM" : " | SOS: nha");
}
