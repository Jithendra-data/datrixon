"""Explicit controls, not an opaque confidence score. Unknown evidence fails closed."""
from datetime import datetime, timezone
import json
from governance.registry import ROOT

DIMENSIONS = ('schema', 'quality', 'referential_integrity', 'freshness', 'reconciliation',
              'metric_certification', 'lineage', 'access_policy', 'contract', 'semantic_equivalence')


def trust_decision(asset, controls):
    controls = {name: controls.get(name, 'FAIL') for name in DIMENSIONS}
    failed = [name for name, status in controls.items() if status not in ('PASS', 'WARNING')]
    return dict(asset=asset, status='BLOCKED' if failed else 'WARNING' if 'WARNING' in controls.values() else 'TRUSTED',
                controls=controls, failed_controls=failed,
                readiness='Blocked' if failed else 'Conditional' if 'WARNING' in controls.values() else 'Ready')


def freshness(timestamp, now=None, max_age_hours=192):
    try:
        age = ((now or datetime.now(timezone.utc)) - datetime.fromisoformat(timestamp)).total_seconds() / 3600
        return 'PASS' if 0 <= age <= max_age_hours else 'FAIL'
    except (ValueError, TypeError): return 'FAIL'


def load_policy():
    return json.loads((ROOT / 'governance/policies/access.json').read_text())


def authorize(metric, decision, role, operation='ai', policy=None):
    policy = policy or load_policy()
    reasons = []
    if operation not in ('ai', 'view', 'publish'): reasons.append('unknown_operation')
    if role not in policy['roles'] or metric['domain'] not in policy['roles'].get(role, []): reasons.append('role_domain_denied')
    if role not in metric['permitted_roles']: reasons.append('metric_role_denied')
    if metric['sensitivity'] == 'Restricted': reasons.append('restricted_field')
    if metric['certification_status'] != 'CERTIFIED_DEMO': reasons.append('uncertified_metric')
    if decision.get('status') not in ('TRUSTED', 'WARNING'): reasons.extend(decision.get('failed_controls') or ['missing_trust'])
    return dict(decision='DENY' if reasons else 'ALLOW', reasons=reasons, metric=metric['metric_id'], role=role, operation=operation,
                boundary='Demo role simulation — not production authentication')
