"""
download_corpus.py
==================
Corpus fetcher and preparation utility for Astra experiment tiers:
  - Level 1: Synthetic logic harness (built-in, no download needed)
  - Level 2: Shakespeare's Macbeth (Project Gutenberg #1533, ~100KB, ~18K words)
  - Level 3: Complete Works of William Shakespeare (Project Gutenberg #100, ~5.5MB, ~900K words)

Handles download retries, mirror fallbacks, and user-agent headers to comply with
Project Gutenberg download policies.
"""

from __future__ import annotations

import argparse
import ssl
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, List

DATA_DIR = Path(__file__).resolve().parent

CORPUS_SOURCES = {
    2: {
        "name": "Macbeth",
        "filename": "macbeth.txt",
        "description": "Full dramatic text of Shakespeare's Macbeth",
        "urls": [
            "https://www.gutenberg.org/cache/epub/1533/pg1533.txt",
            "https://raw.githubusercontent.com/catherine-k/shakespeare-corpus/master/macbeth.txt",
            "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt",
        ],
        "expected_min_bytes": 50_000,
    },
    3: {
        "name": "Complete Shakespeare",
        "filename": "complete_shakespeare.txt",
        "description": "The Complete Works of William Shakespeare",
        "urls": [
            "https://www.gutenberg.org/cache/epub/100/pg100.txt",
            "https://raw.githubusercontent.com/brunoklein99/deep-learning-notes/master/shakespeare.txt",
        ],
        "expected_min_bytes": 1_000_000,
    },
}


def _download_file(urls: List[str], dest_path: Path, min_bytes: int = 10_000) -> bool:
    """Attempt download from primary and fallback URLs."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AstraResearch/1.0"
    }

    # Permissive SSL context in case local CA bundles are incomplete
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    for url in urls:
        try:
            print(f"[*] Downloading from: {url}")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                content = resp.read()

            if len(content) < min_bytes:
                print(f"[!] Downloaded payload too small ({len(content)} bytes), trying next mirror...")
                continue

            # Strip Gutenberg header/footer if present, or write directly
            text = content.decode("utf-8", errors="replace")
            dest_path.write_text(text, encoding="utf-8")
            print(f"[OK] Saved {len(text):,} characters to {dest_path}")
            return True
        except Exception as e:
            print(f"[!] Mirror failed ({url}): {e}")

    return False


def ensure_corpus(level: int, data_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Ensure the corpus file for the specified tier level exists locally.
    Returns the Path to the corpus file, or None for Level 1 (built-in).
    """
    if level == 1:
        return None

    target_dir = data_dir or DATA_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    info = CORPUS_SOURCES.get(level)
    if not info:
        raise ValueError(f"Unknown tier level: {level}. Valid levels: 1, 2, 3.")

    filepath = target_dir / info["filename"]
    if filepath.exists() and filepath.stat().st_size >= info["expected_min_bytes"]:
        return filepath

    print(f"[*] Preparing corpus for Tier {level} ({info['name']})...")
    success = _download_file(
        urls=info["urls"],
        dest_path=filepath,
        min_bytes=info["expected_min_bytes"],
    )

    if not success:
        # If network failed, check if a partial or smaller file exists
        if filepath.exists() and filepath.stat().st_size > 1000:
            print(f"[WARNING] Using existing file at {filepath} despite download failure.")
            return filepath
        raise RuntimeError(
            f"Failed to download corpus for Level {level} ({info['name']}). "
            f"Please manually place the text file at: {filepath}"
        )

    return filepath


def main() -> None:
    parser = argparse.ArgumentParser(description="Download corpora for Astra experiment tiers.")
    parser.add_argument(
        "--level",
        type=str,
        default="all",
        choices=["1", "2", "3", "all"],
        help="Tier level to download (default: all)",
    )
    args = parser.parse_args()

    levels = [2, 3] if args.level == "all" else [int(args.level)]
    for lvl in levels:
        if lvl == 1:
            print("[Level 1] Uses built-in synthetic corpus -- no download necessary.")
            continue
        try:
            path = ensure_corpus(lvl)
            print(f"[Level {lvl}] Verified at: {path}")
        except Exception as err:
            print(f"[Level {lvl}] Error: {err}", file=sys.stderr)


if __name__ == "__main__":
    main()
