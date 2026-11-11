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

