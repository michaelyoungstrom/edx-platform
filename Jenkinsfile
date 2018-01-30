pipeline {
    agent { label 'master' }
    stages {
        stage('sleep') {
            steps {
                sh 'sleep 180'
            }
        }
        stage('echo') {
            steps {
                sh 'echo hey'
            }
        }
    }
}
