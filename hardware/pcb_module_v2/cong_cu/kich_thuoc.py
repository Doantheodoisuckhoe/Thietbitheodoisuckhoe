# Kích thước đo trên module thật (bản 2.0). Dùng chung cho gen_fp.py và kiem_tra_kich_thuoc.py.
# Mọi toạ độ tính bằng mm.

P = 2.54

# ---- AD8232 (bo đỏ 28 x 35 mm). Gốc = tâm lỗ bắt vít góc trên-trái, x sang phải, y xuống dưới,
#      nhìn từ mặt linh kiện của module (module úp lên trên mạch, chân cắm xuống).
AD8232_PADS = {
    '1': ('RA', 19.05, 0.0),
    '2': ('LA', 16.51, 0.0),
    '3': ('RL', 13.97, 0.0),
    '4': ('GND', 0.0, 10.033),
    '5': ('3V3', 0.0, 12.573),
    '6': ('OUTPUT', 0.0, 15.113),
    '7': ('LO-', 0.0, 17.653),
    '8': ('LO+', 0.0, 20.193),
    '9': ('SDN', 0.0, 22.733),
}
AD8232_LO_VIT = [(0.0, 0.0), (24.257, 0.0), (0.0, 32.004), (24.257, 32.004)]   # 4 lỗ bắt vít của module
AD8232_VIEN = (-1.87, -1.5, 26.13, 33.5)        # viền module 28 x 35 mm

# ---- Màn tròn GC9A01 1,28". Gốc = tâm hình tròn. 7 pad bước 2,54 nằm giữa, hàng pad cách tâm 24,7 mm.
#      Thứ tự pad 1..7 theo bản vẽ (CẦN KIỂM TRA TRÊN MODULE THẬT). Pad 8 (BLK) thêm cho module 8 chân.
GC9A01_R = 38.1 / 2
GC9A01_HANG = 24.7
GC9A01_DAI = 45.4                 # từ đỉnh hình tròn tới đầu chân
GC9A01_TAB_W = 22.9
GC9A01_TEN = ['RST', 'CS', 'DC', 'SDA', 'SCL', 'GND', 'VCC', 'BLK']
GC9A01_PADS = {str(i + 1): (GC9A01_TEN[i], (i - 3) * P, GC9A01_HANG) for i in range(8)}

# ---- XIAO nRF52840 Sense hàn thẳng bằng 2 hàng chân 1x7, hai hàng cách 15,24 mm
XIAO_HANG = 15.24
XIAO_THAN = (17.8, 21.0)

# ---- Nút SOS 6x6x7,5 góc vuông (TẠM, chờ đo nút thật): 4 chân xếp 6,5 x 4,5 mm
SOS_DOC, SOS_NGANG = 6.5, 4.5

# ---- Pin 502030
PIN = (20.5, 30.0, 5.5)            # 502030 đo thật ~5,5 x 20,5 x 30 mm (tính cả PCM)

# ---- Motor rung 1027 (đồng xu 10 mm, dày 2,7 mm), 2 pad dây cách 4,0 mm (TẠM)
MOTOR_D = 10.0
MOTOR_BUOC = 4.0

# ---- Chân sạc pogo 2 chân (TẠM): bước 2,54
POGO_BUOC = 2.54
