// Lay mau ECG tu AD8232 o 250 mau/giay bang timer phan cung, in ra Serial dang CSV.
// Board: Seeed XIAO nRF52840 Sense (goi "Seeed nRF52 Boards").
//
// Noi day (module AD8232 -> XIAO):
//   3.3V -> 3V3, GND -> GND, OUTPUT -> A0 (D0), LO+ -> D1, LO- -> D3
//   SDN de trong. Dan 3 dien cuc: do (RA) tay phai, vang (LA) tay trai, xanh (RL) chan phai
//   hoac theo hinh in tren mieng dan cua bo kit.
//
// Vi sao dung timer: ECG can lay mau dung deu nhip (khoang cach giua 2 mau luon 4 ms) thi
// bo loc va thuat toan Pan-Tompkins moi dung. Neu doc trong loop(), luc in Serial cham thi
// mau bi lech. O day TIMER4 (khong bi BLE hay loi Arduino su dung) goi ngat moi 4 ms,
// ngat doc ADC va cat vao bo dem vong; loop() chi viec lay ra va in.
//
// An toan: chi do khi XIAO chay pin hoac cam vao laptop KHONG cam sac.

#include <Adafruit_TinyUSB.h>   // can cho Serial qua cong USB khi sketch khong dung thu vien nao khac

const uint32_t TAN_SO_MAU   = 250;            // mau/giay; ECG can toi thieu khoang 250
const uint8_t  CHAN_ECG     = A0;
const uint8_t  CHAN_LO_DUONG = D1;
const uint8_t  CHAN_LO_AM   = D3;
const uint16_t KICH_THUOC_DEM = 256;          // khoang 1 giay du lieu, phai la luy thua cua 2

struct MauEcg {
  uint16_t giaTri;    // 0..4095 (ADC 12 bit)
  bool     tuotDienCuc;
};

volatile MauEcg  boDem[KICH_THUOC_DEM];
volatile uint16_t viTriGhi = 0;
volatile uint32_t soMauMat = 0;   // tang len neu loop() in khong kip
uint16_t viTriDoc = 0;
uint32_t soMau = 0;

extern "C" void TIMER4_IRQHandler(void) {
  if (NRF_TIMER4->EVENTS_COMPARE[0]) {
    NRF_TIMER4->EVENTS_COMPARE[0] = 0;

    uint16_t ke = (viTriGhi + 1) & (KICH_THUOC_DEM - 1);
    if (ke == viTriDoc) {         // bo dem day
      soMauMat++;
      return;
    }
    boDem[viTriGhi].giaTri = analogRead(CHAN_ECG);
    boDem[viTriGhi].tuotDienCuc = digitalRead(CHAN_LO_DUONG) || digitalRead(CHAN_LO_AM);
    viTriGhi = ke;
  }
}

void batDauTimer() {
  NRF_TIMER4->TASKS_STOP  = 1;
  NRF_TIMER4->MODE        = TIMER_MODE_MODE_Timer;
  NRF_TIMER4->BITMODE     = TIMER_BITMODE_BITMODE_32Bit;
  NRF_TIMER4->PRESCALER   = 4;                       // 16 MHz / 2^4 = 1 MHz, moi nhip 1 us
  NRF_TIMER4->CC[0]       = 1000000 / TAN_SO_MAU;    // 4000 us
  NRF_TIMER4->SHORTS      = TIMER_SHORTS_COMPARE0_CLEAR_Msk;
  NRF_TIMER4->INTENSET    = TIMER_INTENSET_COMPARE0_Msk;
  NVIC_SetPriority(TIMER4_IRQn, 3);                  // muc uu tien ma BLE cho phep ung dung dung
  NVIC_EnableIRQ(TIMER4_IRQn);
  NRF_TIMER4->TASKS_CLEAR = 1;
  NRF_TIMER4->TASKS_START = 1;
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000) {}

  pinMode(CHAN_LO_DUONG, INPUT);
  pinMode(CHAN_LO_AM, INPUT);
  analogReadResolution(12);

  Serial.println("t_ms,ecg,tuot_dien_cuc");
  batDauTimer();
}

void loop() {
  while (viTriDoc != viTriGhi) {
    MauEcg mau;
    mau.giaTri = boDem[viTriDoc].giaTri;
    mau.tuotDienCuc = boDem[viTriDoc].tuotDienCuc;
    viTriDoc = (viTriDoc + 1) & (KICH_THUOC_DEM - 1);

    Serial.print(soMau * (1000 / TAN_SO_MAU));
    Serial.print(',');
    Serial.print(mau.giaTri);
    Serial.print(',');
    Serial.println(mau.tuotDienCuc ? 1 : 0);
    soMau++;
  }

  static uint32_t lanBaoTruoc = 0;
  if (soMauMat != lanBaoTruoc) {
    lanBaoTruoc = soMauMat;
    Serial.print("# Mat mau (in Serial khong kip): ");
    Serial.println(lanBaoTruoc);
  }
}
