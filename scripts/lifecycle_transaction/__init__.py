"""Issue 153 — `project_lifecycle_transaction` split by concern.

The module was 7,524 lines with 208 top-level symbols across 106 distinct name
stems: serialization, journalling, recovery, projected validation, locking,
state transition. Not a long file — a directory that never became one.

Split one concern at a time, verifying the suite is byte-identical before and
after each move. `errors` is first because exceptions reference nothing else.
"""
