"""
admin_app.py

Job: A small Flask backend serving two things to the admin interface:
1. Escalated tickets (from escalation_logger.py) - so a human can see
   what needs attention and why.
2. Policy documents (from demo_data/) - so a business owner can view,
   add, or edit their own policies without touching code.

This is intentionally simple (file-based, no database) since it matches
the project's current scale - swapping to a real database later is a
contained change, not a rewrite.
"""

import os
import sys
from flask import Flask, jsonify, request, send_from_directory

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from escalation_logger import get_all_tickets, get_ticket_summary
from interaction_logger import get_analytics_summary

app = Flask(__name__, static_folder="static", static_url_path="")

POLICY_FOLDER = os.path.join(os.path.dirname(__file__), "..", "..", "demo_data")


@app.route("/")
def serve_admin_page():
    return send_from_directory(app.static_folder, "admin.html")


@app.route("/api/tickets")
def api_tickets():
    """Returns all escalated tickets, newest first."""
    tickets = get_all_tickets()
    tickets.sort(key=lambda t: t["timestamp"], reverse=True)
    return jsonify(tickets)


@app.route("/api/summary")
def api_summary():
    """Returns ticket counts by category, for the top-of-page stats."""
    return jsonify(get_ticket_summary())


@app.route("/api/analytics")
def api_analytics():
    """Returns the full analytics summary: total volume, resolution
    rate, breakdown by handler and escalation category, average
    confidence, and estimated time saved. Powers the Analytics tab."""
    return jsonify(get_analytics_summary())


@app.route("/api/policies")
def api_policies():
    """Returns every policy document's filename and content."""
    policies = []
    for filename in sorted(os.listdir(POLICY_FOLDER)):
        if filename.endswith(".txt"):
            filepath = os.path.join(POLICY_FOLDER, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            policies.append({"filename": filename, "content": content})
    return jsonify(policies)


@app.route("/api/policies/<filename>", methods=["PUT"])
def api_update_policy(filename):
    """Overwrites one policy document's content with what the admin
    submitted. NOTE: the FAISS index needs to be rebuilt (re-run
    embedder.py) after any policy edit for changes to take effect in
    the actual assistant - this endpoint just updates the source file."""
    if not filename.endswith(".txt") or "/" in filename or "\\" in filename:
        return jsonify({"error": "Invalid filename"}), 400

    filepath = os.path.join(POLICY_FOLDER, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    new_content = request.json.get("content", "")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    return jsonify({"success": True, "note": "Re-run embedder.py to apply this change to live answers."})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
