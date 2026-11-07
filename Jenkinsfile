pipeline {
    agent any

    options {

        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timeout(time: 10, unit: 'MINUTES')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git log -1 --oneline'   // dernier commit récupéré
                sh 'ls -la'                 // contenu du workspace
            }
        }

        stage('Test') {
            agent { docker { image 'python:3.13-slim'; reuseNode true; args '-e HOME=/tmp' } }
            steps {
                sh '''
                    pip install --user --no-cache-dir -r requirements-dev.txt
                    python -m pytest --cov --cov-report=xml:coverage.xml --junitxml=test-results.xml
                '''
            }
            post {
                always { junit allowEmptyResults: true, testResults: 'test-results.xml' }
            }
        }
    } 
    post {
        success { echo 'Pipeline OK : checkout + tests réussis.' }
        failure { echo 'Echec : voir Console Output.' }
    }
}
