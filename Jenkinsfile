pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timeout(time: 20, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    // Local Jenkins cannot receive GitHub webhooks, so poll the repo every ~2 minutes.
    triggers { pollSCM('H/2 * * * *') }

    parameters {
        booleanParam(name: 'PUSH_IMAGE', defaultValue: false,
                     description: 'Push the image to Docker Hub (needs credentials "dockerhub-creds")')
        string(name: 'DOCKERHUB_USER', defaultValue: '',
               description: 'Docker Hub username (required when PUSH_IMAGE is true)')
    }

    environment {
        APP_NAME   = 'python-sonar-demo'
        IMAGE_NAME = "${params.DOCKERHUB_USER ? params.DOCKERHUB_USER : 'local'}/python-sonar-demo"
    }

    stages {
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

        

        
    }

  
}
