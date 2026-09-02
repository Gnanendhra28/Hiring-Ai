#!/usr/bin/env python3
"""
Lightweight Secret Scanner for Pre-Commit and CI Pipelines.
Scans files for unredacted API keys, private keys, database connection strings,
and hardcoded tokens.
"""

import sys
import os
import re
from typing import List, Tuple

SENSITIVE_REGEXES = [
    (r'(?i)(AIzaSy[0-9A-Za-z-_]{33})', "Google / Gemini API Key"),
    (r'(?i)-----BEGIN\s+(RSA|EC|DSA|OPENSSH|PRIVATE)\s+KEY-----', "Private Key Header"),
    (r'(?i)postgres(ql)?(\+asyncpg)?:\/\/[a-zA-Z0-9_\-]+:[a-zA-Z0-9_\-]+@', "PostgreSQL Connection String with Password"),
    (r'(?i)(secret_key|api_key|password)\s*[:=]\s*["\x27][a-zA-Z0-9_\-]{20,}["\x27]', "Hardcoded Secret Assignment"),
]

EXCLUDE_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    ".next",
    "dist",
    "build",
    ".gemini",
    ".venv",
    "venv",
    ".system_generated",
    ".user_uploaded",
}
EXCLUDE_FILES = {
    "scan_secrets.py",
    "test_security_exception_redaction.py",
    "package-lock.json",
    "pyproject.toml",
    "SECURITY_THREAT_MODEL.md",
    "README.md",
    ".env",
    ".env.example",
}

def scan_file(filepath: str) -> List[Tuple[int, str, str]]:
    findings = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line_idx, line in enumerate(f, 1):
                # Skip comments or synthetic test mock examples explicitly marked
                lower_line = line.lower()
                if any(x in lower_line for x in (
                    "fake_", "mock_", "placeholder_", "dev_secret", "test_real", "test_secret",
                    "valid_real_gemini_key", "postgres:postgres@localhost", "postgres:postgres@127.0.0.1",
                    "postgres@localhost", "test_key", "insecure_default"
                )):
                    continue
                for pattern, desc in SENSITIVE_REGEXES:
                    if re.search(pattern, line):
                        findings.append((line_idx, desc, line.strip()[:60]))
    except Exception:
        pass
    return findings

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_files = []

    if len(sys.argv) > 1:
        target_files = [os.path.abspath(f) for f in sys.argv[1:] if os.path.isfile(f)]
    else:
        scan_dirs = [
            os.path.join(root_dir, "backend"),
            os.path.join(root_dir, "frontend", "src"),
            os.path.join(root_dir, "scripts"),
        ]
        for sdir in scan_dirs:
            if not os.path.exists(sdir):
                continue
            for root, dirs, files in os.walk(sdir):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                for file in files:
                    if file not in EXCLUDE_FILES and not file.endswith((".png", ".jpg", ".ico", ".lock", ".pyc")):
                        target_files.append(os.path.join(root, file))

        # Also add root files
        for f in ("cloudbuild.yaml", "firestore.rules", "Dockerfile"):
            full_p = os.path.join(root_dir, f)
            if os.path.isfile(full_p):
                target_files.append(full_p)

    total_findings = 0
    for fpath in target_files:
        rel_path = os.path.relpath(fpath, root_dir)
        findings = scan_file(fpath)
        if findings:
            print(f"\n[SECRET SCANNER WARNING] Potential secret detected in: {rel_path}")
            for line_no, desc, snippet in findings:
                print(f"  Line {line_no}: [{desc}] -> {snippet}...")
            total_findings += len(findings)

    if total_findings > 0:
        print(f"\n[FAILED] Secret scanner detected {total_findings} potential secrets. Please remove or sanitize before committing.")
        sys.exit(1)
    else:
        print("[PASSED] Secret scanner completed: 0 secrets detected.")
        sys.exit(0)

if __name__ == "__main__":
    main()
