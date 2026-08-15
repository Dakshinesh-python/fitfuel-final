#!/usr/bin/env python3
"""
Scans fitfuel_mobile/lib/screens and widgets for interactive widget
constructors (TextField, TextFormField, ElevatedButton, OutlinedButton,
TextButton, IconButton, GestureDetector, InkWell, Switch, Slider) and
reports which ones do NOT have a `key:` argument anywhere in their
constructor call, within a generous line window.

This is a heuristic source scan, not a Dart AST parser -- it will miss
keys assigned via a variable/constant reference instead of an inline
`ValueKey(...)`, and it can't tell you whether a key is *correct*, only
whether one is *present*. Treat its output as "worth a second look",
not as ground truth. Run it after any UI change to catch newly-added
unkeyed interactive elements before they turn into a flaky test.

Usage:
    python3 scripts/key_audit.py [path-to-fitfuel_mobile/lib]
"""
import re
import sys
from pathlib import Path

INTERACTIVE_WIDGETS = [
    "TextField",
    "TextFormField",
    "ElevatedButton",
    "ElevatedButton.icon",
    "OutlinedButton",
    "OutlinedButton.icon",
    "TextButton",
    "IconButton",
    "GestureDetector",
    "InkWell",
    "Switch",
    "Slider",
    "Checkbox",
    "Radio",
    "DropdownButton",
]

# Matches "SomeWidget(" possibly with ".icon" suffix
WIDGET_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in INTERACTIVE_WIDGETS) + r")\s*\("
)

LOOKAHEAD_LINES = 6  # how many lines after the constructor call to scan for `key:`


def find_matching_paren(text: str, open_idx: int) -> int:
    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


def audit_file(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    findings = []

    for match in WIDGET_PATTERN.finditer(text):
        widget_name = match.group(1)
        open_paren_idx = match.end() - 1
        close_idx = find_matching_paren(text, open_paren_idx)
        if close_idx == -1:
            continue
        call_body = text[open_paren_idx:close_idx]

        line_no = text[: match.start()].count("\n") + 1
        has_key = bool(re.search(r"\bkey\s*:", call_body))

        if not has_key:
            findings.append(
                {
                    "file": str(path),
                    "line": line_no,
                    "widget": widget_name,
                    "snippet": lines[line_no - 1].strip()[:80],
                }
            )
    return findings


def main():
    lib_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent.parent / "fitfuel_mobile" / "lib"
    if not lib_dir.exists():
        print(f"lib directory not found: {lib_dir}", file=sys.stderr)
        sys.exit(1)

    all_findings = []
    dart_files = sorted(lib_dir.rglob("*.dart"))
    for f in dart_files:
        if "main_test.dart" in f.name:
            continue
        all_findings.extend(audit_file(f))

    total_widgets_scanned = sum(
        len(WIDGET_PATTERN.findall(f.read_text(encoding="utf-8"))) for f in dart_files
    )
    keyed = total_widgets_scanned - len(all_findings)
    pct = round((keyed / total_widgets_scanned) * 100, 1) if total_widgets_scanned else 0.0

    print(f"Scanned {len(dart_files)} .dart files, {total_widgets_scanned} interactive widget constructors found.")
    print(f"With a key: {keyed} ({pct}%)")
    print(f"WITHOUT a key: {len(all_findings)}")
    print()

    if all_findings:
        print("Unkeyed interactive widgets (heuristic scan -- see module docstring):")
        by_file: dict[str, list] = {}
        for f in all_findings:
            by_file.setdefault(f["file"], []).append(f)
        for file, findings in sorted(by_file.items()):
            print(f"\n  {file}")
            for finding in findings:
                print(f"    L{finding['line']:>4}  {finding['widget']:<20} {finding['snippet']}")
    else:
        print("No unkeyed interactive widgets found by this heuristic scan.")

    return 0 if not all_findings else 1


if __name__ == "__main__":
    sys.exit(main())
