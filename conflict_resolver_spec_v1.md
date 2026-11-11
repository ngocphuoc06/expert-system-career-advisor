# Conflict Resolver Specification & Prompting Plan (Version 1.0)

> **Document Metadata**
> - **Module Name:** `conflict_resolver.py` (`ConflictResolver`)
> - **Role Responsibility:** Thành viên 3 (TV3) - Nhóm Lập trình Lõi AI (Inference Engine)
> - **Domain:** Hệ Chuyên Gia Tư Vấn Chọn Ngành Học Sinh THPT (Rule-Based Expert System)
> - **Framework Standard:** Spec-Driven Engineering (Purpose ⟶ Input/Output ⟶ Success Criteria ⟶ How to do)

---

## 1. Purpose (Mục đích)

Mục đích chính của module `conflict_resolver.py` là xây dựng bộ phân xử xung đột luật (**Conflict Resolver**) độc lập, chuẩn mực và đa chiến lược trong Động cơ Suy diễn tiến (Forward Chaining Engine).

### Lý do & Vai trò kỹ thuật trong Hệ Chuyên Gia:
1. **Giải quyết tình trạng bùng nổ xung đột (Rule Conflict Mitigation):** Trong quá trình suy diễn tiến, tại một chu kỳ có thể có nhiều luật cùng thỏa mãn toàn bộ điều kiện vế `IF`. Bộ xử lý xung đột đóng vai trò là "trọng tài" quyết định duy nhất 1 luật tối ưu nhất được kích hoạt (fire) tại mỗi bước.
2. **Tuân thủ quy chuẩn kỹ nghệ tri thức (Knowledge Engineering Standard):** Hiện thực hóa chuẩn xác 4 bước xử lý xung đột kinh điển (Mục 2.4.1 Báo cáo thiết kế cơ sở tri thức):
   - **Refraction (Khúc xạ / Chống lặp):** Ngăn ngừa kích hoạt luật lặp lại vô hạn trên cùng tập sự kiện.
   - **Specificity (Độ đặc thù):** Ưu tiên luật có vế `IF` nhiều điều kiện ràng buộc hơn (ngữ cảnh cụ thể hơn).
   - **Priority / Salience (Độ ưu tiên thiết kế):** Ưu tiên luật thuộc tầng tri thức cao hơn hoặc có trọng số chuyên gia lớn hơn.
   - **Recency (Độ mới của sự kiện):** Ưu tiên luật so khớp với sự kiện mới được nạp vào Working Memory gần nhất để giữ mạch suy luận liên tục.
   - **Deterministic Tie-breaking:** Đảm bảo thứ tự luật ổn định, không ngẫu nhiên khi các chỉ số bằng nhau.
3. **Phân định ranh giới trách nhiệm (Separation of Concerns - SOLID):**
   - TV4 phụ trách: Vòng lặp suy diễn chính, quản lý Working Memory, đối sánh luật (Pha MATCH) và cập nhật sự kiện mới (Pha ACT).
   - TV3 phụ trách: Lập trình độc lập `class ConflictResolver` (Pha RESOLVE) nhận `conflict_set` và trả về đúng 1 luật tốt nhất kèm chuỗi lý do giải trình.
4. **Hỗ trợ đa chiến lược (Strategy Pattern):** Tương tự như Factory Pattern hỗ trợ nhiều kiến trúc trong Deep Learning, `ConflictResolver` hỗ trợ linh hoạt 5 chiến lược phân xử: `combined`, `specificity`, `priority`, `recency`, và `first_match`.

---

## 2. Architecture & Input/Output Design (Kiến trúc & Thiết kế I/O)

### 2.1 Bảng đặc tả 5 chiến lược xử lý xung đột (Strategy Comparison Spec)

| Chiến lược (`strategy`) | Nguyên lý sắp xếp cốt lõi | Vector tiêu chí ưu tiên | Trường hợp ứng dụng |
| :--- | :--- | :--- | :--- |
| **`combined` (Mặc định)** | **Đa tiêu chí chuẩn Hệ chuyên gia:** Kết hợp tuần tự Specificity $\rightarrow$ Priority $\rightarrow$ Recency $\rightarrow$ Tie-break. | `(r.specificity, r.priority, recency)` (Giảm dần) | Tư vấn chọn ngành toàn diện, yêu cầu suy diễn sâu và chính xác nhất. |
| **`specificity`** | **Ưu tiên độ đặc thù cao nhất:** Luật càng nhiều điều kiện `IF` càng được ưu tiên trước. | `(r.specificity, r.priority, recency)` | Khi muốn ưu tiên các quy tắc cá biệt hóa cao cho học sinh có nhiều năng khiếu. |
| **`priority`** | **Ưu tiên độ quan trọng chuyên gia:** Luật có điểm `priority` (Salience) cao hơn sẽ thắng. | `(r.priority, r.specificity, recency)` | Khi cần ưu tiên các luật then chốt (luật loại trừ, luật điều kiện tài chính bắt buộc). |
| **`recency`** | **Ưu tiên dòng sự kiện thời gian thực:** Luật dùng Fact vừa mới suy ra ở bước liền trước sẽ thắng. | `(recency, r.specificity, r.priority)` | Bám sát mạch suy luận liên tục theo chiều sâu (Depth-first reasoning). |
| **`first_match`** | **Thứ tự xuất hiện đầu tiên (FIFO):** Chọn ngay luật đầu tiên khớp theo thứ tự danh mục. | Thứ tự index trong danh sách (FIFO) | Kiểm thử hiệu năng hoặc mô phỏng hệ luật đơn giản không xét trọng số. |

---

### 2.2 Cấu trúc Code và Vị trí lưu trữ (What & Where)

* **Vị trí file mã nguồn:** [`conflict_resolver.py`](file:///d:/TRÍ%20TUỆ%20NHÂN%20TẠO/conflict_resolver.py)
* **Kiến trúc Class hướng đối tượng (OOP Architecture):**
  ```text
  conflict_resolver.py
  └── class ConflictResolver
        ├── SUPPORTED_STRATEGIES = ["combined", "specificity", "priority", "recency", "first_match"]
        ├── __init__(strategy: str = "combined")
        │     └── Kiểm tra bẫy lỗi strategy không hợp lệ (ValueError)
        │
        ├── get_rule_recency(rule: Rule, working_memory: Dict[str, Fact]) -> int
        │     └── Tính max(timestamp_step) của các tiền đề vế IF
        │
        └── resolve(conflict_set: List[Rule], working_memory: Dict[str, Fact]) -> Tuple[Rule, str]
              ├── Bẫy lỗi conflict_set rỗng (ValueError)
              ├── Xử lý nhanh trường hợp len == 1 (Không xung đột)
              ├── Thực hiện sắp xếp Timsort theo chiến lược cấu hình
              └── Trả về (chosen_rule: Rule, resolution_reason: str)
  ```

---

### 2.3 Chi tiết Hợp đồng Input / Output (I/O Contract)

| Thuộc tính | Đầu vào 1: `conflict_set` | Đầu vào 2: `working_memory` | Đầu ra (Return Tuple) |
| :--- | :--- | :--- | :--- |
| **Data Type** | `List[Rule]` | `Dict[str, Fact]` | `Tuple[Rule, str]` |
| **Cấu trúc bên trong** | Danh sách các đối tượng `Rule`: `r.id`, `r.premises`, `r.conclusion`, `r.priority`, `r.specificity`. | Từ điển ánh xạ `fact_id` $\rightarrow$ đối tượng `Fact` (có `timestamp_step: int`). | `(selected_rule, resolution_reason)` |
| **Ràng buộc (Constraints)** | • Độ dài $\ge 1$<br>• Mỗi phần tử là một instance của `Rule`. | • Chứa toàn bộ các fact có trong `rule.premises`.<br>• `timestamp_step >= 0`. | • `selected_rule` thuộc `conflict_set`.<br>• `resolution_reason` là chuỗi mô tả rõ lý do vì sao chọn luật. |
| **Bảo toàn dữ liệu** | Không sửa đổi (mutate) mảng gốc. | Chỉ đọc (`read-only`), không thêm/sửa/xóa Fact. | Phục vụ trực tiếp cho Pha ACT và Module Giải trình "Vì sao?". |

---

## 3. Success Criteria (Tiêu chí thành công & Nghiệm thu định lượng)

Một phiên bản `ConflictResolver` do AI hoặc TV3 viết chỉ được nghiệm thu đạt chuẩn (**PASS**) khi thỏa mãn toàn bộ 8 tiêu chí định lượng sau:

| STT | Tiêu chí (Criteria) | Điều kiện chấp thuận (Acceptance Condition) | Cách kiểm tra |
| :---: | :--- | :--- | :--- |
| **1** | **Bẫy lỗi tập rỗng** | `conflict_set = []` ném ra `ValueError` với thông báo rõ ràng. | `pytest.raises(ValueError)` |
| **2** | **Bẫy lỗi chiến lược** | Khởi tạo với `strategy="unknown"` ném ra `ValueError` kèm danh sách hợp lệ. | `ConflictResolver("invalid")` $\rightarrow$ `ValueError` |
| **3** | **Đơn luật (Single Rule)** | Khi `len(conflict_set) == 1`, trả về ngay chính luật đó mà không cần sắp xếp tốn tài nguyên. | Trả về `(conflict_set[0], reason)` |
| **4** | **Độ đặc thù (Specificity)** | Trong chiến lược `specificity`, luật có vế `IF` 3 điều kiện phải thắng luật 2 điều kiện bất kể priority. | Assert: `chosen.specificity == max(r.specificity)` |
| **5** | **Độ ưu tiên (Priority)** | Trong chiến lược `priority`, luật có `priority` cao hơn phải thắng khi số tiền đề bằng nhau. | Assert: `chosen.priority == max(r.priority)` |
| **6** | **Độ mới (Recency)** | Trong chiến lược `recency`, luật chứa Fact có `timestamp_step` cao nhất phải thắng. | Assert: `recency == max(get_rule_recency)` |
| **7** | **Ổn định (Tie-breaking)** | Khi 2 luật hòa ở cả 3 tiêu chí, thứ tự xuất hiện ban đầu được bảo toàn 100% (Timsort Stable). | Kiểm tra thứ tự luật đầu vào |
| **8** | **Không biến đổi bộ nhớ** | `working_memory` không bị thay đổi bất kỳ phần tử nào sau khi hàm `resolve` chạy xong. | So sánh `hash` hoặc `len(wm)` trước/sau |
| **9** | **Tích hợp hệ thống** | Chạy `python -X utf8 test_suite.py` đạt chuẩn **10/10 PASS**. | Kết quả `test_suite.py` exit code 0 |

---

## 4. How to do (Cách thực hiện & Hướng dẫn triển khai)

### 4.1 Quy trình kỹ thuật từng bước (Step-by-step Implementation)

1. **Bước 1: Khởi tạo lớp & Danh mục chiến lược hợp lệ:**
   - Định nghĩa `SUPPORTED_STRATEGIES = ["combined", "specificity", "priority", "recency", "first_match"]`.
   - Kiểm tra `strategy in SUPPORTED_STRATEGIES`, nếu sai raise `ValueError`.
2. **Bước 2: Lập trình hàm tính Recency:**
   - Lấy giá trị `timestamp_step` cực đại trong số các Fact thuộc `rule.premises` đang có mặt trong `working_memory`.
3. **Bước 3: Lập trình hàm phân xử `resolve()`:**
   - Kiểm tra tập rỗng $\rightarrow$ Raise `ValueError`.
   - Kiểm tra độ dài $= 1 \rightarrow$ Trả về ngay kèm lý do không có xung đột.
   - Sắp xếp giảm dần (`reverse=True`) bằng hàm `sorted()` của Python dựa trên Tuple tiêu chí tương ứng với `self.strategy`.
4. **Bước 4: Sinh chuỗi giải trình ngữ nghĩa (`resolution_reason`):**
   - Format chuỗi giải thích chi tiết vì sao luật được chọn (nêu rõ số điều kiện IF, priority, và bước recency) để bàn giao cho TV5 hiển thị lên UI.

---

### 4.2 Build Prompt cho AI (Independent Prompt)

Dán đoạn prompt độc lập dưới đây vào bất kỳ công cụ AI lập trình nào khi cần tái tạo hoặc nâng cấp module của TV3:

```text
Repository root:
d:\TRÍ TUỆ NHÂN TẠO

Implement exactly one task: Hoàn thiện module xử lý xung đột luật (Conflict Resolver) cho Thành viên 3 (TV3) trong file conflict_resolver.py.

Chỉ được tạo / sửa:
- conflict_resolver.py

Yêu cầu kỹ thuật bắt buộc:
1. Tạo class ConflictResolver theo đúng mẫu thiết kế Strategy/Pluggable.
2. Hỗ trợ đầy đủ 5 chiến lược phân xử: 'combined', 'specificity', 'priority', 'recency', 'first_match'. Mặc định là 'combined'.
3. Khởi tạo với chiến lược không hợp lệ phải ném ValueError kèm danh sách các lựa chọn được hỗ trợ.
4. Hàm get_rule_recency(rule: Rule, working_memory: Dict[str, Fact]) -> int:
   - Tính bước thời gian lớn nhất (timestamp_step) trong số các sự kiện tiền đề vế IF của luật.
5. Hàm resolve(conflict_set: List[Rule], working_memory: Dict[str, Fact]) -> Tuple[Rule, str]:
   - Nếu conflict_set rỗng: ném ValueError("Conflict set rỗng!").
   - Nếu len(conflict_set) == 1: trả về ngay luật đó kèm lý do không có xung đột.
   - Nếu chiến lược 'combined': sắp xếp giảm dần theo vector (r.specificity, r.priority, get_rule_recency).
   - Nếu chiến lược 'specificity': sắp xếp theo (r.specificity, r.priority, recency).
   - Nếu chiến lược 'priority': sắp xếp theo (r.priority, r.specificity, recency).
   - Nếu chiến lược 'recency': sắp xếp theo (recency, r.specificity, r.priority).
   - Nếu chiến lược 'first_match': trả về phần tử đầu tiên (conflict_set[0]).
   - Đảm bảo tính ổn định (Tie-breaking) giữ nguyên thứ tự xuất hiện ban đầu khi các chỉ số bằng nhau.
   - Trả về đúng tuple (selected_rule, resolution_reason) với chuỗi giải thích rõ ràng.
6. Tuân thủ 100% chuẩn Type Hinting (typing.Dict, List, Tuple) và Docstring chuẩn PEP 257 ở đầu class và tất cả methods.
7. Không làm thay đổi (mutate) mảng conflict_set và từ điển working_memory truyền vào.

Sau khi sửa / tạo xong:
1. Chạy Import Test:
   python -X utf8 -c "from conflict_resolver import ConflictResolver; print('Import ConflictResolver PASS')"
2. Chạy Smoke Test logic phân xử:
   python -X utf8 -c "from structs import Rule, Fact; from conflict_resolver import ConflictResolver; r1=Rule('R01', ['F01'], 'F02', 1); r2=Rule('R02', ['F01', 'F03'], 'F04', 2); wm={'F01': Fact('F01', timestamp_step=0), 'F03': Fact('F03', timestamp_step=1)}; res=ConflictResolver('combined'); chosen, reason = res.resolve([r1, r2], wm); assert chosen.id == 'R02'; print('ConflictResolver Smoke Test PASS')"
3. Chạy toàn bộ bộ kiểm thử tích hợp:
   python -X utf8 test_suite.py
4. Báo kết quả 10/10 Test Cases PASS và không sửa bất kỳ file nào ngoài conflict_resolver.py.
```

---

### 4.3 Lệnh kiểm tra và xác minh (Verification & Smoke Tests)

#### Lệnh 1: Import Smoke Test (Kiểm tra cú pháp & module)
```powershell
python -X utf8 -c "from conflict_resolver import ConflictResolver; print('Import ConflictResolver PASS')"
```

#### Lệnh 2: Logic Smoke Test (Kiểm tra tính đúng đắn của thuật toán chọn luật)
```powershell
python -X utf8 -c "from structs import Rule, Fact; from conflict_resolver import ConflictResolver; r1=Rule('R01', ['F01'], 'F02', 1); r2=Rule('R02', ['F01', 'F03'], 'F04', 2); wm={'F01': Fact('F01', timestamp_step=0), 'F03': Fact('F03', timestamp_step=1)}; res=ConflictResolver('combined'); chosen, reason = res.resolve([r1, r2], wm); assert chosen.id == 'R02'; print('ConflictResolver Smoke Test PASS')"
```

#### Lệnh 3: System Regression Test (Kiểm tra toàn bộ 10 kịch bản của hệ thống)
```powershell
python -X utf8 test_suite.py
```
*(Kết quả mong đợi: `10/10 TEST CASES ĐẠT CHUẨN (100% PASS)`).*
