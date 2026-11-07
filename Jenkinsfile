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
                script {
                    env.SHORT_SHA = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()

                    // Anti-boucle : si le dernier commit vient de Jenkins (mise a jour de values.yml),
                    // on saute tous les stages suivants au lieu de relancer un build inutile.
                    def author = sh(returnStdout: true, script: 'git log -1 --pretty=%an').trim()
                    if (author == 'Jenkins CI') {
                        env.SKIP_PIPELINE = 'true'
                        currentBuild.result = 'NOT_BUILT'
                        echo "Dernier commit fait par Jenkins CI -> pipeline ignore."
                    }
                }
            }
        }

        stage('Test') {
            when { beforeAgent true; expression { env.SKIP_PIPELINE != 'true' } }
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
            when { expression { env.SKIP_PIPELINE != 'true' } }
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
            when { expression { env.SKIP_PIPELINE != 'true' } }
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
            when { expression { env.SKIP_PIPELINE != 'true' } }
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
            when { expression { env.SKIP_PIPELINE != 'true' } }
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
            steps {
                // 'github-cred' = Secret text (Personal Access Token avec droit d'ecriture sur le repo)
                withCredentials([string(credentialsId: 'github-cred', variable: 'GH_TOKEN')]) {
                    // ''' (et non """) : Groovy n'interpole pas le token, c'est le shell qui le lit ; Jenkins le masque dans les logs
                    sh '''
                        set -e
                        yq -i '.backend.image.tag = strenv(SHORT_SHA)' values.yml
                        git diff --quiet values.yml && { echo "no change"; exit 0; }

                        git config user.email "jenkins@ci.local"
                        git config user.name  "Jenkins CI"
                        git add values.yml
                        git commit -m "ci: deploy ${SHORT_SHA} [skip ci]"

                        REPO_URL=$(git remote get-url origin | sed "s|https://||")
                        git push "https://x-access-token:${GH_TOKEN}@${REPO_URL}" HEAD:main
                    '''
                }
            }
        }
    }

    post {
        success {
            script {
                if (env.SKIP_PIPELINE != 'true') {
                    echo "Pipeline OK : image publiee -> ${env.IMAGE_NAME}:${env.SHORT_SHA}"
                }
            }
        }
        failure { echo 'Echec : voir Console Output.' }
    }
}