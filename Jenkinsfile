pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
    }

    environment {
        // Credential Jenkins (Username with password) -> cree DOCKER_CRED_USR et DOCKER_CRED_PSW
        DOCKER_CRED = credentials('docker_cred')
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
                        sh "${scannerHome}/bin/sonar-scanner -Dsonar.qualitygate.wait=true -Dsonar.qualitygate.timeout=300"
                    }
                }
            }
        }

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

        // GitOps: the new tag goes into the SEPARATE config repo (watched by Argo CD).
        // That repo has no Jenkins webhook, so this push can never retrigger this pipeline.
        stage('Update config repo (GitOps)') {
            environment {
                CONFIG_REPO = "devsecopstchalim/test-lab-sonarqube-argocd-kubernetes-jenkins-webhook"
                CONFIG_FILE = "test-lab/values.yaml"
            }
            steps {
                withCredentials([string(credentialsId: 'github-cred', variable: 'GITHUB_TOKEN')]) {
                    sh '''
                        set -e
                        workdir=$(mktemp -d)
                        trap 'rm -rf "$workdir"' EXIT   # the clone URL contains the token: always delete it

                        git clone --depth 1 "https://${GITHUB_TOKEN}@github.com/${CONFIG_REPO}.git" "$workdir/config"
                        cd "$workdir/config"

                        git config user.email "jenkins@ci.local"
                        git config user.name  "Jenkins CI"

                        grep -qE '^ *tag:' "$CONFIG_FILE" || { echo "ERROR: no 'tag:' line in $CONFIG_FILE"; exit 1; }

                        sed -i -E "s|^( *tag:).*|\\1 \\"${SHORT_SHA}\\"|" "$CONFIG_FILE"
                        grep -n "tag:" "$CONFIG_FILE"

                        git diff --quiet "$CONFIG_FILE" && { echo "no change: tag already ${SHORT_SHA}"; exit 0; }

                        git add "$CONFIG_FILE"
                        git commit -m "ci: python-sonarqube-demo -> ${SHORT_SHA} (build ${BUILD_NUMBER})"
                        git push origin HEAD:main || { git pull --rebase origin main && git push origin HEAD:main; }
                    '''
                }
            }
        }
    }

    post {
        success { echo "Pipeline OK : image publiee -> ${env.IMAGE_NAME}:${env.SHORT_SHA} build ${env.BUILD_NUMBER} OK; config repo mis a jour" }
        failure { echo 'Echec : voir Console Output.' }
    }
}
