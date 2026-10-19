// ble_link.cpp — xem ble_link.h
#include "ble_link.h"

#include <bluefruit.h>

namespace {
const uint8_t U_SERVICE[16] = HW_UUID(UUID_SERVICE);
const uint8_t U_VITALS[16] = HW_UUID(UUID_VITALS);
const uint8_t U_EVENT[16] = HW_UUID(UUID_EVENT);
const uint8_t U_ECG_DATA[16] = HW_UUID(UUID_ECG_DATA);
const uint8_t U_ECG_RESULT[16] = HW_UUID(UUID_ECG_RESULT);
const uint8_t U_CONTROL[16] = HW_UUID(UUID_CONTROL);

BLEService svc(U_SERVICE);
BLECharacteristic chVitals(U_VITALS);
BLECharacteristic chEvent(U_EVENT);
BLECharacteristic chEcgData(U_ECG_DATA);
BLECharacteristic chEcgResult(U_ECG_RESULT);
BLECharacteristic chControl(U_CONTROL);
BLEDis dis;
BLEBas bas;

volatile uint16_t g_conn = BLE_CONN_HANDLE_INVALID;
volatile uint32_t g_conn_ms = 0;

// hàng đợi lệnh (1 producer: task BLE, 1 consumer: loop)
const int CMD_Q = 8;
uint8_t cmd_buf[CMD_Q][20];
uint8_t cmd_len[CMD_Q];
volatile uint8_t cmd_head = 0, cmd_tail = 0;

void onControlWrite(uint16_t conn_hdl, BLECharacteristic* chr, uint8_t* data, uint16_t len) {
  (void)conn_hdl;
  (void)chr;
  uint8_t next = (cmd_head + 1) % CMD_Q;
  if (next == cmd_tail || len == 0) return;  // đầy -> bỏ
  if (len > 20) len = 20;
  memcpy(cmd_buf[cmd_head], data, len);
  cmd_len[cmd_head] = (uint8_t)len;
  cmd_head = next;
}

void onConnect(uint16_t conn_hdl) {
  g_conn = conn_hdl;
  g_conn_ms = millis();
  if (g_conn_ms == 0) g_conn_ms = 1;
  BLEConnection* c = Bluefruit.Connection(conn_hdl);
  c->requestPHY();
  c->requestDataLengthUpdate();
  c->requestMtuExchange(247);
}

void onDisconnect(uint16_t conn_hdl, uint8_t reason) {
  (void)conn_hdl;
  (void)reason;
  g_conn = BLE_CONN_HANDLE_INVALID;
  g_conn_ms = 0;
}
}  // namespace

namespace BleLink {

void begin(const char* name) {
  Bluefruit.configPrphBandwidth(BANDWIDTH_MAX);  // MTU 247, hàng đợi notify lớn
  Bluefruit.begin();
  Bluefruit.autoConnLed(false);  // tắt LED xanh tự động -> tiết kiệm pin
  Bluefruit.setTxPower(0);
  Bluefruit.setName(name);
  Bluefruit.Periph.setConnectCallback(onConnect);
  Bluefruit.Periph.setDisconnectCallback(onDisconnect);
  Bluefruit.Periph.setConnInterval(40, 80);  // 50–100 ms: cân bằng pin / độ trễ

  dis.setManufacturer("DATN HealthWatch");
  dis.setModel("HW-XIAO-nRF52840");
  dis.begin();
  bas.begin();
  bas.write(100);

  svc.begin();

  chVitals.setProperties(CHR_PROPS_READ | CHR_PROPS_NOTIFY);
  chVitals.setPermission(SECMODE_OPEN, SECMODE_NO_ACCESS);
  chVitals.setFixedLen(sizeof(VitalsPacket));
  chVitals.begin();

  chEvent.setProperties(CHR_PROPS_READ | CHR_PROPS_INDICATE);
  chEvent.setPermission(SECMODE_OPEN, SECMODE_NO_ACCESS);
  chEvent.setFixedLen(sizeof(EventPacket));
  chEvent.begin();

  chEcgData.setProperties(CHR_PROPS_NOTIFY);
  chEcgData.setPermission(SECMODE_OPEN, SECMODE_NO_ACCESS);
  chEcgData.setMaxLen(244);
  chEcgData.begin();

  chEcgResult.setProperties(CHR_PROPS_READ | CHR_PROPS_NOTIFY);
  chEcgResult.setPermission(SECMODE_OPEN, SECMODE_NO_ACCESS);
  chEcgResult.setFixedLen(sizeof(EcgResultPacket));
  chEcgResult.begin();

  chControl.setProperties(CHR_PROPS_WRITE | CHR_PROPS_WRITE_WO_RESP);
  chControl.setPermission(SECMODE_NO_ACCESS, SECMODE_OPEN);
  chControl.setMaxLen(20);
  chControl.setWriteCallback(onControlWrite);
  chControl.begin();

  Bluefruit.Advertising.addFlags(BLE_GAP_ADV_FLAGS_LE_ONLY_GENERAL_DISC_MODE);
  Bluefruit.Advertising.addTxPower();
  Bluefruit.Advertising.addService(svc);
  Bluefruit.ScanResponse.addName();
  Bluefruit.Advertising.restartOnDisconnect(true);
  Bluefruit.Advertising.setInterval(160, 1600);  // 100 ms trong 30 s đầu, sau đó 1 s
  Bluefruit.Advertising.setFastTimeout(30);
  Bluefruit.Advertising.start(0);
}

bool connected() { return g_conn != BLE_CONN_HANDLE_INVALID; }
uint32_t connectedSinceMs() { return g_conn_ms; }

uint16_t mtu() {
  if (!connected()) return 23;
  BLEConnection* c = Bluefruit.Connection(g_conn);
  return c ? c->getMtu() : 23;
}

bool vitalsReady() { return connected() && chVitals.notifyEnabled(g_conn); }
bool eventsReady() { return connected() && chEvent.indicateEnabled(g_conn); }
bool ecgReady() { return connected() && chEcgData.notifyEnabled(g_conn); }

bool sendVitals(const VitalsPacket& p) {
  chVitals.write(&p, sizeof(p));
  return vitalsReady() && chVitals.notify(g_conn, &p, sizeof(p));
}

bool sendEvent(const EventPacket& p) {
  chEvent.write(&p, sizeof(p));
  return eventsReady() && chEvent.indicate(g_conn, &p, sizeof(p));
}

bool sendEcgData(const uint8_t* data, uint16_t len) {
  return ecgReady() && chEcgData.notify(g_conn, data, len);
}

bool sendEcgResult(const EcgResultPacket& p) {
  chEcgResult.write(&p, sizeof(p));
  return connected() && chEcgResult.notifyEnabled(g_conn) && chEcgResult.notify(g_conn, &p, sizeof(p));
}

void setBattery(uint8_t pct) { bas.write(pct); }

bool popCommand(uint8_t* buf, uint8_t* len) {
  if (cmd_tail == cmd_head) return false;
  *len = cmd_len[cmd_tail];
  memcpy(buf, cmd_buf[cmd_tail], *len);
  cmd_tail = (cmd_tail + 1) % CMD_Q;
  return true;
}

}  // namespace BleLink
