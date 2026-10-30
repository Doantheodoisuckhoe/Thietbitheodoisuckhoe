# Web cho người thân

Web React hiện tình trạng người đeo đồng hồ: dòng trạng thái lớn ở đầu trang (ổn / có cảnh báo / mất liên lạc),
số đo hiện tại, biểu đồ 24 giờ và danh sách cảnh báo kèm vị trí. Dữ liệu do app trên điện thoại người đeo
gửi lên Firebase Realtime Database.

```
Đồng hồ --BLE--> App Android --HTTPS--> Firebase Realtime Database <--- Web (người thân)
                     \--SMS--> người thân
```

Địa chỉ web sau khi bật GitHub Pages: **https://doantheodoisuckhoe.github.io/Thietbitheodoisuckhoe/**
Chưa điền cấu hình Firebase thì web hiện **dữ liệu mẫu**. Thêm `?demo=nga` vào cuối địa chỉ để xem lúc có cảnh báo té ngã.

## Cài đặt lần đầu (khoảng 15 phút, làm trên trình duyệt)

### 1. Bật GitHub Pages (1 lần)
GitHub → repo → **Settings** → **Pages** → mục *Build and deployment*, ô **Source** chọn **GitHub Actions**.
Sau đó vào tab **Actions** → **Dua web len mang** → **Run workflow**. Khoảng 1 phút sau web có ở địa chỉ trên.

### 2. Tạo dự án Firebase (miễn phí, gói Spark)
1. Vào https://console.firebase.google.com → **Create a project** → đặt tên, ví dụ `dong-ho-suc-khoe`.
   Tắt Google Analytics (không cần).
2. **Build → Authentication → Get started** → tab *Sign-in method* → **Email/Password** → bật → Save.
3. Tab **Users → Add user**: tạo **một tài khoản gia đình** (email + mật khẩu). App và web cùng dùng tài khoản này.
4. **Build → Realtime Database → Create Database** → chọn vị trí **Singapore (asia-southeast1)** →
   **Start in locked mode**.
   - Tab **Rules**: xóa hết, dán nội dung file [`database.rules.json`](database.rules.json) → **Publish**.
     Luật này chỉ cho tài khoản đã đăng nhập đọc/ghi dữ liệu của chính nó.
   - Tab **Data**: chép địa chỉ ở đầu trang, dạng `https://dong-ho-suc-khoe-default-rtdb.asia-southeast1.firebasedatabase.app`.
5. Bánh răng **Project settings → General** → mục *Your apps* → bấm biểu tượng **`</>`** (Web) → đặt tên `web`,
   không chọn Hosting → **Register app**. Firebase hiện một đoạn `firebaseConfig = { apiKey: ..., ... }`.

### 3. Điền cấu hình vào web
Trên GitHub mở [`web/src/cauHinhFirebase.js`](src/cauHinhFirebase.js) → bấm cây bút (Edit) → chép 5 giá trị
`apiKey`, `authDomain`, `databaseURL`, `projectId`, `appId` từ bước 2.5 vào → **Commit changes** thẳng vào `main`.
GitHub Actions tự build và đưa web mới lên (khoảng 1 phút).

Các giá trị này không phải mật khẩu, Firebase thiết kế để đặt công khai trong web. Dữ liệu được bảo vệ bởi
Rules ở bước 2.4 và mật khẩu tài khoản gia đình. **Không** ghi mật khẩu vào repo.

### 4. Đăng nhập trong app
App trên điện thoại người đeo → tab **Web** → điền *Web API key* (giá trị `apiKey`), *Địa chỉ Realtime Database*,
email và mật khẩu tài khoản gia đình → **Đăng nhập và bắt đầu gửi**. Thẻ màu xanh hiện "Lần gửi cuối" là được.

### 5. Người thân mở web
Mở địa chỉ web, đăng nhập bằng cùng email và mật khẩu. Web tự cập nhật, không cần tải lại trang.

## Dữ liệu trên Firebase

```
nguoiDung/{uid}/
  thongTin   { tenNguoiDeo, dangNhapLuc }
  hienTai    { nhipTim, spo2, nhietDo, pinPhanTram, dangDeo, ketNoi, luc }   app ghi 10 giây/lần
  soDo/{yyyyMMddHHmm}   { nhipTim, spo2, nhietDo, luc }                      trung bình mỗi phút
  canhBao/{luc_ma}      { ma, ten, khanCap, giaTri, moTa, soTinDaGui, soNguoiThan, viDo, kinhDo, luc }
  ecg/{luc}             { luc, soGiay, nhipTb, nhipThapNhat, nhipCaoNhat, soNhip, coTuotDienCuc, soMauThieu }
  ecgSong/{luc}         { luc, tanSo: 250, mau, dinhR }   mau: ADC 12 bit, uint16 little-endian, base64 (~20 KB/lần)
```
`luc` là mili giây tính từ 1/1/1970 (giờ chuẩn). Gói miễn phí Spark cho 1 GB lưu trữ, đủ khoảng vài năm số đo 1 phút/lần.
Mỗi lần đo ECG tốn khoảng 20 KB, nên 1 GB chứa được hàng chục nghìn lần đo.

**Điện tâm đồ:** mỗi lần người đeo đo ECG 30 giây trong app, app tải lên `ecgSong` (sóng) rồi `ecg` (tóm tắt);
mất mạng thì app giữ tối đa 5 lần đo và gửi lại khi có mạng. Web liệt kê 20 lần đo gần nhất, bấm vào một lần để
xem 6 dải sóng 5 giây trên nền giấy ECG (ô nhỏ 0,04 giây, ô lớn 0,2 giây) có chấm đỉnh R, và nút **Tải CSV cho bác sĩ**
(cột `t_ms,adc`, giá trị ADC gốc chưa lọc). Đây là 1 chuyển đạo đo ở hai tay, chưa hiệu chuẩn theo mV, chỉ để tham khảo.

> **Nếu đã dán luật ở bước 2.4 trước ngày 30/10/2026:** dán lại nội dung mới của `database.rules.json` (có thêm dòng `"ecg"`)
> rồi bấm **Publish**, để web lọc nhanh danh sách ECG.

Web coi là **mất liên lạc** khi `hienTai` không được cập nhật quá 5 phút, và hiện cảnh báo ở đầu trang trong 1 giờ.

## Sửa code

Cần Node.js 24.

```
cd web
npm install
npm run dev     # mở http://localhost:5173 (chưa có cấu hình thì chạy dữ liệu mẫu)
npm test        # test phần tính trạng thái và xử lý sóng ECG
npm run build
```

| File | Nội dung |
|---|---|
| `src/App.jsx` | Giao diện: đăng nhập, dải trạng thái, số đo, biểu đồ (recharts), danh sách cảnh báo, điện tâm đồ |
| `src/ecg.js` | Giải mã, lọc, chia dải sóng ECG, xuất CSV (có test `ecg.test.js`) |
| `src/tinhTrang.js` | Tính dòng trạng thái ở đầu trang (có test `tinhTrang.test.js`) |
| `src/duLieu.js` | Đăng nhập Firebase, nghe dữ liệu thời gian thực, dữ liệu mẫu |
| `src/cauHinhFirebase.js` | Cấu hình Firebase của nhóm |
| `database.rules.json` | Luật bảo mật Realtime Database |
