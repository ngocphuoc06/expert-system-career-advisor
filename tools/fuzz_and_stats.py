import random, itertools, json
import rules_data as KB
from reference_engine import *
random.seed(2026)
# ---- 1. FUZZ: 5000 hoc sinh ngau nhien: khong loi, luon dung, khong lap, luon co >=1 ket luan
eng = Engine(); n=0; maxc=0; fb=0
for _ in range(5000):
    st = {}
    for v in KB.SCORE_VARS:
        if random.random() < 0.75: st[v] = round(random.uniform(3, 10), 1)
    st["So_Thich"] = random.sample(KB.SO_THICH_VALUES, random.randint(0, 4))
    st["Nang_Luc_Noi_Troi"] = random.choice(KB.NANG_LUC_VALUES + [None])
    st["To_Hop_Du_Kien"] = random.choice(list(KB.COMBINATIONS) + [None])
    r = eng.run(st)
    keys = [(t["fired"], t["premises"]) for t in r.trace]
    assert len(keys) == len(set(keys))
    assert len(r.recommendations()) >= 1, st
    assert sum(t["fired"] in ("R44","R45","R46") for t in r.trace) <= 1
    for f in r.wm.facts.values(): assert -1e-9 <= f.cf <= 1 + 1e-9
    maxc = max(maxc, len(r.trace)); fb += any(t["fired"] in ("R44","R45","R46") for t in r.trace); n += 1
print("FUZZ: %d ho so ngau nhien, 0 loi, toi da %d chu ky, luon >=1 ket qua; %d ho so (%.1f%%) roi vao luat du phong" % (n, maxc, fb, 100*fb/n))

# ---- 2. KHOANG TRONG BO LUAT CU (R25-R30 nguyen ban) tren cung luoi 648 to hop/nhom
def old_tier3(g, seg, toan, anh, lt):
    if g=="NHOM_CNTT": return (seg=="TOP_DAU" and toan is not None and toan>=9.0) or seg in ("KHA_TOT","AN_TOAN")
    if g=="NHOM_KY_THUAT": return seg=="TOP_DAU"
    if g=="NHOM_KINH_TE_QT": return seg=="TOP_DAU" and anh is not None and anh>=8.5
    if g=="NHOM_SU_PHAM": return toan is not None and toan>=8.5 and seg in ("TOP_DAU","KHA_TOT")
    if g=="NHOM_NGHE_THUAT": return bool(lt)
    return False
tot = {}; miss = {}
for g in KB.NHOM:
    c=m=0
    for seg,toan,anh,lt in itertools.product([None]+KB.PHAN_KHUC_VALUES,[None,7.0,9.5],[None,7.0,9.0],[0,1]):
        c+=1; m += (not old_tier3(g,seg,toan,anh,lt))
    tot[g]=c; miss[g]=m
print("KHOANG TRONG LUAT CU (ty le to hop dau vao khong co ket luan Tang 3):")
for g in KB.NHOM: print("  %-22s %5.1f%%" % (g, 100*miss[g]/tot[g]))

# ---- 3. Trung binh CF / Priority theo nhom luat (de sua bieu do)
def grp(ids): 
    rs=[KB.RULES_BY_ID[i] for i in ids]; return len(rs), sum(r["cf"] for r in rs)/len(rs), min(r["priority"] for r in rs), max(r["priority"] for r in rs)
G = {"T1 khoi (R01-R06,R31)": ["R01","R02","R03","R04","R05","R06","R31"],
     "T1 Holland (R07-R12)": ["R07","R08","R09","R10","R11","R12"],
     "T1 phan khuc (R13-R15)": ["R13","R14","R15"],
     "T2 (R16-R24,R32,R33)": ["R16","R17","R18","R19","R20","R21","R22","R23","R24","R32","R33"],
     "T3 (R25-R30,R34-R43)": [r["id"] for r in KB.RULES if r["tier"]==3],
     "Du phong (R44-R46)": ["R44","R45","R46"]}
print("CF TRUNG BINH THUC TE:")
for k,v in G.items(): n_,a,lo,hi = grp(v); print("  %-26s %2d luat  CF_tb=%.4f  Priority %d-%d" % (k,n_,a,lo,hi))
old = {"R01-R06":["R01","R02","R03","R04","R05","R06"], "R16-R24":["R16","R17","R18","R19","R20","R21","R22","R23","R24"], "R25-R30":["R25","R26","R27","R28","R29","R30"]}
print("CF TB cua bo 30 luat cu:", {k: round(sum(KB.RULES_BY_ID[i]["cf"] for i in v)/len(v),4) for k,v in old.items()})
