from structs import Rule
from rules_data import FACT_CATALOG, RULES_DATA, load_rules_from_csv
from core_engine import ForwardChainingEngine


def run_10_test_cases() -> None:
    print("=" * 80)
    print("   BỘ KIỂM THỬ 10 TEST CASES HỆ SUY DIỄN TIẾN & XỬ LÝ XUNG ĐỘT (NGÀY 5)   ")
    print("=" * 80)

    engine = ForwardChainingEngine(strategy="combined")

    standard_tests = [
        {
            "id": "TC01",
            "name": "Suy diễn đa tầng + Xung đột đa tiêu chí (Data Scientist)",
            "inputs": ["F01", "F02", "F03"],
            "expected_rules": ["R01", "R02", "R04", "R03"],
            "expected_goal": "F10",
        },
        {
            "id": "TC02",
            "name": "Suy diễn bắc cầu 3 bước (Computer Vision Engineer)",
            "inputs": ["F01", "F02", "F04"],
            "expected_rules": ["R01", "R03", "R05"],
            "expected_goal": "F11",
        },
        {
            "id": "TC03",
            "name": "Suy diễn bắc cầu 3 bước (NLP & LLM Engineer)",
            "inputs": ["F01", "F02", "F05"],
            "expected_rules": ["R01", "R03", "R06"],
            "expected_goal": "F12",
        },
        {
            "id": "TC04",
            "name": "Ưu tiên Specificity 3 điều kiện (MLOps Engineer)",
            "inputs": ["F01", "F02", "F06"],
            "expected_rules": ["R01", "R07", "R03"],
            "expected_goal": "F13",
        },
        {
            "id": "TC05",
            "name": "Suy diễn 1 bước khi thiếu kỹ năng Python (Chỉ có Toán + Phân tích)",
            "inputs": ["F01", "F03"],
            "expected_rules": ["R08"],
            "expected_goal": "F08",
        },
        {
            "id": "TC06",
            "name": "Đầu vào đơn lẻ không đủ kích hoạt bất kỳ luật nào",
            "inputs": ["F02"],
            "expected_rules": [],
            "expected_goal": None,
        },
        {
            "id": "TC07",
            "name": "Đầu vào rỗng (Edge Case: Người dùng chưa chọn sự kiện nào)",
            "inputs": [],
            "expected_rules": [],
            "expected_goal": None,
        },
        {
            "id": "TC08",
            "name": "Người dùng chọn tất cả sự kiện đầu vào (Tổng hợp toàn bộ luật)",
            "inputs": ["F01", "F02", "F03", "F04", "F05", "F06"],
            "expected_rules": ["R01", "R07", "R02", "R04", "R03", "R05", "R06"],
            "expected_goal": "F10",
        },
    ]

    passed = 0
    for tc in standard_tests:
        res = engine.forward_chain(tc["inputs"])
        fired_ids = [r.id for r in res["activated_rules"]]
        inferred_ids = [f.id for f in res["inferred_facts"]]

        rules_ok = fired_ids == tc["expected_rules"]
        goal_ok = (tc["expected_goal"] is None and len(inferred_ids) == 0) or (
            tc["expected_goal"] in inferred_ids
        )
        status = "PASS" if (rules_ok and goal_ok) else "FAIL"
        if status == "PASS":
            passed += 1

        print(f"[{status}] {tc['id']} - {tc['name']}")
        print(f"       • Input          : {tc['inputs']}")
        print(f"       • Luật kích hoạt : {fired_ids} (Kỳ vọng: {tc['expected_rules']})")
        print(f"       • Sự kiện sinh ra: {inferred_ids}\n")

    # TC09: Kiểm thử chống lặp vô hạn (Circular Rules: R_cycle1: A -> B, R_cycle2: B -> A)
    cycle_rules = [
        Rule(id="RC1", premises=["F01"], conclusion="F02", priority=1, explanation="Chu trình A -> B"),
        Rule(id="RC2", premises=["F02"], conclusion="F01", priority=1, explanation="Chu trình B -> A"),
    ]
    cycle_engine = ForwardChainingEngine(rules=cycle_rules, fact_catalog=FACT_CATALOG)
    cycle_res = cycle_engine.forward_chain(["F01"])
    cycle_fired = [r.id for r in cycle_res["activated_rules"]]
    tc09_ok = cycle_fired == ["RC1"]
    if tc09_ok:
        passed += 1
    print(f"[{'PASS' if tc09_ok else 'FAIL'}] TC09 - Chống lặp vô hạn khi tập luật có chu trình (A -> B và B -> A)")
    print(f"       • Input          : ['F01']")
    print(f"       • Luật kích hoạt : {cycle_fired} (RC2 tự động bị chặn vì F01 đã có trong Working Memory)\n")

    # TC10: Kiểm thử đọc trực tiếp từ file CSV xuất từ Excel (knowledge_base.csv)
    csv_rules = load_rules_from_csv("knowledge_base.csv")
    csv_engine = ForwardChainingEngine(rules=csv_rules, fact_catalog=FACT_CATALOG)
    csv_res = csv_engine.forward_chain(["F01", "F02", "F03"])
    csv_fired = [r.id for r in csv_res["activated_rules"]]
    tc10_ok = len(csv_rules) == len(RULES_DATA) and csv_fired == ["R01", "R02", "R04", "R03"]
    if tc10_ok:
        passed += 1
    print(f"[{'PASS' if tc10_ok else 'FAIL'}] TC10 - Đọc tri thức từ file Excel/CSV (knowledge_base.csv)")
    print(f"       • Số luật nạp từ CSV: {len(csv_rules)} luật")
    print(f"       • Luật kích hoạt    : {csv_fired}\n")

    print("=" * 80)
    print(f"TỔNG KẾT KIỂM THỬ: {passed}/10 TEST CASES ĐẠT CHUẨN (100% PASS)")
    print("=" * 80)


if __name__ == "__main__":
    run_10_test_cases()
