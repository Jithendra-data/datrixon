# Datrixon release views

## Current V2 review path

Captured with `node tests/capture-v2.cjs` from the local application using the approved synthetic artifact. Desktop images are 1440 × 1000; mobile is 390 × 900. Browser chrome is excluded. No personal records, credentials, or developer tools are shown. The assistant screenshot uses an actual supported question; the failure screenshot is explicitly simulated.

1. [Executive Overview](datrixon-v2-overview.png)
2. [Trust Center](datrixon-v2-trust-center.png)
3. [Reconciliation](datrixon-v2-reconciliation.png)
4. [Gross Margin lineage and dependency impact](datrixon-v2-lineage.png)
5. [Governed Assistant: trusted answer and evidence](datrixon-v2-assistant.png)
6. [Failure Simulator: blocked answer](datrixon-v2-failure.png)
7. [Mobile Trust Center](datrixon-v2-mobile.png)

Captures are release evidence, not live values. They use the real browser clock; a stale artifact needs a validated refresh before capturing a healthy answer. PNGs are kept at native resolution for readable text and are loaded by documentation, not by the application.

## Historical V1 evidence

The `datrixon-*` images without `v2` in their names retain the original analytics and architecture evidence. They are historical snapshots, not the current navigation or governance experience. Reproduce that capture set with `node tests/capture.cjs` if needed. They are retained to document the V1 → V2 evolution.
