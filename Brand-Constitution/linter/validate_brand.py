#!/usr/bin/env python3
"""
Brand Constitution Linter (CLI Validation Agent)
Evaluates markdown documents against rules declared in constitution.example.md.
"""

import sys
import os
import re

# Ensure UTF-8 output encoding across Windows and POSIX terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


FORBIDDEN_TERMS = [
    r"\bdelve\b",
    r"\btapestry\b",
    r"\bgame-changer\b",
    r"\bin today's fast-paced world\b",
    r"\btestament to\b",
    r"\brevolutionary\b",
    r"\bcutting-edge\b",
]

CURLY_QUOTES = ["“", "”", "‘", "’"]

def lint_document(file_path):
    if not os.path.exists(file_path):
        print(f"[ERROR] Target file '{file_path}' does not exist.")
        return 1

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    violations = []

    # 1. Check for banned terms
    for pattern in FORBIDDEN_TERMS:
        matches = re.findall(pattern, content, flags=re.IGNORECASE)
        if matches:
            violations.append(f"Forbidden term detected: '{matches[0]}' (Count: {len(matches)})")

    # 2. Check for curly quotes
    for cq in CURLY_QUOTES:
        if cq in content:
            violations.append(f"Typographical violation: Curly quote '{cq}' detected. Use ASCII straight quotes.")

    # 3. Check for unattributed numbers
    stat_pattern = r"\b\d{1,3}%\b"
    stat_matches = re.findall(stat_pattern, content)
    if stat_matches:
        # Check if words like source, according, client, study, citation appear near stats
        attribution_keywords = ["source", "study", "client", "internal", "according", "experiment", "benchmark"]
        has_attribution = any(kw in content.lower() for kw in attribution_keywords)
        if not has_attribution:
            violations.append(f"Statistical claim detected ({stat_matches[:2]}) without clear attribution keywords.")

    print(f"\n==========================================")
    print(f" Brand Constitution Audit: {os.path.basename(file_path)}")
    print(f"==========================================")

    if violations:
        print(f"[FAIL] Found {len(violations)} brand violations:\n")
        for v in violations:
            print(f"  ❌ {v}")
        print("\nPlease resolve these issues before merging.")
        return 1
    else:
        print(f"[PASS] All brand constitution assertions passed successfully.\n")
        return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_brand.py <path_to_markdown_file>")
        sys.exit(1)

    sys.exit(lint_document(sys.argv[1]))
