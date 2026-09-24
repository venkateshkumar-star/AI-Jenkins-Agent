import os
import json
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from jenkins import get_build_info, get_console_log
from ai_analyzer import analyze_failure


# ---------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------

app = FastAPI(
    title="Jenkins AI Troubleshooting Agent"
)


# ---------------------------------------------------------
# Jinja2 Templates
# ---------------------------------------------------------

templates = Jinja2Templates(
    directory="/root/jenkins-ai-agent/templates"
)


# ---------------------------------------------------------
# Latest Failure Storage
# ---------------------------------------------------------

LATEST_FAILURE = {
    "status": "Waiting",
    "job": "",
    "build": "",
    "error": "",
    "analysis": "",
    "time": ""
}


# ---------------------------------------------------------
# Save Failure Information
# ---------------------------------------------------------

def save_failure(data):

    os.makedirs(
        "/root/jenkins-ai-agent/logs",
        exist_ok=True
    )

    with open(
        "/root/jenkins-ai-agent/logs/latest_failure.json",
        "w"
    ) as file:

        json.dump(
            data,
            file,
            indent=4
        )


# ---------------------------------------------------------
# Dashboard
# ---------------------------------------------------------

@app.get(
    "/",
    response_class=HTMLResponse
)
async def dashboard(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "failure": LATEST_FAILURE
        }
    )


# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------

@app.get("/health")
async def health():

    return {
        "status": "UP",
        "service": "Jenkins AI Troubleshooting Agent"
    }


# ---------------------------------------------------------
# Jenkins Webhook
# ---------------------------------------------------------

@app.post("/webhook")
async def webhook(request: Request):

    global LATEST_FAILURE

    # ---------------------------------------------
    # Read JSON payload
    # ---------------------------------------------

    try:

        payload = await request.json()

    except Exception:

        return JSONResponse(
            {
                "status": "error",
                "message": "Invalid JSON"
            },
            status_code=400
        )


    print("\n====================================")
    print("JENKINS WEBHOOK RECEIVED")
    print("====================================")

    print(payload)


    # ---------------------------------------------
    # Get Job Name
    # ---------------------------------------------

    job_name = (
        payload.get("job_name")
        or payload.get("name")
    )


    if not job_name:

        job_data = payload.get(
            "job",
            {}
        )

        if isinstance(job_data, dict):

            job_name = job_data.get(
                "name"
            )


    if not job_name:

        project_data = payload.get(
            "project",
            {}
        )

        if isinstance(project_data, dict):

            job_name = project_data.get(
                "name"
            )


    # ---------------------------------------------
    # Get Build Number
    # ---------------------------------------------

    build_number = (
        payload.get("build_number")
    )


    if not build_number:

        build_data = payload.get(
            "build",
            {}
        )

        if isinstance(build_data, dict):

            build_number = build_data.get(
                "number"
            )


    # ---------------------------------------------
    # Validate Job + Build
    # ---------------------------------------------

    if not job_name or not build_number:

        return JSONResponse(
            {
                "status": "error",
                "message": "job_name or build_number missing",
                "received": payload
            },
            status_code=400
        )


    # ---------------------------------------------
    # Get Jenkins Build
    # ---------------------------------------------

    try:

        build_info = get_build_info(
            job_name,
            build_number
        )

        result = build_info.get(
            "result"
        )


        print(
            f"Job     : {job_name}"
        )

        print(
            f"Build   : {build_number}"
        )

        print(
            f"Result  : {result}"
        )


        # -----------------------------------------
        # Ignore successful builds
        # -----------------------------------------

        if result != "FAILURE":

            return {
                "status": "ignored",
                "result": result
            }


        # -----------------------------------------
        # Get Jenkins Console Log
        # -----------------------------------------

        console_log = get_console_log(
            job_name,
            build_number
        )


        # -----------------------------------------
        # Send Log to AI
        # -----------------------------------------

        print(
            "Sending Jenkins failure log to AI..."
        )


        analysis = analyze_failure(
            job_name,
            build_number,
            console_log
        )


        # -----------------------------------------
        # Store Result
        # -----------------------------------------

        error_data = {

            "status": "FAILED",

            "job": job_name,

            "build": build_number,

            "error": console_log[-5000:],

            "analysis": analysis,

            "time": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        }


        LATEST_FAILURE = error_data


        save_failure(
            error_data
        )


        print(
            "AI analysis completed."
        )


        return {

            "status": "analyzed",

            "job": job_name,

            "build": build_number
        }


    except Exception as error:

        print(
            "ERROR:",
            str(error)
        )


        return JSONResponse(
            {
                "status": "error",
                "message": str(error)
            },
            status_code=500
        )


# ---------------------------------------------------------
# Manual Jenkins Build Analysis
# ---------------------------------------------------------

@app.post(
    "/analyze/{job_name}/{build_number}"
)
async def manual_analyze(
    job_name: str,
    build_number: int
):

    global LATEST_FAILURE


    try:

        print("\n====================================")
        print("MANUAL JENKINS ANALYSIS")
        print("====================================")

        print(
            f"Job     : {job_name}"
        )

        print(
            f"Build   : {build_number}"
        )


        # -----------------------------------------
        # Get Jenkins Build Information
        # -----------------------------------------

        build_info = get_build_info(
            job_name,
            build_number
        )


        # -----------------------------------------
        # Get Console Log
        # -----------------------------------------

        console_log = get_console_log(
            job_name,
            build_number
        )


        # -----------------------------------------
        # AI Analysis
        # -----------------------------------------

        print(
            "Sending log to AI..."
        )


        analysis = analyze_failure(
            job_name,
            build_number,
            console_log
        )


        # -----------------------------------------
        # Store Result
        # -----------------------------------------

        LATEST_FAILURE = {

            "status": build_info.get(
                "result",
                "UNKNOWN"
            ),

            "job": job_name,

            "build": build_number,

            "error": console_log[-5000:],

            "analysis": analysis,

            "time": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        }


        save_failure(
            LATEST_FAILURE
        )


        print(
            "Analysis completed successfully."
        )


        return LATEST_FAILURE


    except Exception as error:

        print(
            "MANUAL ANALYSIS ERROR:",
            str(error)
        )


        return JSONResponse(
            {
                "status": "error",
                "message": str(error)
            },
            status_code=500
        )


# ---------------------------------------------------------
# Application Startup
# ---------------------------------------------------------

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
