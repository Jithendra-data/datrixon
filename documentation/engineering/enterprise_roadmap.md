# Enterprise Roadmap

**Future Enterprise Capability — design requirements, not deployed features.**

Datrixon currently runs a synthetic, full-rebuild Python/SQLite pipeline and publishes a public static application. It has no live ERP connection, enterprise identity, private query service, production SLA, or measured commercial ROI. This roadmap defines acceptance work before a real deployment.

## Capability boundary

| Status | Evidence |
|---|---|
| Implemented | Versioned source controls, dimensional keys, SQL/Python marts, reconciliation, publication gate, diagnostic bundles, CI and static analytics |
| Demonstrated / Simulated | Synthetic distribution transactions; standalone versioned invoice adapter with replay, corrections and tombstones tested in isolation |
| Future Enterprise Capability | Source-specific extraction, incremental orchestration, private identity/authorization, managed warehouse, operational alerting and governed recovery |

## Source adapters and master data

Proposed flow: ERP API or approved export → versioned ingestion contract → restricted landing storage → staging → warehouse → authorized Datrixon service/application. Keep extraction separate from business rules. Every adapter must emit source system, legal entity, stable record/line ID, source version, operation, effective timestamp, extraction timestamp, batch ID, schema version, currency and unit of measure. Store an immutable batch manifest with counts, sums and hashes.

| Source family | Discovery and acceptance work before implementation |
|---|---|
| SAP | Identify the exact ERP edition and released extraction interface with the source owner; establish posting, cancellation, currency and authorization semantics. SAP integration APIs are a possible boundary, not a Datrixon connector. |
| Oracle ERP | Identify application/version, authorized API or export and supported invoice/procurement grains; validate source control totals and rate limits. |
| Microsoft Dynamics | Evaluate supported entity/package exports for the installed product; prove complete header/line extraction and committed batch handling. |
| NetSuite | Evaluate supported REST records/export scope and account permissions; reconcile subsidiary, currency and posting semantics. |
| Infor, Epicor and other ERP systems | Obtain vendor/version-specific API or approved batch-export contracts. Do not assume that a shared ERP label implies equivalent schemas. |
| WMS, TMS, CRM and finance | Identify the system of record for physical movements, shipment milestones, customer activity and financial postings. Reconcile cross-system keys before joining them. |

Vendor documentation entry points, reviewed September 2026: [SAP API-centric integration](https://help.sap.com/docs/integration-suite/isuite-integrations-and-apis/api-centric-integration), [Dynamics package API](https://learn.microsoft.com/en-us/dynamics365/fin-ops-core/dev-itpro/data-entities/data-management-api), [NetSuite REST services](https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_158022624537.html). Interface selection depends on the customer's licensed release and access policy.

Master-data owners must approve legal-entity/customer/product/vendor/warehouse crosswalks, effective dates, unit conversions and currency rules. Decide unknown-member quarantine versus explicit unknown keys, and SCD Type 2 requirements, before accepting facts. Finance must approve net sales, tax/freight exclusions, credit-note treatment, cost valuation and close-period adjustments. Current synthetic USD and unit-cost policies are not substitutes for that approval.

## Incremental ingestion and replay

1. Capture a bounded source watermark and extraction batch ID. Use a stable tie-breaker where timestamps collide. Prefer CDC only when the source supports reliable change ordering and delete capture.
2. Land the batch and manifest before transformation. Retry with the same batch identity; reject a repeated version with a different payload.
3. Merge by source + legal entity + business grain + version. Preserve deletion tombstones and late-arriving updates; prevent old events from resurrecting deleted records.
4. Handle master-data dependencies explicitly, then validate affected partitions and independently reconcile cumulative source totals.
5. Commit the sink transaction and successful batch ledger before advancing the watermark. Record failures and replay range. A retry must produce the same accepted state.
6. Define an approved overlap/lookback window and a backfill procedure for late corrections beyond that window. Test duplicates, reordered events, partial batches, schema changes and recovery after each commit boundary.

The mock adapter demonstrates a small subset of these semantics. The main pipeline still performs full rebuilds.

## Identity, authorization and secrets

Replace public JSON delivery before loading confidential data. Use corporate SSO with OIDC/OAuth where appropriate, authenticated server-side queries, RBAC, and warehouse row-level controls by tenant/legal entity/region. Browser filters are not authorization. Test denied access and cross-tenant isolation with a permission matrix approved by data owners.

Use separate least-privilege ingestion, transformation and query service identities. Store credentials in a managed secret service; use short-lived workload identity where supported, audited rotation and a tested revocation procedure. Keep secrets out of source control, build output, browser bundles and diagnostic payloads. Define encryption, network access, PII minimization, retention and incident ownership before a pilot.

## Observability and proposed service objectives

These are **initial pilot acceptance targets to negotiate**, not achieved SLAs or benchmark results.

| Signal | Proposed acceptance/alert | Accountable owner |
|---|---|---|
| Freshness | Daily batch available by 08:00 business-local time; warn after 30 minutes and escalate after 60 | Data platform on-call and business reporting owner |
| Pipeline health | Alert on any failed mandatory control, incomplete batch or failed deployment | Data engineering |
| Source volume | Investigate >30% change against comparable weekday baseline; tune for seasonality | Domain steward |
| Reconciliation | Block unexplained variances beyond approved per-measure tolerance | Finance data owner |
| Dashboard availability | Set a measured availability target only after private hosting and monitoring exist | Application owner |
| Data access | Centralized authentication/authorization audit logs and suspicious-access review | Security |

Track build identity, input dataset identity and deployment identity separately. Expose last approved business cutoff, last successful refresh, active failure stage and known exception expiry. Alert messages should link the failed batch and safe diagnostics, avoiding PII. A successful workflow is not evidence that source data is current.

## Auditability and metric governance

Version metric definitions, transformation code and data contracts; assign owners and approve breaking changes. Preserve source-to-report identifiers and column-level lineage for material measures. Exceptions require documented scope, approver, expiry and compensating controls. The synthetic negative-inventory allowance must not migrate automatically into production. Record access, source extraction, transformation, publication and administrative actions with a governed retention policy.

## Recovery and retention

Proposed pilot objectives: RPO of one accepted daily batch and RTO of four hours, subject to a timed restore drill and business approval. These objectives are not demonstrated today.

Back up accepted warehouse versions, immutable authorized extracts, manifests, transformation versions and configuration to access-controlled storage. Define retention with Finance/Security; do not treat the current 14-day Actions artifact lifetime as enterprise backup. Run scheduled restore drills, verify hashes and reconciliation, replay batches from the last committed watermark, and test authorization before reopening access. Roll back application and compatible dataset versions together. Document rollback authority and communication ownership.

Today, successful local bundles contain matched SQLite/JSON evidence. Prepublication failure preserves public JSON; database and JSON replacement are separate operations. See the [current recovery procedure](decisions.md).

## When to change the deployment architecture

Confidential data, row-level access, concurrent writers or authorized unbounded drill-through trigger architectural change regardless of row count. Otherwise measure the existing approach before migrating.

Suggested evaluation thresholds—not SQLite limits or measured capacities—are: refresh exceeding 30 minutes for three consecutive runs, peak process memory above 70% of the build host, compressed overview payload above 5 MB, or p95 first-useful-render above 3 seconds on agreed target devices/network. Confirm these budgets through representative measurement; current allocation tracing is not total process memory.

If requirements exceed those budgets: partition ingestion, adopt a managed cloud warehouse, preserve reconciliations during dual runs, add a governed semantic/API layer with authorized pagination, then deploy an authenticated frontend. Retain the simple full rebuild until incremental state is justified and tested. Migration success is equivalent approved measures, reliable recovery and agreed service performance—not additional technology names.

## Enterprise pilot exit evidence

- Signed source/data contract and master-data ownership.
- Approved financial definitions and source-to-report reconciliation.
- Successful replay, late-arrival, deletion and restore drills.
- Independent access-control and secret-rotation checks.
- Measured freshness, performance, cost and alert-response baselines.
- Real operational outcome baseline, intervention cost and follow-up results.

Until these exist, describe Datrixon as a tested analytics engineering demonstration using synthetic data.
