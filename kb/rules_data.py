"""
rules_data.py  -  CO SO TRI THUC (Knowledge Base) CHO HE CHUYEN GIA TU VAN CHON NGANH THPT

NGUON SU THAT DUY NHAT (single source of truth): moi bang trong bao cao (luat, ma nganh,
khuyen nghi) duoc SINH TU FILE NAY -> khong the "venh ma" giua danh muc, luat va ket luan.

Quy uoc:
  * Facts sinh ra boi luat luon la TAP HOP (set) co CF:  The_Manh_Khoi, Ma_Holland,
    Nhom_Nganh_Phu_Hop, Khuyen_Nghi_Chinh_Thuc.  Phan_Khuc_Diem la don tri (3 luat loai tru nhau).
  * Priority (thu tu chay) tach biet voi CF (do tin cay).  Moi tang co dai Priority rieng, KHONG chong lan.
  * Cac nguong 26.5 / 23.0 / 8.0 ... la QUY UOC KY THUAT CUA NHOM, khong phai nguong tuyen sinh chinh thuc.
"""
import json, re

VERSION = "v3"

# ----------------------------------------------------------------------------------------
# 1. ONTOLOGY
# ----------------------------------------------------------------------------------------
SCORE_VARS = ["Diem_Toan", "Diem_Ly", "Diem_Hoa", "Diem_Sinh", "Diem_Tin",
              "Diem_Van", "Diem_Su", "Diem_Dia", "Diem_Anh", "Diem_Ve"]

SO_THICH_VALUES = ["May_Moc", "Lap_Trinh", "Nghien_Cuu", "Sang_Tao", "Giao_Tiep", "Giang_Day",
                   "Kinh_Doanh", "Con_So_Du_Lieu", "Cham_Soc_Suc_Khoe", "Tranh_Bien_Luat"]
NANG_LUC_VALUES = ["Tu_Duy_Logic", "Thao_Tac_Ky_Thuat", "Tham_My_Nghe_Thuat",
                   "Ngon_Ngu_Dien_Dat", "To_Chuc_Lanh_Dao", "Phan_Tich_Chi_Tiet"]
KHOI_VALUES = ["KHOI_A00", "KHOI_A01", "KHOI_B00", "KHOI_C00", "KHOI_D01", "KHOI_H00", "KHOI_V00"]
HOLLAND_VALUES = ["R_REALISTIC", "I_INVESTIGATIVE", "A_ARTISTIC", "S_SOCIAL",
                  "E_ENTERPRISING", "C_CONVENTIONAL"]
PHAN_KHUC_VALUES = ["TOP_DAU", "KHA_TOT", "AN_TOAN"]

# Nguong phan khuc (quy uoc nhom, de de tham so hoa / hieu chinh)
SEG_TOP = 26.5
SEG_GOOD = 23.0

NHOM = {  # 10 nhom nganh noi bo (khong thay the ma tuyen sinh)
    "NHOM_CNTT": "Máy tính và Công nghệ thông tin",
    "NHOM_KY_THUAT": "Kỹ thuật và Công nghệ kỹ thuật",
    "NHOM_KINH_TE_QT": "Kinh tế, Kinh doanh và Quản lý",
    "NHOM_LOGISTICS": "Logistics và Quản lý chuỗi cung ứng",
    "NHOM_Y_DUOC": "Khoa học sức khỏe và khoa học sự sống",
    "NHOM_SU_PHAM": "Giáo dục và Sư phạm",
    "NHOM_NGON_NGU_XH": "Ngôn ngữ, Nhân văn và Khoa học xã hội",
    "NHOM_PHAP_LUAT": "Pháp luật",
    "NHOM_NGHE_THUAT": "Nghệ thuật và Mỹ thuật ứng dụng",
    "NHOM_HOA_MOI_TRUONG": "Hóa học, Vật liệu và Môi trường",
}

ONTOLOGY = {
    # ten bien : (lop, kieu, mien gia tri)
    "Diem_*": ("initial", "float|null", "[0,10]; kem loai diem (hoc ba/thi thu/thi chinh thuc)"),
    "So_Thich": ("initial", "set[str]", SO_THICH_VALUES),
    "Nang_Luc_Noi_Troi": ("initial", "str", NANG_LUC_VALUES),
    "To_Hop_Du_Kien": ("initial", "str", "ma to hop dung de tinh tong (A00, A01, B00, C00, D01, D07, B08, X06, X26)"),
    "Tong_Diem_Du_Kien": ("initial(derived by code)", "float|null", "[0,30]; = tong 3 mon cung loai diem"),
    "The_Manh_Khoi": ("tier1", "set[str]+CF", KHOI_VALUES),
    "Ma_Holland": ("tier1", "set[str]+CF", HOLLAND_VALUES),
    "Phan_Khuc_Diem": ("tier1", "str+CF (don tri)", PHAN_KHUC_VALUES),
    "Nhom_Nganh_Phu_Hop": ("tier2", "set[str]+CF", list(NHOM)),
    "Khuyen_Nghi_Chinh_Thuc": ("tier3/fallback", "set[rec_key]+CF", "xem RECS"),
}
DERIVED_ATTRS = ["The_Manh_Khoi", "Ma_Holland", "Phan_Khuc_Diem", "Nhom_Nganh_Phu_Hop", "Khuyen_Nghi_Chinh_Thuc"]

COMBINATIONS = {  # to hop -> 3 bien diem (H00/V00 co mon nang khieu: KHONG tinh tong o day)
    "A00": ("Diem_Toan", "Diem_Ly", "Diem_Hoa"),
    "A01": ("Diem_Toan", "Diem_Ly", "Diem_Anh"),
    "B00": ("Diem_Toan", "Diem_Hoa", "Diem_Sinh"),
    "C00": ("Diem_Van", "Diem_Su", "Diem_Dia"),
    "D01": ("Diem_Toan", "Diem_Van", "Diem_Anh"),
    "D07": ("Diem_Toan", "Diem_Hoa", "Diem_Anh"),
    "B08": ("Diem_Toan", "Diem_Sinh", "Diem_Anh"),
    "X06": ("Diem_Toan", "Diem_Ly", "Diem_Tin"),
    "X26": ("Diem_Toan", "Diem_Tin", "Diem_Anh"),
}

def tong_diem(student, to_hop):
    """Tong 3 mon cua to hop; None neu thieu bat ky mon nao (khong tu coi null = 0)."""
    if to_hop not in COMBINATIONS:
        return None
    vals = [student.get(v) for v in COMBINATIONS[to_hop]]
    if any(v is None for v in vals):
        return None
    return round(sum(vals), 2)

# ----------------------------------------------------------------------------------------
# 2. DANH MUC NGANH (nguon duy nhat cho ma nganh)
#    ma_hien_hanh = ma 7 chu so (TT 09/2022 - dung cho tuyen sinh 2026, tra cuu diem chuan lich su)
#    ma_moi       = ma 6 chu so (TT 74/2026, ap dung khoa tuyen sinh tu 01/01/2027)
#    xac_minh     = True neu ma_moi da doi chieu voi van ban/Phu luc TT 74/2026 (xem bao cao muc 2.3.1)
#    ma_moi=None  = nganh bi GOP/DOI TEN, khong duoc suy ma bang cach bo chu so 7.
# ----------------------------------------------------------------------------------------
def _m(ten, cu, moi, ok, ghi_chu=""):
    return {"ten": ten, "ma_hien_hanh": cu, "ma_moi": moi, "xac_minh_tt74": ok, "ghi_chu": ghi_chu}

MAJORS = {
    # --- Nhom CNTT
    "KHMT": _m("Khoa học máy tính", "7480101", "480101", True),
    "MMT":  _m("Mạng máy tính và truyền thông dữ liệu", "7480102", "480102", True),
    "KTPM": _m("Kỹ thuật phần mềm", "7480103", "480103", True),
    "HTTT": _m("Hệ thống thông tin", "7480104", "480104", True),
    "KTMT": _m("Kỹ thuật máy tính", "7480106", "480106", True),
    "AI":   _m("Trí tuệ nhân tạo", "7480107", "480107", True),
    "CNTT": _m("Công nghệ thông tin", "7480201", "480201", False, "chưa đối chiếu Phụ lục I"),
    "KHDL": _m("Khoa học dữ liệu", "7480109", "460108", True, "chuyển sang lĩnh vực 46 (Toán và thống kê) theo TT 74/2026"),
    # --- Ky thuat
    "CKDT": _m("Công nghệ kỹ thuật cơ điện tử", "7510203", "510203", False),
    "DDT":  _m("Công nghệ kỹ thuật điện, điện tử", "7510301", "510301", False),
    "CNKT_DKTDH": _m("Công nghệ kỹ thuật điều khiển và tự động hóa", "7510303", "510303", False),
    "KT_DKTDH": _m("Kỹ thuật điều khiển và tự động hóa", "7520216", "520216", True),
    "OTO":  _m("Công nghệ kỹ thuật ô tô", "7510205", "510205", False),
    # --- Kinh te
    "KTQT": _m("Kinh tế quốc tế", "7310106", "310106", True),
    "KTDT": _m("Kinh tế đầu tư", "7310104", "310104", True),
    "QTKD": _m("Quản trị kinh doanh", "7340101", "340101", True, "TT 74 gộp một số ngành quản trị vào ngành này"),
    "MKT":  _m("Marketing", "7340115", "340115", True),
    "TCNH": _m("Tài chính - Ngân hàng", "7340201", "340201", True),
    "KT":   _m("Kế toán", "7340301", "340301", False),
    # --- Logistics
    "LOG":  _m("Logistics và Quản lý chuỗi cung ứng", "7510605", "510605", False),
    # --- Y duoc
    "YK":   _m("Y khoa", "7720101", "720101", True),
    "DUOC": _m("Dược học", "7720201", "720201", True),
    "DD":   _m("Điều dưỡng", "7720301", "720301", False),
    "YHDP": _m("Y học dự phòng", "7720110", None, False, "cần đối chiếu: TT 74 có sắp xếp lại nhóm Y học"),
    "XN":   _m("Kỹ thuật xét nghiệm y học", "7720601", "720601", False),
    # --- Su pham
    "SP_TOAN": _m("Sư phạm Toán học", "7140209", "140209", True),
    "SP_TIN":  _m("Sư phạm Tin học", "7140210", "140210", True),
    "SP_VAN":  _m("Sư phạm Ngữ văn", "7140217", "140217", False),
    "SP_NN":   _m("Sư phạm Tiếng Anh", "7140231", None, False, "TT 74 gộp thành ngành 'Sư phạm tiếng nước ngoài'; mã mới chưa xác minh"),
    "GDTH":    _m("Giáo dục Tiểu học", "7140202", "140202", True),
    # --- Ngon ngu - XH
    "NNA":  _m("Ngôn ngữ Anh", "7220201", "220201", False),
    "QHQT": _m("Quan hệ quốc tế", "7310206", "310206", False),
    "TLH":  _m("Tâm lý học", "7310401", "310401", False),
    "BC":   _m("Báo chí", "7320101", "320101", False),
    # --- Phap luat
    "LUAT":  _m("Luật", "7380101", "380101", True),
    "LUAT_KT": _m("Luật kinh tế", "7380107", "380107", False),
    # --- Nghe thuat
    "TKDH": _m("Thiết kế đồ họa", "7210403", "210403", False),
    "TKTT": _m("Thiết kế thời trang", "7210404", "210404", False),
    "NTS":  _m("Nghệ thuật số", "7210408", "210408", False, "mã theo bản thảo gốc, CHƯA xác minh"),
    # --- Hoa - Moi truong
    "CNKT_HOA": _m("Công nghệ kỹ thuật hóa học", "7510401", "510401", False),
    "KT_HOA":   _m("Kỹ thuật hóa học", "7520301", "520301", True),
    "VL":   _m("Kỹ thuật vật liệu", "7520309", "520309", True),
    "MT":   _m("Kỹ thuật môi trường", "7520320", "520320", False),
}

# Ket luan Tang 3 (rec) - chi THAM CHIEU ma nganh bang khoa trong MAJORS => khong the lech ma
def _r(nhom, nganh, truong, mo_ta=""):
    return {"ma_nhom": nhom, "nganh": nganh, "nhom_truong": truong, "mo_ta": mo_ta}

RECS = {
    "REC_CNTT_TOP": _r("NHOM_CNTT", ["KHMT", "AI"], "nhóm trường trọng điểm (điểm chuẩn cao)"),
    "REC_CNTT_UNG_DUNG": _r("NHOM_CNTT", ["KTPM", "HTTT", "CNTT"], "nhóm trường công lập khá và ứng dụng"),
    "REC_KT_TOP": _r("NHOM_KY_THUAT", ["KT_DKTDH", "CKDT"], "nhóm trường kỹ thuật trọng điểm"),
    "REC_KT_UNG_DUNG": _r("NHOM_KY_THUAT", ["CKDT", "DDT", "CNKT_DKTDH"], "nhóm trường kỹ thuật công lập khá và ứng dụng"),
    "REC_KTE_QT_TOP": _r("NHOM_KINH_TE_QT", ["KTQT", "KTDT"], "nhóm trường kinh tế - ngoại thương trọng điểm"),
    "REC_KTE_QTKD": _r("NHOM_KINH_TE_QT", ["QTKD", "MKT", "TCNH", "KT"], "nhóm trường kinh tế công lập khá và ứng dụng"),
    "REC_LOGISTICS": _r("NHOM_LOGISTICS", ["LOG"], "trường có chương trình Logistics - tra cứu ADMISSION_REFERENCE"),
    "REC_YD_TOP": _r("NHOM_Y_DUOC", ["YK", "DUOC"], "trường Y - Dược trọng điểm",
                     "Nghề y, dược chỉ hành nghề sau khi đáp ứng điều kiện đào tạo, thực hành và chứng chỉ hành nghề."),
    "REC_YD_CHUNG": _r("NHOM_Y_DUOC", ["DUOC", "DD", "XN", "YHDP"], "trường Y - Dược công lập khá và ứng dụng",
                       "Nghề y, dược chỉ hành nghề sau khi đáp ứng điều kiện đào tạo, thực hành và chứng chỉ hành nghề."),
    "REC_SP_TOAN_TIN": _r("NHOM_SU_PHAM", ["SP_TOAN", "SP_TIN"], "trường sư phạm trọng điểm"),
    "REC_SP_MON": _r("NHOM_SU_PHAM", ["SP_VAN", "SP_NN", "GDTH", "SP_TOAN"], "trường sư phạm (chọn theo môn thế mạnh)"),
    "REC_PL": _r("NHOM_PHAP_LUAT", ["LUAT", "LUAT_KT"], "trường có khoa Luật",
                 "Một số nghề luật đòi hỏi đào tạo nghề và chứng chỉ riêng."),
    "REC_NNXH": _r("NHOM_NGON_NGU_XH", ["NNA", "QHQT", "TLH", "BC"], "trường khoa học xã hội - nhân văn / ngoại ngữ"),
    "REC_NT_SO": _r("NHOM_NGHE_THUAT", ["TKDH", "NTS"], "trường mỹ thuật ứng dụng và công nghệ",
                    "Đối chiếu tổ hợp năng khiếu (H00/V00...) do từng trường công bố."),
    "REC_NT_DOHOA": _r("NHOM_NGHE_THUAT", ["TKDH", "TKTT"], "trường mỹ thuật ứng dụng",
                       "Đối chiếu tổ hợp năng khiếu (H00/V00...) do từng trường công bố."),
    "REC_HOA_MT": _r("NHOM_HOA_MOI_TRUONG", ["CNKT_HOA", "KT_HOA", "VL", "MT"], "trường kỹ thuật / khoa học tự nhiên"),
    # fallback (noi dung dong, xem render_rec trong engine)
    "REC_FB_NHOM": {"ma_nhom": None, "nganh": [], "nhom_truong": "", "mo_ta": "dynamic:nhom"},
    "REC_FB_HOLLAND": {"ma_nhom": None, "nganh": [], "nhom_truong": "", "mo_ta": "dynamic:holland"},
    "REC_INSUFFICIENT": {"ma_nhom": None, "nganh": [], "nhom_truong": "", "mo_ta": "dynamic:insufficient"},
}

HOLLAND_HINTS = {  # dung cho luat du phong R45
    "R_REALISTIC": ["NHOM_KY_THUAT", "NHOM_LOGISTICS"],
    "I_INVESTIGATIVE": ["NHOM_CNTT", "NHOM_HOA_MOI_TRUONG", "NHOM_Y_DUOC"],
    "A_ARTISTIC": ["NHOM_NGHE_THUAT"],
    "S_SOCIAL": ["NHOM_SU_PHAM", "NHOM_NGON_NGU_XH"],
    "E_ENTERPRISING": ["NHOM_KINH_TE_QT", "NHOM_PHAP_LUAT"],
    "C_CONVENTIONAL": ["NHOM_KINH_TE_QT", "NHOM_LOGISTICS"],
}

# Bang tra cuu tuyen sinh (SAO TU PHAN I - TV1 chiu trach nhiem xac minh). Chi de THAM CHIEU.
ADMISSION_REFERENCE = [
    # truong, nganh(khoa MAJORS hoac ten), nam, phuong_thuc, thang, diem_chuan, so_sanh_duoc_voi_tong_3_mon
    ("HUIT", "CNTT", 2026, "THPT", 30, 20.00, True), ("HUIT", "AI", 2026, "THPT", 30, 20.50, True),
    ("HUIT", "KHDL", 2026, "THPT", 30, 19.00, True), ("HUIT", "QTKD", 2026, "THPT", 30, 20.50, True),
    ("HUIT", "MKT", 2026, "THPT", 30, 21.75, True), ("HUIT", "KT", 2026, "THPT", 30, 21.00, True),
    ("HUIT", "LUAT", 2026, "THPT", 30, 21.25, True), ("HUIT", "NNA", 2026, "THPT", 30, 22.50, True),
    ("HUIT", "CNKT_DKTDH", 2026, "THPT", 30, 23.00, True), ("HUIT", "LOG", 2026, "THPT", 30, 22.50, True),
    ("HCMUS", "KHMT", 2026, "TONG_HOP", 30, 29.32, False),  # KHMT chuong trinh tien tien
    ("HCMUS", "AI", 2026, "TONG_HOP", 30, 28.68, False),
]

def admission_refs_for(rec_key):
    keys = set(RECS[rec_key]["nganh"])
    return [r for r in ADMISSION_REFERENCE if r[1] in keys]

# ----------------------------------------------------------------------------------------
# 3. DANH SACH LUAT
#    conds la danh sach (AND).  Toan tu:
#      ("ge"|"gt"|"lt"|"le", bien_so, nguong)   so sanh so (null => khong khop)
#      ("eq"|"has", thuoc_tinh, gia_tri)        gia tri co trong tap / bang
#      ("exists"|"empty", thuoc_tinh)           co / khong co fact nao
#      ("any", [cond..]) = OR (CF=max) ; ("all", [cond..]) = AND long ; ("not", cond) = phu dinh (NAF)
# ----------------------------------------------------------------------------------------
def ge(a, x): return ("ge", a, x)
def lt(a, x): return ("lt", a, x)
def eq(a, x): return ("eq", a, x)
def has(a, x): return ("has", a, x)
def any_(*c): return ("any", list(c))
def all_(*c): return ("all", list(c))
def not_(c): return ("not", c)

TT = "Phan_Khuc_Diem"; KH = "The_Manh_Khoi"; HL = "Ma_Holland"; NG = "Nhom_Nganh_Phu_Hop"
ST = "So_Thich"; NL = "Nang_Luc_Noi_Troi"; KN = "Khuyen_Nghi_Chinh_Thuc"

def R(id_, tier, pri, cf, conds, then, tpl, dep=None):
    return {"id": id_, "tier": tier, "priority": pri, "cf": cf, "conds": conds,
            "then": list(then), "template": tpl, "dep_group": dep}

RULES = [
 # ================= TANG 1 : TRUU TUONG HOA (Priority 81-95) =================
 R("R01", 1, 95, 0.95, [ge("Diem_Toan", 8.0), ge("Diem_Ly", 7.5), ge("Diem_Hoa", 7.5)], (KH, "KHOI_A00"),
   "Toán {Diem_Toan}, Lý {Diem_Ly}, Hóa {Diem_Hoa} đều đạt ngưỡng của luật (Toán ≥ 8,0; Lý, Hóa ≥ 7,5) nên có thế mạnh tổ hợp A00."),
 R("R02", 1, 94, 0.95, [ge("Diem_Toan", 8.0), ge("Diem_Ly", 7.5), ge("Diem_Anh", 7.5)], (KH, "KHOI_A01"),
   "Toán {Diem_Toan}, Lý {Diem_Ly}, Anh {Diem_Anh} đạt ngưỡng (Toán ≥ 8,0; Lý, Anh ≥ 7,5) nên có thế mạnh tổ hợp A01."),
 R("R03", 1, 93, 0.95, [ge("Diem_Toan", 7.5), ge("Diem_Hoa", 8.0), ge("Diem_Sinh", 8.0)], (KH, "KHOI_B00"),
   "Toán {Diem_Toan}, Hóa {Diem_Hoa}, Sinh {Diem_Sinh} đạt ngưỡng (Toán ≥ 7,5; Hóa, Sinh ≥ 8,0) nên có thế mạnh tổ hợp B00."),
 R("R04", 1, 92, 0.90, [ge("Diem_Van", 8.0), ge("Diem_Su", 7.5), ge("Diem_Dia", 7.5)], (KH, "KHOI_C00"),
   "Văn {Diem_Van}, Sử {Diem_Su}, Địa {Diem_Dia} đạt ngưỡng (Văn ≥ 8,0; Sử, Địa ≥ 7,5) nên có thế mạnh tổ hợp C00."),
 R("R05", 1, 91, 0.92, [ge("Diem_Toan", 7.5), ge("Diem_Van", 7.5), ge("Diem_Anh", 8.0)], (KH, "KHOI_D01"),
   "Toán {Diem_Toan}, Văn {Diem_Van}, Anh {Diem_Anh} đạt ngưỡng (Toán, Văn ≥ 7,5; Anh ≥ 8,0) nên có thế mạnh tổ hợp D01."),
 R("R06", 1, 90, 0.90, [ge("Diem_Ve", 8.0), ge("Diem_Van", 7.0)], (KH, "KHOI_H00"),
   "Vẽ {Diem_Ve} (≥ 8,0) và Văn {Diem_Van} (≥ 7,0) phù hợp hướng tổ hợp năng khiếu H00. Cần đối chiếu môn năng khiếu thực tế của từng trường."),
 R("R31", 1, 90, 0.90, [ge("Diem_Ve", 8.0), ge("Diem_Toan", 7.0), ge("Diem_Ly", 7.0)], (KH, "KHOI_V00"),
   "Vẽ {Diem_Ve} (≥ 8,0), Toán {Diem_Toan} và Lý {Diem_Ly} (≥ 7,0) phù hợp hướng tổ hợp năng khiếu V00. Cần đối chiếu quy định của từng trường."),
 R("R07", 1, 89, 0.90, [has(ST, "May_Moc"), eq(NL, "Thao_Tac_Ky_Thuat")], (HL, "R_REALISTIC"),
   "Sở thích máy móc kết hợp năng lực thao tác kỹ thuật gợi ý thiên hướng Thực tế (R) theo mô hình Holland (tham khảo, không phải trắc nghiệm chuẩn)."),
 R("R08", 1, 88, 0.90, [any_(has(ST, "Nghien_Cuu"), has(ST, "Lap_Trinh")), eq(NL, "Tu_Duy_Logic")], (HL, "I_INVESTIGATIVE"),
   "Sở thích nghiên cứu/lập trình ({So_Thich}) và năng lực tư duy logic gợi ý thiên hướng Nghiên cứu (I) theo Holland (tham khảo)."),
 R("R09", 1, 87, 0.88, [has(ST, "Sang_Tao"), eq(NL, "Tham_My_Nghe_Thuat")], (HL, "A_ARTISTIC"),
   "Sở thích sáng tạo kết hợp năng lực thẩm mỹ - nghệ thuật gợi ý thiên hướng Nghệ thuật (A) theo Holland (tham khảo)."),
 R("R10", 1, 86, 0.88, [any_(has(ST, "Giang_Day"), has(ST, "Giao_Tiep"), has(ST, "Cham_Soc_Suc_Khoe")), eq(NL, "Ngon_Ngu_Dien_Dat")], (HL, "S_SOCIAL"),
   "Sở thích giao tiếp/giảng dạy/chăm sóc ({So_Thich}) và khả năng diễn đạt tốt gợi ý thiên hướng Xã hội (S) theo Holland (tham khảo)."),
 R("R11", 1, 85, 0.88, [any_(has(ST, "Kinh_Doanh"), has(ST, "Tranh_Bien_Luat")), eq(NL, "To_Chuc_Lanh_Dao")], (HL, "E_ENTERPRISING"),
   "Sở thích kinh doanh/tranh biện ({So_Thich}) và năng lực tổ chức - lãnh đạo gợi ý thiên hướng Quản lý (E) theo Holland (tham khảo)."),
 R("R12", 1, 84, 0.85, [has(ST, "Con_So_Du_Lieu"), eq(NL, "Phan_Tich_Chi_Tiet")], (HL, "C_CONVENTIONAL"),
   "Sở thích làm việc với dữ liệu, con số và năng lực phân tích chi tiết gợi ý thiên hướng Nghiệp vụ (C) theo Holland (tham khảo)."),
 R("R13", 1, 83, 0.95, [ge("Tong_Diem_Du_Kien", SEG_TOP)], (TT, "TOP_DAU"),
   "Tổng điểm dự kiến {Tong} (tổ hợp {To_Hop}) ≥ 26,5 nên xếp phân khúc TOP_DAU (ngưỡng mô phỏng của nhóm, không phải ngưỡng tuyển sinh)."),
 R("R14", 1, 82, 0.95, [ge("Tong_Diem_Du_Kien", SEG_GOOD), lt("Tong_Diem_Du_Kien", SEG_TOP)], (TT, "KHA_TOT"),
   "Tổng điểm dự kiến {Tong} (tổ hợp {To_Hop}) trong [23,0; 26,5) nên xếp phân khúc KHA_TOT (ngưỡng mô phỏng của nhóm)."),
 R("R15", 1, 81, 0.95, [lt("Tong_Diem_Du_Kien", SEG_GOOD)], (TT, "AN_TOAN"),
   "Tổng điểm dự kiến {Tong} (tổ hợp {To_Hop}) < 23,0 nên xếp phân khúc AN_TOAN (ngưỡng mô phỏng của nhóm)."),
 # ================= TANG 2 : NHOM NGANH (Priority 68-78) =================
 R("R16", 2, 78, 0.90, [has(KH, "KHOI_A00"), has(HL, "I_INVESTIGATIVE"), ge("Diem_Tin", 8.0)], (NG, "NHOM_CNTT"),
   "Thế mạnh khối A00, thiên hướng Nghiên cứu (I) và Tin học {Diem_Tin} (≥ 8,0) cùng chỉ về nhóm Máy tính và CNTT.", dep="CNTT_I"),
 R("R17", 2, 77, 0.85, [has(KH, "KHOI_A01"), has(HL, "I_INVESTIGATIVE"), has(ST, "Lap_Trinh")], (NG, "NHOM_CNTT"),
   "Thế mạnh khối A01, thiên hướng Nghiên cứu (I) và sở thích lập trình củng cố sự phù hợp với nhóm Máy tính và CNTT.", dep="CNTT_I"),
 R("R21", 2, 76, 0.92, [has(KH, "KHOI_B00"), any_(has(HL, "I_INVESTIGATIVE"), has(HL, "S_SOCIAL")), has(ST, "Cham_Soc_Suc_Khoe")], (NG, "NHOM_Y_DUOC"),
   "Thế mạnh khối B00, thiên hướng Nghiên cứu/Xã hội và sở thích chăm sóc sức khỏe gợi ý nhóm Khoa học sức khỏe."),
 R("R18", 2, 75, 0.88, [any_(has(KH, "KHOI_A00"), has(KH, "KHOI_A01")), has(HL, "R_REALISTIC")], (NG, "NHOM_KY_THUAT"),
   "Thế mạnh Toán - Lý (A00/A01) kết hợp thiên hướng Thực tế (R) phù hợp nhóm Kỹ thuật và Công nghệ kỹ thuật."),
 R("R19", 2, 74, 0.85, [any_(has(KH, "KHOI_A01"), has(KH, "KHOI_D01")), any_(has(HL, "E_ENTERPRISING"), has(HL, "C_CONVENTIONAL"))], (NG, "NHOM_KINH_TE_QT"),
   "Nền tảng Toán - Anh (A01/D01) cùng thiên hướng Quản lý (E) hoặc Nghiệp vụ (C) phù hợp nhóm Kinh tế, Kinh doanh và Quản lý."),
 R("R20", 2, 73, 0.86, [any_(has(KH, "KHOI_A00"), has(KH, "KHOI_A01")), has(HL, "C_CONVENTIONAL"), has(ST, "Kinh_Doanh")], (NG, "NHOM_LOGISTICS"),
   "Tư duy Toán khối A, thiên hướng Nghiệp vụ (C) và hứng thú kinh doanh gợi ý nhóm Logistics và Chuỗi cung ứng."),
 R("R22", 2, 72, 0.88, [has(HL, "S_SOCIAL"), has(ST, "Giang_Day"), any_(has(KH, "KHOI_A00"), has(KH, "KHOI_C00"), has(KH, "KHOI_D01"))], (NG, "NHOM_SU_PHAM"),
   "Đam mê giảng dạy, thiên hướng Xã hội (S) trên nền học thuật khối A00/C00/D01 phù hợp nhóm Giáo dục và Sư phạm."),
 R("R32", 2, 71, 0.87, [any_(has(KH, "KHOI_D01"), has(KH, "KHOI_C00")), has(HL, "S_SOCIAL"), has(ST, "Giao_Tiep")], (NG, "NHOM_NGON_NGU_XH"),
   "Thế mạnh D01/C00, thiên hướng Xã hội (S) và sở thích giao tiếp phù hợp nhóm Ngôn ngữ, Nhân văn và Khoa học xã hội."),
 R("R23", 2, 70, 0.87, [any_(has(KH, "KHOI_C00"), has(KH, "KHOI_D01")), has(HL, "E_ENTERPRISING"), has(ST, "Tranh_Bien_Luat")], (NG, "NHOM_PHAP_LUAT"),
   "Năng lực lập luận khối C00/D01, thiên hướng Quản lý (E) và sở thích tranh biện phù hợp nhóm Pháp luật."),
 R("R33", 2, 69, 0.88, [any_(has(KH, "KHOI_A00"), has(KH, "KHOI_B00")), has(HL, "I_INVESTIGATIVE"), ge("Diem_Hoa", 8.0), has(ST, "Nghien_Cuu")], (NG, "NHOM_HOA_MOI_TRUONG"),
   "Khối A00/B00, thiên hướng Nghiên cứu (I), Hóa {Diem_Hoa} (≥ 8,0) và sở thích nghiên cứu phù hợp nhóm Hóa học, Vật liệu và Môi trường."),
 R("R24", 2, 68, 0.88, [any_(has(KH, "KHOI_H00"), has(KH, "KHOI_V00"), has(KH, "KHOI_D01")), has(HL, "A_ARTISTIC")], (NG, "NHOM_NGHE_THUAT"),
   "Thiên hướng Nghệ thuật (A) cùng thế mạnh H00/V00/D01 phù hợp nhóm Nghệ thuật và Mỹ thuật ứng dụng."),
 # ================= TANG 3 : KHUYEN NGHI (Priority 45-60) =================
 R("R25", 3, 60, 0.95, [has(NG, "NHOM_CNTT"), eq(TT, "TOP_DAU"), ge("Diem_Toan", 9.0)], (KN, "REC_CNTT_TOP"),
   "Nhóm CNTT, phân khúc TOP_DAU và Toán {Diem_Toan} (≥ 9,0) cho phép cân nhắc ngành mũi nhọn Khoa học máy tính, Trí tuệ nhân tạo ở nhóm trường điểm cao."),
 R("R34", 3, 59, 0.90, [has(NG, "NHOM_LOGISTICS")], (KN, "REC_LOGISTICS"),
   "Phù hợp nhóm Logistics và Quản lý chuỗi cung ứng, gợi ý ngành Logistics và Quản lý chuỗi cung ứng."),
 R("R26", 3, 58, 0.90, [has(NG, "NHOM_CNTT"), not_(all_(eq(TT, "TOP_DAU"), ge("Diem_Toan", 9.0)))], (KN, "REC_CNTT_UNG_DUNG"),
   "Phù hợp nhóm CNTT; với mức điểm hiện tại, gợi ý Kỹ thuật phần mềm, Hệ thống thông tin, Công nghệ thông tin ở nhóm trường công lập khá và ứng dụng."),
 R("R35", 3, 57, 0.92, [has(NG, "NHOM_Y_DUOC"), eq(TT, "TOP_DAU"), ge("Diem_Hoa", 8.5), ge("Diem_Sinh", 8.5)], (KN, "REC_YD_TOP"),
   "Nhóm Sức khỏe, phân khúc TOP_DAU, Hóa {Diem_Hoa} và Sinh {Diem_Sinh} (≥ 8,5) cho phép cân nhắc Y khoa, Dược học."),
 R("R27", 3, 56, 0.92, [has(NG, "NHOM_KY_THUAT"), eq(TT, "TOP_DAU")], (KN, "REC_KT_TOP"),
   "Nhóm Kỹ thuật và phân khúc TOP_DAU cho phép cân nhắc Kỹ thuật điều khiển và tự động hóa, Cơ điện tử ở nhóm trường kỹ thuật trọng điểm."),
 R("R37", 3, 55, 0.88, [has(NG, "NHOM_PHAP_LUAT")], (KN, "REC_PL"),
   "Phù hợp nhóm Pháp luật, gợi ý ngành Luật, Luật kinh tế. Một số nghề luật cần chứng chỉ riêng sau đào tạo."),
 R("R28", 3, 54, 0.92, [has(NG, "NHOM_KINH_TE_QT"), eq(TT, "TOP_DAU"), ge("Diem_Anh", 8.5)], (KN, "REC_KTE_QT_TOP"),
   "Nhóm Kinh tế, phân khúc TOP_DAU và Anh {Diem_Anh} (≥ 8,5) cho phép cân nhắc Kinh tế quốc tế, Kinh tế đầu tư ở nhóm trường kinh tế trọng điểm."),
 R("R38", 3, 53, 0.86, [has(NG, "NHOM_NGON_NGU_XH")], (KN, "REC_NNXH"),
   "Phù hợp nhóm Ngôn ngữ, Nhân văn và Khoa học xã hội, gợi ý Ngôn ngữ Anh, Quan hệ quốc tế, Tâm lý học, Báo chí."),
 R("R41", 3, 52, 0.85, [has(NG, "NHOM_KINH_TE_QT"), not_(all_(eq(TT, "TOP_DAU"), ge("Diem_Anh", 8.5)))], (KN, "REC_KTE_QTKD"),
   "Phù hợp nhóm Kinh tế; gợi ý Quản trị kinh doanh, Marketing, Tài chính - Ngân hàng, Kế toán ở nhóm trường công lập khá và ứng dụng."),
 R("R39", 3, 51, 0.87, [has(NG, "NHOM_HOA_MOI_TRUONG")], (KN, "REC_HOA_MT"),
   "Phù hợp nhóm Hóa học, Vật liệu và Môi trường, gợi ý Công nghệ kỹ thuật hóa học, Kỹ thuật vật liệu, Kỹ thuật môi trường."),
 R("R29", 3, 50, 0.90, [has(NG, "NHOM_SU_PHAM"), ge("Diem_Toan", 8.5), any_(eq(TT, "TOP_DAU"), eq(TT, "KHA_TOT"))], (KN, "REC_SP_TOAN_TIN"),
   "Thiên hướng Sư phạm, Toán {Diem_Toan} (≥ 8,5) và phân khúc khá trở lên phù hợp Sư phạm Toán học, Sư phạm Tin học."),
 R("R40", 3, 49, 0.88, [has(NG, "NHOM_KY_THUAT"), not_(eq(TT, "TOP_DAU"))], (KN, "REC_KT_UNG_DUNG"),
   "Phù hợp nhóm Kỹ thuật; gợi ý Cơ điện tử, Điện - Điện tử, Điều khiển và tự động hóa ở nhóm trường công lập khá và ứng dụng."),
 R("R30", 3, 48, 0.91, [has(NG, "NHOM_NGHE_THUAT"), has(ST, "Lap_Trinh")], (KN, "REC_NT_SO"),
   "Nhóm Nghệ thuật kết hợp hứng thú lập trình/công nghệ dẫn tới Thiết kế đồ họa và Nghệ thuật số."),
 R("R36", 3, 47, 0.85, [has(NG, "NHOM_Y_DUOC"), not_(all_(eq(TT, "TOP_DAU"), ge("Diem_Hoa", 8.5), ge("Diem_Sinh", 8.5)))], (KN, "REC_YD_CHUNG"),
   "Phù hợp nhóm Sức khỏe; gợi ý Dược học, Điều dưỡng, Kỹ thuật xét nghiệm y học, Y học dự phòng. Nghề y, dược cần điều kiện hành nghề."),
 R("R43", 3, 46, 0.85, [has(NG, "NHOM_NGHE_THUAT"), not_(has(ST, "Lap_Trinh"))], (KN, "REC_NT_DOHOA"),
   "Phù hợp nhóm Nghệ thuật; gợi ý Thiết kế đồ họa, Thiết kế thời trang. Cần đối chiếu tổ hợp năng khiếu của trường."),
 R("R42", 3, 45, 0.85, [has(NG, "NHOM_SU_PHAM"), not_(all_(ge("Diem_Toan", 8.5), any_(eq(TT, "TOP_DAU"), eq(TT, "KHA_TOT"))))], (KN, "REC_SP_MON"),
   "Phù hợp nhóm Sư phạm; gợi ý chọn ngành sư phạm theo môn thế mạnh (Ngữ văn, Tiếng Anh, Giáo dục Tiểu học, Toán)."),
 # ================= DU PHONG (Priority <= 10) - luat chinh thuc, chay SAU CUNG =================
 R("R44", 4, 10, 0.40, [("empty", KN), ("exists", NG)], (KN, "REC_FB_NHOM"),
   "Đã xác định nhóm ngành phù hợp nhưng chưa đủ dữ liệu điểm/tổ hợp để chốt ngành cụ thể; chỉ nêu hướng nhóm ngành tham khảo."),
 R("R45", 4, 9, 0.35, [("empty", KN), ("empty", NG), ("exists", HL)], (KN, "REC_FB_HOLLAND"),
   "Chưa có thế mạnh khối hay nhóm ngành đủ căn cứ; chỉ gợi ý hướng theo thiên hướng Holland ({Holland}) ở mức tham khảo thấp."),
 R("R46", 4, 8, 0.20, [("empty", KN), ("empty", NG), ("empty", HL)], (KN, "REC_INSUFFICIENT"),
   "Dữ liệu hiện có chưa đủ căn cứ để đưa ra khuyến nghị; cần bổ sung điểm, sở thích hoặc năng lực nổi trội."),
]
RULES_BY_ID = {r["id"]: r for r in RULES}
TIER_BANDS = {1: (81, 95), 2: (68, 78), 3: (45, 60), 4: (1, 10)}
TIER_NAMES = {1: "Tầng 1 - Trừu tượng hóa", 2: "Tầng 2 - Nhóm ngành", 3: "Tầng 3 - Khuyến nghị", 4: "Dự phòng"}

# ----------------------------------------------------------------------------------------
# 4. HIEN THI LUAT & KIEM TRA TINH NHAT QUAN
# ----------------------------------------------------------------------------------------
_SYM = {"ge": ">=", "gt": ">", "lt": "<", "le": "<="}
def _num(x): return ("%g" % x) if float(x) != int(x) else "%.1f" % x

def render_cond(c):
    op = c[0]
    if op in _SYM: return "%s %s %s" % (c[1], _SYM[op], _num(c[2]))
    if op == "eq": return '%s == "%s"' % (c[1], c[2])
    if op == "has": return '"%s" IN %s' % (c[2], c[1])
    if op == "exists": return "EXISTS %s" % c[1]
    if op == "empty": return "NOT EXISTS %s" % c[1]
    if op == "any": return "(" + " OR ".join(render_cond(x) for x in c[1]) + ")"
    if op == "all": return "(" + " AND ".join(render_cond(x) for x in c[1]) + ")"
    if op == "not": return "NOT " + (render_cond(c[1]) if c[1][0] in ("all", "any") else "(" + render_cond(c[1]) + ")")
    raise ValueError(op)

def render_if(rule): return " AND ".join(render_cond(c) for c in rule["conds"])

def _atoms(c):
    if c[0] in ("any", "all"): return sum(_atoms(x) for x in c[1])
    if c[0] == "not": return _atoms(c[1])
    return 1
def specificity(rule): return sum(_atoms(c) for c in rule["conds"])

def _attrs(c):
    if c[0] in ("any", "all"): return [a for x in c[1] for a in _attrs(x)]
    if c[0] == "not": return _attrs(c[1])
    return [c[1]]

def _vals(c):
    if c[0] in ("any", "all"): return [v for x in c[1] for v in _vals(x)]
    if c[0] == "not": return _vals(c[1])
    if c[0] in ("eq", "has"): return [(c[1], c[2])]
    return []

VALID = {"So_Thich": SO_THICH_VALUES, "Nang_Luc_Noi_Troi": NANG_LUC_VALUES, "The_Manh_Khoi": KHOI_VALUES,
         "Ma_Holland": HOLLAND_VALUES, "Phan_Khuc_Diem": PHAN_KHUC_VALUES,
         "Nhom_Nganh_Phu_Hop": list(NHOM), "Khuyen_Nghi_Chinh_Thuc": list(RECS)}

def validate_kb(rules=None, verbose=True):
    """Tra ve danh sach loi (rong = hop le). Kiem tra: ID, ten bien, gia tri, dai Priority,
    phan tang (stratification), nhom nganh phu du 10/10, ma nganh, CF."""
    rules = rules or RULES
    errs = []
    ids = [r["id"] for r in rules]
    if len(ids) != len(set(ids)): errs.append("Trung ma luat")
    produced = {}
    for r in rules:
        lo, hi = TIER_BANDS[r["tier"]]
        if not (lo <= r["priority"] <= hi): errs.append("%s: Priority %s ngoai dai tang %s" % (r["id"], r["priority"], r["tier"]))
        if not (0 < r["cf"] <= 1): errs.append("%s: CF khong hop le" % r["id"])
        a, v = r["then"]
        if a not in DERIVED_ATTRS: errs.append("%s: THEN dung thuoc tinh khong phai bien suy dien" % r["id"])
        if v not in VALID[a]: errs.append("%s: gia tri THEN '%s' khong thuoc mien cua %s" % (r["id"], v, a))
        produced.setdefault(a, set()).add(r["tier"])
        for c in r["conds"]:
            for (aa, vv) in _vals(c):
                if aa in VALID and vv not in VALID[aa]: errs.append("%s: '%s' khong thuoc mien %s" % (r["id"], vv, aa))
            for aa in _attrs(c):
                if not (aa in SCORE_VARS or aa == "Tong_Diem_Du_Kien" or aa in VALID):
                    errs.append("%s: bien '%s' khong co trong Ontology" % (r["id"], aa))
    # phan tang: luat tang t (t<=3) chi duoc doc thuoc tinh suy dien do luat tang < t sinh ra
    for r in rules:
        if r["tier"] > 3: continue
        for c in r["conds"]:
            for aa in _attrs(c):
                if aa in DERIVED_ATTRS and any(t >= r["tier"] for t in produced.get(aa, ())):
                    errs.append("%s: doc %s nhung thuoc tinh nay co the do tang >= %d sinh ra (vi pham phan tang)" % (r["id"], aa, r["tier"]))
    # bao phu 10 nhom
    t2 = {r["then"][1] for r in rules if r["then"][0] == NG}
    t3 = {RECS[r["then"][1]]["ma_nhom"] for r in rules if r["tier"] == 3}
    for g in NHOM:
        if g not in t2: errs.append("Nhom %s chua co luat Tang 2" % g)
        if g not in t3: errs.append("Nhom %s chua co luat Tang 3" % g)
    # ma nganh trong RECS
    for k, rec in RECS.items():
        for m in rec["nganh"]:
            if m not in MAJORS: errs.append("%s: nganh '%s' khong co trong MAJOR_CATALOG" % (k, m))
        if rec["ma_nhom"] and rec["ma_nhom"] not in NHOM: errs.append("%s: ma nhom sai" % k)
    # Tang 1 chi dung bien khoi dau vao + Tong; tang 3 khong sinh Nhom
    if verbose:
        print("validate_kb: %d luat, %d loi" % (len(rules), len(errs)))
        for e in errs: print("  -", e)
    return errs

# ----------------------------------------------------------------------------------------
# 5. XUAT JSON (rules_kb.json) CHO NHOM LAP TRINH
# ----------------------------------------------------------------------------------------
def export_json(path="rules_kb.json"):
    out = {"version": VERSION,
           "ontology": {k: {"layer": v[0], "type": v[1], "domain": v[2]} for k, v in ONTOLOGY.items()},
           "constants": {"SEG_TOP": SEG_TOP, "SEG_GOOD": SEG_GOOD, "CF_THRESHOLD": 0.2},
           "tier_bands": {str(k): list(v) for k, v in TIER_BANDS.items()},
           "conflict_resolution": ["refraction", "priority_desc", "specificity_desc", "recency_desc", "rule_id_asc"],
           "nhom_nganh": NHOM, "major_catalog": MAJORS, "recommendations": RECS,
           "holland_hints": HOLLAND_HINTS, "combinations": COMBINATIONS,
           "rules": [dict(r, if_text=render_if(r), specificity=specificity(r)) for r in RULES]}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return path

if __name__ == "__main__":
    validate_kb()
    from collections import Counter
    print(Counter(r["tier"] for r in RULES))
    print("rules_kb.json ->", export_json())
