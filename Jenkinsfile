pipeline {
  agent any
  options { timestamps(); disableConcurrentBuilds() }
  environment {
    IMAGE = "${DOCKERHUB_USER}/eventpass"
    DEPLOY_HOST = credentials('eventpass-host')
  }
  stages {
    stage('Build image') {
      steps { sh 'docker build --pull -t "$IMAGE:$BUILD_NUMBER" -t "$IMAGE:latest" .' }
    }
    stage('Push image') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'DH_USER', passwordVariable: 'DH_TOKEN')]) {
          sh 'echo "$DH_TOKEN" | docker login --username "$DH_USER" --password-stdin'
          sh 'docker push "$IMAGE:$BUILD_NUMBER" && docker push "$IMAGE:latest"'
          sh 'docker logout'
        }
      }
    }
    stage('Deploy to EC2') {
      steps {
        sshagent(credentials: ['eventpass-ec2-key']) {
          sh 'ssh -o StrictHostKeyChecking=accept-new ec2-user@"$DEPLOY_HOST" "sudo docker pull $IMAGE:$BUILD_NUMBER && (sudo docker rm -f eventpass || true) && sudo docker run -d --name eventpass --restart unless-stopped -p 80:8000 -v /opt/eventpass/data:/data $IMAGE:$BUILD_NUMBER"'
        }
      }
    }
  }
  post {
    always { sh 'docker image prune -f || true' }
  }
}
