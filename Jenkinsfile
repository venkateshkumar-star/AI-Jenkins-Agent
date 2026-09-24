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

    stage('Manual Error Test') {
        steps {
            sh '''
                echo "========================================"
                echo "MANUAL ERROR TEST"
                echo "========================================"

                echo "This error is intentional."
                echo "Testing Jenkins -> Monitoring Agent."

                exit 1
            '''
        }
    }

    stage('Build Docker Image') {
        steps {
            sh '''
                set -e

                docker build \
                    -t ${IMAGE_NAME}:${BUILD_NUMBER} \
                    -t ${IMAGE_NAME}:latest \
                    ./app
            '''
        }
    }

    stage('Deploy') {
        steps {
            sh '''
                set -e

                docker rm -f ${CONTAINER_NAME} 2>/dev/null || true

                docker run -d \
                    --name ${CONTAINER_NAME} \
                    --restart unless-stopped \
                    -p ${HOST_PORT}:80 \
                    ${IMAGE_NAME}:${BUILD_NUMBER}

                sleep 5

                docker ps --filter "name=${CONTAINER_NAME}"

                curl -f http://127.0.0.1:${HOST_PORT}/
            '''
        }
    }
}
