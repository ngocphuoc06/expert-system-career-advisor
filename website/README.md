# La Bàn Ngành Nghề

Website **Hệ chuyên gia tư vấn chọn ngành/nghề cho học sinh THPT**, dựng trên
template HTML5 UP Highlights. Phần giao diện được đặt trong `index.html`;
suy diễn tiến, xử lý xung đột, CF và giải thích nằm trong `assets/js/advisor.js`.

## Chạy tại máy

Website đọc trực tiếp cơ sở tri thức đầy đủ tại `kb/rules_kb.json`, nên cần
chạy máy chủ tĩnh từ thư mục gốc của dự án:

```powershell
python -m http.server 8000
```

Sau đó mở `http://localhost:8000/website/`.

## Phạm vi tư vấn

Website nạp bộ luật từ `kb/rules_kb.json`: 46 luật, 10 nhóm ngành và 43 ngành
trong danh mục. Hồ sơ gồm điểm 10 môn, tổ hợp xét điểm, sở thích và năng lực nổi
trội. Hệ thống suy luận theo thứ tự Priority → Specificity → Recency → mã luật;
tính CF, trình bày khối thế mạnh, mã Holland, phân khúc điểm, nhóm ngành, ngành
gợi ý, cây giải thích và nhật ký từng bước.

Điểm số và các ngưỡng phân khúc là quy ước mô phỏng của đồ án, không phải điểm
chuẩn tuyển sinh. Danh mục trường/điểm chuẩn không được dùng để bảo đảm khả năng
trúng tuyển; học sinh cần xác minh mã ngành, tổ hợp và đề án hiện hành của trường.
Hồ sơ chỉ được xử lý trong trình duyệt, không gửi đi hoặc lưu trữ.

Lưu ý: `knowledge_base.csv` ở thư mục gốc hiện chỉ chứa 8 luật minh hoạ cho một
bài toán hẹp về nghề AI; nó không đại diện cho đề tài hướng nghiệp THPT tổng quát.
Website vì vậy dùng bộ tri thức nhiều tầng trong `kb/rules_kb.json`, được sinh từ
`kb/rules_data.py`, thay vì đưa ra gợi ý ngành rộng dựa trên CSV hẹp.

Template, ảnh và tài nguyên gốc được giữ kèm thông tin cấp phép trong
`LICENSE.txt` và `README.txt`. Thiết kế website và logic tư vấn là phần tuỳ biến
của đồ án.
