// Firmware gui so do va canh bao len app dien thoai qua BLE (phuong an 1, chot 21/10/2026):
//   dong ho -> BLE -> app Android -> dien thoai gui SMS / goi cho nguoi than.
// Giao thuc BLE (UUID, tung byte, viec app phai lam): docs/giao-thuc-ble.md
// Board: "Seeed XIAO nRF52840 Sense" (goi "Seeed nRF52 Boards"), Serial Monitor 115200.
//
// Noi day giong test_breadboard:
//   MAX30102 + MAX30205: SDA -> D4, SCL -> D5, VCC -> 3V3   (khong co module nao thi phan do bo trong)
//   Nut SOS: D9 -> GND.  Dong co rung: D2 qua MOSFET (tren breadboard de trong D2).
//   AD8232 (ECG): OUTPUT -> A0 (D0), LO+ va LO- gop vao D1 qua 2 diode (mach 1.2). Tren breadboard noi LO+ -> D1.
//   Man GC9A01 (theo mach 1.2): VCC 3V3, GND, SCL -> D8, SDA -> D10, DC -> D6, CS -> D7, BLK -> D3, RES de trong.
//   Chua cam man thi firmware van chay binh thuong (man chi nhan lenh, khong tra loi).
//   Cach ve tung man va anh mo phong: man_hinh.h, xem_truoc/README.md
//
// Cach dung nut SOS:
//   - Bam nhanh             -> bat man hinh 10 giay.
//   - Giu nut 1 giay        -> canh bao SOS.
//   - Khi dong ho phat hien te nga, no rung 15 giay de hoi "co sao khong?".
//     Bam nut trong 15 giay do -> huy (khong bao). Khong bam -> gui canh bao te nga.
//
// Thu khong can app: mo app nRF Connect -> ket noi "DoAn-SucKhoe" -> bat notify o 2 dac tinh
// cua service 4b3a0001-... (xem docs/giao-thuc-ble.md). Hoac chay app/thu_ble_tren_may_tinh.py.

#include <Adafruit_TinyUSB.h>
#include <bluefruit.h>
#include <Wire.h>
#include "MAX30105.h"
#include "LSM6DS3.h"
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_GC9A01A.h>
#include "man_hinh.h"

// ---------------- Cau hinh ----------------
const char* TEN_THIET_BI = "DoAn-SucKhoe";

const uint8_t CHAN_SOS     = D9;
const uint8_t CHAN_DONG_CO = D2;
const bool    CO_DONG_CO   = true;   // breadboard chua co MOSFET: de true cung khong sao, D2 bo trong

const bool     CO_MAN_HINH  = true;     // false = bo han phan man hinh
const uint8_t  CHAN_TFT_CS  = D7;
const uint8_t  CHAN_TFT_DC  = D6;
const uint8_t  CHAN_TFT_BLK = D3;       // den nen: HIGH = sang
const uint32_t SANG_MAN_HINH_MS = 10000;  // bam nhanh nut -> sang 10 giay roi tat de tiet kiem pin
const uint32_t HIEN_DA_BAO_MS   = 5000;   // man "DA BAO nguoi than" sau khi app xac nhan

const uint32_t NGUONG_CO_TAY = 50000;   // IR duoi muc nay = chua deo / chua dat ngon tay

// Nguong canh bao chi so (phai keo dai THOI_GIAN_BAT_THUONG_MS moi bao).
const uint8_t  NHIP_TIM_CAO  = 120;
const uint8_t  NHIP_TIM_THAP = 40;
const uint8_t  SPO2_THAP     = 90;
const int16_t  NHIET_DO_SOT  = 3800;    // 0,01 do C. Nhiet do co tay thap hon than nhiet, can chinh khi do doi chung
const uint32_t THOI_GIAN_BAT_THUONG_MS = 15000;
const uint32_t NGHI_GIUA_HAI_LAN_BAO_MS = 5UL * 60 * 1000;  // cung 1 loai, khong bao lai trong 5 phut

// Te nga: giong algorithm/te_nga/phat_hien.py
const float NGUONG_VA_CHAM   = 2.5f;   // g
const float NGUONG_ROI       = 0.75f;  // g
const float DO_LECH_NAM_YEN  = 0.2f;   // g
const float GOC_DOI_TU_THE   = 30.0f;  // do
const uint32_t THOI_GIAN_HUY_TE_NGA_MS = 15000;

const uint32_t GIU_NUT_SOS_MS = 1000;
const uint32_t GUI_LAI_CANH_BAO_MS = 5000;   // gui lai cho den khi app xac nhan

// ECG: app gui lenh 03 -> dong ho lay mau AD8232 250 mau/giay trong 30 giay va gui dan qua BLE.
const uint8_t  CHAN_ECG      = A0;
const uint8_t  CHAN_ECG_TUOT = D1;     // HIGH = tuot dien cuc (LO+ / LO-)
const uint16_t TAN_SO_ECG    = 250;
const uint16_t SO_MAU_ECG    = 30 * TAN_SO_ECG;   // 7500 mau = 30 giay

// ---------------- Ma canh bao (giong docs/giao-thuc-ble.md) ----------------
enum MaCanhBao : uint8_t {
  CB_SOS = 1, CB_TE_NGA = 2, CB_NHIP_CAO = 3, CB_NHIP_THAP = 4, CB_SPO2_THAP = 5, CB_SOT = 6
};
enum MaLenh : uint8_t { LENH_XAC_NHAN = 1, LENH_TIM_DONG_HO = 2, LENH_BAT_DAU_ECG = 3, LENH_DUNG_ECG = 4 };

// ---------------- BLE ----------------
// UUID dang 4b3a000X-8f6e-4c2a-9d1b-3e5f7a9c0b1d, viet nguoc byte (little endian) theo yeu cau Bluefruit.
#define UUID_RIENG(x) { 0x1d, 0x0b, 0x9c, 0x7a, 0x5f, 0x3e, 0x1b, 0x9d, \
                        0x2a, 0x4c, 0x6e, 0x8f, x, 0x00, 0x3a, 0x4b }
const uint8_t UUID_DICH_VU[16]  = UUID_RIENG(0x01);
const uint8_t UUID_SO_DO[16]    = UUID_RIENG(0x02);
const uint8_t UUID_CANH_BAO[16] = UUID_RIENG(0x03);
const uint8_t UUID_LENH[16]     = UUID_RIENG(0x04);
const uint8_t UUID_ECG[16]      = UUID_RIENG(0x05);

BLEService        dichVu(UUID_DICH_VU);
BLECharacteristic dtSoDo(UUID_SO_DO);
BLECharacteristic dtCanhBao(UUID_CANH_BAO);
BLECharacteristic dtLenh(UUID_LENH);
BLECharacteristic dtEcg(UUID_ECG);
BLEService        dvNhipTim(UUID16_SVC_HEART_RATE);   // service chuan, app/dong ho nao cung doc duoc
BLECharacteristic dtNhipTim(UUID16_CHR_HEART_RATE_MEASUREMENT);
BLEDis            thongTin;
BLEBas            pinBle;                              // Battery Service chuan (0x180F)

// Goi so do: 10 byte, gui moi giay.
struct __attribute__((packed)) GoiSoDo {
  uint8_t  phienBan;     // = 1
  uint8_t  co;           // bit0 co tay, bit1 nhiet do hop le, bit2 SpO2 hop le, bit3 IMU OK
  uint8_t  nhipTim;      // lan/phut, 0 = chua co
  uint8_t  spo2;         // %, 0 = chua co
  int16_t  nhietDo;      // 0,01 do C
  uint16_t pinMv;        // mV
  uint8_t  pinPhanTram;
  uint8_t  soCanhBaoCho; // so thu tu canh bao dang cho app xac nhan, 0 = khong co
};
struct __attribute__((packed)) GoiCanhBao {
  uint8_t  ma;           // MaCanhBao
  uint8_t  soThuTu;      // 1..255, tang moi canh bao moi
  uint16_t giaTri;       // nhip tim / SpO2 / nhiet do (0,01 C); 0 voi SOS, te nga
};

// Goi ECG: 4 byte dau + n mau (uint16, ADC 12 bit). Xem docs/giao-thuc-ble.md
const uint8_t ECG_CO_TUOT = 1, ECG_CO_HET = 2;
const uint8_t ECG_MAU_MOI_GOI_LON = 25;   // MTU >= 57 (app xin MTU 247)
const uint8_t ECG_MAU_MOI_GOI_NHO = 8;    // MTU mac dinh 23: 4 + 16 = 20 byte

// ---------------- Cam bien ----------------
MAX30105 ppg;
LSM6DS3  imu(I2C_MODE, 0x6A);
bool coPpg = false, coImu = false, coNhietDo = false, nhietDoHopLe = false;
const uint8_t DIA_CHI_MAX30205 = 0x48;

// ---------------- Trang thai ----------------
uint8_t  nhipTim = 0, spo2 = 0;
int16_t  nhietDo = 0;
bool     coTay = false;
uint16_t pinMv = 0;

GoiCanhBao canhBaoCho = {0, 0, 0};   // ma = 0: khong co canh bao dang cho
uint8_t  soThuTuCuoi = 0;
uint32_t lanGuiCanhBao = 0;

bool     dangDemHuyTeNga = false;
uint32_t lucPhatHienTeNga = 0;

uint32_t rungDenLuc = 0;  // millis() khi tat dong co

// Man hinh
Adafruit_GC9A01A tft(CHAN_TFT_CS, CHAN_TFT_DC, -1);   // RES khong noi: thu vien tu reset bang lenh
BoVeManHinh boVe;
bool     manHinhSang = false;
uint32_t tatManHinhLuc = 0;
volatile uint32_t lucAppXacNhan = 0;   // ghi trong callback BLE, chi doc o loop()

// ECG
volatile uint8_t  yeuCauEcg = 0;       // ghi trong callback BLE: 3 = bat dau, 4 = dung
bool     ecgDangDo = false;
const uint16_t KICH_THUOC_DEM_ECG = 512;   // ~2 giay, luy thua cua 2
volatile uint16_t demEcg[KICH_THUOC_DEM_ECG];   // bit15 = tuot dien cuc, bit0-11 = ADC
volatile uint16_t viTriGhiEcg = 0;
volatile uint16_t soMauDaLayEcg = 0;
volatile uint16_t soMauMatEcg = 0;
volatile uint16_t viTriDocEcg = 0;     // loop() doc, ngat so sanh de biet bo dem day
uint16_t soMauDaGuiEcg = 0;
uint32_t lucBatDauEcg = 0;
uint16_t soGoiEcg = 0;

// ============================================================
// Dong co rung
// ============================================================
void rung(uint32_t ms) {
  if (!CO_DONG_CO) return;
  digitalWrite(CHAN_DONG_CO, HIGH);
  rungDenLuc = millis() + ms;
}

void capNhatDongCo() {
  if (!CO_DONG_CO) return;
  // Dang dem huy te nga: rung 300 ms moi giay de nguoi deo biet.
  if (dangDemHuyTeNga) {
    digitalWrite(CHAN_DONG_CO, ((millis() - lucPhatHienTeNga) % 1000) < 300);
    return;
  }
  if ((int32_t)(millis() - rungDenLuc) >= 0) digitalWrite(CHAN_DONG_CO, LOW);
}

// ============================================================
// Canh bao
// ============================================================
void guiGoiCanhBao() {
  dtCanhBao.write(&canhBaoCho, sizeof(canhBaoCho));
  if (Bluefruit.connected()) dtCanhBao.notify(&canhBaoCho, sizeof(canhBaoCho));
  lanGuiCanhBao = millis();
}

void taoCanhBao(MaCanhBao ma, uint16_t giaTri) {
  // SOS va te nga quan trong hon: ghi de canh bao chi so dang cho. Nguoc lai thi khong ghi de.
  bool khanCap = (ma == CB_SOS || ma == CB_TE_NGA);
  bool dangChoKhanCap = (canhBaoCho.ma == CB_SOS || canhBaoCho.ma == CB_TE_NGA);
  if (canhBaoCho.ma != 0 && (dangChoKhanCap || !khanCap)) return;

  soThuTuCuoi = (soThuTuCuoi == 255) ? 1 : soThuTuCuoi + 1;
  canhBaoCho = { (uint8_t)ma, soThuTuCuoi, giaTri };
  Serial.print("# CANH BAO ma="); Serial.print(ma);
  Serial.print(" so="); Serial.print(soThuTuCuoi);
  Serial.print(" gia tri="); Serial.println(giaTri);
  rung(khanCap ? 1500 : 500);
  guiGoiCanhBao();
}

void capNhatCanhBao() {
  // Chua co xac nhan tu app thi gui lai dinh ky (ke ca khi vua ket noi lai).
  if (canhBaoCho.ma != 0 && millis() - lanGuiCanhBao >= GUI_LAI_CANH_BAO_MS) guiGoiCanhBao();
}

void khiNhanLenh(uint16_t ketNoi, BLECharacteristic* dt, uint8_t* duLieu, uint16_t doDai) {
  if (doDai == 0) return;
  if (duLieu[0] == LENH_XAC_NHAN && doDai >= 2 && duLieu[1] == canhBaoCho.soThuTu && canhBaoCho.ma != 0) {
    Serial.print("# App da xac nhan canh bao so "); Serial.println(duLieu[1]);
    canhBaoCho = {0, 0, 0};
    dtCanhBao.write(&canhBaoCho, sizeof(canhBaoCho));
    rung(1000);   // rung dai 1 giay = "da bao cho nguoi than"
    lucAppXacNhan = millis() | 1;
  } else if (duLieu[0] == LENH_TIM_DONG_HO) {
    rung(2000);
  } else if (duLieu[0] == LENH_BAT_DAU_ECG || duLieu[0] == LENH_DUNG_ECG) {
    yeuCauEcg = duLieu[0];   // xu ly o loop(), khong lam viec nang trong callback BLE
  }
}

// Bao khi chi so vuot nguong lien tuc THOI_GIAN_BAT_THUONG_MS.
struct TheoDoiNguong {
  MaCanhBao ma;
  uint32_t  batDau = 0;      // 0 = dang binh thuong
  uint32_t  lanBaoCuoi = 0;
  bool      daBao = false;
  TheoDoiNguong(MaCanhBao m) : ma(m) {}
  void capNhat(bool batThuong, uint16_t giaTri) {
    if (!batThuong) { batDau = 0; return; }
    if (batDau == 0) batDau = millis() | 1;
    bool hetNghi = !daBao || millis() - lanBaoCuoi >= NGHI_GIUA_HAI_LAN_BAO_MS;
    if (millis() - batDau >= THOI_GIAN_BAT_THUONG_MS && hetNghi) {
      taoCanhBao(ma, giaTri);
      daBao = true;
      lanBaoCuoi = millis();
    }
  }
};
TheoDoiNguong ndNhipCao(CB_NHIP_CAO), ndNhipThap(CB_NHIP_THAP), ndSpo2(CB_SPO2_THAP), ndSot(CB_SOT);

// ============================================================
// Nut SOS
// ============================================================
void capNhatNutSos() {
  static bool     dangBam = false;
  static uint32_t lucBam = 0;
  static bool     daXuLy = false;
  bool bam = digitalRead(CHAN_SOS) == LOW;

  if (bam && !dangBam) { lucBam = millis(); daXuLy = false; }
  // Nha nut truoc 1 giay (bam nhanh) -> bat man hinh
  if (!bam && dangBam && !daXuLy && millis() - lucBam >= 50) batManHinh();
  dangBam = bam;
  if (!bam || daXuLy || millis() - lucBam < 50) return;   // chong doi phim 50 ms

  if (dangDemHuyTeNga) {        // bam bat ky luc nao trong 15 giay -> huy
    dangDemHuyTeNga = false;
    digitalWrite(CHAN_DONG_CO, LOW);
    Serial.println("# Nguoi deo da huy canh bao te nga");
    daXuLy = true;
  } else if (millis() - lucBam >= GIU_NUT_SOS_MS) {
    taoCanhBao(CB_SOS, 0);
    daXuLy = true;
  }
}

// ============================================================
// Te nga (IMU, 100 mau/giay) - cung thuat toan voi algorithm/te_nga/phat_hien.py
// ============================================================
const uint16_t TAN_SO = 100;
const uint16_t SO_MAU_TRUOC = 150;   // giu 1,5 giay truoc va cham
float bdX[SO_MAU_TRUOC], bdY[SO_MAU_TRUOC], bdZ[SO_MAU_TRUOC], bdSvm[SO_MAU_TRUOC];
uint16_t viTriBd = 0, soMauBd = 0;

// Sau va cham: bo qua 1 giay, roi gom 2 giay (giay thu 1..3) de xet nam yen va tu the.
bool     dangXetSauVaCham = false;
uint16_t demSauVaCham = 0;
float    tuTheTruoc[3];
double   tongSau[3], tongSvm, tongSvm2;
uint16_t soMauSau = 0;

float doLon(float x, float y, float z) { return sqrtf(x * x + y * y + z * z); }

float gocGiua(const float a[3], const float b[3]) {
  float c = (a[0] * b[0] + a[1] * b[1] + a[2] * b[2]) / (doLon(a[0], a[1], a[2]) * doLon(b[0], b[1], b[2]));
  c = constrain(c, -1.0f, 1.0f);
  return acosf(c) * 57.29578f;
}

// Mau thu i tinh tu mau moi nhat (i = 0 la moi nhat).
uint16_t chiSo(uint16_t luiLai) { return (viTriBd + SO_MAU_TRUOC - 1 - luiLai) % SO_MAU_TRUOC; }

void xuLyMauImu(float x, float y, float z) {
  float svm = doLon(x, y, z);

  if (dangXetSauVaCham) {
    demSauVaCham++;
    if (demSauVaCham > TAN_SO) {   // tu giay thu 1 den giay thu 3
      tongSau[0] += x; tongSau[1] += y; tongSau[2] += z;
      tongSvm += svm; tongSvm2 += (double)svm * svm;
      soMauSau++;
    }
    if (demSauVaCham >= 3 * TAN_SO) {
      dangXetSauVaCham = false;
      float tb = tongSvm / soMauSau;
      float doLech = sqrtf(max(0.0, tongSvm2 / soMauSau - (double)tb * tb));
      float tuTheSau[3] = { (float)(tongSau[0] / soMauSau), (float)(tongSau[1] / soMauSau),
                            (float)(tongSau[2] / soMauSau) };
      float goc = gocGiua(tuTheTruoc, tuTheSau);
      Serial.print("# Xet va cham: do lech "); Serial.print(doLech, 2);
      Serial.print(" g, doi tu the "); Serial.print(goc, 0); Serial.println(" do");
      if (doLech < DO_LECH_NAM_YEN && goc > GOC_DOI_TU_THE && !dangDemHuyTeNga) {
        dangDemHuyTeNga = true;
        lucPhatHienTeNga = millis();
        Serial.println("# PHAT HIEN TE NGA - bam nut trong 15 giay de huy");
      }
      soMauBd = 0;   // bat dau gom lai du lieu truoc va cham
    }
    return;
  }

  bdX[viTriBd] = x; bdY[viTriBd] = y; bdZ[viTriBd] = z; bdSvm[viTriBd] = svm;
  viTriBd = (viTriBd + 1) % SO_MAU_TRUOC;
  if (soMauBd < SO_MAU_TRUOC) soMauBd++;
  if (soMauBd < SO_MAU_TRUOC || svm <= NGUONG_VA_CHAM) return;

  // Co va cham. Dieu kien 2: trong 1 giay truoc co luc SVM duoi NGUONG_ROI.
  float nhoNhat = 99;
  for (uint16_t i = 1; i <= TAN_SO; i++) nhoNhat = min(nhoNhat, bdSvm[chiSo(i)]);
  if (nhoNhat >= NGUONG_ROI) return;

  // Tu the truoc: trung binh tu 1,5 giay den 0,5 giay truoc va cham.
  double t[3] = {0, 0, 0};
  for (uint16_t i = TAN_SO / 2; i < SO_MAU_TRUOC; i++) {
    uint16_t k = chiSo(i);
    t[0] += bdX[k]; t[1] += bdY[k]; t[2] += bdZ[k];
  }
  uint16_t n = SO_MAU_TRUOC - TAN_SO / 2;
  for (int j = 0; j < 3; j++) { tuTheTruoc[j] = t[j] / n; tongSau[j] = 0; }
  tongSvm = tongSvm2 = 0;
  soMauSau = 0;
  demSauVaCham = 0;
  dangXetSauVaCham = true;
  Serial.print("# Va cham "); Serial.print(svm, 2); Serial.println(" g, dang xet 3 giay sau...");
}

void capNhatTeNga() {
  if (dangDemHuyTeNga && millis() - lucPhatHienTeNga >= THOI_GIAN_HUY_TE_NGA_MS) {
    dangDemHuyTeNga = false;
    taoCanhBao(CB_TE_NGA, 0);
  }
}

// ============================================================
// Nhip tim va SpO2 (MAX30102, 100 mau/giay)
// ============================================================
// Nhip tim: loc IR 0,5-5 Hz, lay dao ham, tu tuong quan (autocorrelation) trong cua so 6 giay.
//   Cach nay chiu duoc nen troi do ngon tay xe dich (do thu 24/10: nen troi lon hon ca nhip tim,
//   cach tim dinh cu khong bat duoc nhip nao). Thu bang song gia: algorithm/nhip_tim/thu_nhip_tim.py
// SpO2: ty so R = (AC do / DC do) / (AC IR / DC IR) trong cua so 4 giay, SpO2 ~ 110 - 25R.
// Cong thuc nay la cong thuc chung, CHUA hieu chuan; se chinh he so khi do doi chung voi may kep ngon tay.
const uint16_t CUA_SO_SPO2 = 400;
float  dcDo = 0, dcIr = 0;
double tongAcDo2 = 0, tongAcIr2 = 0, tongDcDo = 0, tongDcIr = 0;
uint16_t soMauCuaSo = 0;
bool   cuaSoHong = false;
float  spo2Cac[3]; uint8_t soSpo2 = 0, viTriSpo2 = 0;

// Bo loc bac 2 (Butterworth, 100 mau/giay): thong cao 0,5 Hz bo nen troi, thong thap 5 Hz bo nhieu.
struct LocBac2 {
  float b0, b1, b2, a1, a2, z1, z2;
  float loc(float x) {
    float y = b0 * x + z1;
    z1 = b1 * x - a1 * y + z2;
    z2 = b2 * x - a2 * y;
    return y;
  }
};
LocBac2 locCao = { 0.97803048f, -1.95606096f, 0.97803048f, -1.95557824f, 0.95654368f, 0, 0 };
LocBac2 locThap = { 0.02008337f, 0.04016673f, 0.02008337f, -1.56101808f, 0.64135154f, 0, 0 };

const uint16_t CUA_SO_NHIP = 600;              // 6 giay
const uint8_t  TRE_MIN = 30, TRE_MAX = 150;    // khoang giua 2 nhip: 0,3-1,5 giay = 200-40 lan/phut
float    songNhip[CUA_SO_NHIP];
uint16_t viTriSong = 0;
uint32_t soMauPpg = 0;                         // so mau tu luc dat tay
float    locTruoc = 0;
uint8_t  cacNhip[3]; uint8_t soNhip = 0, viTriNhip = 0;
uint32_t lanCoNhipCuoi = 0;

void xoaPpg() {
  soNhip = viTriNhip = soSpo2 = viTriSpo2 = 0;
  nhipTim = spo2 = 0;
  soMauPpg = 0;
  dcDo = dcIr = 0;
  cuaSoHong = true;
}

uint8_t trungVi(const uint8_t* a, uint8_t n) {
  uint8_t b[6];
  memcpy(b, a, n);
  for (uint8_t i = 1; i < n; i++)
    for (uint8_t j = i; j > 0 && b[j] < b[j - 1]; j--) { uint8_t t = b[j]; b[j] = b[j - 1]; b[j - 1] = t; }
  return b[n / 2];
}

// Uoc luong nhip tim tu cua so 6 giay. Tra ve 0 neu song khong ro (nhieu, cu dong).
uint8_t uocLuongNhipTim() {
  static float v[CUA_SO_NHIP];
  float tb = 0;
  for (uint16_t k = 0; k < CUA_SO_NHIP; k++) { v[k] = songNhip[(viTriSong + k) % CUA_SO_NHIP]; tb += v[k]; }
  tb /= CUA_SO_NHIP;
  float r0 = 0, nangLuong[6] = {0};
  for (uint16_t k = 0; k < CUA_SO_NHIP; k++) {
    v[k] -= tb;
    r0 += v[k] * v[k];
    nangLuong[k / 100] += v[k] * v[k];
  }
  if (r0 <= 0) return 0;
  // Co 1 giay nang luong gap 8 lan giay khac = cu dong manh, bo cua so nay.
  float nlMin = nangLuong[0], nlMax = nangLuong[0];
  for (uint8_t j = 1; j < 6; j++) { nlMin = min(nlMin, nangLuong[j]); nlMax = max(nlMax, nangLuong[j]); }
  if (nlMax > 8 * nlMin) return 0;

  static float r[TRE_MAX + 2];
  for (uint16_t L = TRE_MIN - 1; L <= TRE_MAX + 1; L++) {
    float tong = 0;
    for (uint16_t k = 0; k + L < CUA_SO_NHIP; k++) tong += v[k] * v[k + L];
    r[L] = tong / r0 * CUA_SO_NHIP / (CUA_SO_NHIP - L);
  }
  // Dinh cao nhat trong cac dinh cuc bo
  uint8_t tot = 0;
  for (uint8_t L = TRE_MIN; L <= TRE_MAX; L++)
    if (r[L] >= r[L - 1] && r[L] >= r[L + 1] && (tot == 0 || r[L] > r[tot])) tot = L;
  if (tot == 0) return 0;
  // Neu co dinh ngan hon cao gan bang va tot gap 2, 3 lan no thi nhip that la dinh ngan (tranh dem thieu nhip)
  for (uint8_t L = TRE_MIN; L < tot; L++) {
    if (r[L] >= r[L - 1] && r[L] >= r[L + 1] && r[L] > 0.8f * r[tot]) {
      float ti = (float)tot / L; int k = (int)(ti + 0.5f);
      if (k >= 2 && fabsf(ti - k) < 0.15f * k) { tot = L; break; }
    }
  }
  if (r[tot] < 0.3f) return 0;                 // song khong du giong nhau giua cac nhip
  float a = r[tot - 1], b = r[tot], c = r[tot + 1];
  float mau = a - 2 * b + c;
  float lech = (mau != 0) ? 0.5f * (a - c) / mau : 0;   // noi suy de chinh xac hon 1 mau
  return (uint8_t)(6000.0f / (tot + lech) + 0.5f);
}

void xuLyMauPpg(uint32_t doRaw, uint32_t irRaw) {
  bool tayTruoc = coTay;
  coTay = irRaw >= NGUONG_CO_TAY;
  if (!coTay) { if (tayTruoc) xoaPpg(); return; }

  if (dcIr == 0) { dcIr = irRaw; dcDo = doRaw; }
  dcIr += (irRaw - dcIr) * 0.02f;   // loc thong thap ~0,3 Hz = thanh phan mot chieu
  dcDo += (doRaw - dcDo) * 0.02f;
  float acIr = irRaw - dcIr, acDo = doRaw - dcDo;

  // --- SpO2 ---
  tongAcIr2 += acIr * acIr; tongAcDo2 += acDo * acDo;
  tongDcIr += dcIr;         tongDcDo += dcDo;
  if (++soMauCuaSo >= CUA_SO_SPO2) {
    if (!cuaSoHong && tongAcIr2 > 0) {
      float r = (sqrt(tongAcDo2 / soMauCuaSo) / (tongDcDo / soMauCuaSo)) /
                (sqrt(tongAcIr2 / soMauCuaSo) / (tongDcIr / soMauCuaSo));
      float s = 110.0f - 25.0f * r;
      if (s >= 70 && s <= 100.5f) {
        spo2Cac[viTriSpo2] = min(s, 100.0f);
        viTriSpo2 = (viTriSpo2 + 1) % 3;
        if (soSpo2 < 3) soSpo2++;
        float tong = 0;
        for (uint8_t i = 0; i < soSpo2; i++) tong += spo2Cac[i];
        spo2 = (uint8_t)(tong / soSpo2 + 0.5f);
      }
    }
    tongAcIr2 = tongAcDo2 = tongDcIr = tongDcDo = 0;
    soMauCuaSo = 0;
    cuaSoHong = false;
  }

  // --- Nhip tim ---
  if (soMauPpg == 0) {                         // vua dat tay: dat san trang thai loc de khong bi giat
    locCao.z1 = -locCao.b0 * irRaw; locCao.z2 = locCao.b2 * irRaw;
    locThap.z1 = locThap.z2 = 0; locTruoc = 0;
  }
  float y = locThap.loc(locCao.loc((float)irRaw));
  songNhip[viTriSong] = y - locTruoc;          // dao ham: lam ro suon len cua moi nhip
  locTruoc = y;
  viTriSong = (viTriSong + 1) % CUA_SO_NHIP;
  soMauPpg++;
  if (soMauPpg < CUA_SO_NHIP + 200 || soMauPpg % 100 != 0) return;   // bo 2 giay dau, moi giay tinh 1 lan

  uint8_t uocLuong = uocLuongNhipTim();
  if (uocLuong == 0) return;                   // giu so cu; qua 5 giay khong co so moi thi loop() xoa
  cacNhip[viTriNhip] = uocLuong;
  viTriNhip = (viTriNhip + 1) % 3;
  if (soNhip < 3) soNhip++;
  lanCoNhipCuoi = millis();
  if (soNhip >= 2) nhipTim = trungVi(cacNhip, soNhip);
}

// ============================================================
// ECG (AD8232) - TIMER4 ngat moi 4 ms, giong firmware/doc_ad8232
// ============================================================
extern "C" void TIMER4_IRQHandler(void) {
  if (!NRF_TIMER4->EVENTS_COMPARE[0]) return;
  NRF_TIMER4->EVENTS_COMPARE[0] = 0;
  if (soMauDaLayEcg >= SO_MAU_ECG) return;
  uint16_t ke = (viTriGhiEcg + 1) & (KICH_THUOC_DEM_ECG - 1);
  if (ke == viTriDocEcg) {          // BLE gui khong kip, bo dem day: mat mau nay (app thay thieu mau)
    soMauMatEcg++;
    soMauDaLayEcg++;                 // van tinh thoi gian de ban do dung 30 giay
    return;
  }
  uint16_t v = analogRead(CHAN_ECG) & 0x0FFF;
  if (digitalRead(CHAN_ECG_TUOT)) v |= 0x8000;
  demEcg[viTriGhiEcg] = v;
  viTriGhiEcg = ke;
  soMauDaLayEcg++;
}

void dungEcg() {
  NRF_TIMER4->TASKS_STOP = 1;
  NVIC_DisableIRQ(TIMER4_IRQn);
  ecgDangDo = false;
}

void batDauEcg() {
  dungEcg();
  pinMode(CHAN_ECG_TUOT, INPUT_PULLDOWN);   // 2 diode gop LO+/LO- chi keo len, can keo xuong
  analogReference(AR_DEFAULT);
  analogReadResolution(12);
  viTriGhiEcg = 0;
  viTriDocEcg = 0;
  soMauDaLayEcg = 0;
  soMauMatEcg = 0;
  soMauDaGuiEcg = 0;
  soGoiEcg = 0;
  lucBatDauEcg = millis();
  ecgDangDo = true;
  NRF_TIMER4->MODE      = TIMER_MODE_MODE_Timer;
  NRF_TIMER4->BITMODE   = TIMER_BITMODE_BITMODE_32Bit;
  NRF_TIMER4->PRESCALER = 4;                         // 1 MHz
  NRF_TIMER4->CC[0]     = 1000000 / TAN_SO_ECG;      // 4000 us
  NRF_TIMER4->SHORTS    = TIMER_SHORTS_COMPARE0_CLEAR_Msk;
  NRF_TIMER4->INTENSET  = TIMER_INTENSET_COMPARE0_Msk;
  NVIC_SetPriority(TIMER4_IRQn, 3);
  NVIC_EnableIRQ(TIMER4_IRQn);
  NRF_TIMER4->TASKS_CLEAR = 1;
  NRF_TIMER4->TASKS_START = 1;
  Serial.println("# Bat dau do ECG 30 giay");
}

// Gui cac mau da lay. Goi khong gui duoc (BLE ban) thi giu lai, lan sau gui tiep.
void capNhatEcg() {
  uint8_t yc = yeuCauEcg;
  if (yc) {
    yeuCauEcg = 0;
    if (yc == LENH_BAT_DAU_ECG && Bluefruit.connected() && dtEcg.notifyEnabled()) batDauEcg();
    else if (yc == LENH_DUNG_ECG && ecgDangDo) { dungEcg(); Serial.println("# App dung do ECG"); }
  }
  if (!ecgDangDo) return;
  if (!Bluefruit.connected()) { dungEcg(); Serial.println("# Mat ket noi, dung do ECG"); return; }
  if (millis() - lucBatDauEcg > 45000) { dungEcg(); Serial.println("# ECG qua 45 giay chua gui xong, dung"); return; }

  BLEConnection* kn = Bluefruit.Connection(Bluefruit.connHandle());
  uint8_t moiGoi = (kn && kn->getMtu() >= 3 + 4 + 2 * ECG_MAU_MOI_GOI_LON) ? ECG_MAU_MOI_GOI_LON : ECG_MAU_MOI_GOI_NHO;

  for (uint8_t lan = 0; lan < 4; lan++) {                 // toi da 4 goi moi vong loop
    bool layXong = soMauDaLayEcg >= SO_MAU_ECG;            // doc truoc coSan: lay xong thi ngat khong ghi them
    uint16_t coSan = (viTriGhiEcg - viTriDocEcg) & (KICH_THUOC_DEM_ECG - 1);
    if (coSan < moiGoi && !layXong) break;
    uint8_t n = coSan < moiGoi ? coSan : moiGoi;     // lay xong ma bo dem rong: gui goi rong co co "het"
    uint8_t goi[4 + 2 * ECG_MAU_MOI_GOI_LON];
    uint8_t co = 0;
    uint16_t vt = viTriDocEcg;
    for (uint8_t i = 0; i < n; i++) {
      uint16_t v = demEcg[vt];
      if (v & 0x8000) co |= ECG_CO_TUOT;
      goi[4 + 2 * i] = v & 0xFF;
      goi[5 + 2 * i] = (v >> 8) & 0x0F;
      vt = (vt + 1) & (KICH_THUOC_DEM_ECG - 1);
    }
    bool het = layXong && coSan == n;
    if (n == 0 && !het) break;
    if (het) co |= ECG_CO_HET;
    goi[0] = soGoiEcg & 0xFF; goi[1] = soGoiEcg >> 8; goi[2] = co; goi[3] = n;
    if (!dtEcg.notify(goi, 4 + 2 * n)) break;              // BLE ban: thu lai vong sau
    viTriDocEcg = vt;
    soMauDaGuiEcg += n;
    soGoiEcg++;
    if (het) {
      dungEcg();
      Serial.print("# Xong ECG: da gui "); Serial.print(soMauDaGuiEcg);
      Serial.print(" mau, mat "); Serial.println(soMauMatEcg);
      break;
    }
  }
}

// ============================================================
// Nhiet do (MAX30205) va pin
// ============================================================
bool docNhietDo(int16_t& ketQua) {
  Wire.beginTransmission(DIA_CHI_MAX30205);
  Wire.write(0x00);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(DIA_CHI_MAX30205, (uint8_t)2) != 2) return false;
  int16_t tho = (int16_t)((Wire.read() << 8) | Wire.read());
  ketQua = (int16_t)((int32_t)tho * 100 / 256);   // 1/256 do C -> 0,01 do C
  return true;
}

uint16_t docPinMv() {
  // XIAO: cau chia 1M/510k tren chan PIN_VBAT, bat bang VBAT_ENABLE = LOW (de LOW suot).
  analogReference(AR_INTERNAL_3_0);
  analogReadResolution(12);
  uint32_t tong = 0;
  for (int i = 0; i < 8; i++) tong += analogRead(PIN_VBAT);
  analogReference(AR_DEFAULT);
  return (uint32_t)(tong / 8) * 3000UL * 1510UL / 510UL / 4096UL;
}

uint8_t phanTramPin(uint16_t mv) {
  // Uoc luong tuyen tinh 3,3 V = 0 %, 4,2 V = 100 % (LiPo).
  if (mv <= 3300) return 0;
  if (mv >= 4200) return 100;
  return (mv - 3300) / 9;
}

// ============================================================
// BLE
// ============================================================
void caiDatBle() {
  Bluefruit.configPrphBandwidth(BANDWIDTH_MAX);   // cho MTU 247 de gui ECG nhanh
  Bluefruit.begin();
  Bluefruit.setName(TEN_THIET_BI);
  Bluefruit.setTxPower(4);
  Bluefruit.Periph.setConnectCallback([](uint16_t) {
    Serial.println("# Dien thoai da ket noi");
    lanGuiCanhBao = 0;   // co canh bao dang cho thi gui lai ngay
  });
  Bluefruit.Periph.setDisconnectCallback([](uint16_t, uint8_t lyDo) {
    Serial.print("# Mat ket noi, ly do 0x"); Serial.println(lyDo, HEX);
  });

  thongTin.setManufacturer("Do an tot nghiep");
  thongTin.setModel("Dong ho suc khoe v1");
  thongTin.begin();
  pinBle.begin();

  dichVu.begin();
  dtSoDo.setProperties(CHR_PROPS_READ | CHR_PROPS_NOTIFY);
  dtSoDo.setPermission(SECMODE_OPEN, SECMODE_NO_ACCESS);
  dtSoDo.setFixedLen(sizeof(GoiSoDo));
  dtSoDo.begin();

  dtCanhBao.setProperties(CHR_PROPS_READ | CHR_PROPS_NOTIFY);
  dtCanhBao.setPermission(SECMODE_OPEN, SECMODE_NO_ACCESS);
  dtCanhBao.setFixedLen(sizeof(GoiCanhBao));
  dtCanhBao.begin();
  dtCanhBao.write(&canhBaoCho, sizeof(canhBaoCho));

  dtLenh.setProperties(CHR_PROPS_WRITE | CHR_PROPS_WRITE_WO_RESP);
  dtLenh.setPermission(SECMODE_NO_ACCESS, SECMODE_OPEN);
  dtLenh.setMaxLen(4);
  dtLenh.setWriteCallback(khiNhanLenh);
  dtLenh.begin();

  dtEcg.setProperties(CHR_PROPS_NOTIFY);
  dtEcg.setPermission(SECMODE_OPEN, SECMODE_NO_ACCESS);
  dtEcg.setMaxLen(4 + 2 * ECG_MAU_MOI_GOI_LON);
  dtEcg.begin();

  dvNhipTim.begin();
  dtNhipTim.setProperties(CHR_PROPS_NOTIFY);
  dtNhipTim.setPermission(SECMODE_OPEN, SECMODE_NO_ACCESS);
  dtNhipTim.setFixedLen(2);
  dtNhipTim.begin();

  Bluefruit.Advertising.addFlags(BLE_GAP_ADV_FLAGS_LE_ONLY_GENERAL_DISC_MODE);
  Bluefruit.Advertising.addService(dichVu);       // app loc theo UUID nay
  Bluefruit.ScanResponse.addName();
  Bluefruit.ScanResponse.addService(dvNhipTim);
  Bluefruit.Advertising.restartOnDisconnect(true);
  Bluefruit.Advertising.setInterval(32, 1600);    // 20 ms luc dau, sau 30 giay chuyen 1 giay de tiet kiem pin
  Bluefruit.Advertising.setFastTimeout(30);
  Bluefruit.Advertising.start(0);
}

void guiSoDo() {
  GoiSoDo g;
  g.phienBan = 1;
  g.co = (coTay ? 1 : 0) | (nhietDoHopLe ? 2 : 0) | (spo2 ? 4 : 0) | (coImu ? 8 : 0);
  g.nhipTim = nhipTim;
  g.spo2 = spo2;
  g.nhietDo = nhietDo;
  g.pinMv = pinMv;
  g.pinPhanTram = phanTramPin(pinMv);
  g.soCanhBaoCho = canhBaoCho.ma ? canhBaoCho.soThuTu : 0;
  dtSoDo.write(&g, sizeof(g));

  if (Bluefruit.connected()) {
    dtSoDo.notify(&g, sizeof(g));
    uint8_t hr[2] = { (uint8_t)(coTay ? 0b110 : 0b100), nhipTim };
    dtNhipTim.notify(hr, sizeof(hr));
  }
  pinBle.write(g.pinPhanTram);

  Serial.print("HR="); Serial.print(nhipTim);
  Serial.print(" SpO2="); Serial.print(spo2);
  Serial.print(" T="); Serial.print(nhietDo / 100.0f, 2);
  Serial.print(" Pin="); Serial.print(pinMv); Serial.print("mV");
  Serial.print(coTay ? "" : " (chua deo)");
  Serial.println(Bluefruit.connected() ? " [BLE]" : "");
}

// ============================================================
// Man hinh GC9A01 (ve trong man_hinh.h)
// ============================================================
void caiDatManHinh() {
  if (!CO_MAN_HINH) return;
  pinMode(CHAN_TFT_BLK, OUTPUT);
  digitalWrite(CHAN_TFT_BLK, LOW);       // tat den nen trong luc khoi dong, tranh hien rac
  tft.begin(8000000);                    // SPI 8 MHz; man tu reset bang lenh vi chan RES de trong
  tft.setRotation(0);                    // anh bi xoay thi doi 0..3
  // SPI.begin() vua cau hinh D9 (MISO mac dinh cua XIAO) thanh ngo vao keo xuong. D9 la nut SOS
  // nen phai dat lai keo len, neu khong firmware tuong nut dang bi giu -> bao SOS gia.
  pinMode(CHAN_SOS, INPUT_PULLUP);
  boVe.veLaiHet();
  Serial.println("# Man hinh GC9A01: da khoi dong (man chi nhan lenh nen khong biet co cam hay khong)");
}

void batManHinh() {
  if (!CO_MAN_HINH) return;
  tatManHinhLuc = millis() + SANG_MAN_HINH_MS;
  if (manHinhSang) return;
  tft.sendCommand(GC9A01A_SLPOUT);
  delay(5);
  tft.sendCommand(GC9A01A_DISPON);
  boVe.veLaiHet();
  manHinhSang = true;
  // den nen bat sau khi ve xong o capNhatManHinh()
}

void tatManHinh() {
  digitalWrite(CHAN_TFT_BLK, LOW);
  tft.sendCommand(GC9A01A_DISPOFF);
  tft.sendCommand(GC9A01A_SLPIN);        // ngu: man gan nhu khong ton dien
  manHinhSang = false;
}

void capNhatManHinh() {
  if (!CO_MAN_HINH) return;
  static uint32_t lanVe = 0;
  uint32_t bayGio = millis();
  if (bayGio - lanVe < 200) return;       // ve toi da 5 lan/giay, chi ve phan thay doi
  lanVe = bayGio;

  TrangThaiManHinh s;
  uint32_t xacNhan = lucAppXacNhan;
  if (dangDemHuyTeNga) {
    s.loai = MH_TE_NGA;
    uint32_t daQua = bayGio - lucPhatHienTeNga;
    s.giayConLai = daQua >= THOI_GIAN_HUY_TE_NGA_MS ? 0 : (THOI_GIAN_HUY_TE_NGA_MS - daQua + 999) / 1000;
  } else if (canhBaoCho.ma != 0) {
    s.loai = MH_CANH_BAO;
    s.maCanhBao = canhBaoCho.ma;
    s.giaTri = canhBaoCho.giaTri;
  } else if (xacNhan && bayGio - xacNhan < HIEN_DA_BAO_MS) {
    s.loai = MH_DA_BAO;
  } else {
    s.loai = MH_CHINH;
  }
  s.coTay = coTay; s.nhipTim = nhipTim; s.spo2 = spo2;
  s.nhietDoHopLe = nhietDoHopLe; s.nhietDo = nhietDo;
  s.pin = phanTramPin(pinMv);
  s.ketNoi = Bluefruit.connected();

  // Te nga, canh bao, "da bao": man luon sang. Man chinh: tat sau SANG_MAN_HINH_MS.
  if (s.loai != MH_CHINH) batManHinh();
  if (!manHinhSang) return;
  if (s.loai == MH_CHINH && (int32_t)(bayGio - tatManHinhLuc) >= 0) { tatManHinh(); return; }

  boVe.ve(tft, s);
  digitalWrite(CHAN_TFT_BLK, HIGH);
}

// ============================================================
void setup() {
  pinMode(CHAN_SOS, INPUT_PULLUP);
  if (CO_DONG_CO) { pinMode(CHAN_DONG_CO, OUTPUT); digitalWrite(CHAN_DONG_CO, LOW); }
  pinMode(VBAT_ENABLE, OUTPUT);
  digitalWrite(VBAT_ENABLE, LOW);

  Serial.begin(115200);
  while (!Serial && millis() < 3000) {}
  Serial.println("# ===== Dong ho suc khoe - BLE =====");

  Wire.begin();
  Wire.setClock(100000);
  coPpg = ppg.begin(Wire, I2C_SPEED_STANDARD);
  if (coPpg) ppg.setup(0x1F, 4, 2, 400, 411, 4096);   // Red + IR, 400 Hz trung binh 4 = 100 mau/giay
  Serial.println(coPpg ? "# MAX30102: OK" : "# MAX30102: KHONG THAY (bo qua nhip tim, SpO2)");

  int16_t t;
  coNhietDo = docNhietDo(t);
  Serial.println(coNhietDo ? "# MAX30205: OK" : "# MAX30205: KHONG THAY (bo qua nhiet do)");

  imu.settings.accelRange = 16;
  imu.settings.accelSampleRate = 416;
  pinMode(PIN_LSM6DS3TR_C_POWER, OUTPUT);
  digitalWrite(PIN_LSM6DS3TR_C_POWER, HIGH);
  delay(50);
  coImu = (imu.begin() == 0);
  Serial.println(coImu ? "# IMU: OK" : "# IMU: LOI (bo qua te nga)");

  pinMv = docPinMv();
  caiDatManHinh();
  batManHinh();                          // vua bat nguon: sang 10 giay
  caiDatBle();
  Serial.println("# Dang quang ba BLE ten DoAn-SucKhoe");
}

void loop() {
  uint32_t bayGio = millis();

  if (coPpg) {
    ppg.check();
    while (ppg.available()) {
      xuLyMauPpg(ppg.getFIFORed(), ppg.getFIFOIR());
      ppg.nextSample();
    }
    if (nhipTim && bayGio - lanCoNhipCuoi > 5000) { nhipTim = 0; soNhip = 0; }  // 5 giay khong thay nhip
  }

  static uint32_t lanImu = 0;
  if (coImu && bayGio - lanImu >= 10) {
    lanImu = (bayGio - lanImu > 50) ? bayGio : lanImu + 10;   // tre qua thi dat lai lich, khong chay bu
    xuLyMauImu(imu.readFloatAccelX(), imu.readFloatAccelY(), imu.readFloatAccelZ());
  }

  capNhatNutSos();
  capNhatTeNga();
  capNhatCanhBao();
  capNhatDongCo();
  capNhatManHinh();
  capNhatEcg();

  static uint32_t lanGiay = 0;
  if (bayGio - lanGiay >= 1000) {
    lanGiay = bayGio;
    nhietDoHopLe = coNhietDo && docNhietDo(nhietDo);
    if (!nhietDoHopLe) nhietDo = 0;
    static uint8_t demPin = 0;
    // 30 giay doc pin 1 lan; khong doc luc dang do ECG vi ngat ECG cung dung ADC
    if (++demPin >= 30 && !ecgDangDo) { demPin = 0; pinMv = docPinMv(); }

    if (coTay) {
      ndNhipCao.capNhat(nhipTim > NHIP_TIM_CAO, nhipTim);
      ndNhipThap.capNhat(nhipTim && nhipTim < NHIP_TIM_THAP, nhipTim);
      ndSpo2.capNhat(spo2 && spo2 < SPO2_THAP, spo2);
      ndSot.capNhat(nhietDoHopLe && nhietDo >= NHIET_DO_SOT, nhietDo);
    } else {
      ndNhipCao.capNhat(false, 0); ndNhipThap.capNhat(false, 0);
      ndSpo2.capNhat(false, 0);    ndSot.capNhat(false, 0);
    }
    guiSoDo();
  }
}
