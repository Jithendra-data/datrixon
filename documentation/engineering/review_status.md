# Implementation evidence and limitations

This guide maps implemented capabilities to supporting code and documentation. Current run results are published in Data Quality and the run manifest; CI records regression outcomes.

| Capability | Supporting implementation / evidence |
|---|---|
| Dimensional warehouse | Executed SQLite schema and loader with primary/foreign keys; separate proposed T-SQL design |
| Financial comparisons | Selected-month comparisons, prior-period coverage and invalid-range handling in the metrics module and JavaScript tests |
| Publication controls | Versioned mandatory registry, explicit severity, summary/detail consistency and validated candidate replacement |
| Reconciliation | Independent raw-source totals, SQLite queries and published measures with explicit units and tolerances |
| Source correctness | Scenario-calendar lifecycle checks, ROUND_HALF_UP arithmetic, source-key integrity and receipt/return relationships |
| Reporting scope | Explicit dataset-bound tables, route scopes, eligible/exported counts and displayed-extract downloads |
| Investigation workflows | Affected-record queues, decision-owner guidance and full-population summaries |
| Shared business rules | Configurable cutoff, canonical SQL views and shared operational transformations |
| Recovery evidence | Stage-specific diagnostics, matched successful run bundles and tests that preserve prior publication on failure |
| Reproducibility | Generation configuration, seed, source hashes, build identity and repeated full-build checks |
| Mock ERP changes | Standalone tested versioned invoice adapter; not connected to a real ERP or the main synthetic runner |
| Responsive application | Domain views, reduced-motion support, keyboard sorting and browser regressions |

## Scope and limitations

The project uses synthetic distribution records and a public static application. It does not demonstrate live ERP connectivity, enterprise authentication, production CDC, financial certification or measured commercial outcomes. SQLite is a portable reference warehouse; SQL Server scripts are a separate deployment design.

Before a real deployment, source owners would need to approve extraction contracts and metric definitions, establish financial and operational baselines, implement access controls and incremental ingestion, and measure recovery and performance objectives. The [Enterprise Roadmap](enterprise_roadmap.md) documents this future work separately from implemented capabilities.

Project ownership and AI-assisted implementation are disclosed in the [README](../../README.md#ownership). The [case study](../../case-study/case_study.md) describes the supported decisions and the business value that a real pilot would need to measure.
