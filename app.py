from flask import Flask, request, jsonify
import subprocess
import re
import json

app = Flask(__name__)

@app.route("/execute", methods=["POST"])
def execute_python():
    """
    Execute user-provided Python code in a secure nsjail environment.
    :return: JSON response with execution result or error message.
    """

    # Get user code from request
    user_code = request.json.get("script")
    if not user_code:
        return jsonify({"error": "No code provided"}), 400

    # Create wrapper code that will run inside nsjail
    execution_wrapper = f"""
import json
import sys

# User's code
{user_code}

# Execution and validation logic
try:
    # Check if main function exists and is callable
    if 'main' not in globals() or not callable(globals().get('main')):
        print("ERROR: main() function is not defined or not callable", file=sys.stderr)
        sys.exit(1)

    # Call main function
    result = main()

    # Validate that the result can be serialized as JSON
    try:
        json_output = json.dumps(result, ensure_ascii=False)
        print("JSON_RESULT:" + json_output)
    except (TypeError, ValueError) as json_error:
        print(f"ERROR: main() function did not return JSON-serializable data: {{json_error}}", file=sys.stderr)
        sys.exit(1)

except NameError:
    print("ERROR: main() function is not defined", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Error executing main() function: {{e}}", file=sys.stderr)
    sys.exit(1)

    """

    # Execute in nsjail using config
    cmd = ["nsjail", "--config", "/etc/nsjail.cfg", "--", "python3"]

    try:
        result = subprocess.run(cmd, input=execution_wrapper, capture_output=True, text=True, timeout=10)

        # Parse the results from nsjail execution
        if result.returncode != 0:
            # Extract error message from stderr
            error_lines = result.stderr.strip().split('\n')
            error_messages = []

            for line in error_lines:
                if line.startswith("ERROR:"):
                    error_messages.append(line[6:].strip())  # Remove "ERROR:" prefix

            if error_messages:
                combined_error = "; ".join(error_messages)
                return jsonify({"error": combined_error}), 400
            else:
                return jsonify({
                    "error": "Code execution failed",
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }), 400

        # Extract JSON result from stdout
        stdout_lines = result.stdout.strip().split('\n')
        json_result = None
        other_output = []

        for line in stdout_lines:
            if line.startswith("JSON_RESULT:"):
                json_result_str = line[12:]  # Remove "JSON_RESULT:" prefix
                try:
                    json_result = json.loads(json_result_str)
                except json.JSONDecodeError:
                    return jsonify({"error": "Invalid JSON format in main() return value"}), 400
            else:
                other_output.append(line)

        if json_result is not None:
            return jsonify({
                "result": json_result,
                "stdout": '\n'.join(other_output) if other_output else ""
            })
        else:
            return jsonify({"error": "main() function did not return JSON data"}), 400

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Execution timed out"}), 504


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
