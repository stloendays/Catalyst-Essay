"""Catalyst families and scale-up classes for the revealed-preference validation (pre-registered, 2026-10-13).

Every rule uses only the catalyst name and the DOI of the frozen candidate tables (no performance or cost value). The
rules were fixed, and the resulting subsets written by make_subsets.py and committed with PREREGISTRATION.md, before
any outcome was computed.

Families (precedence top to bottom; the first rule that matches wins):

  blank        a bare support or single oxide run as a control (ZrO2, SiO2, TiO2, ZnO, ZnTiO3, Fe3O4, NiO and the
               phase variants of ZrO2). Excluded from the family tests H2/H3 and from the "other family" side of H1.
  In2O3        anything that contains indium (In2O3, In/ZrO2, M-promoted In2O3 incl. Pd-, Pt-, Ir-, Ni-, Co-, Cu-,
               Au-In2O3, InNi3C0.5 carbides, CoIn, In-Cu/CeO2, In2O3/ZrO2 physical mixtures).
  Pd           Pd-containing, indium-free (Pd/ZnO, PdZn, Pd-Cu, Pd/ZnZr, the Pd-Zn "P..Z.." codes).
  CuZnAl       Cu/ZnO/Al2O3-type: Cu + Zn + Al (commercial-type coprecipitated Cu-ZnO-Al2O3, CuZnAl, CZA-n,
               CZA200-400, Cu-Zn-Al(-Y) hydrotalcite-derived CHT-Y).
  Cu_other     other Cu catalysts without In or Pd (Cu/ZrO2, CuO-ZrO2 "CZ-", Cu/ZrO2/CNTs, Cu/Al2O3 with Ba/K,
               Cu/ZnO, Cu/SiO2, Cu/CeO2, CuO/CeZrOx).
  ZnZrOx       ZnO-ZrO2 binary oxide (x% ZnO-ZrO2, ZnZr).
  MZrOx_other  Zn-CdZrOx.
  Re           Re/TiO2.

Cu-based (H2) = CuZnAl + Cu_other.

Scale-up classes (H3), evidence in SCALE_EVIDENCE:
  scaled       CuZnAl (commercial methanol catalyst type), Cu-Zn-Zr(-Al) (Mitsui pilot type; no entry in either
               cohort), ZnZrOx (DICP 1,000 t/a demonstration, 2020)
  lab_only     every other non-blank family
  (blank entries are excluded)

Sensitivity class (pre-registered secondary, H3-alt): In2O3/ZrO2 without a further metal counted as scaled, because a
demonstration was announced (ETH Zurich / Total patent and scale-up statement) though no pilot data are published.
"""
import re

BLANKS = {"zro2", "m-zro2", "t-zro2", "a-zro2", "sio2", "tio2", "zno", "zntio3", "fe3o4", "nio"}

# DOI-level rules for name codes that do not spell their elements (checked against the extracted `composition` field)
DOI_IN = {"10.1002/ente.201800747"}                        # Cat-x: In2O3/Al2O3 on Al fibre
DOI_PD = {"10.1016/j.apcata.2018.04.036",                  # 5PC, 5P5ZC, 0.5Ca5P5ZC: Pd(-Zn)/CeO2
          "10.1016/j.cattod.2019.05.040",                  # 5P5ZZr-IMP: Pd-Zn/ZrO2
          "10.1016/j.fuel.2023.127927"}                    # PZC, x Ca-PZC: Pd-Zn/CeO2
DOI_CU = {"10.1039/c6ra28305e",                            # CZ-350..650: (CuO)0.5(ZrO2)0.5
          "10.1039/c5ra04774a"}                            # CZ/CNTs: Cu/ZrO2/CNTs
NAME_IN = {("10.1038/s41467-019-11349-9", "cp"),           # CP: 0.25 wt% Pd-promoted In2O3
           ("10.1021/acscatal.9b01869", "physical mixture"),
           ("10.1021/acscatal.9b01869", "pm-600"),
           ("10.1021/acscatal.9b01869", "pm-800")}         # 2.5 wt% In2O3 in ZrO2, physical mixtures

FAMILY_LABEL = {"blank": "bare support / single-oxide control", "In2O3": "In2O3-based", "Pd": "Pd-based",
                "CuZnAl": "Cu/ZnO/Al2O3-type", "Cu_other": "other Cu", "ZnZrOx": "ZnO-ZrO2 (ZnZrOx)",
                "MZrOx_other": "Zn-CdZrOx", "Re": "Re-based"}

SCALE_EVIDENCE = {
    "CuZnAl": "Commercial methanol catalyst type (Cu/ZnO/Al2O3). Commercial CO2-to-methanol: CRI George Olah plant "
              "(Svartsengi, Iceland, 2011-2012; 1,300 -> 4,000 t/a), built under Johnson Matthey licence with JM "
              "Cu/ZnO-based catalyst (carbonrecycling.com/projects/george-olah).",
    "CuZnZr": "Mitsui Chemicals CO2-to-methanol pilot, Osaka Works, ~100 t/a, 2009-2010 (Mitsui Chemicals release "
              "2008-08-25), Cu-based catalyst from the RITE/NEDO programme (Cu/ZnO/ZrO2/Al2O3/SiO2 type). No entry of "
              "this composition in either cohort.",
    "ZnZrOx": "ZnO-ZrO2 solid-solution catalyst at 1,000 t/a in the DICP liquid-sunshine demonstration, Lanzhou, 2020 "
              "(Chinese Academy of Sciences news, 2020-11-04; english.cas.cn/newsroom/research_news/chem/202011/"
              "t20201102_247124.shtml).",
    "In2O3ZrO2_announced": "In2O3/ZrO2: ETH Zurich-Total joint patent and an announced demonstration unit; no "
                           "published pilot data found (used only in the H3-alt sensitivity).",
}


def norm(name) -> str:
    s = str(name).split(" [")[0].strip().lower()
    for a in ("–", "−", "—"):
        s = s.replace(a, "-")
    return s


def family(name, doi) -> str:
    n = norm(name)
    if n in BLANKS:
        return "blank"
    if ("in2o3" in n or "inni" in n or "coin" in n or "inal" in n or re.search(r"(^|[^a-z])in(?![a-z])", n)
            or re.search(r"\din(?![a-z])", n) or doi in DOI_IN or (doi, n) in NAME_IN):
        return "In2O3"
    if "pd" in n or doi in DOI_PD:
        return "Pd"
    if "cza" in n or "cuznal" in n or "cu-zno-al2o3" in n or n.startswith("cht-y"):
        return "CuZnAl"
    if "cu" in n or doi in DOI_CU:
        return "Cu_other"
    if "zno-zro2" in n or n == "znzr":
        return "ZnZrOx"
    if "cdzrox" in n:
        return "MZrOx_other"
    if "re/tio2" in n:
        return "Re"
    raise ValueError(f"unclassified catalyst {name!r} ({doi})")


def cu_based(fam: str) -> bool:
    return fam in ("CuZnAl", "Cu_other")


def scale_class(name, doi) -> str:
    """'scaled' / 'lab_only' / 'blank' (primary H3 classification)."""
    f = family(name, doi)
    if f == "blank":
        return "blank"
    return "scaled" if f in ("CuZnAl", "ZnZrOx") else "lab_only"


def scale_class_alt(name, doi) -> str:
    """H3-alt: as scale_class, plus In2O3/ZrO2 with no further metal counted as scaled (announced demonstration)."""
    c = scale_class(name, doi)
    if c != "lab_only":
        return c
    n = norm(name)
    if family(name, doi) == "In2O3" and "zro2" in n and "-0zro2" not in n and not re.search(r"pd|pt|ir|ni|co|cu|au|y\d|la|ce|zn", n):
        return "scaled"
    return c
