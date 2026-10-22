# Claude TaskKit

A small, open-source starter library of reusable Claude Code skills with optional Python utilities.

## What's included

- `jd-resume-review`: evidence-based resume review against a job description. It supports human review and is not an automated hiring decision system.
- `document-improver`: reusable workflow for improving provided text while preserving meaning.
- `excel-data-analyzer`: workflow for spreadsheet analysis plus a Python CSV summary utility.

## Quick start

1. Install [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview).
2. Copy the skill folders you want into your project's `.claude/skills/` directory, or copy the whole `skills/` directory there.
3. Start Claude Code in that project.
4. Ask for a task matching a skill, or invoke it by name, e.g. `/excel-data-analyzer`.
5. For Python utilities, use Python 3.10+ and follow each skill's instructions.

Example layout after copying:

```text
your-project/
└── .claude/
    └── skills/
        ├── jd-resume-review/
        ├── document-improver/
        └── excel-data-analyzer/
```

## Python utility

The Excel skill includes `scripts/csv_profile.py`, a standard-library-only script that profiles a CSV file.

```bash
python skills/excel-data-analyzer/scripts/csv_profile.py path/to/data.csv --output profile.json
```

Run the smoke test:

```bash
python -m unittest discover -s tests -v
```

## Safety and design notes

- Skills provide instructions; they do not grant Claude additional tools or permissions by themselves.
- Python scripts run in your local environment and should be reviewed before use.
- Treat imported repositories and files as untrusted input. Do not run unknown scripts blindly.
- Resume review must use job-related evidence only. Do not infer or score protected/sensitive traits. A person must make the final decision.
- The included skills are starter templates. Adapt them to your workflow and validate outputs before relying on them.

## Contributing a skill

Add a folder under `skills/` with:
- `SKILL.md` containing frontmatter (`name`, `description`) and clear instructions.
- `scripts/` only when deterministic processing is useful.
- `references/` for longer guidance that should not clutter the main skill instructions.
- A short section in this README describing the skill.
