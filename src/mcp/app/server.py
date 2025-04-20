import os
from flask import Flask, jsonify, request, send_from_directory
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

app = Flask(__name__)
application = FastAPI()
mcp = FastMCP()

STATIC_FOLDER = os.path.join(os.path.dirname(__file__), '../static')


# Register tools after MCP is initialized to avoid circular imports
def register_tools():
    from app.tools.get_signal_data import get_signal_data  # noqa: F401
    from app.tools.get_worker_metadata import get_worker_metadata  # noqa: F401


def start_flask():
    register_tools()

    if app.config.get('USE_NGROK', False):  # the passed boolean in app context.
        print("ngrok is enabled")
    else:
        print("Running without ngrok")

    if app.config.get('USE_OPENAI', False):  # the passed boolean in app context.
        print("openai is enabled")
    else:
        print("Running without openai")

    app.run(host="0.0.0.0", port=8000, debug=True)


# @app.route('/')
# def home():
#     return 'Welcome to the MCP API!'
@app.route('/favicon.ico')
def favicon():
    return '', 204  # Empty response for favicon


# Optional: redirect root to UI
@app.route('/')
def home():
    return send_from_directory(STATIC_FOLDER, 'index.html')


@app.route("/.well-known/mcp/tools.json")
def tools_json():
    return jsonify(mcp.list_tools())


# curl -X POST http://127.0.0.1:8000/mcp/get_signal_data -H "Content-Type: application/json" -d '{"worker_id": "12345"}'
@app.route("/mcp/<tool_name>", methods=["POST"])
def invoke_tool(tool_name):
    payload = request.get_json() or {}
    try:
        import asyncio
        # result = mcp.call_tool(tool_name, payload)
        result = asyncio.run(mcp.call_tool(tool_name, payload))  # <-- Await coroutine

        return jsonify(result[0].text)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/ui/<path:filename>')
def serve_ui(filename):
    return send_from_directory(STATIC_FOLDER, filename)


@app.route('/ui/')
def serve_ui_index():
    return send_from_directory(STATIC_FOLDER, 'index.html')
