"""test_scenarios.py - kiem thu bo luat v3 bang dong co tham chieu. Chay: python3 test_scenarios.py"""
import itertools, io, sys
import rules_data as KB
from reference_engine import *

OUT = io.StringIO()
def log(*a): print(*a); print(*a, file=OUT)

STUDENTS = {
 "HS001": dict(Diem_Toan=9.0, Diem_Ly=8.5, Diem_Hoa=8.0, Diem_Anh=8.5, Diem_Tin=9.0, So_Thich=["Lap_Trinh","Nghien_Cuu"], Nang_Luc_Noi_Troi="Tu_Duy_Logic", To_Hop_Du_Kien="A01"),
 "HS002": dict(Diem_Toan=8.0, Diem_Hoa=8.5, Diem_Sinh=9.0, Diem_Anh=6.5, So_Thich=["Cham_Soc_Suc_Khoe","Nghien_Cuu"], Nang_Luc_Noi_Troi="Tu_Duy_Logic", To_Hop_Du_Kien="B00"),
 "HS003": dict(Diem_Toan=7.5, Diem_Van=8.5, Diem_Anh=8.5, Diem_Su=8.0, Diem_Dia=8.0, So_Thich=["Giang_Day","Giao_Tiep"], Nang_Luc_Noi_Troi="Ngon_Ngu_Dien_Dat", To_Hop_Du_Kien="D01"),
 "HS004": dict(Diem_Toan=7.0, Diem_Van=7.0, Diem_Anh=8.0, Diem_Ve=9.0, So_Thich=["Sang_Tao","Lap_Trinh"], Nang_Luc_Noi_Troi="Tham_My_Nghe_Thuat", To_Hop_Du_Kien="D01"),
 "HS005": dict(Diem_Toan=6.5, Diem_Ly=6.0, Diem_Hoa=6.0, Diem_Anh=6.5, So_Thich=["Kinh_Doanh"], Nang_Luc_Noi_Troi="To_Chuc_Lanh_Dao", To_Hop_Du_Kien="A01"),
 "DEMO_2.6": dict(Diem_Toan=9.2, Diem_Ly=8.5, Diem_Hoa=8.0, Diem_Tin=8.8, Diem_Anh=9.1, So_Thich=["Lap_Trinh","Nghien_Cuu"], Nang_Luc_Noi_Troi="Tu_Duy_Logic", To_Hop_Du_Kien="A01"),
 "EDGE_DIEM_THAP_KHONG_SO_THICH": dict(Diem_Toan=5.0, Diem_Ly=5.0, Diem_Hoa=5.0, Diem_Van=5.0, Diem_Anh=5.0, So_Thich=[], To_Hop_Du_Kien="A00"),
 "EDGE_THIEU_DIEM_TO_HOP": dict(Diem_Toan=9.0, Diem_Ly=8.5, So_Thich=["Lap_Trinh"], Nang_Luc_Noi_Troi="Tu_Duy_Logic", To_Hop_Du_Kien="A01"),
 "YDUOC_TOP": dict(Diem_Toan=9.5, Diem_Hoa=9.2, Diem_Sinh=9.3, Diem_Anh=8.0, So_Thich=["Cham_Soc_Suc_Khoe","Nghien_Cuu"], Nang_Luc_Noi_Troi="Tu_Duy_Logic", To_Hop_Du_Kien="B00"),
 "PHAP_LUAT": dict(Diem_Toan=7.8, Diem_Van=8.6, Diem_Su=8.0, Diem_Dia=7.8, Diem_Anh=8.2, So_Thich=["Tranh_Bien_Luat"], Nang_Luc_Noi_Troi="To_Chuc_Lanh_Dao", To_Hop_Du_Kien="C00"),
 "LOGISTICS": dict(Diem_Toan=8.2, Diem_Ly=7.8, Diem_Hoa=7.6, So_Thich=["Kinh_Doanh","Con_So_Du_Lieu"], Nang_Luc_Noi_Troi="Phan_Tich_Chi_Tiet", To_Hop_Du_Kien="A00"),
 "KY_THUAT": dict(Diem_Toan=8.5, Diem_Ly=8.0, Diem_Hoa=7.5, So_Thich=["May_Moc"], Nang_Luc_Noi_Troi="Thao_Tac_Ky_Thuat", To_Hop_Du_Kien="A00"),
}
EXPECT = {  # (khoi, holland, phan_khuc, nhom, recs)  - tap ky vong
 "HS001": ({"KHOI_A00","KHOI_A01"}, {"I_INVESTIGATIVE"}, "KHA_TOT", {"NHOM_CNTT","NHOM_HOA_MOI_TRUONG"}, {"REC_CNTT_UNG_DUNG","REC_HOA_MT"}),
 "HS002": ({"KHOI_B00"}, {"I_INVESTIGATIVE"}, "KHA_TOT", {"NHOM_Y_DUOC","NHOM_HOA_MOI_TRUONG"}, {"REC_YD_CHUNG","REC_HOA_MT"}),
 "HS003": ({"KHOI_C00","KHOI_D01"}, {"S_SOCIAL"}, "KHA_TOT", {"NHOM_SU_PHAM","NHOM_NGON_NGU_XH"}, {"REC_SP_MON","REC_NNXH"}),
 "HS004": ({"KHOI_H00"}, {"A_ARTISTIC"}, "AN_TOAN", {"NHOM_NGHE_THUAT"}, {"REC_NT_SO"}),
 "HS005": (set(), {"E_ENTERPRISING"}, "AN_TOAN", set(), {"REC_FB_HOLLAND"}),
 "DEMO_2.6": ({"KHOI_A00","KHOI_A01"}, {"I_INVESTIGATIVE"}, "TOP_DAU", {"NHOM_CNTT","NHOM_HOA_MOI_TRUONG"}, {"REC_CNTT_TOP","REC_HOA_MT"}),
 "EDGE_DIEM_THAP_KHONG_SO_THICH": (set(), set(), "AN_TOAN", set(), {"REC_INSUFFICIENT"}),
 "EDGE_THIEU_DIEM_TO_HOP": (set(), {"I_INVESTIGATIVE"}, None, set(), {"REC_FB_HOLLAND"}),
 "YDUOC_TOP": ({"KHOI_B00"}, {"I_INVESTIGATIVE"}, "TOP_DAU", {"NHOM_Y_DUOC","NHOM_HOA_MOI_TRUONG"}, {"REC_YD_TOP","REC_HOA_MT"}),
 "PHAP_LUAT": ({"KHOI_C00","KHOI_D01"}, {"E_ENTERPRISING"}, "KHA_TOT", {"NHOM_PHAP_LUAT","NHOM_KINH_TE_QT"}, {"REC_PL","REC_KTE_QTKD"}),
 "LOGISTICS": ({"KHOI_A00"}, {"C_CONVENTIONAL"}, "KHA_TOT", {"NHOM_LOGISTICS"}, {"REC_LOGISTICS"}),
 "KY_THUAT": ({"KHOI_A00"}, {"R_REALISTIC"}, "KHA_TOT", {"NHOM_KY_THUAT"}, {"REC_KT_UNG_DUNG"}),
}

def run_all():
    ok = True
    log("="*100); log("1. KIEM TRA CAU TRUC CO SO TRI THUC"); log("="*100)
    errs = KB.validate_kb(verbose=False); log("validate_kb:", "OK - %d luat, 0 loi" % len(KB.RULES) if not errs else errs); ok &= not errs
    # round-trip JSON
    KB.export_json("rules_kb.json"); jr = load_rules_json("rules_kb.json")
    log("rules_kb.json nap lai: %d luat" % len(jr))
    log(); log("="*100); log("2. KICH BAN HOC SINH (ket qua thuc te so voi ky vong)"); log("="*100)
    for name, st in STUDENTS.items():
        for rules, tag in ((KB.RULES, "py"), (jr, "json")):
            res = Engine(rules).run(st)
            khoi, hol, seg, nhom, recs = EXPECT[name]
            got = (set(res.facts("The_Manh_Khoi")), set(res.facts("Ma_Holland")),
                   (list(res.facts("Phan_Khuc_Diem")) or [None])[0], set(res.facts("Nhom_Nganh_Phu_Hop")),
                   {f.value for f in res.recommendations()})
            passed = got == (khoi, hol, seg, nhom, recs)
            # moi (luat, bo fact) chi kich hoat 1 lan; toi da 1 luat du phong
            keys = [(t["fired"], t["premises"]) for t in res.trace]
            assert len(keys) == len(set(keys)), "Refraction that bai"
            assert sum(1 for t in res.trace if t["fired"] in ("R44","R45","R46")) <= 1, "Nhieu luat du phong cung chay"
            ok &= passed
            if tag == "py":
                log("\n[%s] %s  | %d chu ky | luat chay: %s" % ("PASS" if passed else "FAIL", name, len(res.trace), " ".join(t["fired"] for t in res.trace)))
                if not passed: log("   ky vong:", (khoi, hol, seg, nhom, recs)); log("   thuc te:", got)
                for f in res.recommendations(): log("   [CF %.4f] %s" % (f.cf, render_rec(f.value, res)[:150]))
            elif not passed: log("   JSON FAIL", name)
    log(); log("="*100); log("3. TRACE CHI TIET KICH BAN MUC 2.6 (DEMO_2.6)"); log("="*100)
    res = Engine().run(STUDENTS["DEMO_2.6"]); print_trace(res, log); log(); print_answer(res, log)
    log(); log("--- Che do 'conservative' (R16/R17 cung nhom phu thuoc -> chi lay max) ---")
    print_answer(Engine(cf_mode="conservative").run(STUDENTS["DEMO_2.6"]), log)
    log(); log("="*100); log("4. KIEM TRA CONG THUC CF"); log("="*100)
    c = combine_cf(0.81, 0.765); log("combine(0.81, 0.765) = %.5f (ky vong 0.95535)" % c); assert abs(c-0.95535)<1e-9
    c2 = combine_cf(0.85, 0.80); log("combine(0.85, 0.80)  = %.4f (vi du muc 2.4.2, ky vong 0.97)" % c2); assert abs(c2-0.97)<1e-9
    c3 = combine_cf(0.6, -0.4); log("combine(0.6, -0.4)   = %.4f (truong hop trai dau = (0.6-0.4)/(1-0.4))" % c3); assert abs(c3-0.2/0.6)<1e-9
    c4 = combine_cf(-0.5, -0.5); assert abs(c4+0.75)<1e-9; log("combine(-0.5,-0.5)   = %.2f" % c4)
    log("CF R25 = min(0.95535, 0.95, 1.0) x 0.95 = %.4f (ky vong 0.9025)" % (min(0.95535,0.95,1.0)*0.95))
    log(); log("="*100); log("5. KIEM TRA PHU (coverage) - moi nhom ngang co >=1 luat Tang 3 khop voi MOI to hop (Phan_Khuc x diem)"); log("="*100)
    holes = []
    t3 = [r for r in KB.RULES if r["tier"] == 3]
    for g in KB.NHOM:
        n = 0
        for seg, toan, anh, hoa, sinh, lt in itertools.product([None]+KB.PHAN_KHUC_VALUES, [None, 7.0, 9.5], [None, 7.0, 9.0], [None, 7.0, 9.0], [None, 7.0, 9.0], [0, 1]):
            wm = WM({"Diem_Toan": toan, "Diem_Anh": anh, "Diem_Hoa": hoa, "Diem_Sinh": sinh, "So_Thich": ["Lap_Trinh"] if lt else []})
            wm.facts[("Nhom_Nganh_Phu_Hop", g)] = Fact("Nhom_Nganh_Phu_Hop", g, 0.9, 1)
            if seg: wm.facts[("Phan_Khuc_Diem", seg)] = Fact("Phan_Khuc_Diem", seg, 0.95, 1)
            n += 1
            if not any(match(r, wm) for r in t3 if KB.RECS[r["then"][1]]["ma_nhom"] == g): holes.append((g, seg, toan, anh, hoa, sinh, lt))
        log("  %-22s %4d to hop, %d lo hong" % (g, n, len([h for h in holes if h[0] == g])))
    ok &= not holes
    log(); log("="*100); log("6. KIEM TRA LUAT AN TOAN R44 (khong the kich hoat khi 10/10 nhom da co luat Tang 3 -> thu bang cach go R34)"); log("="*100)
    rules_wo = [r for r in KB.RULES if r["id"] != "R34"]
    res = Engine(rules_wo).run(STUDENTS["LOGISTICS"]); fired = [t["fired"] for t in res.trace]
    log("LOGISTICS khi go R34: luat chay =", " ".join(fired)); log("  ->", render_rec(res.recommendations()[0].value, res))
    assert fired[-1] == "R44"; ok &= fired[-1] == "R44"
    log(); log("="*100); log("KET QUA TONG: %s" % ("TAT CA DAT" if ok else "CO LOI")); log("="*100)
    open("test_report.txt", "w", encoding="utf-8").write(OUT.getvalue())
    return ok

if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
