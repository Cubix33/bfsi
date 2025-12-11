import os
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

from main import MasterAgent  # uses your sales.py, risk.py, etc.

# ---------- CONFIG ----------

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY missing in .env")

# path to the built React app
# adjust if needed, e.g. "../frontend/dist"
FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")

app = Flask(
    __name__,
    static_folder=FRONTEND_BUILD_DIR,
    static_url_path="/"
)

# ---------- CHATBOT SESSION LAYER ----------

sessions: dict[str, dict] = {}
SESSION_TIMEOUT = timedelta(minutes=30)


def clean_expired_sessions():
    now = datetime.now()
    expired = [
        sid for sid, data in sessions.items()
        if now - data["last_activity"] > SESSION_TIMEOUT
    ]
    for sid in expired:
        del sessions[sid]


def get_or_create_session(session_id: str) -> MasterAgent:
    clean_expired_sessions()
    if session_id in sessions:
        sessions[session_id]["last_activity"] = datetime.now()
        return sessions[session_id]["agent"]

    agent = MasterAgent(GROQ_API_KEY)
    sessions[session_id] = {"agent": agent, "last_activity": datetime.now()}
    # send initial greeting from backend
    agent.start_conversation()
    return agent

from user_store import get_applications

@app.get("/api/profile")
def profile():
    # simple auth: frontend passes user_id as query or header
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    apps = get_applications(user_id)
    return jsonify({
        "user_id": user_id,
        "applications": apps,
    })
    
from flask import send_from_directory

SANCTION_DIR = os.path.join(os.path.dirname(__file__), "sanction_letters")

@app.route("/sanction_letters/<path:filename>")
def download_sanction_letter(filename):
    return send_from_directory(SANCTION_DIR, filename, as_attachment=True)

@app.post("/api/chat")
def chat():
    data = request.get_json(force=True)
    session_id = data.get("session_id")
    message = data.get("message", "").strip()
    language = data.get("language", "en")

    if not session_id:
        return jsonify({"error": "session_id required"}), 400

    text = message.lower()

    # ---------- NEW: restart handling ----------
    if text in ["restart", "**restart**", "start new", "new loan"]:
        # drop old session (if any)
        if session_id in sessions:
            del sessions[session_id]

        # create a fresh agent
        agent = get_or_create_session(session_id)

        reply = (
            "Starting a fresh loan application. 👋\n\n"
            "Please share your registered phone number to begin."
        )

        # reset state + history for safety
        agent.conversation_history = [{"role": "assistant", "content": reply}]
        agent.state["stage"] = "initial"
        agent.state["final_decision"] = None

        return jsonify({
            "reply": reply,
            "stage": "initial",
            "final_decision": None,
        })
    # ---------- END NEW BLOCK ----------

        # Handle initial greeting request
    if message == "__INIT__":
        agent = get_or_create_session(session_id)
        agent.user_language = language  # ADD THIS
        agent.sales_agent.set_language(language)
        greeting = agent.sales_agent.get_initial_greeting()
        agent.conversation_history = [{"role": "assistant", "content": greeting}]
        return jsonify({
        "reply": greeting,
        "stage": "initial",
        "final_decision": None,
    })

    if not message:
        return jsonify({"error": "message required"}), 400

    agent = get_or_create_session(session_id)
    agent.user_language = language  # ADD THIS
    agent.sales_agent.set_language(language)
    reply = agent.process_message(message)


    return jsonify({
        "reply": reply,
        "stage": agent.state["stage"],
        "final_decision": agent.state.get("final_decision"),
    })


@app.get("/api/status")
def status():
    return {
        "status": "ok",
        "active_sessions": len(sessions),
    }

# ---------- SERVE FRONTEND ----------

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path: str):
    # If file exists in dist/, serve it; otherwise, return index.html (for React Router)
    if path and os.path.exists(os.path.join(FRONTEND_BUILD_DIR, path)):
        return send_from_directory(FRONTEND_BUILD_DIR, path)
    return send_from_directory(FRONTEND_BUILD_DIR, "index.html")


if __name__ == "__main__":
    print(f"Serving frontend from: {FRONTEND_BUILD_DIR}")
    app.run(host="0.0.0.0", port=8000, debug=True)
