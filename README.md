# AI Support Agent — Verve Athletics (Demo)

An AI customer support agent that answers strictly from a business's own
policy documents, catches contradictions between those documents before
a customer ever sees them, looks up real order status live, and knows
when to bring in a human instead of guessing.

Built as a demo/portfolio project around a fictional e-commerce brand,
**Verve Athletics**, using a realistic policy set and a live Shopify
development store — not toy data.

## Why this exists

Most "AI support chatbot" demos wrap a generic LLM around a prompt and
call it done — impressive for 30 seconds, forgettable after. This
project is built around a different, harder promise: **the assistant
refuses to answer beyond what it can actually cite**, and shows its
work. Restraint — correctly saying "I don't know, let me get a human" —
is the core feature, not a fallback.

## What it actually does

- **Answers policy questions strictly from real documents** — shipping,
  returns, warranty, cancellations, account/payment — with every answer
  traceable to a specific source document.
- **Catches genuine contradictions between documents.** If one policy
  file says returns are accepted within 30 days and another (e.g. an
  out-of-date website FAQ) says 14 days, the assistant flags the
  conflict and escalates to a human instead of confidently picking one
  or blending both into a confusing answer.
- **Looks up real order status live** via the Shopify Admin API —
  status, fulfillment, tracking — verified against the customer's order
  number and total before revealing anything (never trusts an order
  number alone).
- **Scores its own confidence** on every answer and escalates when it's
  not confident enough, rather than guessing.
- **Detects anger, urgency, and legal/safety language** and escalates
  immediately, regardless of whether a confident answer exists — some
  things shouldn't be fully automated.
- **Logs every interaction**, resolved or escalated, as the data source
  for real analytics — not just anecdotal claims.
- **Gives the business owner an admin console**: an escalation ticket
  queue, a policy document editor, and an analytics dashboard
  (resolution rate, volume by category, estimated time saved).
- **Ships as a customer-facing chat widget** — an embeddable, branded
  widget (no build step, no dependencies) that a real visitor can
  actually talk to, not just a terminal demo.

## Architecture

```
Customer message
      │
      ▼
Sentiment/urgency check  ──── flagged? ──▶ escalate immediately
      │ not flagged
      ▼
   Router (order vs. policy classification)
      │
      ├── "order" ──▶ Shopify order lookup (verified by order # + total)
      │
      └── "policy" ──▶ RAG retrieval (FAISS + Gemini embeddings)
                              │
                              ▼
                    Conflict check across retrieved chunks
                              │
                low confidence / conflict?  ──▶ escalate, log reason
                              │ no
                              ▼
                    Generate grounded answer (cited, conversational)
```

Every escalation and every resolved interaction is logged — powering
the admin console's ticket queue and analytics dashboard.

## Project structure

```
app/
├── core/
│   ├── document_loader.py      # chunks policy .txt files
│   ├── embedder.py              # builds the FAISS index (Gemini embeddings)
│   ├── retriever.py             # RAG pipeline: retrieve, check conflicts, answer
│   ├── conflict_detector.py     # LLM-judged contradiction detection
│   ├── router.py                 # classifies order vs. policy questions
│   ├── order_lookup.py           # live Shopify Admin API order status
│   ├── sentiment_detector.py     # anger/urgency/legal flag detection
│   ├── escalation_logger.py      # tickets: every escalation, with reason
│   ├── interaction_logger.py     # every interaction, resolved or not
│   └── assistant.py              # ties everything together (terminal entry point)
├── api/
│   ├── admin_app.py               # Flask backend for the admin console
│   ├── chat_api.py                # Flask backend for the customer-facing widget
│   └── static/
│       ├── admin.html             # admin console (tickets / policies / analytics)
│       ├── widget.js              # embeddable customer chat widget
│       └── demo_page.html         # sample storefront page to test the widget on
└── data/                          # FAISS index, chunk metadata, logs (generated, gitignored)

demo_data/                         # Verve Athletics policy documents (~20 policies, 7 docs)
```

## Tech stack

- **Python / Flask** — backend, two separate services (admin console on
  port 5000, customer chat API on port 5001)
- **Google Gemini** (`gemini-3.5-flash-lite` for chat/classification,
  `gemini-embedding-001` for embeddings) — chosen over newer preview
  models specifically for a much higher free-tier daily request limit
- **FAISS** — local vector similarity search over policy chunks
- **Shopify Admin API** — live order lookup against a real development
  store
- **Vanilla JS/HTML/CSS** — the admin console and chat widget, no
  frontend framework or build step

## Setup

1. Clone the repo and create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\Activate.ps1   # Windows PowerShell
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root (see `.env.example`):
   ```
   GEMINI_API_KEY=your_key_here
   SHOPIFY_STORE_DOMAIN=your-store.myshopify.com
   SHOPIFY_ACCESS_TOKEN=your_token_here
   ```

3. Build the vector index (run once, and again any time policy
   documents change):
   ```bash
   python app/core/embedder.py
   ```

4. Run the assistant directly in a terminal:
   ```bash
   python app/core/assistant.py
   ```

   Or run the admin console:
   ```bash
   python app/api/admin_app.py
   # open http://localhost:5000
   ```

   Or run the customer-facing chat API + widget demo:
   ```bash
   pip install flask-cors
   python app/api/chat_api.py
   # open app/api/static/demo_page.html in a browser
   ```

## Design notes worth knowing

- **Order verification uses order number + total, not order number +
  email**, in this demo. Shopify blocks API access to customer PII
  (name, email, phone) on free/development store plans — a real client
  on a paid Shopify plan doesn't have this restriction, so this is a
  documented demo-environment workaround, not a product limitation.
- **Conflict detection is deliberately conservative.** It never guesses
  which of two disagreeing sources is "correct" — it flags the
  disagreement and hands both versions to a human. Auto-resolving in
  favor of one document risks confidently telling a customer the wrong
  thing.
- **The admin console's policy editor updates the source `.txt` file**,
  but does not automatically rebuild the FAISS index — `embedder.py`
  must be re-run after any policy edit for the change to take effect in
  live answers. This is intentional and called out in the UI itself.

## Status

Core pipeline (RAG, conflict detection, order lookup, routing,
escalation, analytics, admin console, customer-facing widget) is built
and tested against real conversations. Not yet deployed to a public
host — currently runs locally. See open items below.

## Known open items
- Automated evaluation harness (`app/tests/evaluation_harness.py`) shows 98.2% accuracy (56/57 test cases passing) across policy Q&A, conflict detection, routing, sentiment, and order lookup — evaluated against the real live pipeline, not mocked.
- Customer-facing chat widget is newly built and not yet fully
  end-to-end verified in a live browser session.
- Public deployment (AWS) not yet started.
- A small number of very specific policy phrasings can still miss
  retrieval and escalate unnecessarily rather than finding a correct
  answer that exists in the documents — mitigated by re-chunking source
  documents when this is found, not by lowering the confidence
  threshold.
