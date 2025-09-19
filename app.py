from flask import Flask, request, jsonify
import uuid
import subprocess
app = Flask(__name__)

@app.route("/")
def hello_world():
    return "Hello, World!"

@app.route("/execute", methods=["POST"])
def execute_python():
    user_code = request.json.get("script")
    if not user_code:
        return jsonify({"error": "No code provided"}), 400

    # Execute in nsjail using config
    cmd = ["nsjail", "--config", "/etc/nsjail.cfg", "--", "python3", "-c", user_code]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        return jsonify({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Execution timed out"}), 504


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
