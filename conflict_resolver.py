"""
=============================================================================
MODULE XỬ LÝ XUNG ĐỘT LUẬT (CONFLICT RESOLVER)
Phụ trách: Thành viên 3 (TV3)
Đồ án: Hệ Chuyên Gia Tư Vấn Chọn Ngành Học Sinh THPT / Kỹ Nghệ Tri Thức
=============================================================================
Mô tả nhiệm vụ TV3:
- Nhận vào danh sách `conflict_set` (các luật cùng thỏa mãn tiền đề ở vòng lặp)
  và `working_memory` (bộ nhớ làm việc chứa các sự kiện hiện hành kèm timestamp).
- Thực hiện thuật toán sắp xếp & lọc đa tiêu chí chuẩn Hệ chuyên gia:
    1. Độ đặc thù (Specificity): Luật nhiều điều kiện vế IF hơn sẽ được ưu tiên.
    2. Độ ưu tiên (Priority/Salience): Trọng số chuyên gia thiết kế (Tầng 1 > Tầng 2 > Tầng 3).
    3. Độ mới của sự kiện (Recency): Ưu tiên luật dựa trên sự kiện mới nạp vào WM gần nhất.
    4. Phá hòa ổn định (Tie-breaking): Giữ thứ tự ổn định tự nhiên theo mã luật.
- Trả về: (selected_rule: Rule, resolution_reason: str) phục vụ Pha Act và Module Giải trình.
=============================================================================
"""

from typing import Dict, List, Optional, Tuple
from structs import Fact, Rule


class ConflictResolver:
    """
    Bộ xử lý xung đột luật (Conflict Resolver) độc lập dành cho Hệ Chuyên Gia.
    Được thiết kế theo nguyên lý Đơn trách nhiệm (Single Responsibility Principle - SOLID)
    để tích hợp mượt mà vào Động cơ Suy diễn (Forward Chaining Engine).
    """

    SUPPORTED_STRATEGIES = [
        "combined",
        "specificity",
        "priority",
        "recency",
        "first_match",
    ]

    def __init__(self, strategy: str = "combined") -> None:
        """
        Khởi tạo Bộ xử lý xung đột.
        :param strategy: Chiến lược xử lý xung đột được cấu hình:
            - 'combined': Đa tiêu chí chuẩn (Specificity -> Priority -> Recency -> Tie-break)
            - 'specificity': Ưu tiên độ đặc thù (nhiều điều kiện vế IF nhất)
            - 'priority': Ưu tiên độ ưu tiên luật (Salience) cao nhất
            - 'recency': Ưu tiên sự kiện mới nạp vào Working Memory nhất
            - 'first_match': Chọn luật đầu tiên theo thứ tự xuất hiện (FIFO)
        """
        if strategy not in self.SUPPORTED_STRATEGIES:
            raise ValueError(
                f"Chiến lược '{strategy}' không được hỗ trợ. "
                f"Các chiến lược hợp lệ: {self.SUPPORTED_STRATEGIES}"
            )
        self.strategy: str = strategy

    def get_rule_recency(self, rule: Rule, working_memory: Dict[str, Fact]) -> int:
        """
        Tính chỉ số Recency (độ mới) của luật dựa trên timestamp_step lớn nhất
        của các sự kiện ở vế IF đang có trong Working Memory.
        """
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
        Hàm chính của TV3: Nhận vào `conflict_set` và `working_memory`,
        áp dụng thuật toán sắp xếp đa tiêu chí để chọn ra 1 luật tốt nhất.

        :param conflict_set: Danh sách các đối tượng Rule đang cùng thỏa mãn tiền đề.
        :param working_memory: Từ điển {fact_id: Fact} hiện tại của hệ thống.
        :return: Tuple gồm (luật được chọn, chuỗi lý do giải trình).
        """
        if not conflict_set:
            raise ValueError("Conflict set rỗng, không có luật nào để xử lý xung đột!")

        # Trường hợp 1: Chỉ có đúng 1 luật thỏa mãn (Không có xung đột thực sự)
        if len(conflict_set) == 1:
            only_rule = conflict_set[0]
            recency = self.get_rule_recency(only_rule, working_memory)
            reason = (
                f"Duy nhất luật [{only_rule.id}] thỏa mãn ở bước này (không có xung đột). "
                f"Specificity={only_rule.specificity}, Priority={only_rule.priority}, Recency={recency}."
            )
            return only_rule, reason

        # Trường hợp 2: Chiến lược First-Match (Chọn luật đầu tiên theo FIFO)
        if self.strategy == "first_match":
            chosen = conflict_set[0]
            return chosen, f"Chọn [{chosen.id}] theo thứ tự xuất hiện đầu tiên (First-Match)."

        # Trường hợp 3: Ưu tiên Độ đặc thù (Specificity) cao nhất
        if self.strategy == "specificity":
            sorted_rules = sorted(
                conflict_set,
                key=lambda r: (r.specificity, r.priority, self.get_rule_recency(r, working_memory)),
                reverse=True
            )
            chosen = sorted_rules[0]
            return (
                chosen,
                f"Xử lý xung đột giữa {[r.id for r in conflict_set]} -> Chọn [{chosen.id}] "
                f"vì có Độ đặc thù (Specificity) cao nhất ({chosen.specificity} điều kiện IF)."
            )

        # Trường hợp 4: Ưu tiên Độ ưu tiên (Priority / Salience) cao nhất
        if self.strategy == "priority":
            sorted_rules = sorted(
                conflict_set,
                key=lambda r: (r.priority, r.specificity, self.get_rule_recency(r, working_memory)),
                reverse=True
            )
            chosen = sorted_rules[0]
            return (
                chosen,
                f"Xử lý xung đột giữa {[r.id for r in conflict_set]} -> Chọn [{chosen.id}] "
                f"vì có Độ ưu tiên (Priority) cao nhất (priority={chosen.priority})."
            )

        # Trường hợp 5: Ưu tiên Tính mới của sự kiện (Recency)
        if self.strategy == "recency":
            sorted_rules = sorted(
                conflict_set,
                key=lambda r: (self.get_rule_recency(r, working_memory), r.specificity, r.priority),
                reverse=True
            )
            chosen = sorted_rules[0]
            rec = self.get_rule_recency(chosen, working_memory)
            return (
                chosen,
                f"Xử lý xung đột giữa {[r.id for r in conflict_set]} -> Chọn [{chosen.id}] "
                f"vì dùng sự kiện mới nhất (Recency step={rec})."
            )

        # Trường hợp mặc định: 'combined' (Chiến lược đa tiêu chí chuẩn Hệ chuyên gia)
        # Vector sắp xếp giảm dần: (Specificity -> Priority -> Recency)
        # Timsort của Python giữ nguyên thứ tự xuất hiện nếu các chỉ số bằng nhau (Tie-breaking)
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

