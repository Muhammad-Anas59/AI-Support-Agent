"""
router.py

Job: Look at an incoming customer message and decide where it should go:
- "order" -> the customer is asking about a specific order's status/tracking
  -> handled by order_lookup.py (live Shopify data)
- "policy" -> a general question about shipping, returns, warranty, etc.
  -> handled by retriever.py (RAG pipeline over policy documents)

This is the piece that makes the system feel like ONE assistant instead of
two separate scripts - the customer just asks a question, and the system
figures out internally which engine should answer it.
"""

import os
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

CHAT_MODEL = "gemini-3.5-flash-lite"


def classify_question(question):
    """Asks Gemini to classify the question as 'order' or 'policy'.
    Kept to a single strict word output so it's cheap and easy to parse."""
    prompt = f"""Classify the customer message below into exactly one word:
"order" - if it's asking about the status, tracking, shipping progress,
  or details of a SPECIFIC order they placed (e.g. "where's my order",
  "has my package shipped", "when will #1001 arrive")
"policy" - if it's a general question about the company's policies,
  rules, or how something works (e.g. "what's your return policy",
  "how long does shipping take", "can I get a refund")

Respond with ONLY the single word "order" or "policy" - nothing else.

Customer message: "{question}"

Classification:"""

    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=prompt
    )
    label = response.text.strip().lower()

    # Safety net: if Gemini returns anything unexpected, default to
    # "policy" - the RAG pipeline safely escalates on no-match anyway,
    # while guessing "order" wrongly would ask for irrelevant details.
    return "order" if "order" in label else "policy"


def extract_order_details(question):
    """Tries to pull an order number and a dollar amount out of the
    message using simple pattern matching. Returns (order_number, total)
    - either can be None if not found, and the caller should ask for
    whichever is missing rather than guessing."""
    order_match = re.search(r"#?\s?(\d{3,6})\b", question)
    total_match = re.search(r"\$?\s?(\d+\.\d{2})\b", question)

    order_number = order_match.group(1) if order_match else None
    total = total_match.group(1) if total_match else None

    return order_number, total


if __name__ == "__main__":
    test_questions = [
        "Where's my order #1001?",
        "What's your return policy?",
        "Has order 1002 shipped yet, it cost me $80.00",
        "How long do refunds take?",
        "Do you sell yoga mats?"
    ]
    for q in test_questions:
        label = classify_question(q)
        order_num, total = extract_order_details(q)
        print(f"'{q}' -> {label} (order_number={order_num}, total={total})")