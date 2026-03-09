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
                    python3 --version || true
                    pip3 --version || true
                '''
            }
        }

        stage('Install dependencies') {
            steps {
                sh '''
                    python3 -m pip install --upgrade pip
                    pip3 install pytest pytest-cov face-recognition opencv-python pillow pyyaml
                '''
            }
        }

        stage('Run tests') {
            steps {
                sh '''
                    mkdir -p reports
                    pytest tests --junitxml=reports/junit.xml --cov=face_app --cov-report=xml:reports/coverage.xml --cov-report=term-missing
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