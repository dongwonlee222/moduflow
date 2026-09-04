---
schema: moduflow.analysis-runs.v1
---

Append one `## run-<uuid4>` section per analysis run. Each section holds exactly one fenced
`json` object whose `id` matches its heading. Never rewrite an existing run: a corrected
analysis is a new run naming the run it supersedes, and a changed judgment amends only the
six fields listed in the spec while appending one `state_history` entry.
