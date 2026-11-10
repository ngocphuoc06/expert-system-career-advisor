from dataclasses import dataclass, field
from typing import List, Optional, Set


@dataclass
class Fact:
    """
    Biểu diễn một Sự kiện (Fact) trong Bộ nhớ làm việc (Working Memory).
    """
    id: str                             # Mã sự kiện, ví dụ: 'F01'
    description: str = ""               # Mô tả sự kiện, ví dụ: 'Máy tính bật không lên nguồn'
    source: str = "user"                # 'user' (người dùng nhập) hoặc 'inferred' (suy diễn ra)
    by_rule: Optional[str] = None       # Mã luật sinh ra sự kiện này (None nếu do user nhập)
    timestamp_step: int = 0             # Bước thời gian sự kiện được nạp vào Working Memory (dùng cho Recency)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Fact):
            return self.id == other.id
        return False

    def __repr__(self) -> str:
        origin = "Ban đầu" if self.source == "user" else f"Do luật {self.by_rule} (Bước {self.timestamp_step})"
        return f"Fact({self.id}: '{self.description}' [{origin}])"


@dataclass
class Rule:
    """
    Biểu diễn một Luật sản xuất (Production Rule) dạng: IF <premises> THEN <conclusion>.
    """
    id: str                             # Mã luật, ví dụ: 'R01'
    premises: List[str]                 # Danh sách mã Fact ở vế IF (Tiền đề), ví dụ: ['F01', 'F02']
    conclusion: str                     # Mã Fact ở vế THEN (Kết luận), ví dụ: 'F05'
    priority: int = 1                   # Độ ưu tiên (Salience/Priority) dùng khi xử lý xung đột
    explanation: str = ""               # Giải thích ngữ nghĩa vì sao IF lại suy ra THEN (phục vụ GĐ 3)

    @property
    def specificity(self) -> int:
        """
        Độ đặc thù của luật (Specificity): Số lượng điều kiện ở vế IF.
        Luật càng nhiều điều kiện IF thì càng cụ thể và được ưu tiên hơn khi xử lý xung đột.
        """
        return len(self.premises)

    def is_triggered(self, known_fact_ids: Set[str]) -> bool:
        """
        Kiểm tra toàn bộ điều kiện vế IF của luật đã có trong Working Memory hay chưa.
        """
        return set(self.premises).issubset(known_fact_ids)

    def format_rule(self) -> str:
        """
        Trả về chuỗi biểu diễn luật dạng chuẩn: R01: IF F01 AND F02 THEN F05
        """
        if_part = " AND ".join(self.premises)
        return f"{self.id}: IF ({if_part}) THEN {self.conclusion}"


@dataclass
class TraceStep:
    """
    Lưu vết 1 vòng lặp suy diễn (Inference Cycle) để phục vụ Module Giải trình (Giai đoạn 3).
    """
    step_number: int                    # Thứ tự bước suy diễn (1, 2, 3...)
    conflict_set: List[str]             # Danh sách các mã luật cùng thỏa mãn trong vòng lặp (Tập xung đột)
    fired_rule: Rule                    # Luật được chọn để kích hoạt sau khi xử lý xung đột
    new_fact: Fact                      # Sự kiện mới được sinh ra và thêm vào Working Memory
    resolution_reason: str              # Lý do chọn luật này từ tập xung đột (Specificity, Priority, Recency...)
    working_memory_snapshot: List[str] = field(default_factory=list)  # Trạng thái WM sau khi thêm sự kiện mới

