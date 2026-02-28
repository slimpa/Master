import os
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

REQ_SR = os.path.join(ROOT, "requirements", "stakeholder.yaml")
REQ_SYS = os.path.join(ROOT, "requirements", "system.yaml")
REQ_SWR = os.path.join(ROOT, "requirements", "software.yaml")

TESTS_YAML = os.path.join(ROOT, "tests", "tests.yaml")


def load_yaml(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or []


def main():
    sr = {r["id"] for r in load_yaml(REQ_SR) if "id" in r}
    sysr = {r["id"] for r in load_yaml(REQ_SYS) if "id" in r}
    swr = {r["id"] for r in load_yaml(REQ_SWR) if "id" in r}

    tests = load_yaml(TESTS_YAML)
    tested_unit = {t.get("verifies") for t in tests if t.get("level") == "unit" and t.get("verifies")}
    tested_int = {t.get("verifies") for t in tests if t.get("level") == "integration" and t.get("verifies")}
    tested_sys = {t.get("verifies") for t in tests if t.get("level") == "system" and t.get("verifies")}

    print("Missing Unit (SWR):", sorted(swr - tested_unit))
    print("Missing Integration (SYS):", sorted(sysr - tested_int))
    print("Missing System (SR):", sorted(sr - tested_sys))


if __name__ == "__main__":
    main()