
import csv
from typing import Dict, List
from structs import Rule


# 1. Danh mục các Sự kiện (Facts) được mã hóa từ bảng Excel
# Phân loại rõ: Sự kiện ban đầu (Triệu chứng/Đầu vào), Sự kiện trung gian, và Kết luận đích.
FACT_CATALOG: Dict[str, str] = {
    # Sự kiện đầu vào (Initial Facts / Quan sát từ người dùng)
    "F01": "Yêu thích Toán học (Đại số tuyến tính, Xác suất thống kê)",
    "F02": "Thành thạo lập trình Python cơ bản",
    "F03": "Thích phân tích dữ liệu, tìm quy luật từ bảng biểu",
    "F04": "Đam mê xử lý hình ảnh, video và thị giác",
    "F05": "Quan tâm đến ngôn ngữ tự nhiên, chatbot và dịch máy",
    "F06": "Có tư duy hệ thống, thích tối ưu hóa hạ tầng & triển khai mô hình",

    # Sự kiện trung gian (Intermediate Facts - được suy diễn ở bước giữa)
    "F07": "Có nền tảng cốt lõi về Máy học (Machine Learning Foundation)",
    "F08": "Có năng lực xử lý dữ liệu có cấu trúc (Structured Data Analytics)",
    "F09": "Có năng lực nghiên cứu Học sâu (Deep Learning Readiness)",

    # Sự kiện kết luận (Goal / Conclusion Facts)
    "F10": "Định hướng phù hợp: Khoa học Dữ liệu (Data Scientist)",
    "F11": "Định hướng phù hợp: Kỹ sư Thị giác Máy tính (Computer Vision Engineer)",
    "F12": "Định hướng phù hợp: Kỹ sư Xử lý Ngôn ngữ Tự nhiên & LLM (NLP Engineer)",
    "F13": "Định hướng phù hợp: Kỹ sư MLOps & Hệ thống AI (MLOps Engineer)",
}


# 2. Tập Luật sản xuất (Production Rules) chuẩn hóa từ Excel
# Thiết kế có chủ đích gồm:
# - Suy diễn bắc cầu nhiều bước (ví dụ: F01 + F02 -> F07; sau đó F07 + F03 -> F08; F08 -> F10)
# - Nhiều luật cùng thỏa mãn để kiểm thử cơ chế Xử lý xung đột (Conflict Resolution) của TV3
RULES_DATA: List[Rule] = [
    Rule(
        id="R01",
        premises=["F01", "F02"],
        conclusion="F07",
        priority=2,
        explanation="Khi sinh viên vừa giỏi Toán (Xác suất, Đại số) vừa biết lập trình Python thì đã đủ nền tảng cốt lõi để học Máy học (Machine Learning)."
    ),
    Rule(
        id="R02",
        premises=["F07", "F03"],
        conclusion="F08",
        priority=2,
        explanation="Có nền tảng Máy học (F07) kết hợp đam mê phân tích số liệu bảng biểu (F03) sẽ hình thành năng lực phân tích dữ liệu có cấu trúc (F08)."
    ),
    Rule(
        id="R03",
        premises=["F07", "F01"],
        conclusion="F09",
        priority=1,
        explanation="Có nền tảng Máy học (F07) và nền tảng Toán vững chắc (F01) cho phép tiếp cận các mô hình Mạng nơ-ron và Học sâu (Deep Learning - F09)."
    ),
    Rule(
        id="R04",
        premises=["F07", "F08", "F03"],
        conclusion="F10",
        priority=3,
        explanation="Hội tụ nền tảng Máy học (F07), năng lực phân tích dữ liệu cấu trúc (F08) và đam mê số liệu (F03) dẫn tới kết luận phù hợp nhất là Khoa học Dữ liệu (Data Scientist - F10)."
    ),
    Rule(
        id="R05",
        premises=["F09", "F04"],
        conclusion="F11",
        priority=3,
        explanation="Sẵn sàng về Học sâu (F09) cộng với đam mê xử lý ảnh/video (F04) là tổ hợp đặc trưng của Kỹ sư Thị giác Máy tính (Computer Vision Engineer - F11)."
    ),
    Rule(
        id="R06",
        premises=["F09", "F05"],
        conclusion="F12",
        priority=3,
        explanation="Sẵn sàng về Học sâu (F09) cộng với đam mê ngôn ngữ/chatbot (F05) dẫn đến định hướng Kỹ sư Xử lý Ngôn ngữ Tự nhiên & LLM (NLP Engineer - F12)."
    ),
    Rule(
        id="R07",
        premises=["F07", "F02", "F06"],
        conclusion="F13",
        priority=2,
        explanation="Có nền tảng Máy học (F07), kỹ năng lập trình Python (F02) và tư duy hạ tầng hệ thống (F06) rất phù hợp với vị trí Kỹ sư MLOps (F13)."
    ),
    Rule(
        id="R08",
        premises=["F01", "F03"],
        conclusion="F08",
        priority=1,
        explanation="Có tư duy Toán học (F01) kết hợp sở thích phân tích bảng biểu (F03) cũng bước đầu hình thành năng lực xử lý dữ liệu có cấu trúc (F08)."
    ),
]


def get_initial_input_facts() -> Dict[str, str]:
    """
    Trả về danh sách các sự kiện đầu vào (Initial Facts) để hiển thị cho người dùng chọn trên UI.
    (Là các sự kiện xuất hiện ở vế IF nhưng không phải là kết luận của luật nào).
    """
    conclusions = {r.conclusion for r in RULES_DATA}
    all_premises = {p for r in RULES_DATA for p in r.premises}
    return {
        fid: desc
        for fid, desc in FACT_CATALOG.items()
        if fid in all_premises and fid not in conclusions
    }


def get_goal_facts() -> Dict[str, str]:
    """
    Trả về danh sách các sự kiện Kết luận Đích (Goal Facts):
    (Là các sự kiện xuất hiện ở vế THEN nhưng không làm tiền đề IF cho luật nào khác).
    """
    conclusions = {r.conclusion for r in RULES_DATA}
    all_premises = {p for r in RULES_DATA for p in r.premises}
    return {
        fid: desc
        for fid, desc in FACT_CATALOG.items()
        if fid in conclusions and fid not in all_premises
    }


def load_rules_from_csv(csv_path: str) -> List[Rule]:
    """
    Hàm tiện ích giúp TV3 đọc trực tiếp file CSV xuất từ Excel của TV1, TV2.
    Định dạng cột CSV: id, premises (cách nhau bởi dấu phẩy), conclusion, priority, explanation
    Ví dụ dòng CSV: R01,"F01,F02",F07,2,"Giải thích luật R01"
    """
    loaded_rules: List[Rule] = []
    with open(csv_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            premises = [p.strip() for p in row["premises"].split(",") if p.strip()]
            loaded_rules.append(
                Rule(
                    id=row["id"].strip(),
                    premises=premises,
                    conclusion=row["conclusion"].strip(),
                    priority=int(row.get("priority", 1) or 1),
                    explanation=row.get("explanation", "").strip(),
                )
            )
    return loaded_rules
