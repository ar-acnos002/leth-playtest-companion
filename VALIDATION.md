# Leth v0.1 rules conversion validation

## Scope: historical findings and current distributions

The findings and tables below record the original FIND-only source conversion
validation. They are preserved as historical findings, not a validation report for
every distribution currently shipped.

The active `rules/scene_pools.json` now contains 16 quest types. The additional
15 quest distributions are outside the scope of the historical source validation
recorded here. Automated structural and encounter-selection tests do not establish
that those newer distributions match their source documents.

## Historical FIND-only source validation

Source PDFs: glossary, FIND numbered encounter distribution, fixed environment distribution.

- Glossary: **76 / 76** IDs; unique names and IDs.
- FIND scene pools: **6 / 6**, source counts matched.
- Environment pools: **9 / 9**, source counts matched; two-column continuation handled in reading order.

## Environment counts

| Environment | Count |
|---|---:|
| TYRANNY | 26 |
| KINGDOM | 19 |
| CITY | 21 |
| SETTLEMENT | 19 |
| VILLAGE | 15 |
| ROAD | 20 |
| WOODS | 27 |
| RUINS | 26 |
| WILDS | 29 |

## Intersection sizes (FIND)

| Mode | Scene | Scene pool | TYRANNY | KINGDOM | CITY | SETTLEMENT | VILLAGE | ROAD | WOODS | RUINS | WILDS |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| TRAVEL | SETUP | 21 | 4 | 5 | 5 | 6 | 5 | 10 | 13 | 4 | 13 |
| TRAVEL | ESCALATION | 25 | 16 | 3 | 4 | 4 | 3 | 10 | 12 | 8 | 14 |
| TRAVEL | CULMINATION | 18 | 9 | 4 | 4 | 0 | 0 | 4 | 5 | 8 | 11 |
| EXPLORE | SETUP | 23 | 9 | 1 | 1 | 0 | 0 | 6 | 14 | 10 | 17 |
| EXPLORE | ESCALATION | 53 | 22 | 8 | 10 | 7 | 6 | 12 | 18 | 25 | 19 |
| EXPLORE | CULMINATION | 24 | 14 | 5 | 6 | 0 | 0 | 3 | 6 | 16 | 9 |

An intersection size of zero is an expected gameplay condition handled through Quiet Beat, Redirect, or Misdirect; it is not a malformed table.

Scene-pool values are **stable glossary IDs**, not the PDF’s local position numbers.

At the time of this historical validation, FIND was the only supplied quest type.
The current expanded distribution contains 16 quest types, as described above.
