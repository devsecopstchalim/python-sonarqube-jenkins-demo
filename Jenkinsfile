pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timeout(time: 20, unit: 'MINUTES')
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
            agent { docker { image 'python:3.12-slim'; reuseNode true; args '-e HOME=/tmp' } }
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

        stage('SonarQube Analysis + Quality Gate') {
            steps {
                script {
                    // 'SonarScanner' = nom de l'outil (Manage Jenkins > Tools)
                    def scannerHome = tool 'SonarScanner'
                    // 'SonarQube' = nom du serveur (Manage Jenkins > System > SonarQube servers)
                    // Jenkins injecte SONAR_HOST_URL et SONAR_TOKEN (credential "sonar") dans l'environnement.
                    withSonarQubeEnv('SonarQube') {
                        // qualitygate.wait : le scanner attend le verdict, sans webhook.
                        sh "${scannerHome}/bin/sonar-scanner -Dsonar.qualitygate.wait=true -Dsonar.qualitygate.timeout=300"
                    }
                }
            }
        }
    }

    post {
        success { echo 'Pipeline OK : checkout + tests + SonarQube (quality gate passé).' }
        failure { echo 'Echec : voir Console Output.' }
    }
}
