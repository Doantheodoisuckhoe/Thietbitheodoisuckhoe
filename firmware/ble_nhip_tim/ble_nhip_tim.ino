// Do nhip tim bang MAX30102 va gui len dien thoai qua BLE (Heart Rate Service chuan).
// Board: Seeed XIAO nRF52840 Sense (goi "Seeed nRF52 Boards").
//
// Noi day giong sketch doc_max30102: VIN -> 3V3, GND -> GND, SDA -> D4, SCL -> D5.
//
// Thu tren dien thoai: mo app nRF Connect -> SCAN -> ket noi "DoAn-SucKhoe"
//   -> Heart Rate -> bam nut 3 mui ten xuong (bat notify) o "Heart Rate Measurement".
// Moi giay thiet bi gui 1 gia tri nhip tim (lan/phut). Serial Monitor 115200 cung in ra.
//
// Day la ban dau de thu BLE: nhip tim tinh bang ham checkForBeat() cua thu vien SparkFun,
// chua loc nhieu chuyen dong. Thuat toan chinh xac hon se thay vao sau (thu muc algorithm/).

#include <bluefruit.h>
#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"

const char*    TEN_THIET_BI    = "DoAn-SucKhoe";
const uint32_t CHU_KY_MAU_MS   = 10;      // 100 mau/giay (400 mau/giay, lay trung binh 4)
const uint32_t NGUONG_CO_NGON  = 50000;   // IR duoi muc nay coi nhu chua dat ngon tay / co tay
const uint8_t  SO_NHIP_TB      = 4;       // lay trung binh 4 nhip gan nhat
const uint32_t CHU_KY_GUI_MS   = 1000;

// Heart Rate Service (UUID 0x180D) la service chuan, app nao doc duoc dong ho/dai deo nhip tim
// cung hieu, nen app Flutter cua SV2 co the dung thu vien BLE san co.
BLEService        dichVuNhipTim(UUID16_SVC_HEART_RATE);
BLECharacteristic dacTinhDoNhipTim(UUID16_CHR_HEART_RATE_MEASUREMENT);
BLECharacteristic dacTinhViTriDo(UUID16_CHR_BODY_SENSOR_LOCATION);
BLEDis            thongTinThietBi;

MAX30105 ppg;

uint32_t soMau = 0;
uint32_t mauNhipTruoc = 0;
uint8_t  cacNhip[SO_NHIP_TB];
uint8_t  viTriNhip = 0;
uint8_t  soNhipDaCo = 0;
uint8_t  nhipTimTB = 0;
bool     coTiepXuc = false;

void khiKetNoi(uint16_t ketNoi) {
  Serial.println("# Dien thoai da ket noi");
}

void khiNgatKetNoi(uint16_t ketNoi, uint8_t lyDo) {
  Serial.print("# Ngat ket noi, ly do 0x");
  Serial.println(lyDo, HEX);
}

void caiDatBle() {
  Bluefruit.begin();
  Bluefruit.setName(TEN_THIET_BI);
  Bluefruit.Periph.setConnectCallback(khiKetNoi);
  Bluefruit.Periph.setDisconnectCallback(khiNgatKetNoi);

  thongTinThietBi.setManufacturer("Do an tot nghiep");
  thongTinThietBi.setModel("Thiet bi deo tay v0");
  thongTinThietBi.begin();

  dichVuNhipTim.begin();

  // Byte co (flags): bit 0 = 0 -> nhip tim 8 bit; bit 1-2 = trang thai tiep xuc voi da
  dacTinhDoNhipTim.setProperties(CHR_PROPS_NOTIFY);
  dacTinhDoNhipTim.setPermission(SECMODE_OPEN, SECMODE_NO_ACCESS);
  dacTinhDoNhipTim.setFixedLen(2);
  dacTinhDoNhipTim.begin();

  dacTinhViTriDo.setProperties(CHR_PROPS_READ);
  dacTinhViTriDo.setPermission(SECMODE_OPEN, SECMODE_NO_ACCESS);
  dacTinhViTriDo.setFixedLen(1);
  dacTinhViTriDo.begin();
  dacTinhViTriDo.write8(2);   // 2 = co tay

  Bluefruit.Advertising.addFlags(BLE_GAP_ADV_FLAGS_LE_ONLY_GENERAL_DISC_MODE);
  Bluefruit.Advertising.addTxPower();
  Bluefruit.Advertising.addService(dichVuNhipTim);
  Bluefruit.ScanResponse.addName();
  Bluefruit.Advertising.restartOnDisconnect(true);
  Bluefruit.Advertising.setInterval(32, 244);   // don vi 0,625 ms: 20 ms luc dau, sau do 152,5 ms
  Bluefruit.Advertising.setFastTimeout(30);
  Bluefruit.Advertising.start(0);               // quang ba mai cho den khi co ket noi
}

void xoaNhip() {
  soNhipDaCo = 0;
  viTriNhip = 0;
  nhipTimTB = 0;
}

void xuLyMau(uint32_t ir) {
  coTiepXuc = ir >= NGUONG_CO_NGON;
  if (!coTiepXuc) {
    xoaNhip();
    return;
  }
  if (!checkForBeat(ir)) return;

  uint32_t khoangCachMs = (soMau - mauNhipTruoc) * CHU_KY_MAU_MS;
  mauNhipTruoc = soMau;
  uint32_t nhip = 60000UL / khoangCachMs;
  if (nhip < 30 || nhip > 220) return;   // bo nhip vo ly (cu dong, nhieu)

  cacNhip[viTriNhip] = nhip;
  viTriNhip = (viTriNhip + 1) % SO_NHIP_TB;
  if (soNhipDaCo < SO_NHIP_TB) soNhipDaCo++;

  uint32_t tong = 0;
  for (uint8_t i = 0; i < soNhipDaCo; i++) tong += cacNhip[i];
  nhipTimTB = tong / soNhipDaCo;
}

void guiNhipTim() {
  // 0b110: co ho tro phat hien tiep xuc, dang tiep xuc; 0b100: khong tiep xuc
  uint8_t duLieu[2] = { (uint8_t)(coTiepXuc ? 0b110 : 0b100), nhipTimTB };
  if (Bluefruit.connected()) dacTinhDoNhipTim.notify(duLieu, sizeof(duLieu));

  Serial.print("Nhip tim: ");
  Serial.print(nhipTimTB);
  Serial.println(coTiepXuc ? "" : "  (chua dat tay len cam bien)");
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000) {}

  if (!ppg.begin(Wire, I2C_SPEED_FAST)) {
    Serial.println("# Khong thay MAX30102: kiem tra day noi va dien tro keo len I2C");
    while (true) delay(1000);
  }
  ppg.setup(0x1F, 4, 2, 400, 411, 4096);   // giong sketch doc_max30102: 100 mau/giay

  caiDatBle();
  Serial.println("# Dang quang ba BLE voi ten DoAn-SucKhoe");
}

void loop() {
  ppg.check();
  while (ppg.available()) {
    xuLyMau(ppg.getFIFOIR());
    ppg.nextSample();
    soMau++;
  }

  static uint32_t lanGuiTruoc = 0;
  if (millis() - lanGuiTruoc >= CHU_KY_GUI_MS) {
    lanGuiTruoc = millis();
    guiNhipTim();
  }
}
