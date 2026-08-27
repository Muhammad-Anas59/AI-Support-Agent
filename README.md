# AI Support Agent

An AI customer support agent for e-commerce brands. It answers from a
business's real policy documents, catches contradictions between those
documents before a customer ever sees them, looks up real order status
from a live Shopify/WooCommerce store, and knows when to escalate to a
human instead of guessing.

Built for any Shopify or e-commerce store — the policy documents, order
lookup credentials, and branding are all swappable per business. This
repository includes one fully worked example so the system can be run
and tested end-to-end out of the box: a fictional activewear brand,
**Verve Athletics**, with its own policy set and a live demo Shopify
store connected. Point it at a different store's policies and Shopify
credentials, and it works the same way for them.

## Screenshots

**Conflict detection catching a real contradiction, live in the chat widget:**
![Conflict detection in the widget](Project-Images/widget_conflict_detected.png)

**Answering a policy question with a live order lookup:**
![Policy answer](Project-Images/widget_policy_answer.png)

**Order lookup:**
![Order lookup](Project-Images/widget_order_lookup.png)

**Admin analytics dashboard:**
![Admin analytics](Project-Images/admin_analytics.png)

**Performance tab:**
![Performance tab](Project-Images/performance_result.png)

**Escalation ticket queue:**
![Escalation tickets](Project-Images/admin_tickets.png)

**Automated evaluation harness results:**
![Evaluation summary](Project-Images/evaluation_summary.png)

## Why this isn't a generic chatbot wrapper

Most "AI support bot" demos are a single LLM call over a prompt. This
project is built around five things that specifically aren't that:

1. **Retrieval-grounded, refuses to guess.** Every answer is generated
   only from retrieved policy text. If the retrieved text doesn't
   actually answer the question, the assistant says so and escalates —
   it never fills the gap with outside knowledge.
2. **Conflict detection.** When a business's own documents disagree with
   each other (e.g. an official policy says one thing, an outdated FAQ
   page says another), the system catches it and escalates instead of
   blending both into one confusing, wrong-sounding answer.
3. **Real order lookup.** Order status/tracking questions are answered
   from a live Shopify Admin API call, not static text.
4. **Sentiment/urgency escalation.** Angry, urgent, or legal-sounding
   messages are escalated immediately, regardless of whether a confident
   automated answer exists — some things shouldn't be fully automated.
5. **Full citation trail + confidence scoring.** Every policy answer
   shows which document it came from and how confident the retrieval
   was — no black box.

## Architecture

```
Customer message
      │
      ▼
sentiment_detector.py  ──flagged──► escalate to human
      │ not flagged
      ▼
   router.py  ── classifies: "order" or "policy"
      │                              │
      ▼                              ▼
order_lookup.py                retriever.py + conflict_detector.py
(live Shopify data)             (RAG over policy documents)
      │                              │
      └──────────► assistant.py ◄────┘
                  (ties it together,
                   logs everything)
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
      escalation_logger.py   interaction_logger.py
      (tickets for humans)   (analytics data)
```

Two ways to talk to the assistant:
- **`assistant.py`** — terminal chat loop, for local testing
- **`chat_api.py` + `widget.js`** — Flask API + an embeddable web chat
  widget, for anything customer-facing

One way to manage the business:
- **`admin_app.py` + `admin.html`** — view escalated tickets, edit policy
  documents, view analytics (resolution rate, volume, categories, time
  saved)

## Project structure

```
app/
  core/
    document_loader.py    # loads + chunks policy .txt files
    embedder.py            # embeds chunks, builds the FAISS index
    retriever.py            # RAG pipeline: retrieve + generate answer
    conflict_detector.py    # checks retrieved chunks for contradictions
    order_lookup.py         # Shopify Admin API order status lookup
    router.py               # classifies order vs. policy questions
    sentiment_detector.py   # flags anger/urgency/legal language
    escalation_logger.py    # logs escalations as tickets
    interaction_logger.py   # logs every interaction for analytics
    assistant.py            # main entry point, ties everything together
  api/
    admin_app.py            # Flask backend for the admin dashboard
    chat_api.py              # Flask backend for the customer chat widget
    static/
      admin.html
      widget.js
      demo_page.html         # test page with the widget embedded
  data/
    policy_index.faiss       # generated - not committed
    chunks_metadata.json     # generated - not committed
    escalation_tickets.jsonl # generated - not committed
    interactions.jsonl       # generated - not committed
  tests/
    eval_cases.json          # 57 labeled test cases across all subsystems
    evaluation_harness.py    # runs every case against the real live pipeline
    evaluation_report.md     # generated - latest scored results
demo_data/                    # example policy set - swap for any client's own docs
  00_brand_info.txt
  01_shipping_policy.txt
  02_returns_policy.txt
  03_website_faq.txt          # deliberately drifted, contains planted conflicts
  04_warranty_policy.txt
  05_cancellation_policy.txt
  06_account_payment_policy.txt
  _conflict_manifest.md       # documents the planted conflicts, for testing
.env.example
requirements.txt
Project-Images/                 # screenshots used in this README
```

## Setup

**1. Install dependencies**
```bash
pip install -r requirements.txt
pip install flask-cors
```

**2. Configure environment variables**

Copy `.env.example` to `.env` and fill in:
```
GEMINI_API_KEY=your_gemini_api_key
SHOPIFY_STORE_DOMAIN=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_your_admin_api_token
```

**3. Build the retrieval index**
```bash
python app/core/embedder.py
```
This reads `demo_data/`, chunks it, embeds every chunk, and saves the
FAISS index + metadata to `app/data/`. Re-run this any time a policy
document changes.

## Running it

**Terminal chat (fastest way to test):**
```bash
python app/core/assistant.py
```

**Customer-facing web chat widget:**
```bash
python app/api/chat_api.py
```
Then open `app/api/static/demo_page.html` directly in a browser.

**Admin dashboard:**
```bash
python app/api/admin_app.py
```
Then visit `http://localhost:5000`.

**Run the evaluation suite:**
```bash
python app/tests/evaluation_harness.py
```
Runs 57 labeled test cases against the real, live pipeline — not
mocked — covering policy Q&A, conflict detection, out-of-scope
handling, order-vs-policy routing, sentiment detection, and order
lookup. Produces a scored report at `app/tests/evaluation_report.md`.

## Accuracy

**56/57 test cases passing (98.2%)** across all subsystems, evaluated
against the real live pipeline:

| Category | Result |
|---|---|
| Policy Q&A | 24/24 |
| Conflict detection | 6/6 |
| Router (order vs. policy classification) | 10/10 |
| Sentiment/urgency detection | 10/11 | later changes to 11/11
| Order lookup | 6/6 |


## Known limitations (honest, on purpose)

- **Order verification uses order number + total, not order number +
  email.** Shopify blocks API access to customer PII (name, email,
  phone, address) unless the store is on a paid plan — the demo store
  used here is free-tier. This is a demo-environment limitation, not a
  product one: a real client's store is on a paid plan by definition, so
  proper email verification works out of the box with zero code changes
  once deployed against a real client's store. See the docstring in
  `order_lookup.py` for details.
- **Email intake isn't built.** Only the web chat widget exists as a
  customer-facing channel right now. Email intake needs a paid mail-
  sending service and hasn't been prioritized before a real client
  needs it.
- **Escalation tickets log the triggering message, not full conversation
  history.** A human resolving a ticket sees what caused the escalation,
  but not the full back-and-forth that led up to it.

## Status

Core pipeline (retrieval, conflict detection, order lookup, routing,
sentiment escalation, admin dashboard, analytics, customer chat widget)
is built and tested against a manifest of planted policy conflicts, a
broad sweep of general questions, and a 57-case automated evaluation
suite, using the included Verve Athletics example dataset and demo
Shopify store. Not yet deployed publicly — running locally only as of
this writing. Adapting this to a new business means swapping the
contents of `demo_data/`, re-running `embedder.py`, and connecting that
business's own Shopify credentials in `.env` — no code changes required.
