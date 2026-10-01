"""Versioned, reviewable metric definitions; metadata is never user input."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'governance/metrics/metric_registry.json'


def load_registry():
    return json.loads(REGISTRY.read_text(encoding='utf-8'))


def breaking_changes(previous, current):
    """Meaning changes require a new major version, including removed metrics."""
    before = {m['metric_id']: m for m in previous['metrics']}
    after = {m['metric_id']: m for m in current['metrics']}
    fields = ('calculation', 'sql', 'business_definition', 'grain', 'filters', 'exclusions',
              'source_columns', 'source_tables', 'unit', 'period_support', 'sensitivity', 'permitted_roles', 'reconciliation_rule')
    return [key for key, old in before.items() if key not in after or
            any(old.get(f) != after[key].get(f) for f in fields)]


def validate_registry(registry=None, previous=None):
    registry = registry or load_registry()
    required = {'metric_id', 'display_name', 'business_definition', 'calculation',
                'source_tables', 'source_columns', 'grain', 'aggregation_type', 'filters',
                'exclusions', 'owner', 'steward', 'domain', 'sensitivity', 'refresh_frequency',
                'reconciliation_rule', 'tolerance', 'effective_date', 'version', 'status',
                'certification_status', 'permitted_roles', 'downstream_consumers'}
    ids = set()
    for metric in registry['metrics']:
        key = metric.get('metric_id')
        if not required <= metric.keys() or not re.fullmatch(r'[a-z][a-z_]+', key or '') or key in ids:
            raise ValueError('Invalid or duplicate metric definition: ' + str(key))
        ids.add(key)
        if metric['sensitivity'] not in ('Public', 'Internal', 'Confidential', 'Restricted'):
            raise ValueError('Unknown classification')
        if metric['certification_status'] not in ('CERTIFIED_DEMO', 'DRAFT'):
            raise ValueError('Invalid certification')
        if not all(metric[f] for f in ('owner', 'steward', 'business_definition', 'version')):
            raise ValueError('Missing accountability or definition')
        if metric['certification_status'] == 'CERTIFIED_DEMO' and not metric.get('sql'):
            raise ValueError('Certified measure requires executable SQL')
        if metric.get('sql') and (not metric['sql'].lstrip().upper().startswith(('SELECT ', 'WITH ')) or ';' in metric['sql']):
            raise ValueError('Only one read-only governed query is allowed')
        if metric['tolerance'] < 0 or not metric['permitted_roles']:
            raise ValueError('Invalid tolerance or roles')
    if previous:
        changed = breaking_changes(previous, registry)
        for key in changed:
            old = next(m for m in previous['metrics'] if m['metric_id'] == key)
            new = next((m for m in registry['metrics'] if m['metric_id'] == key), None)
            if new is None or int(new['version'].split('.')[0]) <= int(old['version'].split('.')[0]):
                raise ValueError('Breaking metric change needs retained history and a major version: ' + key)
    return registry
