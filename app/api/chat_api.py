"""
chat_api.py

Job: Expose assistant.py over HTTP so a website chat widget (or any other
client) can talk to it. This is what turns the assistant from a
terminal-only script into an actual product a browser can use - it's a
prerequisite for deployment, not just for the widget.

Session handling: Flask itself is stateless between requests, but
assistant.get_response() needs a persistent conversation_state dict
across a multi-turn conversation (e.g. collecting an order number, then
a total). Fix: the frontend generates a session_id once per visit and
sends it with every message; this file keeps an in-memory dict mapping
session_id -> conversation_state. Fine for a demo (single server
process) - a real production version would move this to Redis or a
database so state survives a server restart or multiple server
instances, but that's not a concern at this stage.
"""

import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from flask import Flask, request, jsonify
from flask_cors import CORS

from assistant import get_response
from retriever import load_index

app = Flask(__name__)
CORS(app)  # allow the widget to call this API from any page/origin during demo/dev

print("Loading RAG index...")
index, chunks = load_index()
print(f"Loaded {len(chunks)} chunks. Chat API ready.")

# In-memory session store: session_id -> conversation_state dict.
# Lost on server restart - acceptable for a demo, not for production.
sessions = {}


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Main chat endpoint. Expects JSON: {"message": "...", "session_id": "..."}.
    session_id is optional on the very first message - if missing, a new
    one is generated and returned so the client can reuse it for the
    rest of the conversation."""
    data = request.get_json(force=True) or {}
    message = (data.get("message") or "").strip()
    session_id = data.get("session_id") or str(uuid.uuid4())

    if not message:
        return jsonify({"error": "Message is required"}), 400

    conversation_state = sessions.setdefault(session_id, {})

    try:
        result = get_response(message, conversation_state, index, chunks)
    except Exception as e:
        # Never let an internal error leak to the customer as a raw
        # stack trace - always return a normal, friendly message, and
        # keep the real error server-side for debugging.
        print(f"[chat_api] Error handling message: {e}")
        return jsonify({
            "session_id": session_id,
            "answer": "I'm having trouble processing that right now - I'm flagging this for a team member to follow up with you directly.",
            "escalated": True
        }), 200

    return jsonify({
        "session_id": session_id,
        "answer": result["answer"],
        "escalated": result.get("escalated", False)
    })


@app.route("/api/health")
def api_health():
    """Simple check to confirm the server is up and the index loaded -
    useful once this is deployed, to verify it's actually running."""
    return jsonify({"status": "ok", "chunks_loaded": len(chunks)})


if __name__ == "__main__":
    # Different port from admin_app.py (5000) so both can run at once
    app.run(host="0.0.0.0", debug=True, port=5001)
