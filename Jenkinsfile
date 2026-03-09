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
                python3 --version
                pip3 --version
                '''
            }
        }

        stage('Install dependencies') {
            steps {
                sh '''
                python3 -m pip install --upgrade pip
                pip3 install pytest pytest-cov pillow opencv-python
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