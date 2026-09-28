# Datrixon

**ERP Analytics & Operational Intelligence**

Datrixon is an end-to-end analytics engineering portfolio project that models how ERP data from a distribution business becomes decision-ready analytics. Datrixon is the platform; the distributor is fictional. The implementation uses synthetic data, without live ERP connectivity or enterprise authentication.

[Live application](https://jithendra-data.github.io/northstar-distribution-intelligence/) · [Project & Architecture](https://jithendra-data.github.io/northstar-distribution-intelligence/#project-story) · [Actions](https://github.com/Jithendra-data/northstar-distribution-intelligence/actions)

Datrixon helps a fictional distribution leadership team investigate margin movement, stock exposure, overdue purchasing, inactive customers, and service gaps. All records are synthetic. No real customer outcome, recovered revenue, or ROI is claimed.

## What runs today

Synthetic ERP CSV → mandatory source validation → normalized staging CSV → enforced SQLite reference warehouse → SQL sales/customer/vendor/balance marts + shared Python operational analytics → independent source/warehouse/dashboard reconciliation → approved JSON → static browser application.

Four SQLite facts, six dimensions, and a purchase-receipt child table are actually populated by `etl/warehouse.py`. `sql/sqlite/warehouse.sql` is executed. The T-SQL directories are a separate SQL Server deployment design, not an active SQL Server service. Receipt timing and movement-window calculations read staging directly; the architecture diagram shows that branch.

| Implemented | Demonstrated / Simulated | Future Enterprise Capability |
|---|---|---|
| Source controls, normalized staging, SQLite facts, SQL/Python aggregates, five reconciliations, fail-closed publication, hashes and timings, unit/integration/browser tests | Synthetic ERP scenario; standalone tested mock change adapter; separate SQL Server design | Real ERP connection, SSO/RLS, production CDC, SCD Type 2, multi-user warehouse, validated business ROI |

## Run and verify

```bash
python -m pip install -r requirements.txt
python -m etl.run_pipeline
python -m unittest discover -s tests -p 'test_*.py' -v
python -m tests.smoke_pipeline
node --test tests/metrics.test.cjs tests/decisions.test.cjs
pnpm install --frozen-lockfile
pnpm exec playwright install chromium
pnpm test:browser
python -m http.server 8000 --directory web
```

`--skip-generation` reuses raw files. A matching raw generation manifest preserves the seed; otherwise it is explicitly unknown. Input hashes identify the files. `--workspace .test-run` isolates all generated files. Defaults: 75,000 order headers, 10,000 PO headers, 5,000 customers, 2,000 products, four warehouses, and business dates in 2023–2025. Repeated full builds of the same inputs are idempotent; generated timestamps and runtime measurements are intentionally different.

## Trust and evidence

Mandatory failures block publication. The synthetic negative-stock scenario is the only expected control exception; it is not accepted by a real ERP integration policy. Five measures independently reconcile raw records, SQLite SQL queries, and published KPI values. The candidate replaces `dashboard.json` only after serialization and validation. Failed runs retain the last approved public file.

The current run's values, fact row counts, runtime, model/export Python allocation peak, dependencies, and input hashes are published in `web/data/dashboard.json`. The downloadable Actions artifact also includes the SQLite file and run manifest with actual payload bytes/hash. These are measured single-run results, not an enterprise scale benchmark. No static 'current scenario' numbers are copied here because automated refresh changes them.

## Product scope

Overview financial filters compare the exact selected interval to that interval one year earlier. Partial prior coverage is not reported as YoY. Snapshot metrics and signals use the full dataset. Each detail table states its export cap, eligible population, and selection rule; downloads contain the displayed extract. Three investigation queues expose inventory, inactive-customer, and overdue-PO evidence. SQL Server and private API deployment remain separate design work.

## Decisions and limitations

- [Executing architecture and model](documentation/architecture/architecture.md)
- [Decisions, limitations, recovery](documentation/engineering/decisions.md)
- [Mock ERP integration contract](documentation/engineering/integration_contract.md)
- [Enterprise Roadmap and acceptance criteria](documentation/engineering/enterprise_roadmap.md)
- [Security and scale plan](documentation/engineering/security_and_scale.md)
- [Business investigation and methodology](case-study/case_study.md)
- [Metric definitions](documentation/kpi_dictionary/kpi_dictionary.md)
- [Operating guide](documentation/operations/pipeline_operations.md)
- [Review completion and remaining external evidence](documentation/engineering/review_status.md)

## Ownership

Project owner: **Anumala Jithendra**. Developed iteratively with AI-assisted implementation. Repository changes and tests are the evidence; this does not claim unaided authorship or commercial production deployment. [LinkedIn](https://www.linkedin.com/in/anumala-jithendra/) · [Email](mailto:jithendra.anumala1@gmail.com).

MIT licensed. See LICENSE.

## Product evidence

[Release screenshots](screenshots/README.md) show executive analytics, sales, controls, architecture, and an investigation. Domain summaries are calculated from full source populations; financial comparisons follow the selected overview period.

Configuration: `DATRIXON_RANDOM_SEED` (legacy `NORTHSTAR_RANDOM_SEED` supported), `DATRIXON_AS_OF_DATE` (default 2025-12-31). The latter controls business time, not the deployment clock. Validation requires the current versioned control registry.

## Final verification commands

`pnpm test` runs both JavaScript suites. `DATRIXON_BASE_URL` optionally points the browser regression at the deployed Pages URL; `DATRIXON_ALLOW_CDN=1` additionally verifies the normal ECharts path. Without that flag, the browser suite deliberately blocks CDNs to verify fallback charts. All major views are checked at desktop, tablet and 390px widths. These checks are regression evidence, not a security or accessibility certification.
