// ble_link.h — dịch vụ GATT của đồng hồ (thư viện Bluefruit, gói Seeed nRF52 Boards).
#pragma once
#include <Arduino.h>

#include "protocol.h"

namespace BleLink {
void begin(const char* name);
bool connected();
uint32_t connectedSinceMs();  // millis() lúc kết nối, 0 nếu chưa kết nối
uint16_t mtu();

bool vitalsReady();  // điện thoại đã bật notify
bool eventsReady();  // điện thoại đã bật indicate
bool ecgReady();

bool sendVitals(const VitalsPacket& p);
bool sendEvent(const EventPacket& p);  // indicate: chờ điện thoại xác nhận
bool sendEcgData(const uint8_t* data, uint16_t len);
bool sendEcgResult(const EcgResultPacket& p);
void setBattery(uint8_t pct);

// Lệnh từ điện thoại được xếp hàng trong callback BLE, loop() lấy ra xử lý.
bool popCommand(uint8_t* buf, uint8_t* len);  // buf >= 20 byte
}  // namespace BleLink
