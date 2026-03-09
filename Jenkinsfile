pipeline {
    agent {
        docker {
            image 'python:3.11'
            args '-u root:root'
        }
    }

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
                    python --version
                    pip --version
                '''
            }
        }

        stage('Install dependencies') {
            steps {
                sh '''
                    python -m pip install --upgrade pip
                    pip install pytest pytest-cov
                    pip install face-recognition opencv-python pillow pyyaml
                '''
            }
        }

        stage('Run tests') {
            steps {
                sh '''
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