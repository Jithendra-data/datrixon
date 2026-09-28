# Validation strategy

Run Python unit tests, pure-JavaScript metric tests, isolated full-pipeline replay, and persistent browser regression before deployment. The published contract itself must pass the publication validator. Smoke tests never overwrite the checked-in public dataset.

Mandatory failures block publication: unexpected source checks, PK/FK resolution, missing/nonfinite contract measures, or any of five reconciliation failures. The only allowed synthetic exception is Negative ending on-hand; it is explicitly labeled EXPECTED_SCENARIO. A real ERP ingestion policy does not inherit that exception.

Tests and evidence: see documentation/engineering/decisions.md. No claim is made that these tests establish comprehensive security, accessibility conformance, finance certification, or enterprise-scale performance.

The versioned registry defines every required control. Unknown, missing, duplicate, malformed or failed blocking entries cannot be substituted by a generic PASS. Checks include source key integrity, business cutoff, lifecycle, money arithmetic, receipt/return relationships and inventory events. Summary totals must agree with detail. Browser tests bind each table to an explicit dataset identity and exercise routes at 390, 768 and 1440 pixels. The refresh workflow runs browser checks again on newly generated data before commit/deployment.
