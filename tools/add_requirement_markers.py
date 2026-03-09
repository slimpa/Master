#!/usr/bin/env python3
import re
from pathlib import Path

TESTS_DIR = Path("tests")

TEST_DEF_RE = re.compile(r"^(\s*)def\s+(test_[A-Za-z0-9_]+)\s*\(")
REQ_MARKER_RE = re.compile(r'^\s*@pytest\.mark\.requirement\(\s*["\']([A-Z]+_\d+)["\']\s*\)\s*$')

REQ_PATTERNS = [
    (re.compile(r"\bUT_SWR_(\d+)_\d+\b", re.IGNORECASE), "SWR"),
    (re.compile(r"\bIT_SWR_(\d+)_\d+\b", re.IGNORECASE), "SWR"),
    (re.compile(r"\bST_SWR_(\d+)_\d+\b", re.IGNORECASE), "SWR"),
    (re.compile(r"\bST_SR_(\d+)_\d+\b", re.IGNORECASE), "SR"),
    (re.compile(r"\bUT_SR_(\d+)_\d+\b", re.IGNORECASE), "SR"),
    (re.compile(r"\bIT_SR_(\d+)_\d+\b", re.IGNORECASE), "SR"),
    (re.compile(r"\bSWR_(\d+)\b", re.IGNORECASE), "SWR"),
    (re.compile(r"\bSR_(\d+)\b", re.IGNORECASE), "SR"),
]

def extract_requirement(text: str):
    for pattern, prefix in REQ_PATTERNS:
        m = pattern.search(text or "")
        if m:
            return f"{prefix}_{int(m.group(1)):02d}"
    return None

def file_has_pytest_import(lines):
    return any(re.match(r"^\s*import\s+pytest\b", line) or re.match(r"^\s*from\s+pytest\b", line) for line in lines)

def insert_pytest_import(lines):
    if file_has_pytest_import(lines):
        return lines

    insert_at = 0
    if lines and lines[0].startswith("#!"):
        insert_at = 1

    while insert_at < len(lines) and (
        lines[insert_at].startswith("#")
        or lines[insert_at].strip() == ""
        or lines[insert_at].startswith('"""')
        or lines[insert_at].startswith("'''")
    ):
        insert_at += 1

    lines.insert(insert_at, "import pytest\n")
    return lines

def has_requirement_marker_near(lines, def_index):
    j = def_index - 1
    while j >= 0:
        stripped = lines[j].strip()
        if stripped == "":
            j -= 1
            continue
        if stripped.startswith("@"):
            if REQ_MARKER_RE.match(lines[j]):
                return True
            j -= 1
            continue
        break
    return False

def find_requirement_for_test(lines, def_index, func_name):
    search_chunks = []

    # 1) ime funkcije
    search_chunks.append(func_name)

    # 2) par linija iznad funkcije
    above_start = max(0, def_index - 8)
    search_chunks.append("".join(lines[above_start:def_index]))

    # 3) docstring odmah unutar funkcije
    indent_match = re.match(r"^(\s*)def\s+", lines[def_index])
    base_indent = len(indent_match.group(1)) if indent_match else 0

    body_lines = []
    for k in range(def_index + 1, min(len(lines), def_index + 20)):
        line = lines[k]
        if line.strip() == "":
            body_lines.append(line)
            continue

        curr_indent = len(line) - len(line.lstrip(" "))
        if curr_indent <= base_indent and line.strip():
            break
        body_lines.append(line)

    search_chunks.append("".join(body_lines))

    for chunk in search_chunks:
        req = extract_requirement(chunk)
        if req:
            return req

    return None

def process_file(path: Path):
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)

    modified = False
    added_count = 0

    i = 0
    while i < len(lines):
        m = TEST_DEF_RE.match(lines[i])
        if not m:
            i += 1
            continue

        indent, func_name = m.groups()

        if has_requirement_marker_near(lines, i):
            i += 1
            continue

        requirement = find_requirement_for_test(lines, i, func_name)
        if not requirement:
            i += 1
            continue

        marker_line = f"{indent}@pytest.mark.requirement(\"{requirement}\")\n"
        lines.insert(i, marker_line)
        modified = True
        added_count += 1
        i += 2

    if modified:
        lines = insert_pytest_import(lines)
        new_text = "".join(lines)
        path.write_text(new_text, encoding="utf-8")

    return added_count, modified

def main():
    if not TESTS_DIR.exists():
        print(f"Folder ne postoji: {TESTS_DIR}")
        return

    total_added = 0
    changed_files = 0

    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        added, changed = process_file(path)
        if changed:
            changed_files += 1
            print(f"[UPDATED] {path} -> dodano markera: {added}")
            total_added += added
        else:
            print(f"[SKIP]    {path}")

    print()
    print(f"Gotovo. Izmijenjeno fajlova: {changed_files}")
    print(f"Ukupno dodano requirement markera: {total_added}")

if __name__ == "__main__":
    main()