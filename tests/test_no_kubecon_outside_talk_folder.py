# ABOUTME: Platform-genericness test — "kubecon" must not leak outside presentations/.
# ABOUTME: Allowlists the GCP project ID placeholder, kubeauto-ai-day, and the Genericize plan doc.

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import PROJECT_ROOT


# Allowed substrings that *contain* "kubecon" but are legitimate:
# - the GCP project ID placeholder used everywhere as a stand-in for the real ID
# - the kubeauto-ai-day external repo (kubeauto != kubecon)
# - the talk folder itself (presentations/kubecon-na-2026/)
# - the parent directory on disk (Kubecon-NA-2026-Whitney-BurritoBot)
# - Kubernetes terminology that contains the substring
#   (kubecontext, kubeconfig, kubeconform, and the _kubeconfig_ helper name)
ALLOWLIST_PATTERNS = [
    re.compile(r"burritbot-kubecon-2026"),
    re.compile(r"kubeauto-ai-day"),
    re.compile(r"presentations/kubecon-na-2026"),
    re.compile(r'"kubecon-na-2026"'),  # Python path concatenation
    re.compile(r"Kubecon-NA-2026-Whitney-BurritoBot"),  # parent dir on disk
    re.compile(r"kubecontext", re.IGNORECASE),
    re.compile(r"kubeconfig\w*", re.IGNORECASE),
    re.compile(r"kubeconform", re.IGNORECASE),
    re.compile(r"_kubeconfig_\w*", re.IGNORECASE),  # the test fixture helper
]

KUBECON_PATTERN = re.compile(r"kubecon", re.IGNORECASE)

# Directories that are skipped entirely.
SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "presentations",  # the entire presentations/ subtree is allowed to mention kubecon
}

# Files that are allowed to mention kubecon in their content (full path
# relative to PROJECT_ROOT). The Genericize plan and this test file
# legitimately discuss what's being scrubbed; README's "Talks Using This
# Platform" section is the catalog of which events use burritbot.
FILE_ALLOWLIST = {
    "docs/PHASE-G-GENERICIZE-PLAN.md",
    "tests/test_no_kubecon_outside_talk_folder.py",
    "README.md",
}

# Filename glob patterns to skip entirely (e.g. binary files, lockfiles
# that may contain unrelated hashes).
EXTENSION_SKIP = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".lock"}


def _iter_tree_files() -> list[Path]:
    """Return every text file in the tree, minus skipped dirs and binaries."""
    files: list[Path] = []
    for p in PROJECT_ROOT.rglob("*"):
        if not p.is_file():
            continue
        parts = set(p.relative_to(PROJECT_ROOT).parts)
        if parts & SKIP_DIRS:
            continue
        if p.suffix.lower() in EXTENSION_SKIP:
            continue
        if str(p.relative_to(PROJECT_ROOT)) in FILE_ALLOWLIST:
            continue
        files.append(p)
    return files


def _scan_file_for_unallowed_kubecon(path: Path) -> list[tuple[int, str]]:
    """Return (line_number, line_text) tuples for any unallowed kubecon mention."""
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []

    hits: list[tuple[int, str]] = []
    for n, line in enumerate(text.splitlines(), start=1):
        if not KUBECON_PATTERN.search(line):
            continue
        # Strip every allowlisted substring; if "kubecon" still appears,
        # the line has a real event-name leak.
        stripped = line
        for pat in ALLOWLIST_PATTERNS:
            stripped = pat.sub("", stripped)
        if KUBECON_PATTERN.search(stripped):
            hits.append((n, line.strip()))
    return hits


@pytest.mark.static
def test_no_kubecon_outside_talk_folder() -> None:
    """No file outside presentations/ may mention 'kubecon' unless allowlisted.

    Catches event-name leakage if future commits accidentally re-introduce
    KubeCon references into platform code, docs, or configs. The platform
    must stay re-presentable at other conferences without rewrites.
    """
    offenders: dict[str, list[tuple[int, str]]] = {}
    for path in _iter_tree_files():
        hits = _scan_file_for_unallowed_kubecon(path)
        if hits:
            offenders[str(path.relative_to(PROJECT_ROOT))] = hits

    if not offenders:
        return

    lines = ["Unallowed 'kubecon' references found outside presentations/:"]
    for rel, hits in sorted(offenders.items()):
        lines.append(f"\n  {rel}:")
        for n, text in hits:
            lines.append(f"    line {n}: {text}")
    lines.append(
        "\nFix: either move the file under presentations/<event>/, scrub "
        "the reference, or extend the allowlist in this test if the use "
        "is genuinely legitimate."
    )
    raise AssertionError("\n".join(lines))
