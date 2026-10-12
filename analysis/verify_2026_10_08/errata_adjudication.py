"""Final adjudication of the 212 errata rules of errata_classification.py: one class per rule, one root cause per
confirmed error, and the counts the paper may report.

Inputs (all in the repository):
  errata_classification.csv           cell level, first pass (dataset value, paper value, evidence, rule)
  themecat_v1_subset.csv              the TheMeCat v1 columns the STY test needs, every row (index = row id cur_id);
                                      written from the full file with --refresh-subset (Toldy et al., Sci. Data 2026,
                                      CC BY 4.0)
  agent/extraction/eval/errata_applied.csv   which cells each rule changed, by TheMeCat / Suvarna row id
  analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv    inputs of the 40 methanol groups

Rules of adjudication
  1. A difference no larger than 2 % and no larger than one unit of the last printed digit is reading or rounding
     (MINOR, not counted).
  2. TheMeCat's STY_g_per_gcath is not transcribed: on every row it equals
     yield_CH3OH/100 x GHSV x 1/(1 + H2/CO2) x 32.04/24.05 (molar volume 24.05 L/mol). A printed STY that differs from it
     is therefore not an error of the STY column, with two exceptions:
       - the row's stored yield contradicts its own X x S (more than 0.05 percentage points and 5 %), or the row has
         no selectivity so the yield is stored on its own: the stored yield is wrong and the STY rule is an error of
         that yield (ERR);
       - a confirmed error of the same row (X, S, GHSV) explains the gap: with the corrected inputs the log-ratio to
         the printed STY is at most half the original one and at most a factor of 2 (what is left is the paper's own
         rate against X x S x F): the STY follows from that error (DER, counted with its root).
     Every other STY difference is a difference of definition (the paper's own STY, the molar volume, a yield rounded
     to 0.1 percentage points) (CONV, not counted).
  3. Every other first-pass error (unit, assignment, value) was checked against the paper text: printed numbers are
     found in the paper or SI text; plot readings were read on the figure. They stay errors (ERR).
  4. One root cause = one mechanism in one source paper (e.g. MPa stored as bar; one swapped series). Rules and value
     cells are reported alongside; dropped records are counted as records, not as cells.
  5. The 40 methanol groups are built from the Agent's extraction, never from TheMeCat or Suvarna values; for every
     root cause in a paper that enters the groups, the group input is asserted to carry the paper's value.

Outputs: errata_adjudication.csv (one row per rule), errata_cells_audit.csv (one row per cell, with row id, old and
new value and the STY test), errata_adjudication_summary.json.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SUBSET = HERE / "themecat_v1_subset.csv"
SUBSET_COLS = ["doi_link", "catalyst_name", "temperature_k", "pressure_bar", "pH2_pCO2_ratio", "GHSV_nlph_gcat",
               "CO2_conversion", "selectivity_CH3OH", "yield_CH3OH", "STY_g_per_gcath"]
V_M_THEMECAT = 24.05  # L/mol, the molar volume that reproduces TheMeCat's STY
M_MEOH = 32.04

CLASS_ORDER = ["E-unit", "E-assignment", "E-value", "C-derived", "C-convention", "N-minor"]
LABEL = {"ERR": "确认错误", "DER": "随根因派生（不单独计）", "CONV": "口径不同（不计）", "MINOR": "细微差异（不计）"}
KIND_ZH = {"E-unit": "单位", "E-assignment": "标错对象", "E-value": "数值"}

# One root cause per mechanism and source paper: (dataset, doi or Humphreys ref, field set) -> (id, description)
ROOT_EN = {'S1': '7 bar stored as 7 MPa',
           'S2': 'rates of the Fig. 3a series assigned one temperature step low',
           'S3': 'rows at 533 and 573 K, which the paper did not test',
           'S4': 'two 300 °C STY values assigned to the wrong samples (Ir/In₂O₃-5, pristine In₂O₃)',
           'S5': 'rate of 5Ni10Sn/10InZrO₂ assigned to the Sn-free catalyst',
           'T1': 'methanol selectivity below 1 % read as 0–90 % (×100, Fig. 2b); STY derived from it',
           'T2': 'GHSV 3.6 stored as 36.2 NL g⁻¹ h⁻¹ (×10); STY derived from it',
           'T3': 'pressures of 0.4–36 MPa stored as bar',
           'T4': 'yields of two Cu–Ba/Al₂O₃ rows at 553 K stored at ten times X × S',
           'T5': 'conversion curves of In0.25 and In0.12 swapped (Fig. 9a)',
           'T6': 'In₂O₃ yields rotated between 260 and 300 °C (Fig. 9b)',
           'T7': 'bulk In₂O₃ data listed as a second In0.1/ZrO₂ row',
           'T8': 'In13/ZrO₂ conversion differs from the printed values',
           'T9': 'Fig. 10b series read on the left axis instead of the right',
           'T10': 'conversions at 5–50 bar misread (Fig. 7b); STY at 5 bar derived from it',
           'T11': 'CO selectivity of CZA200 stored as CO₂ conversion (Table 1)',
           'T12': 'H₂/CO₂ = 3 stored as 3.1',
           'H1': 'Ru-free TiH₂ and BaTiO2.5H0.5 listed as Ru catalysts',
           'H2': 'volumetric flow 70 dm³ h⁻¹ printed as a space velocity',
           'H3': 'reduction flow (440 NmL min⁻¹) taken as the reaction space velocity',
           'H4': 'nominal Ru loading 1 wt% instead of the measured 0.86 wt%',
           'H5': 'Co rate 5.7 instead of the printed 5.5 mmol g⁻¹ h⁻¹',
           'H6': "space velocity of the Ru row 36,000 (66,000 for the paper's Fe and Co rows)", 'H7': 'space velocity 70,000 instead of the printed 24,000 mL g⁻¹ h⁻¹',
           'H8': 'space velocity 6,000 instead of 60,000 (×0.1)',
           'H9': 'Co loading 3.4 instead of the ICP-AES 3.73 wt%'}

ROOTS = [
    ("Suvarna 2022", "10.1039/c4cy00848k", {"pressure_bar"}, "S1", "7 bar 存成 7 MPa（压力 ×10）"),
    ("Suvarna 2022", "10.1039/c4cy00848k", {"temperature_k"}, "S2", "Fig. 3a 速率整体错配到低一档温度"),
    ("Suvarna 2022", "10.1021/acsami.1c05586", {"(row dropped)"}, "S3", "收录了原文未测的 533 K、573 K 工况（8 条记录）"),
    ("Suvarna 2022", "10.1021/acscatal.0c05628", {"catalyst_name"}, "S4", "300 °C 两个 STY 配错样品（Ir/In2O3-5、纯 In2O3）"),
    ("Suvarna 2022", "10.1021/acsomega.8b00211", {"catalyst_name"}, "S5", "5Ni10Sn/10InZrO2 的速率记到不含 Sn 的样品"),
    ("TheMeCat", "10.1016/j.cej.2022.135090", {"selectivity_CH3OH", "STY_g_per_gcath"}, "T1",
     "双床甲醇选择性 <1% 读成 0–90%（×100），推算 STY 随之 ×100"),
    ("TheMeCat", "10.1016/j.jcat.2016.03.017", {"GHSV_nlph_gcat", "STY_g_per_gcath"}, "T2",
     "空速 3.6 存成 36.2 NL/(g·h)（×10），推算 STY 随之 ×10"),
    ("TheMeCat", "10.1039/c2cy20604h", {"pressure_bar"}, "T3", "0.4/3/10/36 MPa 按 bar 存（压力 ×0.1）"),
    ("TheMeCat", "10.1039/c2cy20604h", {"STY_g_per_gcath"}, "T4", "Cu-Ba/Al2O3 553 K 两行收率存成 X·S 的 10 倍"),
    ("TheMeCat", "10.1002/cphc.202300530", {"CO2_conversion"}, "T5", "Fig. 9a In0.25 与 In0.12 两条转化率曲线互换"),
    ("TheMeCat", "10.1002/cphc.202300530", {"STY_g_per_gcath"}, "T6", "Fig. 9b In2O3 的收率在 260–300 °C 轮换错位"),
    ("TheMeCat", "10.1021/acscatal.9b01869", {"catalyst_name"}, "T7", "体相 In2O3 的数据记成第二条 In0.1/ZrO2"),
    ("TheMeCat", "10.1016/j.fuel.2022.125878", {"CO2_conversion", "STY_g_per_gcath"}, "T8", "In13/ZrO2 转化率与正文印刷值不符"),
    ("TheMeCat", "10.1016/j.fuel.2022.125878", {"selectivity_CH3OH"}, "T9", "Fig. 10b 红色系列读了左轴（应读右轴）"),
    ("TheMeCat", "10.1016/j.fuel.2023.127927", {"CO2_conversion", "STY_g_per_gcath"}, "T10",
     "Fig. 7b 不同压力下的转化率读错，5 bar 推算 STY 随之偏低"),
    ("TheMeCat", "10.1021/acs.iecr.7b01464", {"CO2_conversion"}, "T11", "CZA200 的 CO 选择性 49.3% 存成转化率"),
    ("TheMeCat", "10.1039/c6ra28305e", {"pH2_pCO2_ratio"}, "T12", "H2/CO2 = 3 存成 3.1"),
    ("Humphreys 2021 review", "ref. 104", {"catalyst_as_printed"}, "H1", "ref. 104 不含 Ru 的 TiH2、BaTiO2.5H0.5 记成 Ru 催化剂"),
    ("Humphreys 2021 review", "ref. 100", {"whsv_mL_g_h"}, "H2", "ref. 100 把体积流量 70 dm3/h 当空速"),
    ("Humphreys 2021 review", "ref. 159", {"whsv_mL_g_h"}, "H3", "ref. 159 把还原流量 440 NmL/min 当反应空速"),
    ("Humphreys 2021 review", "ref. 81", {"metal_content_wt_pct"}, "H4", "ref. 81 Ru 负载取名义值 1 wt%（实测 0.86）"),
    ("Humphreys 2021 review", "ref. 81", {"rate_value"}, "H5", "ref. 81 Co 速率 5.7（原文 5.5 mmol/(g·h)）"),
    ("Humphreys 2021 review", "ref. 81", {"whsv_mL_g_h"}, "H6", "ref. 81 Ru 行空速 36000（同文 Fe、Co 行为 66000）"),
    ("Humphreys 2021 review", "ref. 186", {"whsv_mL_g_h"}, "H7", "ref. 186 空速 70000（原文 24000 mL/(g·h)）"),
    ("Humphreys 2021 review", "ref. 199", {"whsv_mL_g_h"}, "H8", "ref. 199 空速 6000（原文 60000，×0.1）"),
    ("Humphreys 2021 review", "ref. 200", {"metal_content_wt_pct"}, "H9", "ref. 200 Co 负载 3.4（ICP 3.73 wt%）"),
]
HUMPHREYS_DOI = {"ref. 81": "10.1002/aenm.201801772", "ref. 100": "10.1021/acs.iecr.8b02126",
                 "ref. 104": "10.1021/jacs.7b08891", "ref. 159": "10.1021/acssuschemeng.7b02812",
                 "ref. 186": "10.1007/s10562-019-02674-1", "ref. 199": "10.1021/acscatal.7b00284",
                 "ref. 200": "10.1038/s41467-020-14287-z"}  # agent/nh3_field/humphreys_refs.csv

# Group inputs of the 40 methanol groups that carry a corrected quantity: (doi, catalyst substring, T_C or None,
# column, value the paper prints)
MAIN_RESULT_CHECKS = [
    ("10.1039/c2cy20604h", "", None, "P_bar", {4, 30, 100, 360}, "T3"),
    ("10.1016/j.jcat.2016.03.017", "", None, "ghsv_key", {"3.6 NL/g/h"}, "T2"),
    ("10.1039/c2cy20604h", "3 MPa]", 279.85, "STY", 0.0350, "T4"),
    ("10.1039/c2cy20604h", "36 MPa]", 279.85, "STY", 0.0419, "T4"),
    ("10.1016/j.jcat.2016.03.017", "Table 5 row 3", 250.0, "STY", 2470 * M_MEOH / 1e6, "T2"),
    ("10.1021/acs.iecr.7b01464", "CZA200", 240.0, "X", 0.313, "T11"),
    ("10.1021/acscatal.9b01869", "bulk In2O3", 280.0, "X", 0.022, "T7"),
    ("10.1021/acscatal.9b01869", "bulk In2O3", 280.0, "SMeOH", 0.607, "T7"),
    ("10.1016/j.fuel.2022.125878", "In13/ZrO2", 219.85, "X", 0.006, "T8"),
    ("10.1039/c6ra28305e", "", None, "h2_co2", {3.0}, "T12"),
    ("10.1021/acscatal.0c05628", "Ir/In2O3-5", 300.0, "STY", 0.605, "S4"),
    ("10.1021/acscatal.0c05628", "Pristine In2O3", 300.0, "STY", 0.326, "S4"),
]


def refresh_subset(path):
    t = pd.read_csv(path)
    t[SUBSET_COLS].to_csv(SUBSET, index_label="cur_id", encoding="utf-8")


def rule_key(cells):
    """errata_rules.csv order of errata_classification.py, then the numbering of the check workbook: first-pass class
    in CLASS_ORDER, then dataset, DOI, field and the rule text."""
    rules = (cells.groupby("rule").agg(dataset=("dataset", "first"), doi=("doi", "first"), field=("field", "first"),
                                       cells=("field", "size"),
                                       first_class=("proposed_class", lambda s: s.mode().iloc[0]),
                                       max_rel_diff=("rel_diff", "max"), evidence=("evidence", "first"))
             .reset_index())
    rules["rank"] = rules.first_class.map(CLASS_ORDER.index)
    rules["doi_"] = rules.doi.fillna("")
    rules = rules.sort_values(["rank", "dataset", "doi_", "field", "rule"], kind="stable").reset_index(drop=True)
    rules.insert(0, "check_no", np.arange(1, len(rules) + 1))
    return rules.drop(columns=["rank", "doi_"])


def humphreys_ref(evidence):
    s = str(evidence)
    return s.split(",")[0].strip() if s.startswith("ref.") else ""


def root_of(dataset, doi, field, evidence):
    src = humphreys_ref(evidence) if dataset.startswith("Humphreys") else doi
    for ds, d, fields, rid, text in ROOTS:
        if ds == dataset and d == src and field in fields:
            return rid, text
    return None, None


def sty_test(cells, tm, applied):
    """Per TheMeCat STY cell: is the stored STY the dataset's own derivation, and what explains the gap."""
    out = {}
    corr = applied[applied.ref.eq("themecat")].copy()
    corr["cur_id"] = corr.cur_id.astype(int)
    sty = corr[corr.field.eq("STY_g_per_gcath")]
    for _, c in sty.iterrows():
        r = tm.loc[c.cur_id]
        f = r.GHSV_nlph_gcat / (1 + r.pH2_pCO2_ratio) * M_MEOH / V_M_THEMECAT
        xs = r.CO2_conversion * r.selectivity_CH3OH / 100 if pd.notna(r.selectivity_CH3OH) else np.nan
        from_yield = r.yield_CH3OH / 100 * f
        from_xs = xs / 100 * f if pd.notna(xs) else np.nan
        derived = bool(np.isclose(r.STY_g_per_gcath, from_yield, rtol=0.03, atol=6e-5)
                       or (pd.notna(from_xs) and np.isclose(r.STY_g_per_gcath, from_xs, rtol=0.03, atol=6e-5)))
        yield_alone = pd.isna(xs)
        yield_bad = (not yield_alone) and abs(r.yield_CH3OH - xs) > max(0.05, 0.05 * xs)
        # inputs of the same row corrected by another rule
        scale, inputs = 1.0, []
        for _, o in corr[(corr.cur_id == c.cur_id) & corr.field.isin(
                ["CO2_conversion", "selectivity_CH3OH", "GHSV_nlph_gcat"])].iterrows():
            old, new = float(o.themecat), float(o.pdf)
            if old:
                scale *= new / old
                inputs.append(o.field)
        printed = float(c.pdf)
        corrected = r.STY_g_per_gcath * scale
        explained = False
        if inputs and printed > 0 and corrected > 0 and r.STY_g_per_gcath > 0:
            res, orig = abs(np.log(corrected / printed)), abs(np.log(r.STY_g_per_gcath / printed))
            explained = res <= 0.5 * orig and res <= np.log(2)
        if derived and (yield_bad or yield_alone):
            verdict = "ERR"
        elif derived and explained:
            verdict = "DER"
        elif derived:
            verdict = "CONV"
        else:
            verdict = "ERR"
        out[(c.cur_id, round(float(c.themecat), 6))] = dict(
            cur_id=int(c.cur_id), sty_from_yield=from_yield, sty_from_xs=from_xs, sty_is_derived=derived,
            yield_stored=r.yield_CH3OH, x_times_s=xs, yield_alone=yield_alone, yield_inconsistent=yield_bad,
            corrected_inputs=";".join(inputs), sty_with_corrected_inputs=corrected if inputs else np.nan,
            sty_verdict=verdict)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh-subset", help="full TheMeCat_v1.csv; rewrites themecat_v1_subset.csv")
    args = ap.parse_args()
    if args.refresh_subset:
        refresh_subset(args.refresh_subset)
    tm = pd.read_csv(SUBSET, index_col="cur_id")
    cells = pd.read_csv(HERE / "errata_classification.csv")
    applied = pd.read_csv(REPO / "agent" / "extraction" / "eval" / "errata_applied.csv")

    # ---- the STY column of TheMeCat is a derivation, on every row of the dataset
    f_all = tm.GHSV_nlph_gcat / (1 + tm.pH2_pCO2_ratio) * M_MEOH / V_M_THEMECAT
    ok = tm.STY_g_per_gcath.notna() & tm.yield_CH3OH.notna() & f_all.notna()
    reproduced = np.isclose(tm.STY_g_per_gcath[ok], (tm.yield_CH3OH / 100 * f_all)[ok], rtol=0.03, atol=6e-5)

    # ---- cell level: row id and the dataset value read back from the raw TheMeCat rows. errata_classification.py
    # writes the TheMeCat / Suvarna cells in the row order of errata_applied.csv, then the Humphreys cells.
    n = len(applied)
    head = cells.iloc[:n]
    same = (head.doi.fillna("").values == applied.doi.fillna("").values) & (head.field.values == applied.field.values)
    if not same.all():
        raise SystemExit("errata_classification.csv is not in the row order of errata_applied.csv")
    cells["row_id"] = list(applied.cur_id.astype(str)) + [""] * (len(cells) - n)
    raw_check = []
    for _, c in cells.iterrows():
        if c.dataset == "TheMeCat" and c.field in tm.columns and str(c.row_id) != "":
            v = tm.at[int(c.row_id), c.field]
            try:
                raw_check.append(bool(np.isclose(float(v), float(c.dataset_value), rtol=1e-6, atol=1e-9)))
            except ValueError:
                raw_check.append(str(v).strip() == str(c.dataset_value).strip())
        else:
            raw_check.append(None)
    cells["raw_value_matches"] = raw_check

    sty = sty_test(cells, tm, applied)
    rules = rule_key(cells)
    rules = rules.merge(cells.groupby("rule").row_id.apply(lambda s: ";".join(str(x) for x in s)).rename("row_ids"),
                        on="rule")

    final, root, root_text, basis = [], [], [], []
    for _, r in rules.iterrows():
        rc = cells[cells.rule == r.rule]
        if r.first_class == "N-minor":
            v, b = "MINOR", "差异 ≤2% 且不超过印刷值末位一个单位，属读数或舍入"
        elif r.dataset == "TheMeCat" and r.field == "STY_g_per_gcath":
            vs = [sty[(int(x.row_id), round(float(x.dataset_value), 6))]["sty_verdict"] for _, x in rc.iterrows()]
            v = "ERR" if "ERR" in vs else ("DER" if "DER" in vs else "CONV")
            if v == "CONV":
                b = ("数据集 STY 由本行 收率×空速×CO2 分率×32.04/24.05 推算（不是转录值）；与原文印刷 STY 的差别来自"
                     "原文自身的 STY 定义、摩尔体积 24.05 L/mol 或收率保留 0.1 个百分点")
            elif v == "DER":
                b = "数据集 STY 为推算值，用同一行已确认的输入更正后，与印刷值的偏差消去一半以上且不超过 2 倍（余量为原文速率与 X×S×F 之差），计入输入的根因"
            else:
                b = "数据集 STY 为推算值，但其所用收率本身与原文不符（与本行 X×S 矛盾或单独存放），计为收率错误"
        elif r.dataset == "Suvarna 2022" and r.field == "STY_g_per_gcath":
            v, b = "CONV", "原文 Table 6 / Fig. 7D 按每克 Cu、正文按每克催化剂给同一组数，均与 X×S×F 不符；不计"
        elif r.first_class == "C-derived":
            v, b = "DER", "STY 原文未印刷，数据集由 X×S×F 推算，随选择性 ×100 一同出错"
        else:
            v = "ERR"
            loc = str(r.evidence)
            plot = any(s in loc for s in ("Fig.", "Figure")) and not any(
                s in loc for s in ("text", "Table", "Section", "Experimental", "abstract"))
            b = ("原文图读数核对" if plot else "原文/SI 印刷值核对") + ("；Humphreys 原始文献 DOI " +
                                                         HUMPHREYS_DOI.get(humphreys_ref(loc), "")
                                                         if r.dataset.startswith("Humphreys") else "")
        rid, rtext = root_of(r.dataset, r.doi if isinstance(r.doi, str) else "", r.field, r.evidence)
        if v in ("ERR", "DER") and rid is None:
            raise SystemExit(f"no root cause for {r.check_no}: {r.rule}")
        final.append(v)
        root.append(rid if v in ("ERR", "DER") else "")
        root_text.append(rtext if v in ("ERR", "DER") else "")
        basis.append(b)
    rules["final_class"] = final
    rules["final_label"] = rules.final_class.map(LABEL)
    rules["error_kind"] = [KIND_ZH.get(c, "") if f == "ERR" else "" for c, f in zip(rules.first_class, final)]
    rules["root_id"] = root
    rules["root_cause"] = root_text
    rules["root_cause_en"] = [ROOT_EN.get(x, "") for x in root]
    rules["basis"] = basis
    rules["source_doi"] = [HUMPHREYS_DOI.get(humphreys_ref(e), "") if d.startswith("Humphreys") else dd
                           for d, dd, e in zip(rules.dataset, rules.doi.fillna(""), rules.evidence)]
    rules["locator"] = [e.split(":")[0] if ":" in e else "" for e in rules.evidence.astype(str)]
    rules["unit_of_count"] = np.where(rules.field.eq("(row dropped)"), "records", "value cells")
    cols = ["check_no", "dataset", "doi", "source_doi", "field", "cells", "unit_of_count", "first_class", "final_class",
            "final_label", "error_kind", "root_id", "root_cause", "root_cause_en", "max_rel_diff", "locator", "basis", "evidence",
            "row_ids", "rule"]
    rules[cols].to_csv(HERE / "errata_adjudication.csv", index=False, encoding="utf-8-sig", float_format="%.6g")

    cells = cells.merge(rules[["rule", "check_no", "final_class", "root_id"]], on="rule")
    extra = []
    for _, c in cells.iterrows():
        s = sty.get((int(c.row_id), round(float(c.dataset_value), 6))) if (
            c.dataset == "TheMeCat" and c.field == "STY_g_per_gcath" and str(c.row_id) != "") else None
        extra.append(s or {})
    ex = pd.DataFrame(extra).drop(columns=["cur_id"], errors="ignore")
    cells = pd.concat([cells.reset_index(drop=True), ex], axis=1)
    keep = ["check_no", "dataset", "doi", "row_id", "catalyst_name", "field", "dataset_value", "raw_value_matches",
            "paper_value", "rel_diff", "proposed_class", "final_class", "root_id", "sty_is_derived", "sty_from_yield",
            "sty_from_xs", "yield_stored", "x_times_s", "yield_alone", "yield_inconsistent", "corrected_inputs",
            "sty_with_corrected_inputs", "sty_verdict", "evidence"]
    cells[[k for k in keep if k in cells.columns]].sort_values(["check_no", "row_id"], key=lambda s: s.astype(str)) \
        .to_csv(HERE / "errata_cells_audit.csv", index=False, encoding="utf-8-sig", float_format="%.6g")

    # ---- the 40 methanol groups carry the paper's values where a root cause sits in their source paper
    lit = pd.read_csv(REPO / "analysis" / "meoh_literature_inversion_2026_10_05" / "literature_candidates.csv")
    checks = []
    for doi, cat, t, col, want, rid in MAIN_RESULT_CHECKS:
        s = lit[(lit.doi == doi) & lit.catalyst.str.contains(cat, regex=False)]
        if rid == "T4":
            s = s[s.catalyst.str.contains("Ba", regex=False)]
        if t is not None:
            s = s[np.isclose(s.T_C, t, atol=0.01)]
        got = s[col].tolist()
        if isinstance(want, set):
            ok_ = bool(len(got)) and set(got) <= want
        else:
            ok_ = bool(len(got)) and all(abs(float(g) - want) <= 0.01 * abs(want) for g in got)
        checks.append(dict(root_id=rid, doi=doi, catalyst=cat, T_C=t, column=col, expected=str(want),
                           used=";".join(str(g) for g in sorted(set(got), key=str)), ok=ok_))
    checks = pd.DataFrame(checks)
    if not checks.ok.all():
        raise SystemExit("group input differs from the paper value:\n" + checks[~checks.ok].to_string())
    group_dois = set(lit.doi)

    err = rules[rules.final_class == "ERR"]
    der = rules[rules.final_class == "DER"]
    counted = pd.concat([err, der])
    value_cells = counted[counted.unit_of_count == "value cells"]

    def by_ds(df, f):
        return {k: int(v) for k, v in f(df).items()}

    summary = dict(
        rules=int(len(rules)),
        cells_first_pass=int(len(cells)),
        themecat_sty_reproduced_from_yield=dict(rows=int(ok.sum()), reproduced=int(reproduced.sum()),
                                                molar_volume_L_per_mol=V_M_THEMECAT),
        raw_rows_read_back=dict(themecat_cells=int(sum(v is not None for v in cells.raw_value_matches)),
                                match=int(sum(v is True for v in cells.raw_value_matches))),
        rules_by_final_class=rules.final_class.value_counts().to_dict(),
        confirmed=dict(
            root_causes=int(err.root_id.nunique()),
            error_rules=int(len(err)),
            derived_rules=int(len(der)),
            value_cells=int(value_cells.cells.sum()),
            value_cells_error_rules=int(err[err.unit_of_count == "value cells"].cells.sum()),
            value_cells_derived=int(der.cells.sum()),
            dropped_records=int(counted[counted.unit_of_count == "records"].cells.sum()),
            source_papers=int(counted.source_doi.nunique()),
            root_causes_by_dataset=by_ds(err, lambda d: d.groupby("dataset").root_id.nunique()),
            error_rules_by_dataset=by_ds(err, lambda d: d.dataset.value_counts()),
            value_cells_by_dataset=by_ds(value_cells, lambda d: d.groupby("dataset").cells.sum()),
            source_papers_by_dataset=by_ds(counted, lambda d: d.groupby("dataset").source_doi.nunique()),
            root_causes_by_kind=by_ds(err.drop_duplicates("root_id"), lambda d: d.error_kind.value_counts()),
        ),
        not_counted=dict(convention_rules=int((rules.final_class == "CONV").sum()),
                         convention_cells=int(rules[rules.final_class == "CONV"].cells.sum()),
                         minor_rules=int((rules.final_class == "MINOR").sum()),
                         minor_cells=int(rules[rules.final_class == "MINOR"].cells.sum())),
        reclassified_from_first_pass=dict(
            first_pass_error_rules=int(rules.first_class.str.startswith("E").sum()),
            error_to_convention=int((rules.first_class.str.startswith("E") & (rules.final_class == "CONV")).sum()),
            error_to_derived=int((rules.first_class.str.startswith("E") & (rules.final_class == "DER")).sum())),
        root_causes=[dict(root_id=rid, text=rt, dataset=ds,
                          rules=int((counted.root_id == rid).sum()),
                          cells=int(counted[counted.root_id == rid].cells.sum()),
                          in_methanol_groups=bool(d in group_dois))
                     for ds, d, _f, rid, rt in ROOTS],
        main_result_checks=checks.to_dict(orient="records"),
    )
    (HERE / "errata_adjudication_summary.json").write_text(
        json.dumps(summary, indent=1, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o))
        + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("rules", "themecat_sty_reproduced_from_yield", "raw_rows_read_back",
                                               "rules_by_final_class", "confirmed", "not_counted",
                                               "reclassified_from_first_pass")}, indent=1, ensure_ascii=False,
                     default=int))


if __name__ == "__main__":
    main()
