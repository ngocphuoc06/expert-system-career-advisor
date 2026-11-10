# ĐẶC TẢ KIẾN TRÚC & LUỒNG HOẠT ĐỘNG MODULE XỬ LÝ XUNG ĐỘT (`ConflictResolver`)


## 1. ĐỊNH VỊ VAI TRÒ & PHÂN CÔNG NHIỆM VỤ CỦA THÀNH VIÊN 3 (TV3)

Theo biên bản phân công công việc nội bộ của nhóm qua tin nhắn trao đổi:
* **Đồng đội phụ trách:** Động cơ suy diễn tiến tổng thể (Phần `ForwardChainingEngine` - Pha MATCH đối sánh tập sự kiện và Pha ACT kích hoạt luật).
* **Thành viên 3 (Tôi) phụ trách:** Lập trình độc lập `class ConflictResolver` (Pha RESOLVE - Xử lý xung đột luật):
  > *"Phần code ông viết code class ConflictResolver xử lý xung đột nha, tui làm phần suy diễn. Ông viết hàm nhận vào cái danh sách conflict_set của tui, xong ông lập trình thuật toán sắp xếp để chọn ra 1 luật tốt nhất."*

```
┌───────────────────────────────────────┐         ┌─────────────────────────────────────────┐
│     ĐỒNG ĐỘI (INFERENCE ENGINE)       │         │        THÀNH VIÊN 3 (CONFLICT RESOLVER) │
│                                       │         │                                         │
│  1. Quản lý Working Memory & History  │         │  1. Nhận danh sách `conflict_set`       │
│  2. Pha MATCH: Tìm luật thỏa mãn      │ ──────> │  2. Thuật toán sắp xếp đa tiêu chí      │
│  3. Pha ACT: Cập nhật sự kiện mới     │ <────── │  3. Chọn đúng 1 luật tối ưu nhất        │
│  4. Quản lý vòng lặp suy diễn chính   │         │  4. Trả về: (selected_rule, reason)     │
└───────────────────────────────────────┘         └─────────────────────────────────────────┘
```

Mục tiêu duy nhất của TV3 là: **Tập trung làm xuất sắc 100% nhiệm vụ xử lý xung đột, tuân thủ nguyên lý Đơn trách nhiệm (Single Responsibility Principle - SOLID), không làm lấn sân sang các phần việc khác của nhóm.**

---

## 2. TẠI SAO KHÔNG ỨNG DỤNG MACHINE LEARNING / PYTORCH VÀO SOURCE CODE CỦA TV3?

Sau khi nghiên cứu cuốn sách *Hands-On Machine Learning with Scikit-Learn and PyTorch* (Aurélien Géron):

| Tiêu chí | Hệ Chuyên Gia Luật (Symbolic AI - Đồ án hiện tại) | Học Máy / Học Sâu (Statistical ML & PyTorch) |
| :--- | :--- | :--- |
| **Bản chất tri thức** | Tường minh, biểu diễn bằng luật `IF <tiền đề> THEN <kết luận>`. | Ẩn trong ma trận trọng số hàng triệu tham số số thực (Continuous weights). |
| **Tính giải trình (XAI)** | **Glass-box (Hộp kính):** Giải thích chính xác 100% nguyên nhân "Vì sao?" qua cây vết suy diễn. | **Black-box (Hộp đen):** Khó giải thích chuỗi lập luận logic hình thức. |
| **Yêu cầu dữ liệu** | Không cần dữ liệu lớn, chỉ cần tri thức chuyên gia chuẩn hóa. | Cần hàng chục nghìn đến hàng triệu dòng dữ liệu huấn luyện có nhãn. |
| **Nhiệm vụ TV3** | Sắp xếp tập luật hữu hạn (`conflict_set`) theo tiêu chí logic. | Tối ưu hóa hàm mất mát (Loss function) qua Gradient Descent. |

### 📌 Kết luận chuyên môn của TV3:
1. **Tuyệt đối KHÔNG đưa Scikit-Learn / PyTorch vào module `ConflictResolver`**: Vì thuật toán giải quyết xung đột trong Hệ chuyên gia là bài toán xếp hạng logic tất định (Deterministic Ranking). Việc nhồi nhét mạng nơ-ron hay mô hình ML vào đây sẽ biến hệ thống thành hộp đen, phá vỡ khả năng giải trình "Vì sao?" (yêu cầu bắt buộc của môn học), và làm chệch hoàn toàn phân công nhiệm vụ của nhóm.
2. **Điểm duy nhất có giá trị tham khảo học thuật (dùng để trả lời khi bảo vệ):** 
   - *Thuật toán Cây quyết định (Decision Tree - ID3/CART ở Chương 6):* Có thể dùng ở giai đoạn mở rộng tương lai để **rút trích luật tự động** từ bảng dữ liệu khảo sát nếu không có chuyên gia viết luật bằng tay.
   - *Sentence Transformers / Embeddings (Chương NLP):* Có thể hỗ trợ cho TV5 làm giao diện phân tích câu hỏi tự nhiên của người dùng để map vào mã `Fact`.
   - Đối với lõi xử lý xung đột của TV3: **Thuật toán sắp xếp đa tiêu chí (Lexicographical Multi-Criteria Sorting) là giải pháp chuẩn xác và tối ưu nhất.**

---

## 3. NGUYÊN LÝ THUẬT TOÁN XỬ LÝ XUNG ĐỘT (THEO MỤC 2.4.1 BÁO CÁO)

Khi có từ hai luật trở lên cùng thỏa mãn điều kiện vế `IF` ở cùng một vòng lặp suy diễn, hệ thống rơi vào trạng thái **Xung đột luật (Rule Conflict)**. `ConflictResolver` của TV3 áp dụng chiến lược sắp xếp đa tầng kinh điển của Hệ chuyên gia:

$$\vec{Score}(R) = \Big( \underbrace{|\text{Premises}(R)|}_{\text{1. Specificity (Độ đặc thù)}}, \quad \underbrace{\text{Priority}(R)}_{\text{2. Salience (Độ ưu tiên)}}, \quad \underbrace{\max_{f \in \text{Premises}(R)} \text{step}(f)}_{\text{3. Recency (Độ mới sự kiện)}} \Big)$$

```mermaid
flowchart TD
    CS["Danh sách luật xung đột (Conflict Set)"] --> S1{"1. Kiểm tra số lượng"}
    S1 -- "len == 1" --> S1_Single["Trả về ngay luật duy nhất\n(Không có xung đột)"]
    S1 -- "len > 1" --> S2["2. Tính toán Vector điểm số cho từng luật:\n(Specificity, Priority, Recency)"]
    
    S2 --> S3["3. Sắp xếp giảm dần theo thứ tự ưu tiên:\n① Specificity (Số điều kiện IF)\n② Priority (Độ ưu tiên chuyên gia)\n③ Recency (Timestamp sự kiện mới nhất)"]
    
    S3 --> S4["4. Tie-breaking (Phá hòa ổn định):\nDuy trì thứ tự xuất hiện ban đầu (Timsort)"]
    
    S4 --> S5["5. Chọn phần tử đầu tiên: R*\nSinh chuỗi giải thích lý do (Reason)"]
    S5 --> Out(["Trả về: (selected_rule = R*, resolution_reason)"])
    S1_Single --> Out
```

### Chi tiết 4 Tiêu chí phân xử:
1. **Tiêu chí 1 - Specificity (Độ đặc thù của luật):**
   - Luật nào có số lượng điều kiện tiền đề ở vế `IF` nhiều hơn thì luật đó mang tính đặc thù cao hơn, xem xét ngữ cảnh chi tiết hơn và ít mơ hồ hơn $\rightarrow$ Ưu tiên kích hoạt trước.
   - *Ví dụ:* Luật xét 3 điều kiện `R04: IF F07 AND F08 AND F03` ($\text{Specificity} = 3$) sẽ thắng luật xét 2 điều kiện `R03: IF F07 AND F01` ($\text{Specificity} = 2$).
2. **Tiêu chí 2 - Priority / Salience (Độ ưu tiên chuyên gia):**
   - Nếu hai luật có cùng số lượng tiền đề, luật nào được chuyên gia gán trọng số ưu tiên cao hơn sẽ được kích hoạt trước.
   - Trong hệ phân tầng: Các luật định hướng cấp cao hoặc luật mang tính quyết định sẽ có `Priority` lớn hơn (ví dụ Priority 3 > Priority 2 > Priority 1).
3. **Tiêu chí 3 - Recency (Tính mới của sự kiện trong Working Memory):**
   - Nếu cả độ đặc thù và độ ưu tiên đều bằng nhau, hệ thống ưu tiên luật so khớp với sự kiện vừa mới được nạp vào Working Memory ở bước gần nhất (`timestamp_step` lớn nhất).
   - *Ý nghĩa:* Giúp động cơ suy diễn bám sát mạch suy luận liên tục, tiếp tục khai thác ngay kết quả vừa tìm được ở chu kỳ liền trước thay vì nhảy cóc sang nhánh suy luận khác.
4. **Tiêu chí 4 - Tie-breaking (Phá hòa ổn định):**
   - Sử dụng thuật toán sắp xếp ổn định **Timsort** tích hợp sẵn của Python (`sorted(..., reverse=True)`). Nếu hai luật hòa nhau ở cả 3 chỉ số, thứ tự định nghĩa luật ban đầu được bảo toàn (Deterministic Rule Order).

---

## 4. SƠ ĐỒ TRÌNH TỰ TƯƠNG TÁC (SEQUENCE DIAGRAM)

Sơ đồ thể hiện rõ sự phân định trách nhiệm giữa Động cơ Suy diễn (đồng đội) và Bộ xử lý xung đột (TV3) trong một chu kỳ suy diễn:

```mermaid
sequenceDiagram
    autonumber
    actor User as Người dùng / UI
    participant Engine as ForwardChainingEngine (Đồng đội)
    participant WM as Working Memory (Bộ nhớ sự kiện)
    participant Resolver as ConflictResolver (Thành viên 3)

    User->>Engine: forward_chain(initial_fact_ids)
    Engine->>WM: Khởi tạo WM với các Fact ban đầu (step = 0)
    
    loop Chu trình suy diễn (Đến khi Conflict Set rỗng)
        Note over Engine: PHA 1: MATCH
        Engine->>WM: Đọc danh sách Fact đã có
        Engine->>Engine: Lọc luật thỏa mãn tiền đề IF & chưa từng fire
        Note over Engine: Thu được list: conflict_set
        
        Note over Resolver: PHA 2: CONFLICT RESOLUTION
        Engine->>Resolver: resolve(conflict_set, working_memory)
        Resolver->>Resolver: Tính Recency của từng luật từ WM
        Resolver->>Resolver: Sắp xếp theo (Specificity, Priority, Recency)
        Resolver-->>Engine: Trả về (selected_rule, resolution_reason)
        
        Note over Engine: PHA 3: ACT / EXECUTE
        Engine->>WM: Thêm Fact mới (kết luận của selected_rule, step = step + 1)
        Engine->>Engine: Ghi nhận TraceStep phục vụ giải trình
    end

    Engine-->>User: Trả về kết quả suy diễn & Báo cáo vết
```

---

## 5. ĐẶC TẢ CHI TIẾT SOURCE CODE `conflict_resolver.py` CỦA TV3

Mã nguồn được đóng gói hoàn chỉnh trong file [`conflict_resolver.py`](file:///d:/TRÍ%20TUỆ%20NHÂN%20TẠO/conflict_resolver.py) với đầy đủ type hinting và docstring:

```python
from typing import Dict, List, Optional, Tuple
from structs import Fact, Rule


class ConflictResolver:
    """
    Bộ xử lý xung đột luật (Conflict Resolver) do Thành viên 3 (TV3) phụ trách.
    Được thiết kế theo nguyên lý Đơn trách nhiệm (Single Responsibility Principle - SOLID).
    """

    SUPPORTED_STRATEGIES = [
        "combined",
        "specificity",
        "priority",
        "recency",
        "first_match",
    ]

    def __init__(self, strategy: str = "combined") -> None:
        if strategy not in self.SUPPORTED_STRATEGIES:
            raise ValueError(f"Chiến lược '{strategy}' không được hỗ trợ.")
        self.strategy: str = strategy

    def get_rule_recency(self, rule: Rule, working_memory: Dict[str, Fact]) -> int:
        """Tính chỉ số Recency = max(timestamp_step) của các tiền đề vế IF."""
        if not rule.premises:
            return 0
        return max(
            working_memory[fid].timestamp_step
            for fid in rule.premises
            if fid in working_memory
        )

    def resolve(
        self,
        conflict_set: List[Rule],
        working_memory: Dict[str, Fact]
    ) -> Tuple[Rule, str]:
        """
        Hàm chính nhận vào conflict_set và working_memory,
        chọn ra 1 luật tốt nhất và lý do giải trình.
        """
        if not conflict_set:
            raise ValueError("Conflict set rỗng!")

        # 1. Nếu chỉ có đúng 1 luật: không có xung đột
        if len(conflict_set) == 1:
            only_rule = conflict_set[0]
            recency = self.get_rule_recency(only_rule, working_memory)
            reason = f"Duy nhất luật [{only_rule.id}] thỏa mãn ở bước này."
            return only_rule, reason

        # 2. Xử lý theo các chiến lược cấu hình
        if self.strategy == "first_match":
            return conflict_set[0], f"Chọn [{conflict_set[0].id}] theo First-Match."

        if self.strategy == "specificity":
            sorted_rules = sorted(
                conflict_set,
                key=lambda r: (r.specificity, r.priority, self.get_rule_recency(r, working_memory)),
                reverse=True
            )
            chosen = sorted_rules[0]
            return chosen, f"Chọn [{chosen.id}] vì có Specificity cao nhất ({chosen.specificity} IF)."

        if self.strategy == "priority":
            sorted_rules = sorted(
                conflict_set,
                key=lambda r: (r.priority, r.specificity, self.get_rule_recency(r, working_memory)),
                reverse=True
            )
            chosen = sorted_rules[0]
            return chosen, f"Chọn [{chosen.id}] vì có Priority cao nhất ({chosen.priority})."

        if self.strategy == "recency":
            sorted_rules = sorted(
                conflict_set,
                key=lambda r: (self.get_rule_recency(r, working_memory), r.specificity, r.priority),
                reverse=True
            )
            chosen = sorted_rules[0]
            return chosen, f"Chọn [{chosen.id}] vì dùng sự kiện mới nhất (Recency={self.get_rule_recency(chosen, working_memory)})."

        # 3. Mặc định: 'combined' (Đa tiêu chí chuẩn Hệ chuyên gia)
        sorted_rules = sorted(
            conflict_set,
            key=lambda r: (r.specificity, r.priority, self.get_rule_recency(r, working_memory)),
            reverse=True
        )
        chosen = sorted_rules[0]
        rec = self.get_rule_recency(chosen, working_memory)
        reason = (
            f"Xử lý xung đột giữa {[r.id for r in conflict_set]} -> Chọn [{chosen.id}] "
            f"(Độ đặc thù={chosen.specificity} điều kiện, Độ ưu tiên={chosen.priority}, "
            f"Độ mới sự kiện={rec})."
        )
        return chosen, reason
```

---

## 6. VÍ DỤ MINH HỌA THỰC TẾ CỦA THUẬT TOÁN (CASE STUDY TEST CASE 1)

**Đầu vào:** `['F01', 'F02', 'F03']` (Học sinh thích Toán, biết Python, thích phân tích dữ liệu).

### 📍 Chu kỳ 1 (Step 1):
* **Working Memory:** `{F01 (step 0), F02 (step 0), F03 (step 0)}`
* **Conflict Set do Engine phát hiện:** `[R01, R08]`
  * `R01`: IF F01 AND F02 THEN F07 (Specificity = 2, Priority = 2, Recency = 0)
  * `R08`: IF F01 AND F03 THEN F08 (Specificity = 2, Priority = 1, Recency = 0)
* **Xử lý xung đột của TV3:**
  * So sánh Specificity: $2 = 2$ (Hòa).
  * So sánh Priority: $R01 (2) > R08 (1)$ $\rightarrow$ **$R01$ THẮNG**.
* **Kết quả:** Kích hoạt $R01 \rightarrow$ Thêm $F07$ vào WM ở bước 1.

### 📍 Chu kỳ 2 (Step 2):
* **Working Memory:** `{F01, F02, F03, F07 (step 1)}`
* **Conflict Set do Engine phát hiện:** `[R02, R03, R08]`
  * `R02`: IF F07 AND F03 THEN F08 (Specificity = 2, Priority = 2, Recency = 1)
  * `R03`: IF F07 AND F01 THEN F09 (Specificity = 2, Priority = 1, Recency = 1)
  * `R08`: IF F01 AND F03 THEN F08 (Specificity = 2, Priority = 1, Recency = 0)
* **Xử lý xung đột của TV3:**
  * So sánh Specificity: Cả 3 luật đều bằng 2 (Hòa).
  * So sánh Priority: $R02 (2) > R03 (1) = R08 (1)$ $\rightarrow$ **$R02$ THẮNG**.
* **Kết quả:** Kích hoạt $R02 \rightarrow$ Thêm $F08$ vào WM ở bước 2.

### 📍 Chu kỳ 3 (Step 3):
* **Working Memory:** `{F01, F02, F03, F07 (step 1), F08 (step 2)}`
* **Conflict Set do Engine phát hiện:** `[R04, R03]` *(Chú ý: R08 bị loại vì kết luận F08 đã có)*
  * `R04`: IF F07 AND F08 AND F03 THEN F10 (Specificity = 3, Priority = 3, Recency = 2)
  * `R03`: IF F07 AND F01 THEN F09 (Specificity = 2, Priority = 1, Recency = 1)
* **Xử lý xung đột của TV3:**
  * So sánh Specificity: $R04 (3) > R03 (2)$ $\rightarrow$ **$R04$ THẮNG NGAY LẬP TỨC**.
* **Kết quả:** Kích hoạt $R04 \rightarrow$ Thêm $F10$ (Khoa học Dữ liệu) vào WM ở bước 3.

### 📍 Chu kỳ 4 (Step 4):
* **Working Memory:** `{F01, F02, F03, F07, F08, F10, F09}`
* **Conflict Set do Engine phát hiện:** `[R03]` (Duy nhất 1 luật).
* **Xử lý xung đột của TV3:** Trả về $R03$ ngay lập tức vì không có xung đột.

$\implies$ **Thứ tự luật kích hoạt chuẩn xác:** `['R01', 'R02', 'R04', 'R03']` (Đạt chuẩn 100% trong bộ test `test_suite.py`).

---

## 7. TỔNG KẾT BÀN GIAO CỦA THÀNH VIÊN 3

1. **File mã nguồn độc lập:** [`conflict_resolver.py`](file:///d:/TRÍ%20TUỆ%20NHÂN%20TẠO/conflict_resolver.py) - Được thiết kế dạng module cắm ghép (pluggable), sẵn sàng để đồng đội gọi qua phương thức `resolve(conflict_set, working_memory)`.
2. **File tích hợp:** [`core_engine.py`](file:///d:/TRÍ%20TUỆ%20NHÂN%20TẠO/core_engine.py) - Đã refactor để `ForwardChainingEngine` ủy quyền toàn bộ việc xử lý xung đột cho `ConflictResolver`.
3. **Kết quả kiểm thử thực nghiệm:** Chạy `python -X utf8 test_suite.py` đạt **10/10 Test Cases PASS (100%)**.
4. **Tài liệu đặc tả:** Toàn bộ flow và kiến trúc đã được trình bày đầy đủ trong file markdown này để nộp báo cáo và thuyết minh đồ án.

