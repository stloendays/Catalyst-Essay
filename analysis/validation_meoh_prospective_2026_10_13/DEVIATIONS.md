# Deviations from PREREGISTRATION.md

Recorded when they occurred, before any extraction output or plant-model output of the new batch existed.

## D1. Criterion 5 (SI retrieved) deferred where the NUS EZproxy session had expired (2026-10-13)

- `fetch_si.py` needs a valid NUS EZproxy session for ACS, Wiley, Springer, Nature and Science SI. The session expired
  twice during the SI runs (`fetch_si.log`, `fetch_si_2.log`: "EZproxy session not logged in"). Logging in needs the
  user's MFA approval, which was not available unattended; no login was automated beyond starting the nus-fetch login
  helper.
- For 23 S3-passing candidates the SI could therefore not be checked. Following PR #78 (whose first batch-2 run hit
  the same expired session and kept the papers, with SI passes run later), these candidates are **included with S4
  marked "deferred"** in `screening.csv`. A definitive negative result still excludes: `fetch_si.py` found no SI
  link on the publisher page (status `none`) for 3 Springer papers, and no SI file on the Elsevier CDN
  (`none_public`) for 1 paper, so those 4 are excluded under criterion 5.
- **Resolved the same day, before any outcome existed.** The session became valid again (the user approved the
  login) while the main pass was paused at the API-YES usage limit. `fetch_si.py` was rerun for every deferred
  candidate (`fetch_si_3.log`): SI retrieved for all but 3 (no SI link on the publisher page: Int. J. Green Energy
  10.1080/15435075.2026.2701155, NSR 10.1093/nsr/nwag532, ACS Omega 10.1021/acsomega.5c11195). The pre-registered
  criterion 5 was then applied as written: those 3 are excluded, and the next three S3-passing candidates in rank
  order (313, 314, 319) complete the 40. None of the 3 had been extracted. D1 therefore leaves no trace in the
  included set; it is kept here as the record of the interruption.
- (Superseded) Consequence while D1 was in force: the 40 included papers are the first 40 S3-passing candidates in rank order after these 4
  exclusions. The si and si_figures extraction passes run for the papers whose SI was retrieved; the others are
  extracted from the main text (main and figures passes), as in PR #78's first batch-2 run.
