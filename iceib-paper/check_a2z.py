#!/usr/bin/env python3
"""Check iceib-paper/main.tex against the OpenSpec changes 000_abstract-006_references.

Usage:
    python3 iceib-paper/check_a2z.py [iceib-paper/main.tex]

Exit codes:
    0  structure OK and ready to submit
    1  structure problems (missing or out-of-order A2Z codes, wrong sections,
       citation mismatches, abstract too long, main.txt differs from main.tex)
    2  structure OK, but submission blockers remain ([TBD] or author
       placeholders)
"""
import hashlib
import re
import sys
from pathlib import Path

A2Z_ORDER = (
    list("ABCDEFGHIJKLMNO")
    + ["P" + c for c in "ABCDEFGHIJKLM"]
    + list("QRSTUVWXYZ")
)
EXPECTED_SECTIONS = [
    "Introduction",
    "Related Work",
    "Proposed Design",
    "Experiment",
    "Conclusion",
]
AUTHOR_PLACEHOLDERS = ["Author Name", "[University]", "[Department]",
                       "[email address]", "[City]"]
ABSTRACT_MAX_WORDS = 250


def strip_comments(text: str) -> str:
    return "\n".join(re.sub(r"(?<!\\)%.*", "", line) for line in text.splitlines())


def abstract_words(body: str) -> int:
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", body, re.S)
    if not m:
        return -1
    t = m.group(1)
    t = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", t)  # drop commands
    t = re.sub(r"[{}$\\~]", " ", t)
    return len([w for w in t.split() if re.search(r"[A-Za-z0-9]", w)])


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("main.tex")
    raw = path.read_text(encoding="utf-8")
    body = strip_comments(raw)
    problems, blockers = [], []

    # A2Z markers: all present, first occurrences in SOP order
    found = re.findall(r"%\s*\[A2Z:([A-Z]{1,2})\]", raw)
    unknown = sorted({c for c in found if c not in A2Z_ORDER})
    if unknown:
        problems.append(f"unknown A2Z codes: {', '.join(unknown)}")
    missing = [c for c in A2Z_ORDER if c not in found]
    if missing:
        problems.append(f"missing A2Z codes: {', '.join(missing)}")
    first = []
    for c in found:
        if c in A2Z_ORDER and c not in first:
            first.append(c)
    expected = [c for c in A2Z_ORDER if c in first]
    if first != expected:
        for i, (got, want) in enumerate(zip(first, expected)):
            if got != want:
                problems.append(
                    f"A2Z order: code #{i + 1} is {got}, expected {want} "
                    f"(first-occurrence order: {' '.join(first)})")
                break

    # Numbered sections
    sections = re.findall(r"\\section\{([^}]*)\}", body)
    if sections != EXPECTED_SECTIONS:
        problems.append(f"sections are {sections}, expected {EXPECTED_SECTIONS}")

    # Abstract length
    n = abstract_words(body)
    if n < 0:
        problems.append("no abstract environment")
    elif n > ABSTRACT_MAX_WORDS:
        problems.append(f"abstract has {n} words (max {ABSTRACT_MAX_WORDS})")

    # Citations
    cited = set()
    for group in re.findall(r"\\cite\{([^}]*)\}", body):
        cited.update(k.strip() for k in group.split(","))
    bib = set(re.findall(r"\\bibitem\{([^}]*)\}", body))
    if cited - bib:
        problems.append(f"\\cite without \\bibitem: {', '.join(sorted(cited - bib))}")
    if bib - cited:
        problems.append(f"\\bibitem never cited: {', '.join(sorted(bib - cited))}")

    # main.txt must be a byte-identical twin of main.tex
    twin = path.with_suffix(".txt")
    if twin.exists():
        same = hashlib.sha256(twin.read_bytes()).digest() == hashlib.sha256(path.read_bytes()).digest()
        twin_status = "identical" if same else "DIFFERENT"
        if not same:
            problems.append(f"{twin.name} differs from {path.name} (run: cp {path} {twin})")
    else:
        twin_status = "missing"
        problems.append(f"{twin.name} is missing (run: cp {path} {twin})")

    # Submission blockers
    tbd_lines = [i + 1 for i, line in enumerate(body.splitlines())
                 if ("\\TBD" in line or "[TBD]" in line) and "\\newcommand" not in line]
    if tbd_lines:
        blockers.append(f"[TBD] on {len(tbd_lines)} line(s): {tbd_lines[:15]}"
                        + (" ..." if len(tbd_lines) > 15 else ""))
    ph = [p for p in AUTHOR_PLACEHOLDERS if p in body]
    if ph:
        blockers.append(f"author placeholders remain: {', '.join(ph)}")

    print(f"Checked {path}")
    print(f"  A2Z codes found: {len(set(found) & set(A2Z_ORDER))}/{len(A2Z_ORDER)}")
    print(f"  sections: {sections}")
    print(f"  abstract words: {n}")
    print(f"  references: {len(bib)} bibitems, {len(cited)} cited keys")
    print(f"  main.txt vs main.tex (SHA-256): {twin_status}")
    for p in problems:
        print(f"STRUCTURE: {p}")
    for b in blockers:
        print(f"NOT READY TO SUBMIT: {b}")
    if problems:
        return 1
    if blockers:
        return 2
    print("OK: ready to submit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
