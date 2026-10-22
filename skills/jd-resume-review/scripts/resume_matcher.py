#!/usr/bin/env python3
"""Evidence-based resume vs job description matcher and evidence extractor.

Standard-library only utility that parses job descriptions and candidate resumes,
extracts verifiable evidence phrases, highlights skills gaps, and flags prompt injections.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

# Prompt injection tripwires commonly found in adversarial resumes
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"system\s*prompt", re.IGNORECASE),
    re.compile(r"you\s+must\s+(give|rate|score)\s+this\s+candidate", re.IGNORECASE),
    re.compile(r"hire\s+this\s+candidate\s+immediately", re.IGNORECASE),
    re.compile(r"override\s+(all\s+)?rules", re.IGNORECASE),
]

COMMON_STOPWORDS = {
    "and", "the", "with", "for", "that", "this", "from", "have", "will", "your",
    "must", "should", "able", "work", "team", "experience", "years", "role",
    "responsibilities", "requirements", "skills", "knowledge", "using", "plus",
}


def scan_for_injections(text: str) -> list[str]:
    """Detect potential prompt injection strings embedded in candidate documents."""
    findings = []
    for pattern in INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            findings.append(match.group(0))
    return findings


def extract_text_from_file(path: Path) -> str:
    """Read document text, supporting plain text, markdown, or raw streams safely."""
    try:
        # Standard UTF-8 text / markdown
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except Exception as e:
        return f"[Error reading file {path.name}: {e}]"


def extract_jd_requirements(jd_text: str) -> list[str]:
    """Extract individual requirements and key qualifications from a job description."""
    lines = [line.strip() for line in jd_text.splitlines() if line.strip()]
    requirements = []

    for line in lines:
        # Bullet points or numbered lists
        bullet_match = re.match(r"^[\-\*\•\d+\.]\s+(.*)", line)
        if bullet_match:
            item = bullet_match.group(1).strip()
            if len(item) > 10:
                requirements.append(item)
        elif len(line) > 20 and any(keyword in line.lower() for keyword in ["required", "experience", "proficient", "bachelor", "master", "knowledge"]):
            requirements.append(line)

    if not requirements:
        # Fallback to sentence split
        sentences = re.split(r"(?<=[.!?])\s+", jd_text)
        requirements = [s.strip() for s in sentences if len(s.strip()) > 20][:10]

    return requirements


def extract_keywords(phrase: str) -> set[str]:
    """Extract meaningful domain and technical keywords from a requirement string."""
    tokens = re.findall(r"\b[A-Za-z0-9\+\#\.\-]{2,}\b", phrase)
    return {t.lower() for t in tokens if t.lower() not in COMMON_STOPWORDS and len(t) > 2}


def evaluate_resume(
    resume_path: Path, requirements: list[str]
) -> dict[str, Any]:
    """Compare a single resume against extracted job description requirements."""
    content = extract_text_from_file(resume_path)
    injections = scan_for_injections(content)

    sentences = re.split(r"(?<=[.!?\n])\s+", content)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]

    matches = []
    missing_evidence = []
    suggested_questions = []

    for req in requirements:
        req_keywords = extract_keywords(req)
        if not req_keywords:
            continue

        best_sentence = ""
        best_overlap = 0

        for sentence in sentences:
            sentence_lower = sentence.lower()
            overlap = sum(1 for kw in req_keywords if kw in sentence_lower)
            if overlap > best_overlap:
                best_overlap = overlap
                best_sentence = sentence

        if best_overlap >= min(2, len(req_keywords)):
            matches.append({
                "requirement": req,
                "evidenced_quote": best_sentence[:200] + ("..." if len(best_sentence) > 200 else ""),
                "matched_keywords": [kw for kw in req_keywords if kw in best_sentence.lower()],
            })
        else:
            missing_evidence.append(req)
            suggested_questions.append(
                f"Could you describe your hands-on experience with: '{req}'?"
            )

    match_ratio = round(len(matches) / len(requirements), 2) if requirements else 0.0

    return {
        "candidate_file": resume_path.name,
        "alignment_ratio": match_ratio,
        "security_flags": injections,
        "evidenced_matches": matches,
        "missing_or_unclear": missing_evidence,
        "suggested_interview_questions": suggested_questions[:5],
        "compliance_notice": "Automated matching aid only. Human reviewer must verify final fit.",
    }


def compare_candidates(
    jd_path: Path, resume_paths: list[Path]
) -> dict[str, Any]:
    """Run evidence-based comparison of multiple resumes against a Job Description."""
    jd_content = extract_text_from_file(jd_path)
    requirements = extract_jd_requirements(jd_content)

    candidate_results = [
        evaluate_resume(r_path, requirements) for r_path in resume_paths
    ]

    return {
        "job_description_file": jd_path.name,
        "extracted_requirements_count": len(requirements),
        "requirements": requirements,
        "candidates": candidate_results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jd_file", type=Path, help="Path to Job Description file")
    parser.add_argument("resume_files", type=Path, nargs="+", help="One or more resume files")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()

    result = compare_candidates(args.jd_file, args.resume_files)
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
