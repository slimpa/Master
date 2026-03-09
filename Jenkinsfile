pipeline {
    agent any

    triggers {
        cron('0 1 * * *')
    }

    options {
        timestamps()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Show workspace') {
            steps {
                sh '''
                    echo "Workspace: $(pwd)"
                    ls -la
                    python3 --version
                    pip3 --version
                    cmake --version
                '''
            }
        }

        stage('Create venv') {
            steps {
                sh '''
                    rm -rf .ci_venv
                    python3 -m venv .ci_venv
                    . .ci_venv/bin/activate
                    python --version
                    pip --version
                    pip install --upgrade pip
                '''
            }
        }

        stage('Install dependencies') {
            steps {
                sh '''
                    . .ci_venv/bin/activate
                    pip install pytest pytest-cov pyyaml pillow opencv-python face-recognition
                '''
            }
        }

        stage('Run tests') {
            steps {
                sh '''
                    . .ci_venv/bin/activate
                    mkdir -p reports
                    pytest tests \
                      --junitxml=reports/junit.xml \
                      --cov=face_app \
                      --cov-report=xml:reports/coverage.xml \
                      --cov-report=term-missing
                '''
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/junit.xml'
            archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/**', fingerprint: true
        }
    }
}