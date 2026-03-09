pipeline {
    agent {
        docker {
            image 'python:3.11'
        }
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install dependencies') {
            steps {
                sh '''
                    pip install -U pip
                    if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
                    pip install pytest
                '''
            }
        }

        stage('Run tests') {
            steps {
                sh '''
                    pytest
                '''
            }
        }
    }
}