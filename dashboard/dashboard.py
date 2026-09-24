from flask import Flask, request, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)

failures = []


HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Jenkins AI Monitor</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            background: #f5f5f5;
        }

        .failure {
            background: white;
            padding: 25px;
            margin-bottom: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .error {
            color: #b00020;
        }

        pre {
            background: #222;
            color: #eee;
            padding: 15px;
            overflow-x: auto;
        }

        code {
            background: #eee;
            padding: 3px;
        }
    </style>
</head>

<body>

<h1>Jenkins Failure Monitor</h1>

{% if not failures %}

<p>No Jenkins failures detected.</p>

{% endif %}

{% for item in failures %}

<div class="failure">

    <h2>
        {{ item.job }}
        #{{ item.build }}
    </h2>

    <p>
        <strong>Status:</strong>
        <span class="error">
            {{ item.result }}
        </span>
    </p>

    <p>
        <strong>Jenkins:</strong>
        <a href="{{ item.build_url }}" target="_blank">
            Open build
        </a>
    </p>

    <h3>Diagnosis</h3>

    <p>
        <strong>Category:</strong>
        {{ item.diagnosis.category }}
    </p>

    <p>
        <strong>Probable cause:</strong>
        {{ item.diagnosis.cause }}
    </p>

    <h3>Step-by-step remediation</h3>

    <ol>
    {% for step in item.diagnosis.steps %}
        <li>{{ step }}</li>
    {% endfor %}
    </ol>

    <h3>Suggested commands</h3>

    {% for command in item.diagnosis.commands %}

        <pre>{{ command }}</pre>

    {% endfor %}

    <h3>Recent Jenkins log</h3>

    <pre>{{ item.log_tail }}</pre>

</div>

{% endfor %}

</body>
</html>
"""


@app.post("/api/failures")
def add_failure():

    data = request.get_json()

    data["detected_at"] = datetime.utcnow().isoformat()

    failures.insert(0, data)

    # Keep latest 50 failures
    del failures[50:]

    return jsonify({
        "status": "stored"
    })


@app.get("/api/failures")
def get_failures():

    return jsonify(failures)


@app.get("/")
def index():

    return render_template_string(
        HTML,
        failures=failures
    )


@app.get("/health")
def health():

    return jsonify({
        "status": "ok"
    })


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )
