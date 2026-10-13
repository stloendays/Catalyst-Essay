"""screening.csv: one row per candidate that reached S2, in rank order (PREREGISTRATION.md section 4).

Stages: S1 screening_s1.csv; S2 fetch_manifest.json (nus-fetch status); S3 s3_fulltext.csv (full-text decision);
S4 si_manifest.json (fetch_si.py status). decision = include when S3 passes and the SI was retrieved (status ok);
the first 40 inclusions in rank order form the batch, later candidates are marked "below the 40th inclusion".
"""
import json

import pandas as pd

from pv_common import HERE

MAX_INCLUDED = 40


def main():
    s1 = pd.read_csv(HERE / "screening_s1.csv")
    man = {r["doi"]: r for r in json.loads((HERE / "fetch_manifest.json").read_text(encoding="utf-8"))}
    s3 = pd.read_csv(HERE / "s3_fulltext.csv").set_index("doi") if (HERE / "s3_fulltext.csv").exists() else None
    sip = HERE / "si_manifest.json"
    si = {r["doi"]: r for r in json.loads(sip.read_text(encoding="utf-8"))} if sip.exists() else {}
    rows, n_inc = [], 0
    for r in s1[s1.s1 == "pass"].itertuples():
        m = man.get(r.doi)
        if m is None:
            continue                                   # not yet sent to S2
        row = dict(rank=r.rank, doi=r.doi, s2=m["status"], pdf_pages=m.get("pages"), doi_in_pdf=m.get("doi_in_pdf"),
                   s3="", s3_reason="", s3_evidence="", s4="", s4_files=0, decision="", reason="")
        if m["status"] not in ("ok", "skip"):
            row.update(decision="not retrieved", reason=f"nus-fetch status {m['status']}: {str(m.get('note') or '')[:120]}")
        elif s3 is None or r.doi not in s3.index:
            row.update(decision="not screened", reason="S3 pending")
        else:
            x = s3.loc[r.doi]
            row.update(s3=x.s3, s3_reason=x.s3_reason, s3_evidence=x.s3_evidence)
            if x.s3 != "pass":
                row.update(decision="exclude", reason=x.s3_reason)
            elif r.doi not in si:
                row.update(decision="not screened", reason="S4 (SI) pending")
            else:
                st = si[r.doi]["status"]
                row.update(s4=st, s4_files=len(si[r.doi].get("files", [])))
                if st != "ok":
                    row.update(decision="exclude", reason=f"criterion 5: SI not retrieved ({st}; {si[r.doi].get('note', '')})")
                elif n_inc >= MAX_INCLUDED:
                    row.update(decision="not counted", reason="below the 40th inclusion")
                else:
                    n_inc += 1
                    row.update(decision="include", reason=f"inclusion {n_inc}")
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "screening.csv", index=False)
    print(out.decision.value_counts().to_dict(), "| S3 pass:", int((out.s3 == "pass").sum()))


if __name__ == "__main__":
    main()
