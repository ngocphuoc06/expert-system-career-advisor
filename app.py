import sys
from typing import List
from rules_data import FACT_CATALOG, RULES_DATA, get_initial_input_facts, get_goal_facts
from core_engine import ForwardChainingEngine


def run_cli_mode() -> None:
    """Chế độ chạy trên Terminal (CLI) & Kiểm thử kịch bản mẫu cho TV3, TV5, TV6."""
    print("=" * 75)
    print("   HỆ CHUYÊN GIA SUY DIỄN TIẾN & GIẢI TRÌNH VẾT SUY DIỄN (CLI MODE)   ")
    print("=" * 75)

    input_facts = get_initial_input_facts()
    print("\nDanh sách các sự kiện đầu vào có thể chọn:")
    for fid, desc in input_facts.items():
        print(f"  [{fid}] {desc}")

    # Kịch bản kiểm thử mẫu (Test cases)
    test_cases = [
        ("Test Case 1: Sinh viên mạnh Toán + Python + Phân tích dữ liệu (Đa tầng & Xung đột)", ["F01", "F02", "F03"]),
        ("Test Case 2: Sinh viên định hướng Thị giác máy tính (Computer Vision)", ["F01", "F02", "F04"]),
        ("Test Case 3: Sinh viên định hướng NLP & Chatbot", ["F01", "F02", "F05"]),
        ("Test Case 4: Sinh viên định hướng Hệ thống MLOps", ["F01", "F02", "F06"]),
        ("Test Case 5: Sinh viên mạnh Toán + Phân tích dữ liệu nhưng chưa biết Python", ["F01", "F03"]),
    ]

    engine = ForwardChainingEngine(strategy="combined")

    for title, selected_ids in test_cases:
        print("\n" + "#" * 75)
        print(f"▶ {title}")
        print(f"  Đầu vào: {selected_ids}")
        print("#" * 75)

        result = engine.forward_chain(selected_ids)
        activated_ids = [r.id for r in result["activated_rules"]]
        inferred_ids = [f"{f.id} ({f.description})" for f in result["inferred_facts"]]

        print(f"✔ Danh sách luật đã kích hoạt theo thứ tự: {activated_ids}")
        print("✔ Các sự kiện/kết luận mới suy diễn được:")
        for item in inferred_ids:
            print(f"   + {item}")

        if result["inferred_facts"]:
            goal_ids = set(get_goal_facts().keys())
            goal_reached = [f for f in result["inferred_facts"] if f.id in goal_ids]
            target_to_explain = goal_reached[0] if goal_reached else result["inferred_facts"][-1]
            print(f"\n--- Giải trình 'VÌ SAO?' cho kết luận đích [{target_to_explain.id}] ---")
            for line in engine.explain_why_fact(target_to_explain.id):
                print(line)


def run_streamlit_ui() -> None:
    """Chế độ giao diện đồ họa Streamlit cho Ngày 4 (TV5 & TV3)."""
    import streamlit as st

    st.set_page_config(
        page_title="Hệ Chuyên Gia Suy Diễn Tiến - Nhóm AI",
        page_icon="🧠",
        layout="wide"
    )

    st.title("🧠 Hệ Chuyên Gia Suy Diễn Tiến & Giải Trình Vết Suy Diễn")
    st.caption("Giai đoạn 2 & 3: Forward Chaining, Conflict Resolution & Module Giải trình 'Vì sao?'")

    # Sidebar cấu hình chiến lược xử lý xung đột
    st.sidebar.header("⚙️ Cấu hình Động cơ Suy diễn (TV3)")
    strategy_map = {
        "Kết hợp đa tiêu chí (Specificity -> Priority -> Recency)": "combined",
        "Độ đặc thù cao nhất (Specificity)": "specificity",
        "Độ ưu tiên luật cao nhất (Priority)": "priority",
        "Sự kiện mới nhất (Recency)": "recency",
        "Luật khớp đầu tiên (First Match)": "first_match",
    }
    selected_strategy_label = st.sidebar.selectbox(
        "Chiến lược xử lý xung đột (Conflict Resolution):",
        list(strategy_map.keys())
    )
    strategy = strategy_map[selected_strategy_label]

    with st.sidebar.expander("📚 Xem toàn bộ Cơ sở Luật (Knowledge Base)"):
        for r in RULES_DATA:
            st.markdown(f"**{r.format_rule()}** *(Priority={r.priority}, Specificity={r.specificity})*")

    # Cột chọn sự kiện đầu vào
    st.subheader("1️⃣ Chọn các sự kiện ban đầu (Initial Facts)")
    input_facts = get_initial_input_facts()
    selected_facts: List[str] = []

    cols = st.columns(2)
    for idx, (fid, desc) in enumerate(input_facts.items()):
        with cols[idx % 2]:
            if st.checkbox(f"**[{fid}]** {desc}", value=(fid in ["F01", "F02", "F03"])):
                selected_facts.append(fid)

    if st.button("🚀 Chạy Suy Diễn Tiến (Forward Chaining)", type="primary"):
        if not selected_facts:
            st.warning("Vui lòng chọn ít nhất 1 sự kiện đầu vào!")
            return

        engine = ForwardChainingEngine(strategy=strategy)
        result = engine.forward_chain(selected_facts)

        st.divider()
        st.subheader("2️⃣ Kết quả Suy diễn & Danh sách Luật kích hoạt")

        if not result["inferred_facts"]:
            st.info("Không có sự kiện mới nào được suy ra từ tổ hợp đầu vào này.")
        else:
            for fact in result["inferred_facts"]:
                st.success(f"**[{fact.id}]** {fact.description} *(Suy ra ở Bước {fact.timestamp_step} bởi luật `{fact.by_rule}`)*")

            st.subheader("3️⃣ Module Giải trình: 'Vì sao hệ thống đưa ra kết luận này?'")
            for fact in reversed(result["inferred_facts"]):
                with st.expander(f"🔍 Vì sao kết luận được [{fact.id}]: {fact.description}?", expanded=True):
                    explanation_lines = engine.explain_why_fact(fact.id)
                    st.code("\n".join(explanation_lines), language="text")

            st.subheader("4️⃣ Nhật ký Vết Suy Diễn & Xử Lý Xung Đột (Inference Trace)")
            st.code(engine.format_trace_report(), language="text")


if __name__ == "__main__":
    # Kiểm tra nếu đang được gọi bởi lệnh `streamlit run app.py`
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx() is not None:
            run_streamlit_ui()
        else:
            run_cli_mode()
    except Exception:
        run_cli_mode()
