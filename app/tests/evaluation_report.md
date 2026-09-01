# Evaluation Report

Generated: 2026-08-30T13:22:55.270630+00:00

**Knowledge base:** 7 policy documents / 39 chunks

**Overall accuracy: 89.8%** (53/59 test cases passed)

## By category

| Category | Passed | Total | Accuracy |
|---|---|---|---|
| policy_qa | 26 | 28 | 92.9% |
| conflict_detection | 3 | 4 | 75.0% |
| router | 10 | 10 | 100.0% |
| sentiment | 11 | 11 | 100.0% |
| order_lookup | 3 | 6 | 50.0% |

## Failed cases

- **policy_cancellation_window** (policy_qa): Can I cancel my order after placing it?
  - Details: `{'actual_escalated': True, 'actual_answer': "I found conflicting information in our policies on this - I don't want to give you the wrong answer, so I'm flagging this for a team member to confirm and get back to you.", 'escalated_match': False, 'content_match': False}`
- **policy_address_change** (policy_qa): Can I change my shipping address?
  - Details: `{'actual_escalated': False, 'actual_answer': "Hi there! According to our cancellation and shipping policies, you can request a change to your shipping address within the first hour of placing your order. If your order hasn't shipped yet and you caught an error, please reach out to support immediately so we can try to correct it for you!", 'escalated_match': True, 'content_match': False}`
- **conflict_refund_time** (conflict_detection): How long does a refund take?
  - Details: `{'actual_escalated': False, 'actual_answer': 'According to our return policy, refunds are typically processed within 5 to 7 business days after we receive your returned item, while store credit refunds are processed within 1 to 2 business days.', 'escalated_match': False, 'content_match': False}`
- **order_lookup_shipped** (order_lookup): order=1002 total=80.00
  - Details: `{'actual_found': False, 'actual_status': None, 'error': 'Shopify API request failed: 401 Client Error: Unauthorized for url: https://verve-athletics-demo.myshopify.com/admin/api/2025-01/orders.json?name=%231002&status=any'}`
- **order_lookup_processing** (order_lookup): order=1001 total=200.00
  - Details: `{'actual_found': False, 'actual_status': None, 'error': 'Shopify API request failed: 401 Client Error: Unauthorized for url: https://verve-athletics-demo.myshopify.com/admin/api/2025-01/orders.json?name=%231001&status=any'}`
- **order_lookup_whitespace** (order_lookup): order= 1001  total= 200.00 
  - Details: `{'actual_found': False, 'actual_status': None, 'error': 'Shopify API request failed: 401 Client Error: Unauthorized for url: https://verve-athletics-demo.myshopify.com/admin/api/2025-01/orders.json?name=%231001&status=any'}`