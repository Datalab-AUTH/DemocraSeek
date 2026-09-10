/*
 * Jenkinsfile to pull the source code from git, build a docker image
 * using a Dockerfile and push that image to a registry.
 */


pipeline {

  agent any

  environment {
    /*
     * edit the following variables
     */
    
    // the name of your docker image
    // set to 'datalabauth/projectname' for Dockerhub
    // or just to 'projectname' if you're using our private registry
    dockertag = 'datalabauth/democraseek'

    // the registry name
    // set to 'https://registry.hub.docker.com' for DockerHub
    // or to 'https://registry.csd.auth.gr' for our private registry
    registry = 'https://registry.hub.docker.com'

    // the credentials to the above registry as stored in Jenkins
    // set to 'dockerhub' for DockerHub 
    // or 'datalab-registry' for our private registry
    registry_credentials = 'dockerhub'
  }

  // you probably don't need to edit anything below this line
  stages {
           
    stage('Checkout the source code') {
      steps {
        checkout scm
      }
    }

    stage('Build') {
      steps {
        script {
          image_db          = docker.build("${dockertag}-db", "-f deployment/Dockerfile.database .")
          image_backend     = docker.build("${dockertag}-backend", "-f deployment/Dockerfile.backend .")
          image_frontend    = docker.build("${dockertag}-frontend", "-f deployment/Dockerfile.frontend .")
        }
      }
    }

    stage('Push') {
      steps {
        script {
          docker.withRegistry(registry, registry_credentials) {
            image_db.push()
            image_backend.push()
            image_frontend.push()
          }
        }
      }
    }
  }
}

