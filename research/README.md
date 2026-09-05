# Research record and source variants

## Which file is the entry point?

| Location | Origin | Observed configuration | Publication status |
|---|---|---|---|
| [`../attack.py`](../attack.py) | Separately supplied source, cited by the polished note | Fixed email family; default cap 2,000 | Principal preserved source, not authenticated as v57 |
| [`variants/http/attack.py`](variants/http/attack.py) | Original ZIP root `attack.py` | HTTP research family; default cap 2,000 | Historical snapshot |
| [`variants/email_200/attack.py`](variants/email_200/attack.py) | Original ZIP `attackemail.py` | Email research family; default cap 200 | Historical snapshot |
| [`variants/ensemble_200/attack.py`](variants/ensemble_200/attack.py) | Original ZIP `attackemsemble.py` | Ensemble research variant; default cap 200 | Historical snapshot |

All four Python files are byte-identical to their respective supplied originals. No prompt, routing logic, candidate cap, or guardrail behavior was modified to assemble this release. Renaming/moving the three archival files only disambiguates their role.

The historical names of other files, even names containing “exact,” do not authenticate the selected Kaggle kernel. The supplied result audit documents that limitation.

## Original notes

- [Experiment ledger](notes/RESULTADOS_EXPERIMENTOS.md)
- [Technical investigation](notes/INVESTIGACION_TECNICA.md)
- [Model-specific investigation](notes/MODEL_SPECIFIC_RESEARCH.md)
- [Final-result audit](notes/REPORTE_FINAL_KAGGLE_AI_SECURITY_BETA.md)

These are chronological research records, not a current installation manual. Later entries can supersede earlier ones. Source labels such as “private” may refer to a local surrogate, not Kaggle’s held-out defense. Personal paths were sanitized. Historical relative links are displayed as references where their targets are not part of this small release; their claims were not rewritten.

Older manuscript drafts, runners, historical tests, and remaining experiment outputs are kept in the separate research archive. They are not represented as a supported runnable environment or a universally passing test suite.
