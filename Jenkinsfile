pipeline {
    agent { label 'master' }
    stages {
        stage('checkout') {
            steps {
                checkout([$class: 'GitSCM', branches: [[name: '*/master']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[url: 'https://github.com/edx/testeng-ci']]])
                stash 'testeng-ci'
            }
        }
        stage('try to cd to the dir') {
            steps {
                sh 'cd testeng-ci'
            }
        }
        stage('try to cd to the dir after unstash') {
            steps {
                unstash 'testeng-ci'
                sh 'cd testeng-ci'
            }
        }
    }
}
