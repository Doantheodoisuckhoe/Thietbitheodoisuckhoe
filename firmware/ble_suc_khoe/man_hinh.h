// Ve man hinh tron GC9A01 240 x 240 cho dong ho suc khoe.
// Chi dung ham cua Adafruit_GFX nen ve duoc ca len man that lan len anh mo phong tren may tinh
// (firmware/ble_suc_khoe/xem_truoc/). Chu khong dau vi font cua Adafruit GFX chi co ky tu ASCII.
//
// Cac man:
//   MH_CHINH    : gio, nhip tim, SpO2, nhiet do, pin, ket noi dien thoai
//   MH_TE_NGA   : nen do, dem nguoc 15 giay, bam nut de huy
//   MH_CANH_BAO : canh bao dang cho app xac nhan (SOS, te nga, nhip tim, SpO2, sot)
//   MH_DA_BAO   : nen xanh "DA BAO nguoi than" (app da xac nhan)
// Chi ve lai phan thay doi de khong nhap nhay va khong chiem lau vong lap (IMU 100 mau/giay).
#pragma once
#include <Adafruit_GFX.h>
#include <Fonts/FreeSans9pt7b.h>
#include <Fonts/FreeSansBold12pt7b.h>
#include <Fonts/FreeSansBold18pt7b.h>
#include <Fonts/FreeSansBold24pt7b.h>

enum LoaiManHinh : uint8_t { MH_CHINH = 0, MH_TE_NGA, MH_CANH_BAO, MH_DA_BAO };

struct TrangThaiManHinh {
  uint8_t  loai = MH_CHINH;
  // Man chinh
  bool     coTay = false;
  uint8_t  nhipTim = 0;          // 0 = chua co
  uint8_t  spo2 = 0;             // 0 = chua co
  bool     nhietDoHopLe = false;
  int16_t  nhietDo = 0;          // 0,01 do C
  uint8_t  pin = 0;              // %
  bool     ketNoi = false;       // dien thoai dang ket noi BLE
  int16_t  phutTrongNgay = -1;   // gio x 60 + phut; -1 = chua co gio (app chua ket noi lan nao)
  // Man te nga
  uint8_t  giayConLai = 0;
  // Man canh bao (ma giong MaCanhBao trong ble_suc_khoe.ino)
  uint8_t  maCanhBao = 0;
  uint16_t giaTri = 0;
};

constexpr uint16_t mau565(uint8_t r, uint8_t g, uint8_t b) {
  return (uint16_t)(((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3));
}
const uint16_t MH_DEN        = 0x0000;
const uint16_t MH_TRANG      = 0xFFFF;
const uint16_t MH_XAM        = mau565(140, 140, 140);
const uint16_t MH_XAM_TOI    = mau565(60, 60, 60);
const uint16_t MH_DO_TIM     = mau565(255, 60, 80);
const uint16_t MH_DO_NEN     = mau565(190, 0, 0);
const uint16_t MH_CAM_NEN    = mau565(235, 140, 0);
const uint16_t MH_XANH_NEN   = mau565(0, 140, 60);
const uint16_t MH_XANH_LA    = mau565(60, 210, 90);
const uint16_t MH_CAM        = mau565(255, 170, 0);
const uint16_t MH_XANH_DUONG = mau565(40, 130, 255);
const uint16_t MH_XANH_SPO2  = mau565(90, 200, 255);
const uint16_t MH_VANG_NHIET = mau565(255, 210, 90);

class BoVeManHinh {
public:
  // Goi khi man vua bat lai (het ngu) de ve lai toan bo.
  void veLaiHet() { hopLe = false; }

  void ve(Adafruit_GFX& g, const TrangThaiManHinh& s) {
    bool het = !hopLe || s.loai != cu.loai;
    switch (s.loai) {
      case MH_CHINH:    veChinh(g, s, het); break;
      case MH_TE_NGA:   veTeNga(g, s, het); break;
      case MH_CANH_BAO: veCanhBao(g, s, het || s.maCanhBao != cu.maCanhBao || s.giaTri != cu.giaTri); break;
      default:          if (het) veDaBao(g); break;
    }
    cu = s;
    hopLe = true;
  }

private:
  TrangThaiManHinh cu;
  bool hopLe = false;

  // ---------- tien ich ----------
  static void chuGiua(Adafruit_GFX& g, const char* s, int16_t cx, int16_t y, const GFXfont* f,
                      uint16_t mau, uint8_t co = 1) {
    int16_t x1, y1; uint16_t w, h;
    g.setFont(f); g.setTextSize(co); g.setTextColor(mau);
    g.getTextBounds(s, 0, y, &x1, &y1, &w, &h);
    g.setCursor(cx - (int16_t)(w / 2) - x1, y);
    g.print(s);
  }

  static int16_t rongChu(Adafruit_GFX& g, const char* s, const GFXfont* f) {
    int16_t x1, y1; uint16_t w, h;
    g.setFont(f); g.setTextSize(1);
    g.getTextBounds(s, 0, 100, &x1, &y1, &w, &h);
    return w;
  }

  // "36.5 °C" can giua; font khong co dau do nen ve vong tron nho.
  static void nhietDoGiua(Adafruit_GFX& g, int16_t t100, int16_t cx, int16_t y, const GFXfont* f, uint16_t mau) {
    char so[12];
    int16_t a = t100 < 0 ? -t100 : t100;
    int16_t le = (a % 100 + 5) / 10, nguyen = a / 100;
    if (le == 10) { nguyen++; le = 0; }
    snprintf(so, sizeof so, "%s%d.%d", t100 < 0 ? "-" : "", nguyen, le);
    int16_t wSo = rongChu(g, so, f), wC = rongChu(g, "C", f);
    int16_t tong = wSo + 4 + 6 + 3 + wC;
    int16_t x = cx - tong / 2;
    g.setFont(f); g.setTextSize(1); g.setTextColor(mau);
    int16_t x1, y1; uint16_t w, h;
    g.getTextBounds(so, 0, y, &x1, &y1, &w, &h);
    g.setCursor(x - x1, y); g.print(so);
    g.drawCircle(x + wSo + 7, y1 + 3, 3, mau);
    g.drawCircle(x + wSo + 7, y1 + 3, 2, mau);
    g.getTextBounds("C", 0, y, &x1, &y1, &w, &h);
    g.setCursor(x + wSo + 13 - x1, y); g.print("C");
  }

  static void veTim(Adafruit_GFX& g, int16_t x, int16_t y, uint16_t mau) {
    g.fillCircle(x - 6, y, 7, mau);
    g.fillCircle(x + 6, y, 7, mau);
    g.fillTriangle(x - 13, y + 2, x + 13, y + 2, x, y + 17, mau);
  }

  static void veBle(Adafruit_GFX& g, int16_t x, int16_t y, uint16_t mau) {   // ky hieu Bluetooth cao 16
    g.drawLine(x + 4, y, x + 4, y + 16, mau);
    g.drawLine(x + 4, y, x + 8, y + 4, mau);
    g.drawLine(x + 8, y + 4, x, y + 12, mau);
    g.drawLine(x + 4, y + 16, x + 8, y + 12, mau);
    g.drawLine(x + 8, y + 12, x, y + 4, mau);
  }

  static void vePin(Adafruit_GFX& g, int16_t x, int16_t y, uint8_t pt) {
    uint16_t mau = pt <= 15 ? MH_DO_TIM : (pt <= 30 ? MH_CAM : MH_XANH_LA);
    g.drawRect(x, y, 22, 12, MH_TRANG);
    g.fillRect(x + 22, y + 3, 2, 6, MH_TRANG);
    g.fillRect(x + 2, y + 2, (uint16_t)18 * pt / 100, 8, mau);
  }

  // ---------- man chinh ----------
  static const char* dongTrangThai(const TrangThaiManHinh& s, uint16_t& mau) {
    if (!s.coTay)      { mau = MH_XAM; return "Chua deo"; }
    if (!s.nhipTim)    { mau = MH_XAM; return "Dang do..."; }
    if (!s.ketNoi)     { mau = MH_CAM; return "Mat ket noi DT"; }
    mau = MH_XANH_LA;  return "Binh thuong";
  }

  void veChinh(Adafruit_GFX& g, const TrangThaiManHinh& s, bool het) {
    if (het) {
      g.fillScreen(MH_DEN);
      veTim(g, 52, 92, MH_DO_TIM);
      chuGiua(g, "nhip/phut", 128, 143, &FreeSans9pt7b, MH_XAM);
      g.drawFastHLine(45, 150, 150, MH_XAM_TOI);
      g.drawFastVLine(120, 156, 42, MH_XAM_TOI);
      chuGiua(g, "SpO2", 80, 170, &FreeSans9pt7b, MH_XAM);
      chuGiua(g, "Nhiet do", 162, 170, &FreeSans9pt7b, MH_XAM);
    }
    // Gio tren cung
    if (het || s.phutTrongNgay != cu.phutTrongNgay) {
      g.fillRect(56, 14, 128, 40, MH_DEN);
      char gio[6];
      if (s.phutTrongNgay >= 0) snprintf(gio, sizeof gio, "%02d:%02d", s.phutTrongNgay / 60, s.phutTrongNgay % 60);
      else strcpy(gio, "--:--");
      chuGiua(g, gio, 120, 48, &FreeSansBold18pt7b, s.phutTrongNgay >= 0 ? MH_TRANG : MH_XAM);
    }
    // Hang thu hai: ket noi + pin
    if (het || s.ketNoi != cu.ketNoi || s.pin != cu.pin) {
      g.fillRect(70, 54, 100, 21, MH_DEN);
      veBle(g, 82, 57, s.ketNoi ? MH_XANH_DUONG : MH_XAM_TOI);
      vePin(g, 100, 60, s.pin);
      char pt[6]; snprintf(pt, sizeof pt, "%u%%", s.pin);
      g.setFont(&FreeSans9pt7b); g.setTextSize(1); g.setTextColor(MH_TRANG);
      g.setCursor(129, 72); g.print(pt);
    }
    // Nhip tim
    if (het || s.nhipTim != cu.nhipTim || s.coTay != cu.coTay) {
      g.fillRect(72, 76, 112, 46, MH_DEN);
      char so[5];
      if (s.coTay && s.nhipTim) snprintf(so, sizeof so, "%u", s.nhipTim); else strcpy(so, "--");
      chuGiua(g, so, 128, 118, &FreeSansBold24pt7b, MH_TRANG);
    }
    // SpO2
    if (het || s.spo2 != cu.spo2 || s.coTay != cu.coTay) {
      g.fillRect(42, 176, 76, 26, MH_DEN);
      char so[6];
      if (s.coTay && s.spo2) snprintf(so, sizeof so, "%u%%", s.spo2); else strcpy(so, "--");
      chuGiua(g, so, 80, 197, &FreeSansBold12pt7b, MH_XANH_SPO2);
    }
    // Nhiet do
    if (het || s.nhietDoHopLe != cu.nhietDoHopLe || s.nhietDo / 10 != cu.nhietDo / 10) {
      g.fillRect(122, 176, 82, 26, MH_DEN);
      if (s.nhietDoHopLe) nhietDoGiua(g, s.nhietDo, 162, 197, &FreeSansBold12pt7b, MH_VANG_NHIET);
      else chuGiua(g, "--", 162, 197, &FreeSansBold12pt7b, MH_VANG_NHIET);
    }
    // Dong trang thai duoi cung
    uint16_t mauMoi, mauCu;
    const char* moi = dongTrangThai(s, mauMoi);
    const char* cuChu = dongTrangThai(cu, mauCu);
    if (het || moi != cuChu) {
      g.fillRect(52, 204, 136, 20, MH_DEN);
      chuGiua(g, moi, 120, 219, &FreeSans9pt7b, mauMoi);
    }
  }

  // ---------- man te nga ----------
  void veTeNga(Adafruit_GFX& g, const TrangThaiManHinh& s, bool het) {
    if (het) {
      g.fillScreen(MH_DO_NEN);
      chuGiua(g, "TE NGA?", 120, 72, &FreeSansBold18pt7b, MH_TRANG);
      chuGiua(g, "Bam nut", 120, 184, &FreeSans9pt7b, MH_TRANG);
      chuGiua(g, "neu ban khong sao", 120, 203, &FreeSans9pt7b, MH_TRANG);
    }
    if (het || s.giayConLai != cu.giayConLai) {
      g.fillRect(55, 88, 130, 78, MH_DO_NEN);
      char so[4]; snprintf(so, sizeof so, "%u", s.giayConLai);
      chuGiua(g, so, 120, 160, &FreeSansBold24pt7b, MH_TRANG, 2);
    }
  }

  // ---------- man canh bao ----------
  static void dongKetNoi(Adafruit_GFX& g, bool ketNoi, uint16_t nen, uint16_t chu) {
    g.fillRect(40, 164, 160, 48, nen);
    if (ketNoi) {
      chuGiua(g, "Dang bao", 120, 182, &FreeSans9pt7b, chu);
      chuGiua(g, "nguoi than...", 120, 203, &FreeSans9pt7b, chu);
    } else {
      chuGiua(g, "Chua ket noi", 120, 182, &FreeSans9pt7b, chu);
      chuGiua(g, "dien thoai", 120, 203, &FreeSans9pt7b, chu);
    }
  }

  void veCanhBao(Adafruit_GFX& g, const TrangThaiManHinh& s, bool het) {
    bool khanCap = s.maCanhBao == 1 || s.maCanhBao == 2;   // SOS, te nga
    uint16_t nen = khanCap ? MH_DO_NEN : MH_CAM_NEN;
    uint16_t chu = khanCap ? MH_TRANG : MH_DEN;
    if (het) {
      g.fillScreen(nen);
      char so[10] = "";
      const char* tieuDe = "CANH BAO";
      switch (s.maCanhBao) {
        case 1: tieuDe = "SOS"; break;
        case 2: tieuDe = "TE NGA"; break;
        case 3: tieuDe = "NHIP TIM CAO"; snprintf(so, sizeof so, "%u", s.giaTri); break;
        case 4: tieuDe = "NHIP TIM THAP"; snprintf(so, sizeof so, "%u", s.giaTri); break;
        case 5: tieuDe = "SpO2 THAP"; snprintf(so, sizeof so, "%u%%", s.giaTri); break;
        case 6: tieuDe = "SOT"; break;
      }
      if (khanCap) {
        chuGiua(g, tieuDe, 120, 128, &FreeSansBold24pt7b, chu);
      } else {
        chuGiua(g, tieuDe, 120, 82, &FreeSansBold12pt7b, chu);
        if (s.maCanhBao == 6) nhietDoGiua(g, (int16_t)s.giaTri, 120, 140, &FreeSansBold24pt7b, chu);
        else chuGiua(g, so, 120, 140, &FreeSansBold24pt7b, chu);
      }
    }
    if (het || s.ketNoi != cu.ketNoi) dongKetNoi(g, s.ketNoi, nen, chu);
  }

  // ---------- man da bao ----------
  static void veDaBao(Adafruit_GFX& g) {
    g.fillScreen(MH_XANH_NEN);
    // dau tich
    for (int8_t d = -2; d <= 2; d++) {
      g.drawLine(92, 70 + d, 110, 88 + d, MH_TRANG);
      g.drawLine(110, 88 + d, 148, 50 + d, MH_TRANG);
    }
    chuGiua(g, "DA BAO", 120, 135, &FreeSansBold18pt7b, MH_TRANG);
    chuGiua(g, "nguoi than", 120, 168, &FreeSansBold12pt7b, MH_TRANG);
  }
};
