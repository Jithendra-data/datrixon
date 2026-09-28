# Operating guide

Scheduled refresh runs Mondays at 10:00 UTC, or manually with a numeric seed and record counts. Both refresh and Pages deployment depend on reusable regression checks. GitHub scheduling remains best effort.

1. Install exact Python and browser-test dependencies.
2. Generate synthetic masters and transactions, or reuse raw files with `--skip-generation`.
3. Fail on unexpected source controls. Document the synthetic negative-stock exception.
4. Normalize staging CSVs; load enforced SQLite dimensions and facts; calculate SQL/Python aggregates once.
5. Build a candidate contract and independently reconcile raw, SQLite, and candidate totals.
6. Fail closed on missing, nonfinite, or unreconciled measures. Atomically replace public JSON only after approval.
7. Retain the database, control output, reconciliation, and run manifest as a 14-day Actions artifact.
8. Commit the approved JSON and deploy directly from the refresh workflow. Ordinary code pushes deploy through Pages after reusable checks.

`data_through` is the business cutoff; `refreshed_at_utc` is generation time. A reused raw run retains the seed only when its generation manifest matches all input hashes; otherwise its seed is unknown. The manifest records dependencies, interpreter, commit/run identity, fact counts, runtime, model/export Python allocation peak, and payload hash/bytes. The web page does not claim that a recent generation timestamp makes the historical business dates current.

Recovery: consult engineering/decisions.md. Raw and processed build files are local artifacts; only synthetic `web/` content is public. Expected exceptions must not be silently broadened to make a failed pipeline green.

## Versioned controls, diagnostics and identity

The current contract/control versions and mandatory IDs are defined in validation/registry.py. Removing, duplicating or changing a required control, malformed counts/statuses, or summary disagreement blocks publication. Only the named synthetic negative-ledger scenario has an exception.

Each build writes data/processed/runs/<build_id>/. Successful bundles contain the warehouse, exact published JSON, manifest and controls. Failures write failure.json with the failed stage; available check/reconciliation CSVs are retained. The refresh workflow uploads diagnostics with `if: always()` while commit/deployment remain success-only.

Dataset identity hashes input-file hashes. Build identity identifies an execution. Deployment identity belongs to the separate Pages deployment. A raw generation manifest records seed/configuration and hashes; reuse only retains the seed when those hashes match. Local builds record commit and dirty-worktree status honestly.

Full rebuilds replace SQLite and JSON separately. The public JSON remains unchanged on prepublication failures; this is not a distributed atomic transaction across every build artifact. The successful run bundle is the matched warehouse/JSON evidence for review. Local bundles require manual retention management; hosted Actions artifacts expire after 14 days.
