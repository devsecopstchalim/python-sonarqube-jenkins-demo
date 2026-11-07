pipeline {
    agent any

    options {
        // On désactive le checkout automatique : seul le stage ci-dessous récupère le code.
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
    }

    post {
        success { echo 'Checkout OK : le pipeline est correctement relié à GitHub.' }
        failure { echo 'Echec : voir Console Output.' }
    }
}
