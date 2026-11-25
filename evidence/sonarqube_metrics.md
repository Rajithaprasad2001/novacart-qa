# SonarQube analysis – NovaCart (project key `novacart-qa`)

- Server: SonarQube Community Build 26.11.0.134175 (local, http://localhost:9000, MQR mode)
- Scanner: sonar-scanner CLI 8.3.1 with `sonar-project.properties` (sources: `app.py`, `templates/`; tests: `tests`, `tests_ui`, `features`)
- Coverage input: `coverage.xml` from `pytest tests --cov=app --cov-branch --cov-report=xml`
- Analysis date: 2026-11-25. Quality gate: **Passed** (Sonar way)

## Key metrics (overall code)

| Metric | Value |
|---|---|
| Lines of code (ncloc) | 2,004 (2,676 lines; `app.py` + 10 templates, 12 files) |
| Coverage | **98.8 %** (line 99.2 %, branch 97.4 %; 2 of 249 lines and 2 of 78 conditions uncovered) |
| Duplications | 0.0 % |
| Security | 2 open issues, rating **D** (1 High, 1 Low) |
| Reliability | 1 open issue, rating **C** (Medium) |
| Maintainability (code smells) | **0** issues, rating **A** |
| Technical debt | **0 min** on maintainability (debt ratio 0.0 %); 11 min total remediation effort on all 3 issues |
| Security hotspots | 0 (SonarQube 26 reports former hotspots such as CSRF and debug mode as security issues) |
| Cyclomatic complexity | 75 total over 18 functions |
| Cognitive complexity | 73 |
| Comment density | 1.4 % |
| Defect density (QA defects) | 13 defects / 2.004 KLOC (Sonar ncloc) = 6.5 per KLOC; 22 per KLOC on 589 Python SLOC (radon) |

## Top issues (all 3 open issues – SonarQube reported fewer than 10)

| # | Severity (impact) | Type | Rule | Location | Message | Effort | Related QA defect |
|---|---|---|---|---|---|---|---|
| 1 | High (Security) | Vulnerability | python:S4502 | app.py:19 | Make sure disabling CSRF protection is safe here. | 5 min | BUG-02 |
| 2 | Medium (Reliability) | Bug | Web:InputWithoutLabelCheck | templates/detail.html:1 | Add an "id" attribute to this input field and associate it with a label. | 5 min | new (accessibility, WCAG 2 A) |
| 3 | Low (Security) | Vulnerability | python:S4507 | app.py:859 | Make sure this debug feature is deactivated before delivering the code in production. | 1 min | BUG-03 |

## Screenshots

- `screenshots/sonar_01_overview.png` – project summary, quality gate, ratings, coverage
- `screenshots/sonar_02_issues.png` – the 3 open issues
- `screenshots/sonar_03_measures.png` – coverage measures
- `screenshots/sonar_04_hotspots.png` – security hotspots page (none; moved into issues in this version)
