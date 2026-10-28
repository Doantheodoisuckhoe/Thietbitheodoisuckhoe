// Ve thu cac man hinh cua dong ho ra file anh (PPM) tren may tinh, dung dung code man_hinh.h.
// Cach chay: xem README.md trong thu muc nay.
#include <Adafruit_GFX.h>
#include "../man_hinh.h"

static void luuAnh(GFXcanvas16& c, const char* ten) {
  FILE* f = fopen(ten, "wb");
  if (!f) { perror(ten); return; }
  fprintf(f, "P6\n240 240\n255\n");
  const uint16_t* p = c.getBuffer();
  for (int i = 0; i < 240 * 240; i++) {
    uint16_t v = p[i];
    uint8_t rgb[3] = { (uint8_t)((v >> 11) * 255 / 31), (uint8_t)(((v >> 5) & 63) * 255 / 63),
                       (uint8_t)((v & 31) * 255 / 31) };
    fwrite(rgb, 1, 3, f);
  }
  fclose(f);
  printf("da ghi %s\n", ten);
}

int main() {
  GFXcanvas16 c(240, 240);
  BoVeManHinh bv;
  TrangThaiManHinh s;

  // 1. Dang deo, so do binh thuong, co ket noi
  s.loai = MH_CHINH; s.coTay = true; s.nhipTim = 78; s.spo2 = 98;
  s.nhietDoHopLe = true; s.nhietDo = 3462; s.pin = 85; s.ketNoi = true;
  bv.ve(c, s); luuAnh(c, "1_man_chinh.ppm");

  // 2. Cap nhat tung phan (khong ve lai het): nhip tim doi, mat ket noi, pin yeu
  s.nhipTim = 102; s.ketNoi = false; s.pin = 12; s.nhietDo = 3471;
  bv.ve(c, s); luuAnh(c, "2_man_chinh_mat_ket_noi.ppm");

  // 3. Chua deo
  s.coTay = false; s.nhipTim = 0; s.spo2 = 0; s.ketNoi = true; s.pin = 60;
  bv.ve(c, s); luuAnh(c, "3_chua_deo.ppm");

  // 4. Te nga: dem nguoc
  s.loai = MH_TE_NGA; s.giayConLai = 15;
  bv.ve(c, s);
  s.giayConLai = 9;
  bv.ve(c, s); luuAnh(c, "4_te_nga_dem_nguoc.ppm");

  // 5. SOS dang gui, co ket noi
  s.loai = MH_CANH_BAO; s.maCanhBao = 1; s.giaTri = 0; s.ketNoi = true;
  bv.ve(c, s); luuAnh(c, "5_sos.ppm");

  // 6. Nhip tim cao, chua ket noi dien thoai
  s.maCanhBao = 3; s.giaTri = 134; s.ketNoi = false;
  bv.ve(c, s); luuAnh(c, "6_nhip_tim_cao.ppm");

  // 7. Sot
  s.maCanhBao = 6; s.giaTri = 3820; s.ketNoi = true;
  bv.ve(c, s); luuAnh(c, "7_sot.ppm");

  // 8. App da xac nhan
  s.loai = MH_DA_BAO;
  bv.ve(c, s); luuAnh(c, "8_da_bao.ppm");
  return 0;
}
