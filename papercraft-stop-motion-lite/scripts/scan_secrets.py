#!/usr/bin/env python3
"""Refuse to publish API keys. Scans text files under a folder; exits 1 if anything looks like a secret.

  python3 scripts/scan_secrets.py .
"""
import re
import sys
from pathlib import Path

PATTERNS = {
    "OpenAI/OpenRouter key": r"sk-(?:or-|proj-|ant-)?[A-Za-z0-9_\-]{20,}",
    "Google API key": r"AIza[0-9A-Za-z_\-]{35}",
    "GitHub token": r"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}",
    "AWS key": r"AKIA[0-9A-Z]{16}",
    "Slack token": r"xox[abprs]-[A-Za-z0-9\-]{10,}",
    "ElevenLabs/hex key": r"(?i)(?:xi-api-key|elevenlabs)[\"'\s:=]+[0-9a-f]{32}",
    "Private key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "Assigned secret": r"(?i)(?:api[_-]?key|secret|token|password)\s*[:=]\s*[\"'][^\"'\s]{16,}[\"']",
}
SKIP_DIRS = {".git", "node_modules", "__pycache__", "frames"}
BAD_NAMES = {".env", "credentials.json", "secrets.json", "token.json"}


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    hits = []
    for p in root.rglob("*"):
        if any(part in SKIP_DIRS for part in p.parts) or not p.is_file():
            continue
        if p.name in BAD_NAMES or p.suffix in {".pem", ".key"} or p.name.startswith(".env"):
            hits.append(f"{p}: secret-like file name")
            continue
        if p.stat().st_size > 2_000_000 or p.suffix.lower() in {".png", ".jpg", ".mp4", ".wav", ".ttc", ".ttf"}:
            continue
        try:
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        for name, rx in PATTERNS.items():
            for m in re.finditer(rx, text):
                if p.name == "scan_secrets.py":
                    break
                hits.append(f"{p}:{text.count(chr(10), 0, m.start()) + 1}: possible {name}")
    if hits:
        print("\n".join(hits))
        sys.exit(1)
    print("no secrets found")


if __name__ == "__main__":
    main()
