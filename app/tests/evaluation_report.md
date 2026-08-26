# Evaluation Report

Generated: 2026-08-26T10:06:13.756111+00:00

**Knowledge base:** 7 policy documents / 38 chunks

**Overall accuracy: 94.7%** (54/57 test cases passed)

## By category

| Category | Passed | Total | Accuracy |
|---|---|---|---|
| policy_qa | 23 | 24 | 95.8% |
| conflict_detection | 5 | 6 | 83.3% |
| router | 10 | 10 | 100.0% |
| sentiment | 10 | 11 | 90.9% |
| order_lookup | 6 | 6 | 100.0% |

## Failed cases

- **policy_shipping_international** (policy_qa): How long does international shipping take?
  - Details: `{'error': 'Server disconnected without sending a response.'}`
- **multi_intent_return_and_shipping** (conflict_detection): What's your return policy, and also do you ship to Canada?
  - Details: `{'actual_escalated': False, 'actual_answer': 'Hi there! Our return policy allows you to return items due to customer preference for free using our prepaid label, and yes, we do ship to Canada.', 'escalated_match': False, 'content_match': False}`
- **sentiment_urgent_but_not_safety** (sentiment): Please help ASAP, my card was charged twice!
  - Details: `{'actual_flagged': True, 'reason': 'the customer is expressing urgency and a time-critical financial problem due to a double charge.'}`