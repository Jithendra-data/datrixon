# Trust, readiness and publication policy

Each metric has an explicit decision with ten dimensions: schema, quality, referential integrity, freshness, reconciliation, certification, lineage, access coverage, contract and semantic equivalence.

- Any missing/failed mandatory dimension: **BLOCKED / Blocked**.
- All mandatory controls pass, with an acknowledged exception: **WARNING / Conditional**.
- All pass: **TRUSTED / Ready** for the synthetic demonstration.

No numerical confidence score is used. The synthetic negative-ledger allowance is inherited only for inventory-related interpretation and remains visible. Draft metrics are blocked individually; they do not prevent the independently certified product from publishing.

The build gate is enforced in Python before atomic replacement. Definitions, contracts and policy must match repository metadata. The serialized candidate is revalidated. At answer time JavaScript checks trust, current batch age, metric certification, role policy and applicable reconciliation evidence again. A stale approved artifact remains available as disclosed historical analytics; new assistant access is denied after 192 hours.

Readiness ownership/definition/classification evidence comes from registry validation. Authorization coverage means configured demo roles, not authenticated identities. Source datasets are Conditional for direct AI use: raw tables are never exposed through the assistant; only certified metrics and bounded approved extracts are supported.

The Trust Center, Metric Catalog, Reconciliation and Readiness pages share this evidence. Failure Simulator overrides a copied control decision, never the data. Actual source drift, stage failures and governance failures are separately injected by automated pipeline tests that compare the prior published bytes.

## Controls and observability

The existing 37 source controls remain registered in `validation/registry.py`. V2 exports contract checks and governance dimensions with control identity, category, severity, asset, owner, logic, threshold, tested records, failed records where meaningful, last run, remediation and evidence route. A failed assertion is not converted into PASS to make the product look healthier. Single-run results do not imply control trends; local run bundles support historical inspection.
