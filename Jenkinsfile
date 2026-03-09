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
                pip install pytest pytest-cov pillow opencv-python
                '''
            }
        }

        stage('Run tests') {
            steps {
                sh '''
                . .ci_venv/bin/activate
                mkdir -p reports
                pytest tests --junitxml=reports/junit.xml
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