# Detection Evaluation Report

The existing `analyze_text` signature detector was evaluated against `security_events.jsonl`. Ground-truth labels were never supplied to the detector and are removed by the adapter before persistence.

| Metric | Result |
| --- | ---: |
| True positives | 20 |
| False positives | 0 |
| True negatives | 290 |
| False negatives | 10 |
| Precision | 1.0000 |
| Recall | 0.6667 |
| F1 | 0.8000 |

The false negatives are synthetic repeated failed-login events. This is expected: the present detector matches text signatures such as SQL injection and traversal, not temporal authentication correlation. Synthetic results do not establish production detection performance.
