# Evaluation Report

Generated: 2026-09-03T03:03:13.147660+00:00

**Knowledge base:** 7 policy documents / 39 chunks

**Overall accuracy: 98.3%** (58/59 test cases passed)

## By category

| Category | Passed | Total | Accuracy |
|---|---|---|---|
| policy_qa | 27 | 28 | 96.4% |
| conflict_detection | 4 | 4 | 100.0% |
| router | 10 | 10 | 100.0% |
| sentiment | 11 | 11 | 100.0% |
| order_lookup | 6 | 6 | 100.0% |

## Failed cases

- **policy_swap_color** (policy_qa): Is there a fee to swap for a different color?
  - Details: `{'actual_escalated': True, 'actual_answer': "I found conflicting information in our policies on this - I don't want to give you the wrong answer, so I'm flagging this for a team member to confirm and get back to you.", 'escalated_match': False, 'content_match': False}`