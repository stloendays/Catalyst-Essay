# Working-document figure sync — a locked repo asset is not a synced document (2026-09-16)

A figure can be LOCKED and content-addressed in this repository while the working document that people actually read
still embeds an older render of the same figure. That happened, it was not caught by any existing check, and this note
records the finding and the check that catches it.

## What happened

The Gist working document (`Gist 工作文档.docx`) embedded **FINAL-1.0** renders for Figures 1–6 while the repository had
the **FINAL-1.1** renders locked since 2026-09-05 and validated on 2026-09-10.

The embedded Figure 5 carried the title *"Ru requires a 2171.56-fold activity increase to reach Fe cost parity"*, an Fe
optimum of \$10.199/t, a Ru baseline of \$17.592/t, a break-even operating point of 400 °C / 155 bar, and a footnote
reading *"under NH₃-FINAL-1.0"*. The canonical FINAL-1.1 asset gives **201.22×**, Fe **15.292 USD/t**, Ru **22.031 USD/t**
and 425 °C / 190 bar. The embedded Figure 4 was titled *"Final optimized pressure envelopes (NH3-FINAL-1.0)"* with a
pressure axis truncated at the 300 bar FINAL-1.0 edge.

The failure mode is worth naming precisely. The first pass over this discrepancy checked the **provenance bundle**
assets, found them correct, and concluded that no figure needed redoing. That conclusion was wrong: the bundle and the
document are different artefacts, and only the document is what a reader or a supervisor sees. Verifying the canonical
asset says nothing about what a distributed document contains.

## The check

Embedded images are addressable. Compare the SHA-256 of every image part inside the `.docx` against the locked assets:

```python
import docx, zipfile, hashlib
from docx.oxml.ns import qn
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"

d, z = docx.Document(path), zipfile.ZipFile(path)
for i, p in enumerate(d.paragraphs):
    for blip in p._p.findall(".//" + qn("a:blip")):
        part = d.part.rels[blip.get(RID)].target_ref.split("/")[-1]
        sha = hashlib.sha256(z.read("word/media/" + part)).hexdigest()
        # compare sha against the locked asset for the caption that precedes this paragraph
```

Two properties make this reliable: each figure sits alone in its own paragraph directly after its caption, so the
caption identifies which locked asset the image should match; and a mismatch is decisive, because the locked assets are
already content-addressed in `data/figure_lock_registry_2026-09-10.csv`.

## What was corrected

Figures 1–6 in the working document were replaced with the locked FINAL-1.1 renders from
`provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z/figures/`. All six were verified
byte-identical to the locked assets after the swap. On-page width (5.77 in) and position were preserved; height follows
each new image's own aspect ratio. The original document was not modified — the corrected document is a new file.

Figure 9 in the working document embeds the legacy cross-reaction leverage figure showing **328× (273–410×)** and the
NH₃ TOF normalization **0.001145**, both derived from the pre-FINAL-1.1 ≈10.2 USD/t baseline. That figure is classified
`METRIC_EQUIVALENCE_NOT_ESTABLISHED` and is excluded from the current manuscript. It was **not deleted**: the caption is
now marked `[ARCHIVED — pre-FINAL-1.1 normalization; not used for any current claim]` with a note recording the HOLD
status, so the document does not present a withdrawn number as current.

Figures 7 and 8 in the working document are older MeOH renders that differ from the repository's locked assets
(`figures/meoh/MeOH_F03_UpstreamToEconomicRanking_D01v3.png` and
`figures/meoh/F08_MeOH_selectivity_recycle_D01v3.svg`). Their numbers are not wrong, but they are different figures with
different panel compositions, so swapping them requires rewriting the captions. Left unchanged pending that decision.

## Rule

Before any working document is circulated or submitted, every embedded figure is verified against the locked asset by
hash, not by filename, caption or memory. Locking an asset in the repository and updating a caption are two separate
actions, and neither one updates the other.
