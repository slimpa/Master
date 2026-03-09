pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Python dependencies') {
            steps {
                sh '''
                python3 -m pip install --upgrade pip
                pip3 install pytest
                if [ -f requirements.txt ]; then pip3 install -r requirements.txt; fi
                '''
            }
        }

        stage('Run tests') {
            steps {
                sh '''
                pytest tests
                '''
            }
        }

    }
}