pipeline {
    agent any

    environment {
        APP_NAME = "jenkins-demo-app"
        IMAGE_NAME = "jenkins-demo-app"
        CONTAINER_NAME = "jenkins-demo-app"
        HOST_PORT = "8081"
        MONITOR_URL = "http://127.0.0.1:5001"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Validate') {
            steps {
                sh '''
                    set -e

                    echo "Checking application files..."

                    test -f app/index.html
                    test -f app/Dockerfile

                    echo "Validation successful."
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    set -e

                    echo "Building Docker image..."

                    docker build \
                        -t ${IMAGE_NAME}:${BUILD_NUMBER} \
                        -t ${IMAGE_NAME}:latest \
                        ./app

                    echo "Docker image build successful."
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    set -e

                    echo "Stopping previous container if it exists..."

                    docker rm -f ${CONTAINER_NAME} 2>/dev/null || true

                    echo "Starting new container..."

                    docker run -d \
                        --name ${CONTAINER_NAME} \
                        --restart unless-stopped \
                        -p ${HOST_PORT}:80 \
                        ${IMAGE_NAME}:${BUILD_NUMBER}

                    echo "Waiting for application..."

                    sleep 5

                    echo "Checking container..."

                    docker ps --filter "name=${CONTAINER_NAME}"

                    echo "Running application health check..."

                    curl -f http://127.0.0.1:${HOST_PORT}/

                    echo "Application health check successful."
                '''
            }
        }
    }

    post {

        success {
            echo "========================================"
            echo "DEPLOYMENT SUCCESSFUL"
            echo "========================================"

            echo "Build: ${BUILD_NUMBER}"
            echo "Application port: ${HOST_PORT}"
            echo "Build URL: ${BUILD_URL}"
        }

        failure {
            echo "========================================"
            echo "BUILD FAILED"
            echo "========================================"

            echo "Job: ${JOB_NAME}"
            echo "Build: ${BUILD_NUMBER}"
            echo "Build URL: ${BUILD_URL}"

            sh '''
                echo "Sending failure notification to monitoring agent..."

                curl -sS \
                    --max-time 30 \
                    -X POST \
                    --data-urlencode "job_name=${JOB_NAME}" \
                    --data-urlencode "build_number=${BUILD_NUMBER}" \
                    "${MONITOR_URL}/jenkins/failure" \
                    || echo "WARNING: Monitoring agent notification failed."
            '''
        }

        always {
            echo "========================================"
            echo "BUILD FINISHED"
            echo "========================================"

            echo "Job: ${JOB_NAME}"
            echo "Build: ${BUILD_NUMBER}"
            echo "Result: ${currentBuild.currentResult}"
            echo "Build URL: ${BUILD_URL}"
        }
    }
}
