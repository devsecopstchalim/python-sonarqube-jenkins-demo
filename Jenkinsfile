pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
    }

    environment {
        // Credential Jenkins (Username with password) -> crée DOCKER_CRED_USR et DOCKER_CRED_PSW
        DOCKER_CRED = credentials('docker_cred')
        // Le nom d'utilisateur Docker Hub vient du credential : plus rien à écrire en dur
        IMAGE_NAME  = "${DOCKER_CRED_USR}/python-sonarqube-demo"
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

        // Les stages suivants ne s'exécutent que si le quality gate est PASSED
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
                sh '''
                    echo "$DOCKER_CRED_PSW" | docker login -u "$DOCKER_CRED_USR" --password-stdin
                    docker push "$IMAGE_NAME:$BUILD_NUMBER"
                    docker push "$IMAGE_NAME:$SHORT_SHA"
                    docker push "$IMAGE_NAME:latest"
                    docker logout
                '''
            }
        }

        stage('Update values.yml') {
    when { expression { env.SKIP_PIPELINE != 'true' } }
    environment {
        GIT_USER_NAME = "devsecopstchalim"
        GIT_REPO_NAME = "python-sonarqube-jenkins-demo"
    }
    steps {
        withCredentials([string(credentialsId: 'github-cred', variable: 'GITHUB_TOKEN')]) {
            sh '''
                set -e
                git config user.email "jenkins@ci.local"
                git config user.name  "Jenkins CI"

                sed -i -E "s|^( *tag:).*|\\1 \\"${SHORT_SHA}\\"|" values.yml
                git diff --quiet values.yml && { echo "no change"; exit 0; }

                git add values.yml
                git commit -m "ci: deploy ${SHORT_SHA} [skip ci]"
                git push https://${GITHUB_TOKEN}@github.com/${GIT_USER_NAME}/${GIT_REPO_NAME}.git HEAD:main
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
