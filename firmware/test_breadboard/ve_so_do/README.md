# Vẽ sơ đồ cắm breadboard

`ve.py` liệt kê từng dây (lỗ đầu, lỗ cuối, màu) và vẽ breadboard thành SVG; `trang.py` ghép thêm bảng dây và ghi chú; `chup.js` chụp thành PNG bằng Playwright.

```
python ve_so_do/ve.py so_do.svg day.json mau.json
python ve_so_do/trang.py          # đọc so_do.svg, day.json, mau.json trong thư mục hiện tại
node ve_so_do/chup.js %CD%/so_do.html so_do_breadboard_28-10.png
```

Đổi dây thì sửa danh sách `DAY` trong `ve.py`.
