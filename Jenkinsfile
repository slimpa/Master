pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Show environment') {
            steps {
                sh '''
                echo "Workspace: $(pwd)"
                ls -la
                python3 --version
                '''
            }
        }

        stage('Create venv') {
            steps {
                sh '''
                python3 -m venv .ci_venv
                . .ci_venv/bin/activate
                python -m pip install --upgrade pip
                '''
            }
        }

        stage('Install dependencies') {
            steps {
                sh '''
                . .ci_venv/bin/activate
                pip install pytest pytest-cov pytest-json-report pillow opencv-python-headless
                '''
            }
        }

        stage('Run tests') {
            steps {
                sh '''
                . .ci_venv/bin/activate
                mkdir -p reports

                pytest tests \
                  --ignore=tests/test_gui_branches.py \
                  --ignore=tests/test_gui_missing_branches.py \
                  --ignore=tests/test_gui_remaining_branches.py \
                  --ignore=tests/test_gui_runtime.py \
                  --ignore=tests/test_gui_unit.py \
                  --json-report \
                  --json-report-file=reports/pytest-report.json \
                  --junitxml=reports/junit.xml
                '''
            }
        }

        stage('Publish results to ELK') {
            steps {
                sh '''
                . .ci_venv/bin/activate

                python - <<PY
import json
import os
import re
import urllib.request
from datetime import datetime, timezone

REPORT = "reports/pytest-report.json"
ELASTIC_URL = os.environ.get("ELASTIC_URL", "http://host.docker.internal:9200")
INDEX = os.environ.get("ELASTIC_INDEX", "test-results")

BUILD_NUMBER = os.environ.get("BUILD_NUMBER", "")
JOB_NAME = os.environ.get("JOB_NAME", "")
BUILD_URL = os.environ.get("BUILD_URL", "")
GIT_COMMIT = os.environ.get("GIT_COMMIT", "")

def detect_level(nodeid: str, test_name: str) -> str:
    text = f"{nodeid} {test_name}".upper()
    if "ST_" in text or "SYSTEM" in text:
        return "system"
    if "IT_" in text or "INTEGRATION" in text:
        return "integration"
    return "unit"

def extract_test_id(nodeid: str) -> str:
    name = nodeid.split("::")[-1]
    m = re.search(r'(UT_[A-Z]+_\\d+_\\d+|IT_[A-Z]+_\\d+_\\d+|ST_[A-Z]+_\\d+_\\d+)', name.upper())
    if m:
        return m.group(1)
    return name

def extract_requirement_id(nodeid: str) -> str:
    text = nodeid.upper().replace("-", "_")
    patterns = [
        r'\\bSWR_(\\d+)\\b',
        r'\\bSR_(\\d+)\\b',
        r'\\bUT_SWR_(\\d+)_\\d+\\b',
        r'\\bIT_SWR_(\\d+)_\\d+\\b',
        r'\\bST_SR_(\\d+)_\\d+\\b',
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            if "SR_" in pattern and "SWR_" not in pattern:
                return f"SR_{m.group(1)}"
            if "ST_SR_" in pattern:
                return f"SR_{m.group(1)}"
            return f"SWR_{m.group(1)}"
    return "UNKNOWN"

with open(REPORT, "r", encoding="utf-8") as f:
    data = json.load(f)

tests = data.get("tests", [])
published = 0

for test in tests:
    nodeid = test.get("nodeid", "unknown")
    outcome = test.get("outcome", "unknown").upper()
    test_id = extract_test_id(nodeid)
    requirement_id = extract_requirement_id(nodeid)

    duration = None
    if isinstance(test.get("call"), dict):
        duration = test["call"].get("duration")
    elif isinstance(test.get("setup"), dict):
        duration = test["setup"].get("duration")

    doc = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test_id": test_id,
        "requirement_id": requirement_id,
        "status": outcome,
        "level": detect_level(nodeid, test_id),
        "duration": duration,
        "nodeid": nodeid,
        "build_number": BUILD_NUMBER,
        "job_name": JOB_NAME,
        "build_url": BUILD_URL,
        "git_commit": GIT_COMMIT
    }

    try:
        req = urllib.request.Request(
            f"{ELASTIC_URL}/{INDEX}/_doc",
            data=json.dumps(doc).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            print(resp.read().decode("utf-8"))
        published += 1
    except Exception as e:
        print(f"Failed to publish {nodeid}: {e}")

print(f"Published {published}/{len(tests)} test results to Elasticsearch.")
PY
                '''
            }
        }
    }

    post {
        always {
            junit testResults: 'reports/junit.xml', allowEmptyResults: true
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
        }
    }
}