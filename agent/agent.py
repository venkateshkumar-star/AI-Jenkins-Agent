import os
import re
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

JENKINS_URL = os.environ["JENKINS_URL"].rstrip("/")
JENKINS_USER = os.environ["JENKINS_USER"]
JENKINS_TOKEN = os.environ["JENKINS_TOKEN"]
DASHBOARD_URL = os.environ["DASHBOARD_URL"].rstrip("/")

jenkins_auth = (JENKINS_USER, JENKINS_TOKEN)


def get_build_info(job_name, build_number):
    url = (
        f"{JENKINS_URL}/job/"
        f"{requests.utils.quote(job_name, safe='')}/"
        f"{build_number}/api/json"
    )

    response = requests.get(
        url,
        auth=jenkins_auth,
        timeout=15
    )

    response.raise_for_status()
    return response.json()


def get_console_log(job_name, build_number):
    url = (
        f"{JENKINS_URL}/job/"
        f"{requests.utils.quote(job_name, safe='')}/"
        f"{build_number}/consoleText"
    )

    response = requests.get(
        url,
        auth=jenkins_auth,
        timeout=30
    )

    response.raise_for_status()
    return response.text


def diagnose_failure(log):
    log_lower = log.lower()

    diagnosis = "Unknown Jenkins failure"
    severity = "medium"

    steps = []
    commands = []

    if "permission denied" in log_lower:
        diagnosis = "Permission denied during the Jenkins build."
        severity = "high"

        steps = [
            "Check which Linux user Jenkins is running as.",
            "Verify that the Jenkins user has permission to access the required files or resources.",
            "If Docker is being used, verify that the Jenkins user belongs to the docker group.",
            "Restart Jenkins after changing group membership."
        ]

        commands = [
            "id jenkins",
            "groups jenkins",
            "sudo -u jenkins docker ps",
            "sudo systemctl restart jenkins"
        ]

    elif (
        "cannot connect to the docker daemon" in log_lower
        or "docker.sock" in log_lower
        or "docker daemon" in log_lower
    ):
        diagnosis = "Jenkins could not communicate with the Docker daemon."
        severity = "high"

        steps = [
            "Check that Docker is running.",
            "Check whether the Jenkins user can access Docker.",
            "Verify Jenkins has membership in the docker group.",
            "Restart Jenkins if its group membership was recently changed."
        ]

        commands = [
            "systemctl status docker",
            "docker ps",
            "id jenkins",
            "sudo -u jenkins docker ps",
            "sudo systemctl restart jenkins"
        ]

    elif "docker build" in log_lower and (
        "error" in log_lower or "failed" in log_lower
    ):
        diagnosis = "The Docker image build failed."
        severity = "high"

        steps = [
            "Review the Docker build error in the Jenkins console log.",
            "Verify that the Dockerfile exists.",
            "Check the Dockerfile syntax and referenced files.",
            "Run the Docker build manually from the application directory."
        ]

        commands = [
            "ls -la",
            "cat Dockerfile",
            "docker build -t jenkins-demo-app:test ./app"
        ]

    elif (
        "curl:" in log_lower
        or "curl -f" in log_lower
        or "failed to connect" in log_lower
    ):
        diagnosis = "The application health check failed after deployment."
        severity = "high"

        steps = [
            "Check whether the Docker container is running.",
            "Check the container logs.",
            "Verify that the application is listening on port 80.",
            "Verify the Jenkins host port mapping.",
            "Retry the application health check."
        ]

        commands = [
            "docker ps",
            "docker logs jenkins-demo-app",
            "docker inspect jenkins-demo-app",
            "curl -v http://127.0.0.1:8081/"
        ]

    elif "npm" in log_lower and (
        "error" in log_lower or "failed" in log_lower
    ):
        diagnosis = "An npm/Node.js build step failed."
        severity = "medium"

        steps = [
            "Check the npm error reported in the console log.",
            "Verify package.json and package-lock.json.",
            "Install dependencies again.",
            "Retry the build."
        ]

        commands = [
            "node --version",
            "npm --version",
            "npm install",
            "npm test"
        ]

    elif "maven" in log_lower or "mvn" in log_lower:
        diagnosis = "A Maven build step appears to have failed."
        severity = "medium"

        steps = [
            "Review the Maven error in the Jenkins console.",
            "Check pom.xml.",
            "Verify Java and Maven versions.",
            "Retry the Maven build."
        ]

        commands = [
            "java -version",
            "mvn -version",
            "mvn test"
        ]

    elif "test" in log_lower and (
        "failed" in log_lower or "failure" in log_lower
    ):
        diagnosis = "A test stage failed."
        severity = "medium"

        steps = [
            "Identify the failing test in the Jenkins console log.",
            "Run the failing test locally.",
            "Fix the application or test failure.",
            "Commit the fix and rerun the Jenkins pipeline."
        ]

        commands = [
            "git status",
            "git log -1",
            "git diff"
        ]

    else:
        diagnosis = "Jenkins reported a build failure that requires log inspection."
        severity = "medium"

        steps = [
            "Open the Jenkins console log.",
            "Locate the first ERROR or FAILURE message.",
            "Identify the pipeline stage where the failure occurred.",
            "Reproduce the failing command manually.",
            "Apply the required fix and rerun the pipeline."
        ]

        commands = [
            "docker ps",
            "docker logs jenkins-demo-app"
        ]

    return {
        "diagnosis": diagnosis,
        "severity": severity,
        "steps": steps,
        "commands": commands
    }


def send_to_dashboard(data):
    url = f"{DASHBOARD_URL}/api/failures"

    response = requests.post(
        url,
        json=data,
        timeout=15
    )

    response.raise_for_status()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "jenkins-monitor-agent"
    })


@app.route("/jenkins/failure", methods=["POST"])
def jenkins_failure():

    data = request.get_json(silent=True)

    if not data:
        data = request.form.to_dict()

    job_name = data.get("job_name")
    build_number = data.get("build_number")

    if not job_name or not build_number:
        return jsonify({
            "status": "error",
            "message": "job_name and build_number are required"
        }), 400

    try:
        build_info = get_build_info(
            job_name,
            build_number
        )

        console_log = get_console_log(
            job_name,
            build_number
        )

        analysis = diagnose_failure(console_log)

        result = {
            "job_name": job_name,
            "build_number": str(build_number),
            "build_result": build_info.get("result"),
            "build_url": build_info.get("url"),
            "timestamp": build_info.get("timestamp"),
            "duration": build_info.get("duration"),
            "diagnosis": analysis["diagnosis"],
            "severity": analysis["severity"],
            "steps": analysis["steps"],
            "commands": analysis["commands"],
            "log_tail": console_log[-5000:]
        }

        send_to_dashboard(result)

        return jsonify({
            "status": "processed",
            "job_name": job_name,
            "build_number": build_number,
            "diagnosis": analysis["diagnosis"]
        })

    except requests.RequestException as exc:
        return jsonify({
            "status": "error",
            "message": f"Jenkins/Dashboard request failed: {str(exc)}"
        }), 502

    except Exception as exc:
        return jsonify({
            "status": "error",
            "message": str(exc)
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5001
    )
