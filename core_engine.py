from typing import Dict, List, Optional, Set, Tuple
from structs import Fact, Rule, TraceStep
from rules_data import FACT_CATALOG, RULES_DATA
from conflict_resolver import ConflictResolver


class ForwardChainingEngine:
    """
    Động cơ Suy diễn tiến (Forward Chaining) chuẩn theo chu trình:
    MATCH (Đối sánh) -> CONFLICT RESOLUTION (Xử lý xung đột) -> ACT/EXECUTE (Kích hoạt luật).
    """

    def __init__(
        self,
        rules: List[Rule] = RULES_DATA,
        fact_catalog: Dict[str, str] = FACT_CATALOG,
        strategy: str = "combined"
    ) -> None:
        """
        Khởi tạo Động cơ suy diễn.
        :param rules: Danh sách các đối tượng Rule trong Cơ sở tri thức (Knowledge Base).
        :param fact_catalog: Từ điển ánh xạ mã Fact -> Mô tả tiếng Việt.
        :param strategy: Chiến lược xử lý xung đột:
            - 'combined': Kết hợp chuẩn (Specificity -> Priority -> Recency -> Rule Order)
            - 'specificity': Ưu tiên luật có nhiều điều kiện IF nhất
            - 'priority': Ưu tiên luật có độ ưu tiên (priority) cao nhất
            - 'recency': Ưu tiên luật khớp với sự kiện mới được sinh ra gần nhất
            - 'first_match': Chọn luật đầu tiên khớp theo thứ tự danh sách (FIFO)
        """
        self.rules: List[Rule] = rules
        self.fact_catalog: Dict[str, str] = fact_catalog
        self.strategy: str = strategy
        # Module Xử lý Xung đột do Thành viên 3 (TV3) phụ trách
        self.conflict_resolver: ConflictResolver = ConflictResolver(strategy=strategy)

        # Bộ nhớ làm việc (Working Memory): Lưu trữ dict {fact_id: Fact}
        self.working_memory: Dict[str, Fact] = {}
        # Tập các mã luật đã kích hoạt (phục vụ nguyên lý Refractoriness - không lặp lại luật cũ)
        self.fired_rule_ids: Set[str] = set()
        # Danh sách vết suy diễn theo trình tự thời gian (phục vụ GĐ 3 - Giải trình)
        self.trace_history: List[TraceStep] = []

    def reset(self) -> None:
        """Làm sạch Working Memory và lịch sử vết suy diễn trước mỗi lần chạy mới."""
        self.working_memory.clear()
        self.fired_rule_ids.clear()
        self.trace_history.clear()

    def load_initial_facts(self, initial_fact_ids: List[str]) -> None:
        """
        Nạp các sự kiện ban đầu do người dùng cung cấp vào Working Memory (Bước 0).
        """
        self.reset()
        for fid in initial_fact_ids:
            desc = self.fact_catalog.get(fid, f"Sự kiện {fid}")
            self.working_memory[fid] = Fact(
                id=fid,
                description=desc,
                source="user",
                by_rule=None,
                timestamp_step=0
            )

    def _match_conflict_set(self) -> List[Rule]:
        """
        PHA 1 - MATCH (ĐỐI SÁNH):
        Tìm tất cả các luật khả dụng tạo thành Tập xung đột (Conflict Set / Agenda).
        Điều kiện một luật được đưa vào Tập xung đột:
        1. Nguyên lý Refractoriness: Luật chưa từng được kích hoạt trước đó.
        2. Tính mới của tri thức: Kết luận của luật chưa có trong Working Memory.
        3. Thỏa mãn tiền đề: Mọi Fact ở vế IF đều đã có mặt trong Working Memory.
        """
        known_ids = set(self.working_memory.keys())
        conflict_set: List[Rule] = []

        for rule in self.rules:
            if rule.id in self.fired_rule_ids:
                continue
            if rule.conclusion in known_ids:
                continue
            if rule.is_triggered(known_ids):
                conflict_set.append(rule)

        return conflict_set

    def _get_rule_recency(self, rule: Rule) -> int:
        """
        Tính chỉ số Recency (độ mới) của một luật.
        Ủy nhiệm cho module ConflictResolver của TV3.
        """
        return self.conflict_resolver.get_rule_recency(rule, self.working_memory)

    def _resolve_conflict(self, conflict_set: List[Rule]) -> Tuple[Rule, str]:
        """
        PHA 2 - CONFLICT RESOLUTION (XỬ LÝ XUNG ĐỘT):
        Ủy quyền toàn bộ xử lý xung đột cho class ConflictResolver do TV3 phụ trách.
        Nhận vào tập xung đột (conflict_set) và Working Memory, trả về 1 luật tối ưu nhất.
        """
        return self.conflict_resolver.resolve(conflict_set, self.working_memory)

    def forward_chain(
        self,
        initial_fact_ids: List[str],
        target_fact_id: Optional[str] = None
    ) -> Dict[str, object]:
        """
        PHA 3 - VÒNG LẶP SUY DIỄN TIẾN CHÍNH (MAIN INFERENCE LOOP):
        Chạy liên tục chu trình Match -> Resolve -> Act cho đến khi:
        - Tập xung đột rỗng (Không còn luật nào kích hoạt thêm được nữa), HOẶC
        - Đã tìm thấy sự kiện đích `target_fact_id` (nếu có chỉ định đích cụ thể).
        """
        self.load_initial_facts(initial_fact_ids)
        step_counter = 0

        while True:
            # Nếu người dùng chỉ định cần chứng minh 1 kết luận đích và đích đã có trong WM -> Dừng
            if target_fact_id and target_fact_id in self.working_memory:
                break

            # 1. MATCH: Tìm tập luật xung đột
            conflict_set = self._match_conflict_set()
            if not conflict_set:
                break  # Điểm dừng thuật toán: Không còn luật nào có thể kích hoạt

            # 2. RESOLVE: Giải quyết xung đột để chọn 1 luật tối ưu
            selected_rule, reason = self._resolve_conflict(conflict_set)

            # 3. ACT / EXECUTE: Kích hoạt luật và bổ sung sự kiện mới vào Working Memory
            step_counter += 1
            new_fact_id = selected_rule.conclusion
            new_fact = Fact(
                id=new_fact_id,
                description=self.fact_catalog.get(new_fact_id, f"Sự kiện {new_fact_id}"),
                source="inferred",
                by_rule=selected_rule.id,
                timestamp_step=step_counter
            )

            self.working_memory[new_fact_id] = new_fact
            self.fired_rule_ids.add(selected_rule.id)

            # Lưu vết suy diễn (TraceStep) cho Module Giải trình ở Giai đoạn 3
            trace_step = TraceStep(
                step_number=step_counter,
                conflict_set=[r.id for r in conflict_set],
                fired_rule=selected_rule,
                new_fact=new_fact,
                resolution_reason=reason,
                working_memory_snapshot=list(self.working_memory.keys())
            )
            self.trace_history.append(trace_step)

        # Tổng hợp kết quả trả về cho UI (TV5) và Kiểm thử (TV6)
        inferred_facts = [
            f for f in self.working_memory.values() if f.source == "inferred"
        ]
        activated_rules = [step.fired_rule for step in self.trace_history]

        return {
            "initial_facts": [
                f for f in self.working_memory.values() if f.source == "user"
            ],
            "inferred_facts": inferred_facts,
            "all_facts": list(self.working_memory.values()),
            "activated_rules": activated_rules,
            "trace_history": self.trace_history,
        }

    # =========================================================================
    # MODULE GIẢI TRÌNH VẾT SUY DIỄN ("VÌ SAO?" / "NHƯ THẾ NÀO?") - GIAI ĐOẠN 3
    # =========================================================================

    def explain_why_fact(self, fact_id: str, indent: int = 0) -> List[str]:
        """
        Giải trình đệ quy (Backward Proof Tree trên vết suy diễn):
        Trả lời câu hỏi "Vì sao hệ thống lại kết luận được sự kiện `fact_id`?"
        bằng cách lần ngược từ kết luận về các luật và sự kiện ban đầu của người dùng.
        """
        prefix = "    " * indent
        lines: List[str] = []

        if fact_id not in self.working_memory:
            lines.append(f"{prefix}- Sự kiện [{fact_id}] không tồn tại trong bộ nhớ làm việc hiện tại.")
            return lines

        fact = self.working_memory[fact_id]
        if fact.source == "user":
            lines.append(
                f"{prefix}✔ [{fact.id}] {fact.description} "
                f"(Sự kiện gốc do người dùng cung cấp ban đầu)."
            )
            return lines

        # Tìm bước suy diễn đã sinh ra fact này
        rule_obj = next((r for r in self.rules if r.id == fact.by_rule), None)
        if not rule_obj:
            lines.append(f"{prefix}➜ [{fact.id}] {fact.description} (Suy diễn từ luật {fact.by_rule}).")
            return lines

        lines.append(
            f"{prefix}🎯 [{fact.id}] {fact.description} "
            f"<-- Được suy ra ở Bước {fact.timestamp_step} nhờ kích hoạt luật [{rule_obj.id}]:"
        )
        lines.append(f"{prefix}   💡 Giải thích chuyên gia ({rule_obj.id}): {rule_obj.explanation}")
        lines.append(f"{prefix}   📌 Vì tất cả {len(rule_obj.premises)} điều kiện của [{rule_obj.id}] đều đã thỏa mãn:")

        # Đệ quy giải thích từng điều kiện ở vế IF của luật đó
        for premise_id in rule_obj.premises:
            lines.extend(self.explain_why_fact(premise_id, indent=indent + 2))

        return lines

    def format_trace_report(self) -> str:
        """
        Xuất báo cáo chi tiết từng bước kích hoạt luật (Sản phẩm bàn giao Ngày 3).
        """
        if not self.trace_history:
            return "Không có luật nào được kích hoạt từ tập sự kiện đầu vào."

        report_lines: List[str] = [
            "======================================================================",
            "         BÁO CÁO VẾT SUY DIỄN TIẾN & DANH SÁCH LUẬT KÍCH HOẠT         ",
            "======================================================================"
        ]

        for step in self.trace_history:
            r = step.fired_rule
            premises_str = ", ".join(
                f"{pid} ({self.fact_catalog.get(pid, '')})" for pid in r.premises
            )
            report_lines.append(f"\n[BƯỚC {step.step_number}]")
            report_lines.append(f"  • Tập luật xung đột (Conflict Set): {step.conflict_set}")
            report_lines.append(f"  • Quyết định xử lý xung đột       : {step.resolution_reason}")
            report_lines.append(f"  • Luật được kích hoạt             : {r.format_rule()}")
            report_lines.append(f"  • Tiền đề đã khớp                 : {premises_str}")
            report_lines.append(f"  • Sự kiện mới sinh ra             : [{step.new_fact.id}] {step.new_fact.description}")
            report_lines.append(f"  • Bộ nhớ làm việc (WM) hiện tại   : {step.working_memory_snapshot}")

        return "\n".join(report_lines)


if __name__ == "__main__":
    # Chạy kiểm thử nhanh cho TV3 ở Ngày 2 & Ngày 3
    engine = ForwardChainingEngine(strategy="combined")
    sample_inputs = ["F01", "F02", "F03"]
    print(f">>> Sự kiện đầu vào của người dùng: {sample_inputs}")
    result = engine.forward_chain(sample_inputs)

    print(engine.format_trace_report())
    print("\n" + "=" * 70)
    print("GIẢI TRÌNH 'VÌ SAO?' CHO KẾT LUẬN CUỐI CÙNG:")
    print("=" * 70)
    for inferred in result["inferred_facts"]:
        print("\n".join(engine.explain_why_fact(inferred.id)))
        print("-" * 50)

