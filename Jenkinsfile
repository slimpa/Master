pipeline {
    agent any

    triggers {
        pollSCM('H/2 * * * *')
    }

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
                rm -rf .ci_venv
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
                  -v \
                  --ignore=tests/test_gui_branches.py \
                  --ignore=tests/test_gui_missing_branches.py \
                  --ignore=tests/test_gui_remaining_branches.py \
                  --ignore=tests/test_gui_runtime.py \
                  --ignore=tests/test_gui_unit.py \
                  --json-report \
                  --json-report-file=reports/pytest-report.json \
                  --junitxml=reports/junit.xml \
                  --cov=face_app \
                  --cov-report=xml:reports/coverage.xml
                '''
            }
        }

        stage('Publish results to ELK') {
            steps {
                sh '''
                . .ci_venv/bin/activate

                python - <<'PY'
import json
import os
import urllib.request
from datetime import datetime, timezone

REPORT = "reports/pytest-report.json"
ELASTIC_URL = os.environ.get("ELASTIC_URL", "http://localhost:9200")
INDEX = os.environ.get("ELASTIC_INDEX", "test-results")

BUILD_NUMBER = os.environ.get("BUILD_NUMBER", "")
JOB_NAME = os.environ.get("JOB_NAME", "")
BUILD_URL = os.environ.get("BUILD_URL", "")
GIT_COMMIT = os.environ.get("GIT_COMMIT", "")
BRANCH_NAME = os.environ.get("BRANCH_NAME", "")

def detect_level(nodeid: str, test_name: str) -> str:
    text = f"{nodeid} {test_name}".upper()
    if "ST_" in text or "SYSTEM" in text:
        return "system"
    if "IT_" in text or "INTEGRATION" in text:
        return "integration"
    return "unit"

def extract_test_id(test: dict) -> str:
    markers = test.get("markers", [])
    for marker in markers:
        if marker.get("name") == "test_id":
            args = marker.get("args", [])
            if args:
                return str(args[0])

    nodeid = test.get("nodeid", "unknown")
    return nodeid.split("::")[-1]

def extract_requirement_ids(test: dict):
    reqs = []
    markers = test.get("markers", [])

    for marker in markers:
        if marker.get("name") == "requirement":
            args = marker.get("args", [])
            for arg in args:
                value = str(arg).strip()
                if value and value not in reqs:
                    reqs.append(value)

    return reqs if reqs else ["UNKNOWN"]

with open(REPORT, "r", encoding="utf-8") as f:
    data = json.load(f)

tests = data.get("tests", [])
published = 0

for test in tests:
    nodeid = test.get("nodeid", "unknown")
    outcome = test.get("outcome", "unknown").upper()
    test_id = extract_test_id(test)
    requirement_ids = extract_requirement_ids(test)

    duration = None
    if isinstance(test.get("call"), dict):
        duration = test["call"].get("duration")
    elif isinstance(test.get("setup"), dict):
        duration = test["setup"].get("duration")

    doc = {
        "@timestamp": datetime.now(timezone.utc).isoformat(),
        "test_id": test_id,
        "requirement_id": requirement_ids,
        "status": outcome,
        "level": detect_level(nodeid, test_id),
        "duration": duration,
        "nodeid": nodeid,
        "build_number": BUILD_NUMBER,
        "job_name": JOB_NAME,
        "build_url": BUILD_URL,
        "git_commit": GIT_COMMIT,
        "git_branch": BRANCH_NAME
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