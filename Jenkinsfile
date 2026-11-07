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

        stage('SonarQube Analysis + Quality Gate') {
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'
                    withSonarQubeEnv('SonarQube') {
                        // sonar.qualitygate.wait makes the scanner poll SonarQube, so no webhook is needed.
                        sh "${scannerHome}/bin/sonar-scanner -Dsonar.qualitygate.wait=true -Dsonar.qualitygate.timeout=300"
                    }
                }
            }
        }

        stage('Docker Build') {
            steps {
                script { env.SHORT_SHA = env.GIT_COMMIT ? env.GIT_COMMIT.take(7) : 'nogit' }
                sh '''
                    docker build --pull \
                        -t "$IMAGE_NAME:$BUILD_NUMBER" \
                        -t "$IMAGE_NAME:$SHORT_SHA" \
                        -t "$IMAGE_NAME:latest" .
                '''
            }
        }

        stage('Smoke Test Image') {
            steps {
                sh '''
                    cid=$(docker run -d -p 127.0.0.1::8000 "$IMAGE_NAME:$BUILD_NUMBER")
                    trap 'docker rm -f "$cid" >/dev/null' EXIT
                    port=$(docker port "$cid" 8000/tcp | head -n1 | sed 's/.*://')
                    for i in $(seq 1 20); do
                        if curl -fsS "127.0.0.1:$port/health"; then echo; exit 0; fi
                        sleep 1
                    done
                    docker logs "$cid"
                    exit 1
                '''
            }
        }

        stage('Docker Push') {
            when { expression { return params.PUSH_IMAGE } }
            steps {
                script {
                    if (!params.DOCKERHUB_USER) { error('DOCKERHUB_USER is required when PUSH_IMAGE is true') }
                }
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                                                  usernameVariable: 'DH_USER',
                                                  passwordVariable: 'DH_PASS')]) {
                    sh '''
                        echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
                        docker push "$IMAGE_NAME:$BUILD_NUMBER"
                        docker push "$IMAGE_NAME:$SHORT_SHA"
                        docker push "$IMAGE_NAME:latest"
                        docker logout
                    '''
                }
            }
        }
    }

    post {
        success { echo "Image ready: ${env.IMAGE_NAME}:${env.BUILD_NUMBER}" }
        failure { echo 'Build failed - check the stage that is red (tests, Sonar quality gate, Docker).' }
    }
}
