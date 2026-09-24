import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5.4-mini"
)

SYSTEM_PROMPT = """
You are an expert AWS DevOps and SRE troubleshooting engineer.

You analyze Jenkins CI/CD pipeline failures and provide practical,
step-by-step troubleshooting instructions.

The application may use:

- Git
- GitHub
- Jenkins
- Docker
- Docker Compose
- Docker Hub
- AWS ECR
- AWS EC2
- AWS EKS
- Kubernetes
- Helm
- Terraform
- Ansible
- Trivy
- SonarQube
- Linux
- Nginx
- AWS IAM

For Docker-related failures, specifically investigate:

- Dockerfile syntax errors
- Docker build failures
- Missing files
- Wrong COPY paths
- Wrong WORKDIR
- Missing dependencies
- Docker image naming/tagging problems
- Docker daemon problems
- Docker permission problems
- Container startup failures
- Container immediately exiting
- Port conflicts
- Incorrect EXPOSE configuration
- Incorrect application binding
- Environment variables
- Docker networking
- Docker Compose problems
- Docker login failures
- Docker registry failures
- AWS ECR authentication
- ECR push/pull failures
- Image architecture problems
- Container health-check failures

Always provide:

1. FAILURE SUMMARY
2. FAILED STAGE
3. IMPORTANT ERROR
4. LIKELY ROOT CAUSE
5. STEP-BY-STEP FIX
6. COMMANDS TO RUN
7. CONFIGURATION CHANGES
8. VERIFICATION
9. PREVENTION

Important rules:

- Do not invent information.
- Use the Jenkins log as the primary evidence.
- Clearly distinguish confirmed errors from likely causes.
- If the exact root cause cannot be determined, say:

"Root cause cannot be confirmed from the available log."

- Give commands that are appropriate for the technology involved.
- Prefer practical commands that a DevOps engineer can execute.
"""


def analyze_failure(job_name, build_number, console_log):

    # --------------------------------------------------
    # Limit log size
    # --------------------------------------------------

    max_log_size = 30000

    if len(console_log) > max_log_size:

        console_log = console_log[-max_log_size:]


    # --------------------------------------------------
    # AI Prompt
    # --------------------------------------------------

    prompt = f"""
Jenkins Job:
{job_name}

Build Number:
{build_number}

Jenkins Console Log:

---------------- LOG START ----------------

{console_log}

---------------- LOG END ----------------

Analyze this Jenkins failure.

Identify:

FAILURE SUMMARY

FAILED STAGE

IMPORTANT ERROR

LIKELY ROOT CAUSE

STEP-BY-STEP FIX

COMMANDS

CONFIGURATION CHANGES

VERIFICATION

PREVENTION

If Docker is involved, explain the Docker-specific problem
and provide the exact Docker/Linux commands that should be
checked.

If AWS ECR is involved, also explain the AWS/ECR-specific
problem and commands to verify it.

Do not assume information that is not present in the log.
"""


    # --------------------------------------------------
    # OpenAI Request
    # --------------------------------------------------

    response = client.chat.completions.create(

        model=MODEL,

        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.1
    )


    # --------------------------------------------------
    # Return AI Analysis
    # --------------------------------------------------

    return response.choices[0].message.content
