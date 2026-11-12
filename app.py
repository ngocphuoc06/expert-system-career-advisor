from typing import Dict, List
from rules_data import RULES_DATA, get_initial_input_facts, get_goal_facts
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
    st.caption("Nhập thông tin học sinh, nhận định hướng nghề nghiệp và xem hệ thống suy luận như thế nào.")

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

    st.subheader("1️⃣ Thông tin học sinh")
    st.info(
        "Điểm số được lưu để tham khảo trong hồ sơ, chưa tham gia suy diễn vì cơ sở luật "
        "hiện tại chưa định nghĩa ngưỡng điểm. Hãy chọn các năng lực và sở thích bên dưới "
        "để làm căn cứ cho hệ chuyên gia."
    )

    input_facts = get_initial_input_facts()
    goal_facts = get_goal_facts()
    descriptions = {**input_facts, **goal_facts}
    submitted = False
    selected_facts: List[str] = []
    scores: Dict[str, float] = {}
    student_name = ""

    with st.form("student_profile"):
        student_name = st.text_input("Tên học sinh (không bắt buộc)")
        enter_scores = st.checkbox("Bổ sung điểm số tham khảo")
        if enter_scores:
            score_cols = st.columns(3)
            for col, subject in zip(score_cols, ("Toán", "Tin học", "Tiếng Anh")):
                with col:
                    scores[subject] = st.number_input(
                        f"Điểm {subject}",
                        min_value=0.0,
                        max_value=10.0,
                        value=0.0,
                        step=0.5,
                    )

        st.markdown("**Chọn những năng lực và sở thích phù hợp:**")
        cols = st.columns(2)
        for idx, (fid, desc) in enumerate(input_facts.items()):
            with cols[idx % 2]:
                if st.checkbox(f"**[{fid}]** {desc}", key=f"profile_{fid}"):
                    selected_facts.append(fid)

        submitted = st.form_submit_button("🚀 Nhận tư vấn")

    if submitted:
        st.session_state.pop("last_recommendation", None)
        if not selected_facts:
            st.session_state["recommendation_error"] = "Vui lòng chọn ít nhất một năng lực hoặc sở thích."
        else:
            st.session_state.pop("recommendation_error", None)
            engine = ForwardChainingEngine(strategy=strategy)
            result = engine.forward_chain(selected_facts)
            recommendation_ids = [
                fact.id for fact in result["inferred_facts"] if fact.id in goal_facts
            ]
            st.session_state["last_recommendation"] = {
                "student_name": student_name.strip(),
                "scores": scores,
                "strategy_label": selected_strategy_label,
                "inferred_facts": [
                    {
                        "id": fact.id,
                        "description": fact.description,
                        "timestamp_step": fact.timestamp_step,
                        "by_rule": fact.by_rule,
                    }
                    for fact in result["inferred_facts"]
                ],
                "recommendation_ids": recommendation_ids,
                "explanations": {
                    fact_id: engine.explain_why_fact(fact_id)
                    for fact_id in recommendation_ids
                },
                "trace_report": engine.format_trace_report(),
            }

    if "recommendation_error" in st.session_state:
        st.warning(st.session_state["recommendation_error"])

    recommendation = st.session_state.get("last_recommendation")
    if recommendation:
        st.divider()
        st.subheader("2️⃣ Kết quả tư vấn")
        if recommendation["student_name"]:
            st.write(f"**Học sinh:** {recommendation['student_name']}")
        if recommendation["scores"]:
            score_summary = " · ".join(
                f"{subject}: {score:g}/10"
                for subject, score in recommendation["scores"].items()
            )
            st.write(f"**Điểm tham khảo:** {score_summary}")
        st.caption(f"Chiến lược xử lý xung đột: {recommendation['strategy_label']}")

        if recommendation["recommendation_ids"]:
            for fact_id in recommendation["recommendation_ids"]:
                st.success(f"**[{fact_id}]** {descriptions[fact_id]}")

            st.subheader("3️⃣ Vì sao hệ thống đưa ra khuyến nghị này?")
            selected_goal = st.selectbox(
                "Chọn khuyến nghị cần giải thích:",
                recommendation["recommendation_ids"],
                format_func=lambda fact_id: f"[{fact_id}] {descriptions[fact_id]}",
            )
            st.code(
                "\n".join(recommendation["explanations"][selected_goal]),
                language="text",
            )
        elif recommendation["inferred_facts"]:
            st.info("Hệ thống suy ra được dữ kiện trung gian nhưng chưa đủ căn cứ để đưa ra ngành nghề cụ thể.")
            for fact in recommendation["inferred_facts"]:
                st.write(f"- **[{fact['id']}]** {fact['description']}")
        else:
            st.info("Chưa có luật nào được kích hoạt. Hãy thử chọn thêm năng lực hoặc sở thích.")

        with st.expander("Xem nhật ký vết suy diễn và xử lý xung đột"):
            st.code(recommendation["trace_report"], language="text")


if __name__ == "__main__":
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except ModuleNotFoundError as exc:
        if exc.name != "streamlit":
            raise
        run_cli_mode()
    else:
        if get_script_run_ctx() is not None:
            run_streamlit_ui()
        else:
            run_cli_mode()
