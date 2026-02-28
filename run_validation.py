from tools.loader import load_yaml
from tools.traceability import build_sw_trace
from tools.validator import validate_software_requirements

sw_requirements = load_yaml("requirements/software.yaml")
trace = build_sw_trace(sw_requirements)

errors = validate_software_requirements(trace)

if not errors:
    print("✔ All software requirements are implemented")
else:
    print("✖ Validation errors:")
    for e in errors:
        print(e)