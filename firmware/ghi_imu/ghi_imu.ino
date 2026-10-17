// Ghi du lieu IMU (LSM6DS3 tren XIAO nRF52840 Sense) o 100 mau/giay, in CSV ra Serial
// de thu du lieu cho thuat toan phat hien te nga. Khong can noi them gi.
// Board: "Seeed XIAO nRF52840 Sense" (goi "Seeed nRF52 Boards"), Serial 115200.
// Dinh dang moi dong: t_ms,ax,ay,az,gx,gy,gz   (gia toc theo g, con quay theo do/giay)
// Dong bat dau bang '#' la thong bao, khong phai du lieu.
// Luu thanh file bang algorithm/te_nga/ghi_du_lieu.py (dong Serial Monitor truoc).

#include "LSM6DS3.h"
#include "Wire.h"

const uint32_t CHU_KY_US = 10000;  // 100 Hz

LSM6DS3 imu(I2C_MODE, 0x6A);

void setup() {
  pinMode(LED_GREEN, OUTPUT);
  digitalWrite(LED_GREEN, HIGH);  // LED tren XIAO sang khi muc LOW

  Serial.begin(115200);
  while (!Serial && millis() < 5000) {}

  // Te nga tao xung gia toc lon, nen dat thang do +-16 g va +-2000 do/giay.
  imu.settings.accelRange = 16;
  imu.settings.accelSampleRate = 416;
  imu.settings.gyroRange = 2000;
  imu.settings.gyroSampleRate = 416;

  pinMode(PIN_LSM6DS3TR_C_POWER, OUTPUT);
  digitalWrite(PIN_LSM6DS3TR_C_POWER, HIGH);
  delay(50);
  if (imu.begin() != 0) {
    Serial.println("# LOI: khong khoi dong duoc IMU");
    while (true) {
      digitalWrite(LED_RED, !digitalRead(LED_RED));
      delay(200);
    }
  }
  Serial.println("# IMU OK, 100 Hz");
  Serial.println("t_ms,ax,ay,az,gx,gy,gz");
}

void loop() {
  static uint32_t lanToi = micros();
  static uint32_t dem = 0;
  if ((int32_t)(micros() - lanToi) < 0) return;
  lanToi += CHU_KY_US;
  // Khi may tinh khong doc Serial, lenh in bi chan va chuong trinh tre lich. Khong chay bu
  // (se lay mau doan nhanh hon 100 Hz), ma dat lai lich tu thoi diem hien tai.
  if ((int32_t)(micros() - lanToi) > (int32_t)CHU_KY_US) lanToi = micros() + CHU_KY_US;

  // In bang Serial.print vi printf cua mot so loi Arduino khong ho tro so thuc.
  Serial.print(millis());
  Serial.print(','); Serial.print(imu.readFloatAccelX(), 3);
  Serial.print(','); Serial.print(imu.readFloatAccelY(), 3);
  Serial.print(','); Serial.print(imu.readFloatAccelZ(), 3);
  Serial.print(','); Serial.print(imu.readFloatGyroX(), 1);
  Serial.print(','); Serial.print(imu.readFloatGyroY(), 1);
  Serial.print(','); Serial.println(imu.readFloatGyroZ(), 1);

  // Nhay xanh la 1 lan/giay = dang ghi.
  if (++dem % 100 == 0) digitalWrite(LED_GREEN, !digitalRead(LED_GREEN));
}
