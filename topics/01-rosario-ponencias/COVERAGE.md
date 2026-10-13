# How the list of Justice Rosario's ponencias was built

Checked on October 13, 2026. Cutoff: promulgated on or before June 30, 2026.

## Result

**89 decisions and resolutions** with "ROSARIO, J." as ponente (main opinion), June 2021 to April 2026.

| | Count |
|---|---|
| En Banc | 33 |
| First Division | 48 |
| Second Division | 5 |
| Third Division (one is a Special Third Division) | 3 |
| Decisions / Resolutions | 82 / 7 |
| G.R. cases / administrative and disciplinary cases (A.M., A.C., OCA IPI, JIB) | 72 / 17 |
| By year: 2021 / 2022 / 2023 / 2024 / 2025 / 2026 | 7 / 14 / 10 / 11 / 38 / 9 |

The full list, with source links, is in [ponencias-index.json](ponencias-index.json).

## Sources and method

1. **SC E-Library.** Every decision listed for October 2020 to June 2026 (3,508 documents) was opened and the
   ponente line read from the decision itself (`tools/find_ponencias_elib.py`). 89 matched ROSARIO.
2. **SC website.** All 8,258 posts were listed through the site's API (`tools/list_sc_posts.py`). The 945 decision
   PDFs not already in the E-Library crawl were downloaded and their text read (`tools/scan_sc_pdfs.py`).
   Eight were Rosario ponencias, all already found in step 1.
3. **Scanned PDFs.** 143 PDFs had no readable text or garbled OCR. Each was checked page by page. Two were
   Rosario ponencias, both already in the list. Most of the rest were unsigned Notices of Resolution, which have no ponente.
4. **Cross-check.** SC press releases that credit "Associate Justice Ricardo R. Rosario" as writer
   (G.R. Nos. 269921, 222448, 263615, 255749) are all in the list.

## Limits

- The Court uploads decisions to the E-Library and website months after promulgation. A decision promulgated before
  June 30, 2026 but not yet uploaded by October 13, 2026 cannot appear here. Re-run the pipeline in CLAUDE.md
  closer to the exam to catch late uploads; `merge_ponencias.py` keeps the status of cases already digested.
- Separate (concurring/dissenting) opinions by Justice Rosario are excluded, because only main opinions are examinable.
- Unsigned minute resolutions are excluded because they have no ponente.
