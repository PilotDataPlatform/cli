pipeline {
    agent { label 'guacamole-vm-core' }
    stages {
      stage('Git clone for dev') {
          when {branch "k8s-dev"}
          steps{
            script {
            git branch: "k8s-dev",
                url: 'https://git.indocresearch.org/charite/command_line_tool_vrectl.git',
                credentialsId: 'lzhao'
              }
          }
      }
      stage('DEV unit test') {
        when {branch "k8s-dev"}
        steps{
          sh "pip3 install -r requirements.txt"
          sh "pip3 install -r tests/test_requirements.txt"
          sh "pytest tests/test_core.py"
        }
      }
  }
    post {
        failure {
        slackSend color: '#FF0000', message: "Build Failed! - ${env.JOB_NAME} ${env.BUILD_NUMBER}  (<${env.BUILD_URL}|Open>)", channel: 'jenkins-dev-staging-monitor'
    }
  }

}
