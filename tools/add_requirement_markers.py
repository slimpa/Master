import re
from pathlib import Path


TEST_ID_RE = re.compile(r'\b((?:UT|IT|ST)_[A-Z]+_\d+(?:_\d+)*)\b')
REQ_FROM_TEST_ID_RE = re.compile(r'^(?:UT|IT|ST)_([A-Z]+_\d+)(?:_\d+)*$')


def extract_test_id_from_docstring(block: str):
    """
    Traži npr:
      UT_SWR_03_04
      IT_SWR_02_01
      ST_SR_01_02
    """
    m = TEST_ID_RE.search(block)
    return m.group(1) if m else None


def requirement_from_test_id(test_id: str):
    """
    Iz:
      UT_SWR_03_04 -> SWR_03
      ST_SR_01_02  -> SR_01
    """
    m = REQ_FROM_TEST_ID_RE.match(test_id)
    return m.group(1) if m else None


def ensure_pytest_import(lines):
    for line in lines:
        if re.match(r'^\s*import\s+pytest\b', line) or re.match(r'^\s*from\s+pytest\b', line):
            return lines

    insert_at = 0

    if lines and lines[0].startswith("#!"):
        insert_at = 1

    # preskoči encoding komentar
    if insert_at < len(lines) and "coding" in lines[insert_at]:
        insert_at += 1

    # preskoči module docstring ako postoji
    if insert_at < len(lines):
        stripped = lines[insert_at].lstrip()
        if stripped.startswith('"""') or stripped.startswith("'''"):
            quote = '"""' if stripped.startswith('"""') else "'''"

            first = lines[insert_at]
            if first.count(quote) >= 2 and first.strip() != quote:
                insert_at += 1
            else:
                insert_at += 1
                while insert_at < len(lines) and quote not in lines[insert_at]:
                    insert_at += 1
                if insert_at < len(lines):
                    insert_at += 1

    lines.insert(insert_at, "import pytest\n")
    if insert_at + 1 < len(lines) and lines[insert_at + 1].strip():
        lines.insert(insert_at + 1, "\n")
    return lines


def process_file(path: Path):
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    lines = ensure_pytest_import(lines)

    i = 0
    changed = False
    new_lines = []

    while i < len(lines):
        line = lines[i]

        func_match = re.match(r'^(\s*)def\s+(test_[A-Za-z0-9_]+)\s*\(', line)
        if not func_match:
            new_lines.append(line)
            i += 1
            continue

        indent = func_match.group(1)

        # pokupi prethodne dekoratore koji već stoje neposredno iznad funkcije
        decorator_block_start = len(new_lines)
        j = len(new_lines) - 1
        while j >= 0:
            prev = new_lines[j]
            if prev.strip().startswith("@"):
                j -= 1
                continue
            if prev.strip() == "":
                j -= 1
                continue
            break

        existing_block = "".join(new_lines[j + 1:])

        has_test_id_marker = re.search(r'@\s*pytest\.mark\.test_id\s*\(', existing_block) is not None
        has_req_marker = re.search(r'@\s*pytest\.mark\.requirement\s*\(', existing_block) is not None

        # uzmi kompletnu funkciju da nađemo docstring
        func_block = [line]
        k = i + 1
        while k < len(lines):
            next_line = lines[k]
            if re.match(rf'^{indent}def\s+test_[A-Za-z0-9_]+\s*\(', next_line):
                break
            if re.match(r'^\S', next_line) and not next_line.startswith(indent + " ") and not next_line.startswith(indent + "\t"):
                # top-level nešto drugo
                break
            func_block.append(next_line)
            k += 1

        func_text = "".join(func_block)
        test_id = extract_test_id_from_docstring(func_text)
        requirement = requirement_from_test_id(test_id) if test_id else None

        decorators_to_add = []
        if test_id and not has_test_id_marker:
            decorators_to_add.append(f'{indent}@pytest.mark.test_id("{test_id}")\n')
        if requirement and not has_req_marker:
            decorators_to_add.append(f'{indent}@pytest.mark.requirement("{requirement}")\n')

        if decorators_to_add:
            insert_pos = len(new_lines)
            while insert_pos > 0 and new_lines[insert_pos - 1].strip().startswith("@"):
                insert_pos -= 1
            for dec in decorators_to_add:
                new_lines.insert(insert_pos, dec)
                insert_pos += 1
            changed = True

        new_lines.append(line)
        i += 1

    updated = "".join(new_lines)

    if updated != original:
        path.write_text(updated, encoding="utf-8")
        return True
    return changed


def main():
    tests_dir = Path("tests")
    if not tests_dir.exists():
        print("Folder 'tests' nije pronađen.")
        return

    files = sorted(tests_dir.rglob("test_*.py"))
    if not files:
        print("Nema test fajlova.")
        return

    changed_count = 0
    for file in files:
        changed = process_file(file)
        if changed:
            changed_count += 1
            print(f"[UPDATED] {file}")
        else:
            print(f"[SKIPPED] {file}")

    print(f"\nGotovo. Ažurirano fajlova: {changed_count}/{len(files)}")


if __name__ == "__main__":
    main()