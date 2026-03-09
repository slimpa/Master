pipeline {
    agent any

    triggers {
        cron('0 1 * * *')
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
                    python3 --version || python --version || true
                    pip3 --version || pip --version || true
                    pytest --version || true
                '''
            }
        }

        stage('Install dependencies') {
            steps {
                sh '''
                    python3 -m pip install --upgrade pip || python -m pip install --upgrade pip
                    pip3 install -r requirements.txt || pip install -r requirements.txt
                '''
            }
        }

        stage('Run tests') {
            steps {
                sh '''
                    mkdir -p reports
                    pytest tests --junitxml=reports/junit.xml
                '''
            }
        }
    }

    post {
        always {
            junit 'reports/junit.xml'
            archiveArtifacts artifacts: 'reports/**', fingerprint: true
        }
    }
}