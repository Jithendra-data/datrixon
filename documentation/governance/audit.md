# Data versions, audit and reconciliation evidence

Each run records a run/build ID, source-hash dataset identity, publication schema version, source-contract version, metric-registry version, code commit and dirty flag, business cutoff, generation seed, per-file source hashes, warehouse hash and UTC timestamp. The exact published bytes and their SHA-256 are in the matched `run_manifest.json`, outside the hashed JSON artifact.

`data/processed/runs/<run_id>/audit.jsonl` records pipeline start, validated source/contracts, warehouse load, reconciliation, registry validation, lineage validation, trust decision construction, publication approval or rejection. Approval records completion of the gate; atomic filesystem replacement remains the final operation and may fail separately. The successful bundle retains the exact matched JSON and warehouse. Failed runs retain the current stage's safe diagnostics.

Reconciliation remains independent: raw CSV arithmetic, SQLite facts and candidate JSON. The center shows source/warehouse/published totals, unit, variances, tolerance, cutoff and validation time. Five measures have three-way evidence; other measures explicitly rely on source controls and semantic computation and must not be described as independently financially reconciled.

Browser events are a separate in-memory demonstration log (question evaluated, allowed/blocked answer, simulation/reset). They are neither durable nor authenticated. A production system needs server-side append-only audit storage, retention, actor identity, correlation IDs, alerts and recovery drills.
