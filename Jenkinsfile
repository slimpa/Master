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
                pip install pytest pytest-cov pillow opencv-python-headless
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
                  --junitxml=reports/junit.xml
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