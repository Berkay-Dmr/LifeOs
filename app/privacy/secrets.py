from __future__ import annotations

import re
from pathlib import Path

# Secret patterns to detect in file names
SECRET_FILE_NAMES: set[str] = {
    ".env", ".env.local", ".env.production", ".env.staging",
    "credentials.json",
    "service-account.json",
}

SECRET_FILE_PATTERNS: list[re.Pattern] = [
    re.compile(r"\.pem$", re.IGNORECASE),
    re.compile(r"\.key$", re.IGNORECASE),
    re.compile(r"id_rsa", re.IGNORECASE),
    re.compile(r"id_dsa", re.IGNORECASE),
    re.compile(r"id_ecdsa", re.IGNORECASE),
    re.compile(r"id_ed25519", re.IGNORECASE),
    re.compile(r"credentials", re.IGNORECASE),
    re.compile(r"secrets?\.(json|yaml|yml|toml|env)", re.IGNORECASE),
]

# Content patterns to redact
CONTENT_SECRET_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("OPENAI_API_KEY", re.compile(r"(OPENAI_API_KEY\s*=\s*)(\S+)")),
    ("API_KEY", re.compile(r"(API_KEY\s*=\s*)(\S+)")),
    ("AWS_SECRET", re.compile(r"(AWS_SECRET\s*=\s*)(\S+)")),
    ("PASSWORD", re.compile(r"(password\s*=\s*)(\S+)", re.IGNORECASE)),
    ("TOKEN", re.compile(r"(token\s*=\s*)(\S+)", re.IGNORECASE)),
    ("SECRET", re.compile(r"(secret\s*=\s*)(\S+)", re.IGNORECASE)),
    ("PRIVATE_KEY", re.compile(r"(PRIVATE_KEY\s*=\s*)(\S+)")),
    ("DATABASE_URL", re.compile(r"(DATABASE_URL\s*=\s*)(\S+)")),
]


def is_secret_file(path: Path) -> bool:
    """Check if a file is likely a secret/credential file."""
    if path.name in SECRET_FILE_NAMES:
        return True
    for pattern in SECRET_FILE_PATTERNS:
        if pattern.search(path.name):
            return True
    return False


def redact_secrets(text: str) -> str:
    """Replace secret values with [REDACTED] in content."""
    result = text
    for label, pattern in CONTENT_SECRET_PATTERNS:
        result = pattern.sub(lambda m: m.group(1) + "[REDACTED]", result)
    return result


def scan_for_secrets(text: str) -> list[tuple[str, int]]:
    """Scan text for potential secret patterns. Returns list of (label, line_number)."""
    findings: list[tuple[str, int]] = []
    for i, line in enumerate(text.splitlines(), 1):
        for label, pattern in CONTENT_SECRET_PATTERNS:
            if pattern.search(line):
                findings.append((label, i))
    return findings
