# HƯỚNG DẪN CHẠY SOURCE CODE

> **Lưu ý:** Thêm cờ `-X utf8` khi chạy trên Windows để hiển thị tiếng Việt có dấu chuẩn xác.

---

### 1. Chạy kiểm thử tự động 10 Test Cases (Khuyên dùng)
Kiểm tra toàn bộ thuật toán Suy diễn tiến, Xử lý xung đột, Chống lặp vô hạn và Đọc CSV:
```powershell
python -X utf8 test_suite.py
```
*(Kết quả kỳ vọng: `10/10 TEST CASES ĐẠT CHUẨN (100% PASS)`)*

---

### 2. Chạy mô phỏng tư vấn & Giải trình "Vì sao?" (CLI Mode)
Chạy 5 kịch bản học sinh thực tế và xuất vết suy diễn:
```powershell
python -X utf8 app.py
```

---

### 3. Chạy trực tiếp Lõi Suy diễn & Xử lý xung đột
Kiểm tra riêng thuật toán `ForwardChainingEngine` và `ConflictResolver`:
```powershell
python -X utf8 core_engine.py
```

---

### 4. Chạy giao diện Web (Streamlit)
Dành cho demo giao diện trực quan:
```powershell
# Bước 1: Cài thư viện (chỉ làm 1 lần đầu)
pip install streamlit

# Bước 2: Khởi động giao diện web
streamlit run app.py
```

Trong giao diện, nhập hồ sơ học sinh, chọn các năng lực/sở thích rồi bấm **Nhận tư vấn**.
Có thể bổ sung điểm Toán, Tin học và Tiếng Anh để hiển thị cùng hồ sơ; điểm hiện chỉ mang
tính tham khảo vì cơ sở luật chưa có điều kiện/ngưỡng điểm. Phần giải thích chỉ rõ luật và
các sự kiện đầu vào dẫn đến từng khuyến nghị; nhật ký suy diễn có thể mở ở cuối kết quả.

### 5. Chạy website tĩnh dựa trên template HTML5 UP
Website tư vấn chọn ngành/nghề THPT nằm trong thư mục `website` và nạp cơ sở tri thức
tổng quát từ `kb/rules_kb.json`. Vì vậy, chạy máy chủ từ thư mục gốc:
```powershell
python -m http.server 8000
```
Sau đó mở `http://localhost:8000/website/`. Không mở trực tiếp file HTML vì trình duyệt
có thể chặn việc nạp JSON cục bộ. Website có form điểm môn, tổ hợp dự kiến, sở thích,
năng lực, kết quả tư vấn, giải thích chuỗi suy diễn và nhật ký xử lý xung đột. Xem thêm
`website/README.md` để biết giới hạn của khuyến nghị.
