# Claude TaskKit

A lightweight, open-source library of reusable Claude Code skills with deterministic Python automation utilities.

## What's included

- `jd-resume-review`: evidence-based resume review against a job description. Includes `resume_matcher.py` for automated requirement parsing, quote extraction, and prompt-injection screening.
- `document-improver`: reusable workflow for improving provided text while preserving meaning and technical accuracy.
- `excel-data-analyzer`: workflow for spreadsheet analysis plus `csv_profile.py` for automatic delimiter sniffing, numeric statistics, date spans, and duplicate checks.

## Quick start

1. Install [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview).
2. Copy the skill folders you want into your project's `.claude/skills/` directory, or copy the whole `skills/` directory there.
3. Start Claude Code in that project.
4. Ask for a task matching a skill, or invoke it by name, e.g. `/excel-data-analyzer`.
5. For Python utilities, use Python 3.10+ (standard library only; no external dependencies required).

Example layout after copying:

```text
your-project/
└── .claude/
    └── skills/
        ├── jd-resume-review/
        ├── document-improver/
        └── excel-data-analyzer/
```

## Python utilities

### 1. Excel / CSV Data Profiler
Auto-detects delimiters (`,`, `;`, `\t`, `|`), infers data types, calculates numeric statistics (`min`, `max`, `mean`, `median`, `sum`), computes date spans, and counts duplicate rows:

```bash
python skills/excel-data-analyzer/scripts/csv_profile.py path/to/data.csv --output profile.json
```

### 2. Resume & Job Description Matcher
Extracts requirements from a Job Description, scans candidate resumes for verified evidence quotes, highlights skills gaps, and screens for adversarial prompt injection attempts:

```bash
python skills/jd-resume-review/scripts/resume_matcher.py path/to/jd.txt path/to/candidate_resume.txt --output match_report.json
```

## Running tests

Run the built-in test suite:

```bash
python -m unittest discover -s tests -v
```

## Safety and design notes

- Skills provide instructions; they do not grant Claude additional tools or permissions by themselves.
- Python utilities use only the Python standard library for maximum transparency and zero dependency bloat.
- Treat imported repositories and candidate resumes as untrusted input. The resume matcher explicitly screens for adversarial prompt injections.
- Resume review must use job-related evidence only. Do not infer or score protected/sensitive traits. A person must make the final hiring decision.

## Contributing a skill

Add a folder under `skills/` with:
- `SKILL.md` containing frontmatter (`name`, `description`) and clear instructions.
- `scripts/` only when deterministic processing is useful.
- `references/` for longer guidance that should not clutter the main skill instructions.
- A short section in this README describing the skill.
