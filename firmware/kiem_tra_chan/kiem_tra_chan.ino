// Kiem tra moi han chan XIAO: tim chan bi chap voi GND, voi 3V3, hoac chap voi nhau.
// Board: "Seeed XIAO nRF52840 Sense" (goi "Seeed nRF52 Boards"), Serial Monitor 115200.
//
// QUAN TRONG: rut het day va module ra khoi XIAO truoc khi chay. Module noi vao chan
// (vi du AD8232 keo chan LO len/xuong) se lam sketch bao chap gia.
// Sketch chi kiem tra duoc 11 chan D0..D10. Ba chan 5V, GND, 3V3 phai do bang dong ho (xem README).
//
// Cach lam voi moi chan:
//   1. Bat dien tro keo len ben trong: chan phai doc HIGH. Doc LOW = chap xuong GND.
//   2. Bat dien tro keo xuong ben trong: chan phai doc LOW. Doc HIGH = chap len 3V3.
//   3. Keo mot chan xuong LOW, cac chan khac de keo len: chan nao cung bi LOW theo = hai chan chap nhau.
// Dien tro keo ben trong chi khoang 13 kOhm nen dong rat nho, khong hai board du co chap.

#include <Adafruit_TinyUSB.h>

const uint8_t SO_CHAN = 11;
const uint8_t CHAN[SO_CHAN] = {D0, D1, D2, D3, D4, D5, D6, D7, D8, D9, D10};
const char*   TEN[SO_CHAN]  = {"D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10"};

void tatCaKeoLen() {
  for (uint8_t i = 0; i < SO_CHAN; i++) pinMode(CHAN[i], INPUT_PULLUP);
  delay(5);
}

uint8_t kiemTra() {
  uint8_t loi = 0;
  bool chapGnd[SO_CHAN];

  // Buoc 1 va 2: tung chan voi GND va 3V3
  for (uint8_t i = 0; i < SO_CHAN; i++) {
    pinMode(CHAN[i], INPUT_PULLUP);
    delay(2);
    chapGnd[i] = (digitalRead(CHAN[i]) == LOW);
    pinMode(CHAN[i], INPUT_PULLDOWN);
    delay(2);
    bool chap3v3 = (digitalRead(CHAN[i]) == HIGH);
    pinMode(CHAN[i], INPUT_PULLUP);

    if (chapGnd[i]) { Serial.print("  LOI: "); Serial.print(TEN[i]); Serial.println(" chap xuong GND"); loi++; }
    if (chap3v3)    { Serial.print("  LOI: "); Serial.print(TEN[i]); Serial.println(" chap len 3V3"); loi++; }
  }

  // Buoc 3: tung cap chan voi nhau (bo qua chan da chap GND vi luc nao cung doc LOW)
  for (uint8_t i = 0; i < SO_CHAN; i++) {
    if (chapGnd[i]) continue;
    tatCaKeoLen();
    pinMode(CHAN[i], OUTPUT);
    digitalWrite(CHAN[i], LOW);
    delay(2);
    for (uint8_t j = i + 1; j < SO_CHAN; j++) {
      if (chapGnd[j]) continue;
      if (digitalRead(CHAN[j]) == LOW) {
        Serial.print("  LOI: "); Serial.print(TEN[i]); Serial.print(" chap voi "); Serial.println(TEN[j]);
        loi++;
      }
    }
  }
  tatCaKeoLen();
  return loi;
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 5000) {}
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
}

void loop() {
  Serial.println("===== Kiem tra chan D0..D10 (rut het day ra khoi XIAO) =====");
  uint8_t loi = kiemTra();
  if (loi == 0) {
    Serial.println("TAT CA 11 CHAN TOT: khong chap GND, khong chap 3V3, khong chap nhau");
    digitalWrite(LED_GREEN, LOW);   // LED tren XIAO sang khi muc LOW
    digitalWrite(LED_RED, HIGH);
  } else {
    Serial.print("Tim thay "); Serial.print(loi); Serial.println(" loi, xem cac dong LOI o tren");
    digitalWrite(LED_GREEN, HIGH);
    digitalWrite(LED_RED, LOW);
  }
  Serial.println();
  delay(3000);
}
