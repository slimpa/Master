import sys
import os
import subprocess
import ast

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTreeWidget, QTreeWidgetItem, QPushButton, QLabel,
    QLineEdit, QTextEdit, QMessageBox, QDialog, QComboBox, QListWidget
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

from requirements_model import RequirementsModel
from generate_test_yaml import generate_yaml


class RequirementsGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Requirements Management Tool")

        # --- Auto-generate tests/tests.yaml on startup ---
        try:
            generate_yaml()
        except Exception as e:
            print("YAML generation failed:", e)

        self.model = RequirementsModel()
        self.selected_requirement_id = None

        self.init_ui()
        self.build_tree()
        self.update_coverage()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # -------------------------
        # COLUMN 1 – REQUIREMENTS TREE
        # -------------------------
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Requirements")
        self.tree.itemClicked.connect(self.on_select)

        # Selected item black
        self.tree.setStyleSheet("""
        QTreeWidget::item:selected {
            background-color: black;
            color: white;
        }
        """)

        # -------------------------
        # COLUMN 2 – DETAILS
        # -------------------------
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)

        self.id_field = QLineEdit()
        self.id_field.setReadOnly(True)

        self.desc_field = QTextEdit()

        details_layout.addWidget(QLabel("Requirement ID"))
        details_layout.addWidget(self.id_field)

        details_layout.addWidget(QLabel("Description"))
        details_layout.addWidget(self.desc_field)

        btn_save = QPushButton("Save")
        btn_add = QPushButton("Add Requirement")
        btn_delete = QPushButton("Delete Requirement")
        btn_trace = QPushButton("Export Traceability (CSV)")
        btn_impact = QPushButton("Impact Analysis")

        btn_save.clicked.connect(self.save)
        btn_add.clicked.connect(self.add_requirement)
        btn_delete.clicked.connect(self.delete_requirement)
        btn_trace.clicked.connect(self.export_trace)
        btn_impact.clicked.connect(self.show_impact_analysis)

        details_layout.addWidget(btn_save)
        details_layout.addWidget(btn_add)
        details_layout.addWidget(btn_delete)
        details_layout.addWidget(btn_trace)
        details_layout.addWidget(btn_impact)

        self.coverage_label = QLabel("Coverage")
        details_layout.addWidget(self.coverage_label)

        btn_run_coverage = QPushButton("Run Test Coverage")
        btn_run_coverage.clicked.connect(self.run_code_coverage)
        details_layout.addWidget(btn_run_coverage)

        # -------------------------
        # COLUMN 3 – LINKED TESTS + OUTPUT + IMPACT
        # -------------------------
        tests_widget = QWidget()
        tests_layout = QVBoxLayout(tests_widget)

        tests_layout.addWidget(QLabel("Linked Tests"))

        self.tests_tree = QTreeWidget()
        self.tests_tree.setHeaderLabel("Test Files")
        self.tests_tree.itemClicked.connect(self.on_test_tree_click)
        tests_layout.addWidget(self.tests_tree)

        self.output_label = QLabel("Test Details")
        tests_layout.addWidget(self.output_label)
        self.test_code_view = QTextEdit()
        self.test_code_view.setReadOnly(True)
        self.test_code_view.setMinimumHeight(220)
        tests_layout.addWidget(self.test_code_view)

        tests_layout.addWidget(QLabel("Impact Analysis (Tests to Re-run)"))
        self.impact_list = QListWidget()
        tests_layout.addWidget(self.impact_list)

        # -------------------------
        # ADD COLUMNS TO MAIN LAYOUT
        # -------------------------
        layout.addWidget(self.tree, 2)
        layout.addWidget(details_widget, 3)
        layout.addWidget(tests_widget, 3)

    # -------------------------
    # TREE BUILD + COLORING
    # -------------------------
    def build_tree(self):
        self.tree.clear()

        # children maps
        sys_by_sr = {}
        for sy in self.model.sys:
            sys_by_sr.setdefault(sy.get("parent"), []).append(sy)

        swr_by_sys = {}
        for sw in self.model.swr:
            swr_by_sys.setdefault(sw.get("parent"), []).append(sw)

        def color_item(item, status):
            if status == "green":
                item.setBackground(0, QColor("lightgreen"))
            elif status == "orange":
                item.setBackground(0, QColor("orange"))
            else:
                item.setBackground(0, QColor("red"))

        def compute_status(req_id, level, child_statuses):
            # self coverage at its level
            self_covered = self.model.is_req_tested(req_id, level=level)

            # leaf node
            if not child_statuses:
                return "green" if self_covered else "red"

            all_green = self_covered and all(s == "green" for s in child_statuses)
            any_covered = self_covered or any(s in ("green", "orange") for s in child_statuses)

            if all_green:
                return "green"
            if any_covered:
                return "orange"
            return "red"

        for sr in self.model.sr:
            sr_item = QTreeWidgetItem([sr["id"]])
            sr_item.setData(0, Qt.UserRole, sr)

            sys_children = sys_by_sr.get(sr["id"], [])
            sys_statuses = []

            for sy in sys_children:
                sys_item = QTreeWidgetItem([sy["id"]])
                sys_item.setData(0, Qt.UserRole, sy)

                swr_children = swr_by_sys.get(sy["id"], [])
                swr_statuses = []

                for sw in swr_children:
                    sw_item = QTreeWidgetItem([sw["id"]])
                    sw_item.setData(0, Qt.UserRole, sw)

                    sw_status = "green" if self.model.is_req_tested(sw["id"], level="unit") else "red"
                    color_item(sw_item, sw_status)

                    swr_statuses.append(sw_status)
                    sys_item.addChild(sw_item)

                sys_status = compute_status(sy["id"], level="integration", child_statuses=swr_statuses)
                color_item(sys_item, sys_status)

                sys_statuses.append(sys_status)
                sr_item.addChild(sys_item)

            sr_status = compute_status(sr["id"], level="system", child_statuses=sys_statuses)
            color_item(sr_item, sr_status)

            self.tree.addTopLevelItem(sr_item)

        self.tree.expandAll()

    # -------------------------
    # SELECT + TEST LIST
    # -------------------------
    def on_select(self, item):
        req = item.data(0, Qt.UserRole)
        if not req:
            return

        self.selected_requirement_id = req["id"]
        self.impact_list.clear()

        self.id_field.setText(req["id"])
        self.desc_field.setText(req.get("description", ""))

        self.tests_tree.clear()
        self.test_code_view.clear()

        tests = self.model.get_tests_for_requirement(req["id"])
        if not tests:
            self.tests_tree.expandAll()
            return

        # group by file (no duplicates)
        files_dict = {}
        for t in tests:
            file_path = t["file"]
            files_dict.setdefault(file_path, []).append(t)

        for file_path, test_list in files_dict.items():
            file_item = QTreeWidgetItem([file_path])
            file_item.setData(0, Qt.UserRole, {"type": "file", "path": file_path})

            for test in test_list:
                test_item = QTreeWidgetItem([test["test_id"]])
                test_item.setData(0, Qt.UserRole, {
                    "type": "test",
                    "file": file_path,
                    "function": test.get("function"),
                    "test_id": test.get("test_id")
                })
                file_item.addChild(test_item)

            self.tests_tree.addTopLevelItem(file_item)

        self.tests_tree.expandAll()

    def on_test_tree_click(self, item, column):
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        if data.get("type") == "test":
            self.show_test_code(data["file"], data["function"])
        else:
            self.test_code_view.clear()

    def show_test_code(self, file_path, test_name):
        self.output_label.setText("Test Details")
        file_path = (file_path or "").replace("\\", "/")
        if not file_path or not os.path.exists(file_path):
            self.test_code_view.setPlainText(f"File not found:\n{file_path}")
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == test_name:
                    lines = source.splitlines()
                    start_line = node.lineno - 1
                    end_line = node.end_lineno
                    function_code = "\n".join(lines[start_line:end_line])
                    self.test_code_view.setPlainText(function_code)
                    return

            self.test_code_view.setPlainText("Test function not found.")

        except Exception as e:
            self.test_code_view.setPlainText(f"Error parsing file:\n{e}")

    # -------------------------
    # CRUD
    # -------------------------
    def save(self):
        item = self.tree.currentItem()
        if not item:
            return
        req = item.data(0, Qt.UserRole)
        req["description"] = self.desc_field.toPlainText()
        req["version"] = str(float(req.get("version", "1.0")) + 0.1)
        self.model.save_all()
        QMessageBox.information(self, "Saved", "Requirement updated")

    def add_requirement(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Requirement")
        l = QVBoxLayout(dialog)

        level_box = QComboBox()
        level_box.addItems(["SR", "SYS", "SWR"])

        parent_box = QComboBox()
        parent_box.addItem("None")

        desc = QTextEdit()

        def update_parents():
            parent_box.clear()
            parent_box.addItem("None")

            level = level_box.currentText()
            if level == "SYS":
                parent_box.addItems([r["id"] for r in self.model.sr])
            elif level == "SWR":
                parent_box.addItems([r["id"] for r in self.model.sys])

        level_box.currentTextChanged.connect(update_parents)
        update_parents()

        btn = QPushButton("Add")

        def on_add():
            level = level_box.currentText()
            parent = parent_box.currentText()
            parent = None if parent == "None" else parent

            new_id = self.model.add_requirement(
                level=level,
                description=desc.toPlainText(),
                parent=parent
            )

            QMessageBox.information(self, "Added", f"Requirement {new_id} added successfully")

            dialog.accept()
            self.build_tree()
            self.update_coverage()

        btn.clicked.connect(on_add)

        l.addWidget(QLabel("Level"))
        l.addWidget(level_box)
        l.addWidget(QLabel("Parent"))
        l.addWidget(parent_box)
        l.addWidget(QLabel("Description"))
        l.addWidget(desc)
        l.addWidget(btn)

        dialog.exec_()

    def delete_requirement(self):
        item = self.tree.currentItem()
        if not item:
            return

        req = item.data(0, Qt.UserRole)
        req_id = req["id"]

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete requirement {req_id} and all its children?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.model.delete_requirement(req_id)
            self.build_tree()
            self.update_coverage()

    def export_trace(self):
        self.model.export_traceability_csv()
        QMessageBox.information(self, "Exported", "traceability_matrix.csv generated")

    # -------------------------
    # COVERAGE + RUN
    # -------------------------
    def update_coverage(self):
        level_cov = self.model.coverage_by_level()

        def percent(data):
            if data["total"] == 0:
                return 0.0
            return round((data["covered"] / data["total"]) * 100.0, 1)

        unit_p = percent(level_cov["unit"])
        int_p = percent(level_cov["integration"])
        sys_p = percent(level_cov["system"])

        self.coverage_label.setText(
            f"Unit: {unit_p}% | Integration: {int_p}% | System: {sys_p}%"
        )

    def run_code_coverage(self):
        self.output_label.setText("Coverage Report")

        try:
            # Monospace da bi poravnanje radilo
            self.test_code_view.setFontFamily("Consolas")

            # 1) erase
            p = subprocess.run(["coverage", "erase"], capture_output=True, text=True)
            if p.returncode != 0:
                self.test_code_view.setPlainText("coverage erase failed:\n" + (p.stderr or p.stdout or ""))
                return

            # 2) run pytest
            p = subprocess.run(["coverage", "run", "-m", "pytest"], capture_output=True, text=True)
            if p.returncode != 0:
                self.test_code_view.setPlainText(
                    "Pytest failed while running coverage.\n\n"
                    "STDOUT:\n" + (p.stdout or "") + "\n\n"
                                                     "STDERR:\n" + (p.stderr or "")
                )
                return

            # 3) report
            r = subprocess.run(["coverage", "report", "-m"], capture_output=True, text=True)
            if r.returncode != 0:
                self.test_code_view.setPlainText("coverage report failed:\n" + (r.stderr or r.stdout or ""))
                return

            lines = (r.stdout or "").splitlines()

            rows = []
            total_row = None

            for raw in lines:
                s = raw.strip()
                if not s:
                    continue

                if s.startswith("face_app") and "__init__.py" not in s:
                    parts = s.split()
                    # Name  Stmts  Miss  Cover  Missing
                    if len(parts) >= 4:
                        name = parts[0].replace("face_app\\", "").replace("face_app/", "")
                        statements = parts[1]
                        missing_lines = parts[2]
                        coverage_pct = parts[3]
                        rows.append((name, statements, missing_lines, coverage_pct))

                if s.startswith("TOTAL"):
                    parts = s.split()
                    if len(parts) >= 4:
                        total_row = ("TOTAL", parts[1], parts[2], parts[3])

            # Ako nema ničega, pokaži raw
            if not rows and not total_row:
                self.test_code_view.setPlainText(r.stdout or "")
                return

            # Izračunaj širine kolona (da bude uvijek poravnato)
            file_w = max([len("File")] + [len(x[0]) for x in rows] + ([len("TOTAL")] if total_row else [])) + 2
            col_w = 16  # dovoljno za tekst "Missing Lines"

            header = (
                f"{'File':<{file_w}}"
                f"{'Statements':>{col_w}}"
                f"{'Missing Lines':>{col_w}}"
                f"{'Coverage %':>{col_w}}"
            )
            sep = "-" * (file_w + col_w * 3)

            out_lines = []
            out_lines.append("Coverage Report")
            out_lines.append(sep)
            out_lines.append(header)
            out_lines.append(sep)

            for name, stmts, miss, cov in rows:
                out_lines.append(
                    f"{name:<{file_w}}{stmts:>{col_w}}{miss:>{col_w}}{cov:>{col_w}}"
                )

            if total_row:
                out_lines.append(sep)
                name, stmts, miss, cov = total_row
                out_lines.append(
                    f"{name:<{file_w}}{stmts:>{col_w}}{miss:>{col_w}}{cov:>{col_w}}"
                )

            self.test_code_view.setPlainText("\n".join(out_lines))

        except FileNotFoundError as e:
            self.test_code_view.setPlainText(
                "Coverage failed: command not found.\n"
                "Make sure 'coverage' is installed in the same Python environment.\n\n"
                f"{e}"
            )
        except Exception as e:
            self.test_code_view.setPlainText(f"Coverage failed:\n{e}")

    # -------------------------
    # IMPACT ANALYSIS
    # -------------------------
    def show_impact_analysis(self):
        self.output_label.setText("Impact Analysis")
        if not self.selected_requirement_id:
            QMessageBox.information(self, "Impact Analysis", "Select a requirement first.")
            return

        impacted_reqs = self.model.get_impacted_requirements(self.selected_requirement_id)
        impacted_tests = self.model.get_impacted_tests(self.selected_requirement_id)

        self.impact_list.clear()

        if not impacted_tests:
            self.impact_list.addItem("No impacted tests found.")
        else:
            def _key(t):
                return (t.get("level", ""), t.get("test_id", ""))

            for t in sorted(impacted_tests, key=_key):
                lvl = t.get("level", "unknown")
                tid = t.get("test_id", "")
                f = t.get("file", "")
                self.impact_list.addItem(f"[{lvl}] {tid}  —  {os.path.basename(f)}")

        # summary in output panel
        summary_lines = [
            f"Impact Analysis for: {self.selected_requirement_id}",
            f"Impacted requirements ({len(impacted_reqs)}): {', '.join(impacted_reqs)}",
            f"Impacted tests ({len(impacted_tests)}):",
        ]
        for t in impacted_tests:
            summary_lines.append(f"- {t.get('test_id')} ({t.get('level')}) -> {t.get('file')}")

        self.test_code_view.setPlainText("\n".join(summary_lines))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = RequirementsGUI()
    w.showMaximized()
    sys.exit(app.exec_())