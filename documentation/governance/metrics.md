# Governed metrics and semantic layer

`governance/metrics/metric_registry.json` is the current machine-readable definition. `history/2.0.0.json` preserves the release baseline. Definitions include owner/steward (demo roles), source columns, grain, SQL, exclusions, sensitivity, roles, cadence, version, certification, reconciliation dependencies and consumers.

`python -m governance.validate` checks definitions, history compatibility, policy coverage and the published evidence. Breaking changes include calculation/SQL, grain, scope, sources, roles and classification; they need a major metric version. Removing an old metric without a migration path fails. For a later release, retain the previous baseline, deliberately review changes and update the baseline reference; do not silently overwrite history to suppress a failure.

## Executable interface

```python
from pathlib import Path
from governance.semantic import SemanticLayer

semantic = SemanticLayer(Path('data/processed/warehouse.sqlite'), '2025-12-31')
print(semantic.get_metric('revenue', year=2025))
print(semantic.get_metric('gross_margin'))
print(semantic.get_metric('inventory_exposure'))
```

Only registered, demo-certified metrics can execute. SQLite opens read-only and an authorizer denies mutations. Period parameters are bound. User text is never treated as SQL or a filename.

Material V1 metrics are compared independently to semantic results before the payload uses the canonical value. Revenue, profit, units, inventory and PO value also retain independent raw/SQLite/JSON reconciliation. Selected-period frontend ratios use the existing tested `reportingPeriod` helper over the approved series; new catalog/assistant sections consume canonical values. Operational detail calculations still use the shared V1 transforms rather than duplicating their business rules in UI code.

## Deliberately unresolved definitions

Net-of-credits sales cannot be inferred from physical returns. AOV requires an agreed eligible booking population. An overall return rate needs an explicit denominator, period and cohort. These three entries are DRAFT, have no executable query and deny analytical answers. This preserves the existing KPI dictionary instead of quietly changing its meaning.

Certification means repository-approved demo definition, not approval by a real Finance owner. Ratios are undefined at zero denominators. Inactivity thresholds and movement windows remain sourced from `utils/business_rules.py`.
