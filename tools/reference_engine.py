"""
reference_engine.py - DONG CO SUY DIEN TIEN THAM CHIEU (oracle) de TV3/TV4/TV6 doi chieu ket qua.
Khong thay the ma nguon cua nhom lap trinh; muc dich: chung minh bo luat chay dung, dung va khong lap.

Chu ky Match -> Select -> Act.  Xu ly xung dot:
   Refraction -> Priority giam -> Specificity giam -> Recency moi nhat -> ma luat tang dan.
CF: AND = min ; OR = max ; truyen CF = CF_luat x CF_tien_de ; nhieu luat cung ket luan = hop nhat MYCIN.
Moi fact luu {rule_id: CF dong gop}; CF fact TINH LAI tu cac dong gop (khong cong don khi luat ban lai)
=> idempotent, khong dem trung do cung mot luat chay lai.
"""
import json, re
from collections import defaultdict
import rules_data as KB

CF_THRESHOLD = 0.2     # tien de chi "dung" khi CF > 0.2 (quy uoc MYCIN)
MAX_CYCLES = 500

def combine_cf(a, b):
    """Ham ket hop MYCIN day du 3 truong hop."""
    if a > 0 and b > 0: return a + b * (1 - a)
    if a < 0 and b < 0: return a + b * (1 + a)
    return (a + b) / (1 - min(abs(a), abs(b)))

def tuple_cond(c):
    """JSON (list) -> tuple, de nap duoc tu rules_kb.json."""
    if isinstance(c, list):
        c = list(c)
        if c[0] in ("any", "all"): return (c[0], [tuple_cond(x) for x in c[1]])
        if c[0] == "not": return ("not", tuple_cond(c[1]))
        return tuple(c)
    return c

def load_rules_json(path):
    with open(path, encoding="utf-8") as f: d = json.load(f)
    rules = []
    for r in d["rules"]:
        r = dict(r); r["conds"] = [tuple_cond(c) for c in r["conds"]]; rules.append(r)
    return rules

class Fact:
    __slots__ = ("attr", "value", "cf", "timetag", "version", "contrib", "initial")
    def __init__(self, attr, value, cf, timetag, initial=False):
        self.attr, self.value, self.cf, self.timetag = attr, value, cf, timetag
        self.version, self.contrib, self.initial = 0, {}, initial

class WM:
    """Working Memory: so (Diem_*, Tong) + fact roi rac (thuoc_tinh, gia_tri) -> Fact (tap hop co CF)."""
    def __init__(self, student):
        self.student = student
        self.num = {v: student.get(v) for v in KB.SCORE_VARS if student.get(v) is not None}
        self.to_hop = student.get("To_Hop_Du_Kien")
        tong = KB.tong_diem(student, self.to_hop) if self.to_hop else None
        if tong is not None: self.num["Tong_Diem_Du_Kien"] = tong
        self.facts = {}
        for v in student.get("So_Thich", []):
            self.facts[("So_Thich", v)] = Fact("So_Thich", v, 1.0, 0, True)
        if student.get("Nang_Luc_Noi_Troi"):
            self.facts[("Nang_Luc_Noi_Troi", student["Nang_Luc_Noi_Troi"])] = Fact("Nang_Luc_Noi_Troi", student["Nang_Luc_Noi_Troi"], 1.0, 0, True)
    def values(self, attr): return sorted(v for (a, v), f in self.facts.items() if a == attr and f.cf > CF_THRESHOLD)
    def get(self, attr, value): return self.facts.get((attr, value))

def ev(c, wm):
    """Danh gia dieu kien -> (cf, [khoa fact]) hoac None."""
    op = c[0]
    if op in ("ge", "gt", "lt", "le"):
        v = wm.num.get(c[1])
        if v is None: return None
        ok = {"ge": v >= c[2], "gt": v > c[2], "lt": v < c[2], "le": v <= c[2]}[op]
        return (1.0, []) if ok else None
    if op in ("eq", "has"):
        f = wm.get(c[1], c[2])
        return (f.cf, [(c[1], c[2], f.version)]) if f and f.cf > CF_THRESHOLD else None
    if op == "exists":
        fs = [f for (a, v), f in wm.facts.items() if a == c[1] and f.cf > CF_THRESHOLD]
        return (max(f.cf for f in fs), [(f.attr, f.value, f.version) for f in fs]) if fs else None
    if op == "empty":
        return None if any(a == c[1] and f.cf > CF_THRESHOLD for (a, v), f in wm.facts.items()) else (1.0, [])
    if op in ("any", "all"):
        rs = [ev(x, wm) for x in c[1]]
        if op == "any":
            sat = [r for r in rs if r]
            return (max(r[0] for r in sat), sorted({k for r in sat for k in r[1]})) if sat else None
        if any(r is None for r in rs): return None
        return (min(r[0] for r in rs), sorted({k for r in rs for k in r[1]}))
    if op == "not": return (1.0, []) if ev(c[1], wm) is None else None
    raise ValueError(op)

def match(rule, wm):
    cfs, keys = [], []
    for c in rule["conds"]:
        r = ev(c, wm)
        if r is None: return None
        cfs.append(r[0]); keys += r[1]
    return (min(cfs) if cfs else 1.0), tuple(sorted(set(keys)))

class Engine:
    def __init__(self, rules=None, cf_mode="mycin"):
        """cf_mode='mycin' (chuan, mac dinh) | 'conservative' (luat cung dep_group chi lay max, tranh dem trung bang chung)."""
        self.rules = sorted(rules or KB.RULES, key=lambda r: int(r["id"][1:]))
        self.cf_mode = cf_mode
        self.spec = {r["id"]: KB.specificity(r) for r in self.rules}

    def _fact_cf(self, f):
        if self.cf_mode == "conservative":
            groups = defaultdict(list)
            for rid, cf in f.contrib.items():
                g = KB.RULES_BY_ID[rid].get("dep_group") or rid
                groups[g].append(cf)
            vals = [max(v) for v in groups.values()]
        else:
            vals = list(f.contrib.values())
        out = 0.0
        for cf in sorted(vals, reverse=True): out = combine_cf(out, cf) if out else cf
        return out

    def run(self, student, max_cycles=MAX_CYCLES):
        wm = WM(student); fired = set(); trace = []; last_prem = {}; last_cycle = {}
        for cycle in range(1, max_cycles + 1):
            agenda = []
            for r in self.rules:
                m = match(r, wm)
                if not m: continue
                key = (r["id"], m[1])
                if key in fired: continue                                  # 1) REFRACTION
                rec = max([wm.facts[(a, v)].timetag for a, v, _ in m[1]] or [0])
                agenda.append((-r["priority"], -self.spec[r["id"]], -rec, int(r["id"][1:]), r, m, key))
            main = [t for t in agenda if t[4]["tier"] <= 3]
            if main: agenda = main            # luat du phong (tang 4) chi vao Agenda khi Agenda chinh RONG
            if not agenda: break                                           # Agenda rong => dung
            agenda.sort(key=lambda t: t[:4])                               # 2) Priority 3) Specificity 4) Recency 5) id
            _, _, _, _, r, (pcf, keys), key = agenda[0]
            fired.add(key)
            attr, val = r["then"]
            cf_out = round(r["cf"] * pcf, 6)                               # CF(H)=CF_luat x min(CF tien de)
            f = wm.facts.get((attr, val)); new = f is None
            if new: f = wm.facts[(attr, val)] = Fact(attr, val, 0.0, cycle)
            f.contrib[r["id"]] = cf_out
            newcf = round(self._fact_cf(f), 6); changed = new or abs(newcf - f.cf) > 1e-9
            f.cf = newcf
            if changed: f.version += 1; f.timetag = cycle
            last_prem[r["id"]] = keys; last_cycle[r["id"]] = cycle
            trace.append({"cycle": cycle, "agenda": [(t[4]["id"], t[4]["priority"]) for t in agenda],
                          "fired": r["id"], "priority": r["priority"], "premises": keys, "pcf": pcf,
                          "fact": (attr, val), "cf_out": cf_out, "cf_after": newcf, "new": new, "changed": changed,
                          "locked": len(fired)})
        else:
            raise RuntimeError("Vuot MAX_CYCLES - nghi ngo vong lap")
        return Result(wm, trace, last_prem, last_cycle)

class Result:
    def __init__(self, wm, trace, last_prem, last_cycle):
        self.wm, self.trace, self.last_prem, self.last_cycle = wm, trace, last_prem, last_cycle
    def facts(self, attr):
        return {v: round(f.cf, 4) for (a, v), f in self.wm.facts.items() if a == attr and not f.initial}
    def recommendations(self):
        fs = [f for (a, v), f in self.wm.facts.items() if a == "Khuyen_Nghi_Chinh_Thuc"]
        return sorted(fs, key=lambda f: -f.cf)
    def why(self, attr, value):
        """Chuoi luat dan toi fact (duyet nguoc cac dong gop), sap theo thu tu kich hoat."""
        seen, order = set(), []
        def walk(a, v):
            f = self.wm.facts.get((a, v))
            if not f: return
            for rid in f.contrib:
                if rid in seen: continue
                seen.add(rid)
                for (pa, pv, _) in self.last_prem[rid]:
                    if (pa, pv) in self.wm.facts and not self.wm.facts[(pa, pv)].initial: walk(pa, pv)
                order.append(rid)
        walk(attr, value)
        return sorted(set(order), key=lambda r: self.last_cycle[r])

# ----------------------------- Hien thi / giai trinh -----------------------------
def _fmt(x): return "%.1f" % x if x is not None else "?"
def context(res):
    wm, s = res.wm, res.wm.student
    ctx = defaultdict(lambda: "?")
    for v in KB.SCORE_VARS:
        if wm.num.get(v) is not None: ctx[v] = ("%.1f" % wm.num[v]).replace(".", ",")
    ctx["Tong"] = ("%.1f" % wm.num["Tong_Diem_Du_Kien"]).replace(".", ",") if "Tong_Diem_Du_Kien" in wm.num else "?"
    ctx["To_Hop"] = wm.to_hop or "?"
    ctx["So_Thich"] = ", ".join(s.get("So_Thich", [])) or "?"
    ctx["Holland"] = ", ".join(wm.values("Ma_Holland")) or "?"
    return ctx

def explain_rule(res, rid):
    return KB.RULES_BY_ID[rid]["template"].format_map(context(res))

def premise_text(res, keys):
    wm = res.wm; out = []
    for a, v, _ in keys:
        out.append("%s=%s" % (a, v))
    return "; ".join(out) if out else "(điều kiện số trên dữ liệu đầu vào)"

def render_rec(key, res):
    rec = KB.RECS[key]; d = rec["mo_ta"]
    if d == "dynamic:nhom":
        return "Hướng nhóm ngành tham khảo: " + ", ".join(KB.NHOM[g] for g in res.wm.values("Nhom_Nganh_Phu_Hop")) + \
               " (chưa đủ dữ liệu điểm/tổ hợp để chốt ngành cụ thể)."
    if d == "dynamic:holland":
        gs = []
        for h in res.wm.values("Ma_Holland"):
            for g in KB.HOLLAND_HINTS[h]:
                if g not in gs: gs.append(g)
        seg = res.facts("Phan_Khuc_Diem")
        extra = " Mức điểm hiện ở phân khúc AN_TOAN: nên cân nhắc chương trình cao đẳng/đại học ứng dụng xét học bạ." if "AN_TOAN" in seg else ""
        return "Gợi ý tham khảo theo Holland (%s): %s.%s" % (", ".join(res.wm.values("Ma_Holland")), ", ".join(KB.NHOM[g] for g in gs), extra)
    if d == "dynamic:insufficient":
        return "CHƯA ĐỦ CĂN CỨ để khuyến nghị. Cần bổ sung điểm các môn, sở thích hoặc năng lực nổi trội."
    names = ["%s (%s%s)" % (KB.MAJORS[m]["ten"], KB.MAJORS[m]["ma_hien_hanh"],
                            " / " + KB.MAJORS[m]["ma_moi"] if KB.MAJORS[m]["ma_moi"] else "") for m in rec["nganh"]]
    s = "%s — %s — %s" % (KB.NHOM[rec["ma_nhom"]], "; ".join(names), rec["nhom_truong"])
    return s + (" Lưu ý: " + rec["mo_ta"] if rec["mo_ta"] else "")

def print_trace(res, out=print):
    for t in res.trace:
        ag = ", ".join("%s[%d]" % x for x in t["agenda"][:8]) + (" ..." if len(t["agenda"]) > 8 else "")
        out("Chu kỳ %d | Agenda: %s" % (t["cycle"], ag))
        out("   Chọn %s (Priority %d) | tiền đề: %s | CF tiền đề min = %.4f" % (t["fired"], t["priority"], premise_text(res, t["premises"]), t["pcf"]))
        out("   => %s = %s | CF luật×tiền đề = %.4f | CF sau hợp nhất = %.4f%s" % (t["fact"][0], t["fact"][1], t["cf_out"], t["cf_after"],
            "" if t["new"] else "  (HỢP NHẤT với bằng chứng trước)"))
    out("Agenda rỗng sau chu kỳ %d => DỪNG (đã khóa %d bộ luật–sự kiện)." % (len(res.trace), res.trace[-1]["locked"] if res.trace else 0))

def print_answer(res, out=print):
    for k in ("The_Manh_Khoi", "Ma_Holland", "Phan_Khuc_Diem", "Nhom_Nganh_Phu_Hop"):
        out("%-20s %s" % (k, res.facts(k)))
    out("Khuyen_Nghi_Chinh_Thuc:")
    for f in res.recommendations():
        out("  [CF %.4f] %s" % (f.cf, render_rec(f.value, res)))
        out("     Vì: " + " -> ".join(res.why("Khuyen_Nghi_Chinh_Thuc", f.value)) + " -> " + f.value)
