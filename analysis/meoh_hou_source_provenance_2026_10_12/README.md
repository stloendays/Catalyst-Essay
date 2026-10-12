# Proposed source-level errata: Hou 2024, DOI 10.1016/j.jes.2023.05.010

**UNAPPLIED SOURCE PROPOSAL.** This folder deliberately does not edit the frozen extraction files or the primary 310 printed candidate analysis. The verified publisher article Section 1.4 specifies catalytic activity of Au/In2O3 and bare In2O3 with **H2:CO2:Ar=4:1:1**.

The 30 normalized source records contain:

| Original record discrepancy | Number of entries | Treatment |
|---|---:|---|
| Wrong source gas species named N2, while original method uses Ar | 13 | Propose replacing gas name and retain already correct 1/6 inert share, subject to scientific review |
| Only H2:CO2=4 written, without the full Ar-diluted feed | 5 | Propose full 4:1:1 lab feed; includes the 3 bare SI Table S5 points incorrectly assigned zero inert fraction |
| Gas feed and inert fraction absent from extracted SI Figure rows | 12 | **BLOCK applying change until source figure/caption applicability review** |

Exactly **6 of 30 Hou entries** occur in the existing 310-point printed methanol cohort: 3 Au/In2O3 whose inert fraction was already 1/6 and 3 bare In2O3 whose inert fraction was zero. The Ar fugacity chemical identity itself was N2-proxied for all six in the old lab equilibrium model.

Outputs of generate_erratum_proposal.py are the 30-row review proposal and summary. GitHub Actions independently verifies source-entry identity and counts, and saves a review artifact. Every row explicitly says UNAPPLIED_SIDE_CAR. No measured experimental conversion, methanol selectivity or STY is altered.

Private publisher PDF, PDF-SI and DOCX-SI source SHA256 manifest were independently verified by private GitHub Actions. The corresponding *prospective* lab-feed effects on 310-source-group economic conclusions have been separately modeled in the adjacent meoh_hou_feed_recheck_2026_10_12 directory.

**Do not automatically apply these proposals** to the paper's frozen primary figures, source extraction, or 24 non-primary plotted-source rows. Review and approve source patch first; then rebuild its affected upstream derivations, explicitly comparing old and new source-level hashes, before a new scientific freeze.
