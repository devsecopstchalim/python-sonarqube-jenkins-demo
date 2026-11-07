pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
    }

    environment {
        // >>> A MODIFIER : ton nom d'utilisateur Docker Hub (en minuscules) <<<
        DOCKERHUB_USER = 'devsecopstchalim'
        IMAGE_NAME     = "${DOCKERHUB_USER}/python-sonarqube-demo"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git log -1 --oneline'
                script { env.SHORT_SHA = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim() }
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
                    def scannerHome = tool 'SonarScanner'
                    withSonarQubeEnv('SonarQube') {
                        // qualitygate.wait : le scanner attend le verdict, sans webhook.
                        sh "${scannerHome}/bin/sonar-scanner -Dsonar.qualitygate.wait=true -Dsonar.qualitygate.timeout=300"
                    }
                }
            }
        }

        // Ces stages ne s'exécutent que si le quality gate est PASSED
        stage('Docker Build') {
            steps {
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
            steps {
                withCredentials([usernamePassword(credentialsId: 'docker_cred',
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
        success { echo "Pipeline OK : image publiee -> ${env.IMAGE_NAME}:${env.BUILD_NUMBER}" }
        failure { echo 'Echec : voir Console Output.' }
    }
}
