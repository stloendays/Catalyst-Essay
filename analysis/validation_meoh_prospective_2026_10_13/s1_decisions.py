"""Stage S1 (title and abstract) decisions, in rank order (PREREGISTRATION.md section 4). Ambiguous records pass.

Writes screening_s1.csv for ranks 1..LAST_RANK of search_results.csv (rows without a DOI and repeated DOIs dropped).
"""
import pandas as pd

from pv_common import HERE

LAST_RANK = 220
REVIEW, THEORY, OTHER_PRODUCT = "review / perspective / account", "computation or modelling only", "target product is not methanol"
EXCLUDE = {
    1: REVIEW, 3: THEORY + " (microkinetics)", 6: THEORY + " (DFT, Cu2O(111))", 10: REVIEW, 11: REVIEW, 12: REVIEW,
    21: REVIEW, 22: "photothermal", 27: REVIEW, 29: REVIEW, 30: REVIEW, 34: REVIEW, 45: "plasma", 52: "plasma",
    57: "process optimisation, no catalyst measurement", 60: REVIEW, 69: REVIEW, 86: THEORY, 88: "homogeneous catalysis",
    91: REVIEW + " (photothermal)", 94: REVIEW + " (plasma)", 95: REVIEW + " (account, repository copy)",
    96: REVIEW + " (DME)", 100: REVIEW, 102: "preview / highlight", 105: "homogeneous catalysis",
    107: OTHER_PRODUCT + " (LPG)", 108: THEORY + " (microkinetics)", 112: "plasma", 114: REVIEW,
    115: THEORY + " (DNS)", 117: REVIEW + " (homogeneous)", 118: REVIEW + " (homogeneous)", 120: OTHER_PRODUCT + " (aromatics)",
    121: "homogeneous catalysis", 123: REVIEW, 124: REVIEW, 127: "techno-economic / LCA", 129: OTHER_PRODUCT + " (ethanol)",
    131: REVIEW, 132: OTHER_PRODUCT + " (p-xylene)", 136: "preview / highlight", 137: OTHER_PRODUCT + " (aromatics)",
    138: REVIEW, 139: THEORY + " (DFT)", 141: OTHER_PRODUCT + " (aromatics)", 143: "plasma", 144: REVIEW,
    145: OTHER_PRODUCT + " (CH4)", 148: REVIEW, 149: "electrochemical", 153: THEORY + " (microkinetics)",
    154: "photothermal", 156: "electrochemical", 159: REVIEW, 160: THEORY + " (process simulation)", 161: REVIEW,
    162: THEORY + " (machine learning on literature data)", 163: OTHER_PRODUCT + " (olefins)", 169: REVIEW,
    173: OTHER_PRODUCT + " (olefins)", 174: OTHER_PRODUCT + " (CO)", 176: "perspective", 177: REVIEW,
    179: OTHER_PRODUCT + " (C3+ alcohols)", 180: "perspective", 181: REVIEW, 182: OTHER_PRODUCT + " (ethanol)",
    184: REVIEW, 185: REVIEW + " (DME)", 191: "methanol-to-hydrogen (photothermal)", 193: "dry reforming",
    200: OTHER_PRODUCT + " (DME)", 202: OTHER_PRODUCT + " (olefins)", 204: THEORY + " (membrane reactor model)",
    206: "life-cycle assessment", 212: REVIEW, 213: "plasma", 217: "slurry (liquid-phase) reactor kinetics",
    218: REVIEW + " (account)", 219: REVIEW, 220: THEORY + " (machine learning)",
}


# Ranks 221-400 (screened second, once 1-220 were exhausted of candidates): the records that pass; every other record
# of this range is excluded by its title as not a thermocatalytic CO2-to-methanol measurement (reviews, other
# products, electro-/photo-/plasma-driven, homogeneous, computation, reforming, other reactions).
PASS_221_400 = {222, 225, 226, 227, 228, 229, 231, 233, 237, 239, 240, 245, 248, 252, 253, 254, 256, 261, 263, 267,
                273, 277, 278, 281, 293, 296, 303, 304, 305, 306, 307, 312, 313, 314, 315, 319, 334, 335, 354, 366,
                367, 387, 389, 400}
OFF_TOPIC = "title: not a thermocatalytic CO2-to-methanol measurement (review, other product or reaction, " \
            "electro-/photo-/plasma-driven, homogeneous or computation)"
LAST_RANK = 400
for _r in range(221, LAST_RANK + 1):
    if _r not in PASS_221_400:
        EXCLUDE[_r] = OFF_TOPIC


def main():
    d = pd.read_csv(HERE / "search_results.csv")
    d = d[d["rank"] <= LAST_RANK]
    nodoi = d.doi.isna()
    dup = d.doi.duplicated() & ~nodoi
    rows = []
    for r in d.itertuples():
        if pd.isna(r.doi):
            rows.append(dict(rank=r.rank, doi="", s1="dropped", s1_reason="no DOI"))
        elif dup[r.Index]:
            rows.append(dict(rank=r.rank, doi=r.doi, s1="dropped", s1_reason="repeated DOI"))
        elif r.rank in EXCLUDE:
            rows.append(dict(rank=r.rank, doi=r.doi, s1="exclude", s1_reason=EXCLUDE[r.rank]))
        else:
            rows.append(dict(rank=r.rank, doi=r.doi, s1="pass", s1_reason=""))
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "screening_s1.csv", index=False)
    print(out.s1.value_counts().to_dict())
    p = out[out.s1 == "pass"]
    (HERE / "s1_pass_dois.txt").write_text("\n".join(p.doi) + "\n", encoding="utf-8")
    print("non-Elsevier passes:", int((~p.doi.str.startswith("10.1016/")).sum()))


if __name__ == "__main__":
    main()
