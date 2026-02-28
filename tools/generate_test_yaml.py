import os
import ast
import yaml
from typing import Optional, List, Dict

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

TESTS_FOLDER = os.path.join(PROJECT_ROOT, "tests")
OUTPUT_FILE = os.path.join(TESTS_FOLDER, "tests.yaml")


def extract_test_id_from_docstring(docstring: Optional[str]) -> Optional[str]:
    """
    Uzimamo prvi ne-prazan red docstringa kao test_id.
    """
    if not docstring:
        return None
    for line in docstring.splitlines():
        line = line.strip()
        if line:
            return line
    return None


def extract_requirement_from_id(test_id: Optional[str]) -> Optional[str]:
    """
    UT_SWR_03_01 -> SWR_03
    IT_SYS_01_01 -> SYS_01
    ST_SR_02_01  -> SR_02
    """
    if not test_id:
        return None

    if " " in test_id:
        test_id = test_id.split()[0].strip()

    parts = test_id.split("_")
    if len(parts) >= 3:
        return f"{parts[1]}_{parts[2]}"
    return None


def extract_level(test_id: Optional[str]) -> str:
    if not test_id:
        return "unknown"
    if test_id.startswith("UT"):
        return "unit"
    if test_id.startswith("IT"):
        return "integration"
    if test_id.startswith("ST"):
        return "system"
    return "unknown"


def parse_test_file(filepath: str) -> List[Dict]:
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)
    tests = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            docstring = ast.get_docstring(node)
            test_id = extract_test_id_from_docstring(docstring)
            if not test_id:
                continue

            verifies = extract_requirement_from_id(test_id)
            level = extract_level(test_id)

            tests.append({
                "test_id": test_id,
                "function": node.name,
                "verifies": verifies,
                "level": level,
                "file": os.path.abspath(filepath).replace("\\", "/")
            })

    return tests


def scan_tests() -> List[Dict]:
    all_tests = []

    if not os.path.isdir(TESTS_FOLDER):
        raise FileNotFoundError(f"Tests folder not found: {TESTS_FOLDER}")

    for root, _, files in os.walk(TESTS_FOLDER):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                path = os.path.join(root, file)
                all_tests.extend(parse_test_file(path))

    return all_tests


def generate_yaml():
    tests = scan_tests()

    os.makedirs(TESTS_FOLDER, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        yaml.dump(tests, f, sort_keys=False, allow_unicode=True)

    print(f"Generated {OUTPUT_FILE} with {len(tests)} tests.")


if __name__ == "__main__":
    generate_yaml()