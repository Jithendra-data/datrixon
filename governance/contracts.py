"""Strict source contracts and drift evidence evaluated before normalization."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from governance.registry import ROOT


def load_contracts():
    return json.loads((ROOT / 'governance/contracts/sources.json').read_text())


def inspect_frame(frame, contract, version='1.0.0'):
    issues = []
    def issue(kind, detail, severity='BREAKING'):
        issues.append(dict(kind=kind, detail=detail, severity=severity))
    if version != contract['version']:
        issue('version_mismatch', 'Source contract version does not match approved version')
    expected = set(contract['columns'])
    for col in sorted(expected - set(frame.columns)): issue('removed_column', col)
    for col in sorted(set(frame.columns) - expected): issue('added_column', col)
    for name, spec in contract['columns'].items():
        if name not in frame: continue
        values = frame[name]
        nulls = values.isna() | values.astype(str).str.strip().eq('')
        if not spec['nullable'] and nulls.any(): issue('null_violation', name)
        present = values[~nulls]
        if spec['type'] in ('number', 'integer'):
            number = pd.to_numeric(present, errors='coerce')
            if (~np.isfinite(number)).any() or (spec['type'] == 'integer' and (number % 1 != 0).any()):
                issue('type_change', name)
        elif spec['type'] == 'date':
            if pd.to_datetime(present, errors='coerce').isna().any(): issue('type_change', name)
        elif spec['type'] == 'boolean':
            if not present.astype(str).str.lower().isin(['true', 'false']).all(): issue('type_change', name)
        if spec.get('allowed_values') and not present.astype(str).isin(spec['allowed_values']).all():
            issue('invalid_category', name)
        if spec.get('max_null_rate') is not None and float(nulls.mean()) > spec['max_null_rate']:
            issue('null_rate', name, 'WARNING')
    if set(contract['keys']) <= set(frame.columns) and frame.duplicated(contract['keys']).any():
        issue('duplicate_key', ', '.join(contract['keys']))
    return dict(source=contract['source'], version=version, records_tested=len(frame),
                status='FAIL' if any(i['severity'] == 'BREAKING' for i in issues) else 'WARNING' if issues else 'PASS',
                issues=issues, owner=contract['owner'], grain=contract['grain'])


def validate_sources(source: Path, version='1.0.0'):
    contracts = load_contracts()
    results = []
    for contract in contracts['sources']:
        path = source / (contract['source'] + '.csv')
        if not path.exists():
            results.append(dict(source=contract['source'], status='FAIL', records_tested=0,
                                issues=[dict(kind='missing_source', severity='BREAKING', detail=path.name)]))
        else:
            results.append(inspect_frame(pd.read_csv(path), contract, version))
    return results


def enforce_contracts(results):
    expected = {c['source'] for c in load_contracts()['sources']}
    if {r['source'] for r in results} != expected or len(results) != len(expected) or any(r['status'] == 'FAIL' for r in results):
        raise ValueError('Source contract / schema drift blocked publication: ' +
                         ', '.join(r['source'] for r in results if r['status'] == 'FAIL'))
