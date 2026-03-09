pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test environment') {
            steps {
                sh '''
                    echo "Testing shell access"
                    uname -a || true
                    python3 --version || python --version || true
                    pip3 --version || pip --version || true
                    pytest --version || true
                '''
            }
        }
    }
}