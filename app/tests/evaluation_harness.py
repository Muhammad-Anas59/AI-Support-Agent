"""
evaluation_harness.py

Job: Automated accuracy evaluation for the whole assistant, not just the
RAG pipeline. Loads a labeled test set (eval_cases.json) covering all six
subsystems - policy Q&A, conflict detection, out-of-scope handling,
router classification, sentiment detection, and order lookup - runs each
case against the REAL live pipeline (not mocked), grades it automatically
against its expected outcome, and produces a scored report.

This exists so accuracy numbers are measured, not guessed - the same
reason an evaluation harness is worth having on any RAG/ML system.

Grading approach per category:
- policy_qa / conflict_detection: runs the full assistant.get_response()
  pipeline (sentiment check -> router -> retriever/conflict detector ->
  answer generation), same as a real customer would experience. Checks
  the escalated flag matches expectation, and that the answer contains
  at least one of a list of acceptable substrings - not an exact string
  match, since LLM phrasing varies run to run, but specific facts (like
  "5-7" business days) and assistant.py's own fixed escalation wording
  are stable enough to check for reliably.
- router: tests classify_question() directly (unit-level), independent
  of the rest of the pipeline.
- sentiment: tests check_sentiment() directly (unit-level).
- order_lookup: tests find_order() directly against the real Shopify
  API (unit-level), independent of the conversational multi-turn flow.

Cost note: policy_qa/conflict_detection cases each trigger multiple real
Gemini API calls (sentiment + router + conflict-check + answer
generation). Running the full 30-case suite makes roughly 70-80 API
calls total. With billing enabled this costs a few cents - budget for
that before running the full suite.
"""

import sys
import os
import json
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from assistant import get_response
from retriever import load_index
from router import classify_question
from sentiment_detector import check_sentiment
from order_lookup import find_order

CASES_FILE = os.path.join(os.path.dirname(__file__), "eval_cases.json")
REPORT_JSON = os.path.join(os.path.dirname(__file__), "evaluation_results.json")
REPORT_MD = os.path.join(os.path.dirname(__file__), "evaluation_report.md")


def load_cases():
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def contains_any(text, options):
    text_lower = (text or "").lower()
    return any(opt.lower() in text_lower for opt in options)


def run_policy_or_conflict_case(case, index, chunks):
    """Runs a policy_qa or conflict_detection case through the full,
    real assistant pipeline - exactly what a customer would experience."""
    result = get_response(case["question"], {}, index, chunks)
    expected = case["expected"]

    escalated_ok = result.get("escalated", False) == expected["escalated"]
    content_ok = True
    if "must_contain_any" in expected:
        content_ok = contains_any(result.get("answer", ""), expected["must_contain_any"])

    passed = escalated_ok and content_ok
    return passed, {
        "actual_escalated": result.get("escalated"),
        "actual_answer": result.get("answer"),
        "escalated_match": escalated_ok,
        "content_match": content_ok
    }


def run_router_case(case):
    label = classify_question(case["question"])
    expected_label = case["expected"]["label"]
    passed = label == expected_label
    return passed, {"actual_label": label, "expected_label": expected_label}


def run_sentiment_case(case):
    result = check_sentiment(case["question"])
    passed = result["flagged"] == case["expected"]["flagged"]
    return passed, {"actual_flagged": result["flagged"], "reason": result["reason"]}


def run_order_lookup_case(case):
    result = find_order(case["order_number"], case["total"])
    expected = case["expected"]

    found_ok = result["found"] == expected["found"]
    status_ok = True
    if expected.get("found") and "status" in expected:
        status_ok = result.get("status") == expected["status"]

    passed = found_ok and status_ok
    return passed, {
        "actual_found": result["found"],
        "actual_status": result.get("status"),
        "error": result.get("error")
    }


def run_case(case, index, chunks):
    """Dispatches a single test case to the right runner based on
    category, and never lets one failing case crash the whole batch -
    an exception is recorded as a failed case with the error attached,
    not a harness crash."""
    try:
        if case["category"] in ("policy_qa", "conflict_detection"):
            return run_policy_or_conflict_case(case, index, chunks)
        elif case["category"] == "router":
            return run_router_case(case)
        elif case["category"] == "sentiment":
            return run_sentiment_case(case)
        elif case["category"] == "order_lookup":
            return run_order_lookup_case(case)
        else:
            return False, {"error": f"Unknown category: {case['category']}"}
    except Exception as e:
        return False, {"error": str(e)}


def run_case_with_retry(case, index, chunks, max_retries=3):
    """Wraps run_case with retry-with-backoff specifically for rate-limit
    errors. The free tier caps requests PER MINUTE (not just per day) -
    firing 70+ calls back-to-back with no pause can exhaust that
    per-minute allowance within seconds, which looks identical to a
    logic bug (everything fails from that point on) unless you know to
    look for it. A short delay between cases plus a retry on 429/
    RESOURCE_EXHAUSTED errors specifically (not other failures) fixes
    this without masking genuine bugs."""
    for attempt in range(max_retries):
        passed, details = run_case(case, index, chunks)
        error_text = str(details.get("error", ""))
        is_rate_limit = "429" in error_text or "RESOURCE_EXHAUSTED" in error_text

        if not is_rate_limit:
            return passed, details

        wait = 15 * (attempt + 1)
        print(f"    (rate limited, waiting {wait}s before retry {attempt + 1}/{max_retries})")
        time.sleep(wait)

    return passed, details


def run_all(index, chunks):
    cases = load_cases()
    results = []

    print(f"Running {len(cases)} test cases...\n")

    for i, case in enumerate(cases, 1):
        passed, details = run_case_with_retry(case, index, chunks)
        status = "PASS" if passed else "FAIL"
        print(f"[{i}/{len(cases)}] {status} - {case['id']} ({case['category']})")

        results.append({
            "id": case["id"],
            "category": case["category"],
            "question": case.get("question") or f"order={case.get('order_number')} total={case.get('total')}",
            "passed": passed,
            "details": details
        })

        # Small pause between every case to stay comfortably under the
        # free tier's per-minute request cap, not just its daily one.
        time.sleep(3)

    return results


def summarize(results):
    total = len(results)
    passed = sum(1 for r in results if r["passed"])

    by_category = {}
    for r in results:
        cat = r["category"]
        by_category.setdefault(cat, {"total": 0, "passed": 0})
        by_category[cat]["total"] += 1
        if r["passed"]:
            by_category[cat]["passed"] += 1

    category_accuracy = {
        cat: round(v["passed"] / v["total"] * 100, 1)
        for cat, v in by_category.items()
    }

    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "overall_accuracy": round(passed / total * 100, 1) if total else 0,
        "by_category": by_category,
        "category_accuracy": category_accuracy
    }


def write_reports(results, summary, doc_count, chunk_count):
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)

    lines = [
        "# Evaluation Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"**Knowledge base:** {doc_count} policy documents / {chunk_count} chunks",
        "",
        f"**Overall accuracy: {summary['overall_accuracy']}%** ({summary['passed']}/{summary['total']} test cases passed)",
        "",
        "## By category",
        "",
        "| Category | Passed | Total | Accuracy |",
        "|---|---|---|---|"
    ]
    for cat, acc in summary["category_accuracy"].items():
        v = summary["by_category"][cat]
        lines.append(f"| {cat} | {v['passed']} | {v['total']} | {acc}% |")

    failed = [r for r in results if not r["passed"]]
    if failed:
        lines.append("")
        lines.append("## Failed cases")
        lines.append("")
        for r in failed:
            lines.append(f"- **{r['id']}** ({r['category']}): {r['question']}")
            lines.append(f"  - Details: `{r['details']}`")

    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    index, chunks = load_index()
    doc_count = len(set(c["source"] for c in chunks))
    chunk_count = len(chunks)

    results = run_all(index, chunks)
    summary = summarize(results)
    write_reports(results, summary, doc_count, chunk_count)

    print("\n--- SUMMARY ---")
    print(f"Knowledge base: {doc_count} documents / {chunk_count} chunks")
    print(f"Overall: {summary['passed']}/{summary['total']} passed ({summary['overall_accuracy']}%)")
    for cat, acc in summary["category_accuracy"].items():
        v = summary["by_category"][cat]
        print(f"  {cat}: {v['passed']}/{v['total']} ({acc}%)")
    print(f"\nFull report written to {REPORT_MD}")