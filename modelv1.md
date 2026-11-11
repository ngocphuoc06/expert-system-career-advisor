# Conflict Resolver Specification Plan (Version 1.0)

> **Document Metadata**
> - **Module Name:** `conflict_resolver.py` (`ConflictResolver`)
> - **Created Date:** 11/11/2026
> - **Role Responsibility:** Thành viên 3 (TV3) – Nhóm Lập trình Lõi AI (Inference Engine)
> - **Domain:** Hệ Chuyên Gia Tư Vấn Chọn Ngành Học Sinh THPT (Rule-Based Expert System)
> - **Framework Standard:** Spec-Driven Engineering (Flow: 1. Purpose ⟶ 2. Input/Output ⟶ 3. Success Criteria ⟶ 4. How to do)

---

## 1. Purpose (Mục đích)

Mục đích chính của module `conflict_resolver` là xây dựng bộ phân xử xung đột luật (**Conflict Resolver**) độc lập, chuẩn mực và đa chiến lược trong Động cơ Suy diễn tiến (Forward Chaining Engine).

### Lý do & Vai trò kỹ thuật:
1. **Giải quyết tình trạng bùng nổ xung đột (Rule Conflict Mitigation):** Trong quá trình suy diễn tiến, tại một chu kỳ thường có nhiều luật cùng thỏa mãn toàn bộ tiền đề vế `IF`. Module đóng vai trò là "trọng tài" quyết định duy nhất 1 luật tối ưu nhất được kích hoạt (fire) tại mỗi bước.
2. **Tuân thủ quy chuẩn kỹ nghệ tri thức (Knowledge Engineering Standard):** Hiện thực hóa chuẩn xác 4 bước xử lý xung đột kinh điển (Mục 2.4.1 Báo cáo thiết kế cơ sở tri thức):
   - **Refraction (Khúc xạ / Chống lặp):** Ngăn ngừa kích hoạt lại luật trên cùng một tập sự kiện.
   - **Specificity (Độ đặc thù):** Ưu tiên luật có vế `IF` nhiều điều kiện ràng buộc hơn (ngữ cảnh cụ thể hơn).
   - **Priority / Salience (Độ ưu tiên thiết kế):** Ưu tiên luật thuộc tầng tri thức cao hơn hoặc có trọng số chuyên gia lớn hơn.
   - **Recency (Độ mới của sự kiện):** Ưu tiên luật so khớp với sự kiện mới được nạp vào Working Memory gần nhất để giữ mạch suy luận liên tục.
   - **Deterministic Tie-breaking:** Đảm bảo thứ tự luật ổn định, không ngẫu nhiên khi các chỉ số bằng nhau.
3. **Phân định ranh giới trách nhiệm (Separation of Concerns - SOLID):**
   - **Đồng đội (TV4):** Phụ trách vòng lặp suy diễn chính, quản lý Working Memory, lọc luật khả dụng (Pha MATCH) và cập nhật sự kiện mới (Pha ACT).
   - **TV3 (Bạn):** Phụ trách độc lập class `ConflictResolver` (Pha RESOLVE) nhận `conflict_set` và trả về đúng 1 luật tốt nhất kèm chuỗi lý do giải trình.
4. **Hỗ trợ đa chiến lược (Strategy Pattern):** Tương tự như Factory Pattern hỗ trợ đa kiến trúc trong Deep Learning, `ConflictResolver` cung cấp interface thống nhất hỗ trợ linh hoạt 5 chiến lược phân xử: `combined`, `specificity`, `priority`, `recency`, và `first_match`.

---

## 2. Model Architecture & Input/Output Design (Kiến trúc mô hình & Thiết kế I/O)

Mục này mô tả chi tiết kiến trúc hướng đối tượng, bảng đặc tả 5 chiến lược phân xử và hợp đồng dữ liệu vào/ra (I/O Contract) chặt chẽ của module.

---

### 2.1 Bảng đặc tả 5 chiến lược xử lý xung đột (Strategy Comparison Spec)

| Chiến lược (`strategy`) | Nguyên lý cốt lõi | Vector tiêu chí ưu tiên | Ngữ cảnh ứng dụng |
| :--- | :--- | :--- | :--- |
| **`combined` (Mặc định)** | **Đa tiêu chí chuẩn Hệ chuyên gia:** Kết hợp Specificity $\rightarrow$ Priority $\rightarrow$ Recency $\rightarrow$ Tie-break. | `(r.specificity, r.priority, recency)` (Giảm dần) | Tư vấn chọn ngành toàn diện, yêu cầu suy diễn sâu và chính xác nhất. |
| **`specificity`** | **Ưu tiên độ đặc thù cao nhất:** Luật càng nhiều điều kiện `IF` càng được ưu tiên trước. | `(r.specificity, r.priority, recency)` | Ưu tiên các quy tắc cá biệt hóa cao cho học sinh có nhiều năng khiếu cụ thể. |
| **`priority`** | **Ưu tiên độ quan trọng chuyên gia:** Luật có điểm `priority` (Salience) cao hơn sẽ thắng. | `(r.priority, r.specificity, recency)` | Ưu tiên các luật then chốt (luật điều kiện bắt buộc, luật loại trừ). |
| **`recency`** | **Ưu tiên dòng sự kiện mới:** Luật dùng Fact vừa suy ra ở bước gần nhất sẽ thắng. | `(recency, r.specificity, r.priority)` | Bám sát mạch suy luận liên tục theo chiều sâu (Depth-first reasoning). |
| **`first_match`** | **Thứ tự xuất hiện đầu tiên (FIFO):** Chọn luật đầu tiên khớp theo danh mục. | Thứ tự index trong danh sách (FIFO) | Kiểm thử tốc độ hoặc mô phỏng hệ luật đơn giản không gán trọng số. |

---

### 2.2 Cấu trúc Code và Vị trí lưu trữ (What & Where)

* **Vị trí file mã nguồn:** [conflict_resolver.py](file:///d:/TRÍ%20TUỆ%20NHÂN%20TẠO/conflict_resolver.py)
* **Kiến trúc Class hướng đối tượng (OOP Architecture):**
  ```text
  conflict_resolver.py
  └── class ConflictResolver
        ├── SUPPORTED_STRATEGIES = ["combined", "specificity", "priority", "recency", "first_match"]
        ├── __init__(strategy: str = "combined")
        │     └── Bẫy lỗi strategy không hợp lệ (ValueError)
        │
        ├── get_rule_recency(rule: Rule, working_memory: Dict[str, Fact]) -> int
        │     └── Tính max(timestamp_step) của các tiền đề vế IF
        │
        └── resolve(conflict_set: List[Rule], working_memory: Dict[str, Fact]) -> Tuple[Rule, str]
              ├── Bẫy lỗi conflict_set rỗng (ValueError)
              ├── Fast-path: len == 1 trả về ngay (Không có xung đột)
              ├── Sắp xếp Timsort ổn định theo chiến lược tương ứng
              └── Trả về tuple: (chosen_rule: Rule, resolution_reason: str)
  ```

---

### 2.3 Chi tiết Hợp đồng Input / Output (I/O Contract)

| Thuộc tính | Đầu vào 1: `conflict_set` | Đầu vào 2: `working_memory` | Đầu ra (Return Tuple) |
| :--- | :--- | :--- | :--- |
| **Data Type** | `List[Rule]` | `Dict[str, Fact]` | `Tuple[Rule, str]` |
| **Cấu trúc dữ liệu** | Mảng đối tượng `Rule`: `r.id`, `r.premises`, `r.conclusion`, `r.priority`, `r.specificity`. | Dict `{fact_id: Fact}` (mỗi Fact có thuộc tính `timestamp_step: int`). | `(selected_rule, resolution_reason)` |
| **Ràng buộc (Constraints)** | • Độ dài $\ge 1$<br>• Mỗi phần tử là một instance của `Rule`. | • Chứa các Fact thuộc `rule.premises`.<br>• `timestamp_step >= 0`. | • `selected_rule` là 1 phần tử trong `conflict_set`.<br>• `resolution_reason` là chuỗi mô tả rõ lý do chọn luật. |
| **Bảo toàn dữ liệu** | Không sửa đổi (mutate) mảng ban đầu. | Read-only, không thêm/sửa/xóa Fact. | Phục vụ trực tiếp cho Pha ACT và Module Giải trình "Vì sao?". |

---

## 3. Success Criteria (Tiêu chí thành công & Nghiệm thu định lượng)

Một module `ConflictResolver` chỉ được nghiệm thu đạt chuẩn (**PASS**) khi thỏa mãn toàn bộ 9 tiêu chí định lượng sau:

| STT | Tiêu chí (Criteria) | Điều kiện chấp thuận (Acceptance Condition) | Cách kiểm tra |
| :---: | :--- | :--- | :--- |
| **1** | **Bẫy lỗi tập rỗng** | `conflict_set = []` ném ra `ValueError` có thông báo rõ ràng. | Test với `pytest.raises(ValueError)`. |
| **2** | **Bẫy lỗi chiến lược** | Khởi tạo với chiến lược không hợp lệ phải ném `ValueError` kèm danh sách gợi ý. | Khởi tạo `ConflictResolver("unknown")` $\rightarrow$ `ValueError`. |
| **3** | **Tối ưu đơn luật (Fast-path)** | Khi `len(conflict_set) == 1`, trả về ngay chính luật đó mà không cần tốn chi phí sắp xếp. | Trả về `(conflict_set[0], reason)`. |
| **4** | **Độ đặc thù (Specificity)** | Trong chiến lược `specificity`, luật có vế `IF` 3 điều kiện phải thắng luật 2 điều kiện bất kể priority. | Assert: `chosen.specificity == max(r.specificity)`. |
| **5** | **Độ ưu tiên (Priority)** | Trong chiến lược `priority`, luật có `priority` cao hơn phải thắng khi số tiền đề bằng nhau. | Assert: `chosen.priority == max(r.priority)`. |
| **6** | **Độ mới sự kiện (Recency)** | Trong chiến lược `recency`, luật chứa Fact có `timestamp_step` cao nhất phải thắng. | Assert: `recency == max(get_rule_recency)`. |
| **7** | **Phá hòa ổn định (Tie-break)**| Khi các chỉ số bằng nhau, thứ tự định nghĩa luật ban đầu được bảo toàn (Timsort Stable). | So sánh thứ tự luật đầu vào. |
| **8** | **Bảo toàn bộ nhớ (Immutability)** | `working_memory` không bị thay đổi bất kỳ phần tử nào sau khi hàm `resolve` chạy xong. | Kiểm tra `len(wm)` trước và sau khi gọi hàm. |
| **9** | **Tích hợp hồi quy hệ thống** | Tương thích 100% với `ForwardChainingEngine`, chạy `test_suite.py` đạt **10/10 PASS**. | Chạy `python -X utf8 test_suite.py` exit code 0. |

---

## 4. How to do (Cách thực hiện & Hướng dẫn triển khai)

### 4.1 Quy trình kỹ thuật từng bước (Step-by-step Implementation)

1. **Bước 1: Khởi tạo lớp & Danh mục chiến lược hợp lệ:**
   - Định nghĩa hằng số `SUPPORTED_STRATEGIES = ["combined", "specificity", "priority", "recency", "first_match"]`.
   - Kiểm tra `strategy in SUPPORTED_STRATEGIES`, nếu không hợp lệ raise `ValueError`.
2. **Bước 2: Lập trình hàm tính Recency:**
   - Lấy giá trị `timestamp_step` lớn nhất trong số các Fact thuộc `rule.premises` đang có mặt trong `working_memory`.
3. **Bước 3: Lập trình hàm phân xử `resolve()`:**
   - Kiểm tra tập rỗng $\rightarrow$ Raise `ValueError`.
   - Kiểm tra độ dài $= 1 \rightarrow$ Trả về ngay kèm chuỗi lý do không có xung đột.
   - Sắp xếp giảm dần (`reverse=True`) bằng hàm `sorted()` của Python dựa trên Tuple tiêu chí tương ứng với `self.strategy`.
4. **Bước 4: Sinh chuỗi giải trình ngữ nghĩa (`resolution_reason`):**
   - Format chuỗi giải thích chi tiết vì sao luật được chọn (nêu rõ số điều kiện IF, priority, và bước recency) để bàn giao cho TV5 hiển thị lên UI.

---

### 4.2 Build Prompt cho AI (Independent Prompt)

Dán đoạn prompt độc lập dưới đây vào bất kỳ công cụ AI nào khi cần tạo mới, tái cấu trúc hoặc bảo trì module của TV3:

```text
Repository root:
d:\TRÍ TUỆ NHÂN TẠO

Implement exactly one task: Hoàn thiện module xử lý xung đột luật (Conflict Resolver) cho Thành viên 3 (TV3) trong file conflict_resolver.py.

Chỉ được tạo / sửa:
- conflict_resolver.py

Yêu cầu kỹ thuật bắt buộc:
1. Tạo class ConflictResolver độc lập theo đúng mẫu thiết kế Pluggable Strategy Pattern.
2. Hỗ trợ đầy đủ 5 chiến lược phân xử: 'combined', 'specificity', 'priority', 'recency', 'first_match'. Giá trị mặc định là 'combined'.
3. Khởi tạo với chiến lược không hợp lệ phải ném ValueError kèm danh sách các lựa chọn được hỗ trợ.
4. Hàm get_rule_recency(rule: Rule, working_memory: Dict[str, Fact]) -> int:
   - Tính bước thời gian lớn nhất (timestamp_step) trong số các sự kiện tiền đề vế IF của luật đang có trong Working Memory. Nếu rule không có tiền đề, trả về 0.
5. Hàm resolve(conflict_set: List[Rule], working_memory: Dict[str, Fact]) -> Tuple[Rule, str]:
   - Nếu conflict_set rỗng: ném ValueError("Conflict set rỗng, không có luật nào để xử lý xung đột!").
   - Nếu len(conflict_set) == 1: trả về ngay luật đó kèm lý do không có xung đột.
   - Nếu chiến lược 'combined': sắp xếp giảm dần theo vector (r.specificity, r.priority, get_rule_recency).
   - Nếu chiến lược 'specificity': sắp xếp theo (r.specificity, r.priority, recency).
   - Nếu chiến lược 'priority': sắp xếp theo (r.priority, r.specificity, recency).
   - Nếu chiến lược 'recency': sắp xếp theo (recency, r.specificity, r.priority).
   - Nếu chiến lược 'first_match': trả về phần tử đầu tiên (conflict_set[0]).
   - Đảm bảo tính ổn định (Tie-breaking) giữ nguyên thứ tự xuất hiện ban đầu khi các chỉ số bằng nhau (dùng Timsort chuẩn của Python).
   - Trả về đúng tuple (selected_rule, resolution_reason) với chuỗi giải thích ngữ nghĩa rõ ràng.
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

### 4.3 Lệnh kiểm tra và xác minh (Verification Commands & Smoke Tests)

#### Lệnh 1: Import Smoke Test (Kiểm tra cú pháp & tính sẵn sàng của module)
```powershell
python -X utf8 -c "from conflict_resolver import ConflictResolver; print('Import ConflictResolver PASS')"
```
*(Kết quả mong đợi: `Import ConflictResolver PASS`)*

#### Lệnh 2: Logic Smoke Test (Kiểm tra thuật toán phân xử và tính recency)
```powershell
python -X utf8 -c "from structs import Rule, Fact; from conflict_resolver import ConflictResolver; r1=Rule('R01', ['F01'], 'F02', 1); r2=Rule('R02', ['F01', 'F03'], 'F04', 2); wm={'F01': Fact('F01', timestamp_step=0), 'F03': Fact('F03', timestamp_step=1)}; res=ConflictResolver('combined'); chosen, reason = res.resolve([r1, r2], wm); assert chosen.id == 'R02'; print('ConflictResolver Smoke Test PASS')"
```
*(Kết quả mong đợi: `ConflictResolver Smoke Test PASS`)*

#### Lệnh 3: System Regression Test (Kiểm tra tích hợp toàn hệ thống 10 kịch bản)
```powershell
python -X utf8 test_suite.py
```
*(Kết quả mong đợi: `TỔNG KẾT KIỂM THỬ: 10/10 TEST CASES ĐẠT CHUẨN (100% PASS)`)*
