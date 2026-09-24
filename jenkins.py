import os
import requests
from dotenv import load_dotenv

load_dotenv()

JENKINS_URL = os.getenv("JENKINS_URL").rstrip("/")
JENKINS_USER = os.getenv("JENKINS_USER")
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN")

AUTH = (JENKINS_USER, JENKINS_TOKEN)


def get_build_info(job_name, build_number):
    """
    Get Jenkins build information.
    """

    url = (
        f"{JENKINS_URL}/job/"
        f"{job_name.replace('/', '/job/')}/"
        f"{build_number}/api/json"
    )

    response = requests.get(
        url,
        auth=AUTH,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def get_console_log(job_name, build_number):
    """
    Get Jenkins console output.
    """

    url = (
        f"{JENKINS_URL}/job/"
        f"{job_name.replace('/', '/job/')}/"
        f"{build_number}/consoleText"
    )

    response = requests.get(
        url,
        auth=AUTH,
        timeout=60
    )

    response.raise_for_status()

    return response.text


def get_last_build(job_name):
    """
    Get latest build.
    """

    url = (
        f"{JENKINS_URL}/job/"
        f"{job_name.replace('/', '/job/')}/api/json"
        "?tree=lastBuild[number,result,url]"
    )

    response = requests.get(
        url,
        auth=AUTH,
        timeout=30
    )

    response.raise_for_status()

    return response.json()
