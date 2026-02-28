import yaml
import os
import csv
from typing import Optional


class RequirementsModel:

    def __init__(self, req_path="requirements", test_file="tests/tests.yaml"):
        # dozvoli da radi iz bilo kog foldera
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.req_path = os.path.abspath(os.path.join(project_root, req_path))
        self.test_file = os.path.abspath(os.path.join(project_root, test_file))

        self.sr = []
        self.sys = []
        self.swr = []
        self.tests = []

        self.load_all()

    def load_yaml(self, path):
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or []

    def load_all(self):
        self.sr = self.load_yaml(os.path.join(self.req_path, "stakeholder.yaml"))
        self.sys = self.load_yaml(os.path.join(self.req_path, "system.yaml"))
        self.swr = self.load_yaml(os.path.join(self.req_path, "software.yaml"))
        self.tests = self.load_yaml(self.test_file)

    def save_all(self):
        os.makedirs(self.req_path, exist_ok=True)
        for name, data in [
            ("stakeholder.yaml", self.sr),
            ("system.yaml", self.sys),
            ("software.yaml", self.swr),
        ]:
            with open(os.path.join(self.req_path, name), "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=False)

    # ---------------- TRACEABILITY ----------------

    def generate_traceability(self):
        matrix = []

        for sr in self.sr:
            for sy in [x for x in self.sys if x.get("parent") == sr["id"]]:
                for sw in [x for x in self.swr if x.get("parent") == sy["id"]]:
                    related_tests = [
                        t["test_id"] for t in self.tests if t.get("verifies") == sw["id"]
                    ]

                    matrix.append({
                        "SR": sr["id"],
                        "SYS": sy["id"],
                        "SWR": sw["id"],
                        "TEST": ", ".join(related_tests)
                    })

        return matrix

    def export_traceability_csv(self, filename="traceability_matrix.csv"):
        matrix = self.generate_traceability()
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["SR", "SYS", "SWR", "TEST"])
            writer.writeheader()
            writer.writerows(matrix)

    # ---------------- COVERAGE ----------------

    def is_req_tested(self, req_id: str, level: Optional[str] = None) -> bool:
        for t in self.tests:
            if t.get("verifies") == req_id and (level is None or t.get("level") == level):
                return True
        return False

    def is_swr_tested(self, swr_id):
        # unit test coverage za SWR
        return self.is_req_tested(swr_id, level="unit")

    def get_tests_for_requirement(self, req_id):
        return [t for t in self.tests if t.get("verifies") == req_id]

    def coverage_by_level(self):
        """
        - unit coverage se računa preko SWR
        - integration coverage preko SYS
        - system coverage preko SR
        """
        result = {
            "unit": {"total": 0, "covered": 0},
            "integration": {"total": 0, "covered": 0},
            "system": {"total": 0, "covered": 0}
        }

        for req in self.swr:
            result["unit"]["total"] += 1
            if self.is_req_tested(req["id"], level="unit"):
                result["unit"]["covered"] += 1

        for req in self.sys:
            result["integration"]["total"] += 1
            if self.is_req_tested(req["id"], level="integration"):
                result["integration"]["covered"] += 1

        for req in self.sr:
            result["system"]["total"] += 1
            if self.is_req_tested(req["id"], level="system"):
                result["system"]["covered"] += 1

        return result

    # ---------------- IMPACT ANALYSIS ----------------

    def _get_level(self, req_id):
        if any(r.get("id") == req_id for r in self.sr):
            return "SR"
        if any(r.get("id") == req_id for r in self.sys):
            return "SYS"
        if any(r.get("id") == req_id for r in self.swr):
            return "SWR"
        return None

    def _get_children_ids(self, req_id):
        level = self._get_level(req_id)
        if level == "SR":
            return [r["id"] for r in self.sys if r.get("parent") == req_id]
        if level == "SYS":
            return [r["id"] for r in self.swr if r.get("parent") == req_id]
        return []

    def get_descendants_ids(self, req_id):
        """
        Returns all downstream requirements (children, grandchildren...).
        SR -> SYS -> SWR
        SYS -> SWR
        SWR -> []
        """
        descendants = []
        queue = list(self._get_children_ids(req_id))

        while queue:
            cur = queue.pop(0)
            descendants.append(cur)
            queue.extend(self._get_children_ids(cur))

        return descendants

    def get_impacted_requirements(self, req_id):
        """
        Impact set = selected requirement + all descendants.
        """
        impacted = [req_id] + self.get_descendants_ids(req_id)
        # unique, stable order
        seen = set()
        out = []
        for x in impacted:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    def get_impacted_tests(self, req_id):
        """
        Returns tests that should be re-run if req_id changes.
        Includes tests verifying req_id or any impacted descendants.
        """
        impacted_reqs = set(self.get_impacted_requirements(req_id))
        return [t for t in self.tests if t.get("verifies") in impacted_reqs]

    # ---------------- ADD REQUIREMENT ----------------

    def add_requirement(self, level, description, parent=None):
        req_id = self.generate_next_id(level)

        req = {
            "id": req_id,
            "description": description,
            "version": "1.0"
        }

        if parent:
            req["parent"] = parent

        if level == "SR":
            self.sr.append(req)
        elif level == "SYS":
            self.sys.append(req)
        elif level == "SWR":
            self.swr.append(req)

        self.save_all()
        return req_id

    # ---------------- GENERATE REQUIREMENT ID ----------------

    def generate_next_id(self, level):
        """
        Generates next incremental ID for given level.
        Example: SWR_03 -> SWR_04
        """
        if level == "SR":
            existing = [r["id"] for r in self.sr]
            prefix = "SR"
        elif level == "SYS":
            existing = [r["id"] for r in self.sys]
            prefix = "SYS"
        elif level == "SWR":
            existing = [r["id"] for r in self.swr]
            prefix = "SWR"
        else:
            raise ValueError("Unknown requirement level")

        numbers = []
        for eid in existing:
            try:
                numbers.append(int(eid.split("_")[1]))
            except Exception:
                pass

        next_number = max(numbers, default=0) + 1
        return f"{prefix}_{next_number:02d}"

    def delete_requirement(self, req_id):
        """
        Deletes requirement and all children (if SR or SYS).
        """
        # Delete SWR
        self.swr = [r for r in self.swr if r["id"] != req_id]

        # Delete SYS and its SWRs
        self.sys = [s for s in self.sys if s["id"] != req_id]
        self.swr = [r for r in self.swr if r.get("parent") != req_id]

        # Delete SR and its SYS/SWR
        self.sys = [s for s in self.sys if s.get("parent") != req_id]
        self.swr = [r for r in self.swr if r.get("parent") not in [s["id"] for s in self.sys]]

        self.sr = [r for r in self.sr if r["id"] != req_id]

        self.save_all()