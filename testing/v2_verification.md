# V2 verification

## Baseline before changes

2026-10-01, local Windows checkout synchronized with GitHub `ec1bb7c` (latest scheduled dataset):

- 31 existing Python tests passed.
- 7 existing JavaScript tests passed.
- Existing browser regression passed using installed Edge, including desktop/tablet/mobile, charts, filters, CSV, routing and failure fallback.

## V2 execution evidence

The expanded suites contain 67 Python tests and 21 JavaScript tests. Local runs passed, including actual source drift and governance failures preserving previous publication bytes; roles, Restricted requests, stale datasets, unsupported questions, provenance and copied-decision incident scenarios.

Both browser suites have been executed. V2 checks all 11 new routes at 390, 768 and 1440 pixels, citations, lineage impact, policy denial, escaped hostile input, recovery, keyboard navigation and reduced-motion support. V1 browser checks remain intact. This is basic accessibility regression, not WCAG certification.

A full 75,000-order / 10,000-PO build with seed 36462180390 produced 170,575 sales lines, 269,465 inventory movements, 39,314 purchase lines and 4,643 return records. All eight V1 executive KPIs matched the prior publication within existing tolerances. The initial full V2 build took 274.768 seconds locally. Later replay timings are in the published manifest; performance varies with machine load and tracing. No enterprise scale claim is made.

## Reproduce

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
python -m tests.smoke_pipeline
python -m governance.validate --source data/raw
python -m validation.publication
python -m tests.security_scan
pnpm test
pnpm test:browser
```

`tests/browser-v2.cjs` prints first-evidence-render time and actual payload bytes. It fixes the browser clock to the artifact timestamp for reproducibility; separate unit tests deliberately advance time past freshness expiry. `DATRIXON_TEST_PAYLOAD` supports isolated artifacts. `DATRIXON_BASE_URL` targets deployed assets. Screenshots go to ignored `test-results/`.

The credential scanner checks nonignored/tracked source files for selected private-key, token and credential patterns and reports file names only. It does not establish the absence of every possible secret. External live integrations, corporate SSO, real Finance approval and production performance cannot be verified in this repository.
