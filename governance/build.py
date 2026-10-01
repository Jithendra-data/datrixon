"""Attach governance and canonical semantic values to the existing atomic publication."""
import hashlib
import json
import math
from datetime import datetime, timezone
from governance.registry import validate_registry, ROOT
from governance.contracts import load_contracts, enforce_contracts
from governance.semantic import SemanticLayer
from governance.lineage import build_lineage, validate_lineage
from governance.trust import DIMENSIONS, trust_decision, load_policy, authorize


def at_path(payload, path):
    result = payload
    for part in path.split('.'): result = result[part]
    return result


def build_governance(payload, warehouse, contract_results, audit):
    previous = json.loads((ROOT/'governance/metrics/history/2.0.0.json').read_text())
    registry = validate_registry(previous=previous)
    enforce_contracts(contract_results)
    from validation.publication import enforce_controls
    enforce_controls(payload['data_quality']['results'], synthetic=True)
    if len(payload['reconciliation']) != 5 or any(r['Status'] != 'PASS' or
        max(abs(r['RawValue']-r['FactValue']), abs(r['RawValue']-r['DashboardValue'])) > r['Tolerance']
        for r in payload['reconciliation']):
        raise ValueError('Reconciliation blocked governed publication')
    meta = payload['pipeline_metadata']; cutoff = meta['business_as_of_date']
    semantic = SemanticLayer(warehouse, cutoff, registry)
    values = semantic.export()
    equivalence = []
    for metric in registry['metrics']:
        key = metric['metric_id']
        if key not in values: continue
        result = values[key]['value']; path = metric.get('published_path')
        if path:
            old = at_path(payload, path)
            equal = old is None and result is None or old is not None and result is not None and abs(old-result) <= metric['tolerance']
            equivalence.append(dict(metric=key, warehouse=result, published=old, tolerance=metric['tolerance'], status='PASS' if equal else 'FAIL'))
            if not equal: raise ValueError('Semantic/warehouse/dashboard mismatch: ' + key)
            # Canonical values replace the independently checked legacy aggregate.
            parent = at_path(payload, '.'.join(path.split('.')[:-1]))
            parent[path.split('.')[-1]] = result
    contracts = load_contracts()
    lineage = build_lineage(registry['metrics'], values, contracts)
    validate_lineage(lineage, registry['metrics'])
    decisions = {}
    policy = load_policy()
    for metric in registry['metrics']:
        controls = dict.fromkeys(DIMENSIONS, 'PASS')
        if metric['sensitivity']=='Restricted' or any(metric['domain'] not in policy['roles'].get(role,[]) for role in metric['permitted_roles']):
            controls['access_policy']='FAIL'
        if metric['certification_status'] != 'CERTIFIED_DEMO':
            controls.update(metric_certification='FAIL', lineage='FAIL', semantic_equivalence='FAIL')
        if metric['domain'] == 'Inventory' and meta['expected_exceptions']:
            controls['quality'] = 'WARNING'
        decisions[metric['metric_id']] = trust_decision(metric['metric_id'], controls)
        if metric['certification_status']=='CERTIFIED_DEMO' and authorize(metric,decisions[metric['metric_id']], 'Administrator','publish',policy)['decision']!='ALLOW':
            raise ValueError('Publication policy denied '+metric['metric_id'])
    # Full-population yearly totals are precomputed through the same SQL measure implementation.
    years = sorted({int(r['YearMonth'][:4]) for r in payload['sales_trend']})
    periods = {str(year): {m['metric_id']: semantic.get_metric(m['metric_id'], year)['value']
                          for m in registry['metrics'] if m.get('period_support')} for year in years}
    controls = [dict(control_id=r['ControlID'], name=r['TestName'], description=r['TestName'],
                     category='quality', severity=r['Severity'], asset=r['Domain'], owner='Data Engineering (demo)',
                     logic='validation/run_data_quality_checks.py + arithmetic.py + lifecycle.py', threshold=0,
                     blocking=r['Severity']=='BLOCKING', status='WARNING' if r['Severity']=='EXPECTED_SCENARIO' and r['Status']=='FAIL' else r['Status'],
                     last_run=meta['publication_timestamp'], records_tested=r['RecordsChecked'], failing_rows=r['FailedRecords'],
                     remediation=r.get('ExceptionReason') or 'Inspect source keys and affected batch; correct source then rebuild.',
                     evidence_reference='#quality') for r in payload['data_quality']['results']]
    for dim in DIMENSIONS:
        controls.append(dict(control_id='G-'+dim, name=dim.replace('_',' ').title(), category=dim,
                             severity='BLOCKING', asset='certified metrics', owner='Data Engineering (demo)',
                             logic='governance/build.py', threshold='All certified metrics pass; explicit inventory warning allowed',
                             blocking=True, status='WARNING' if dim=='quality' and meta['expected_exceptions'] else 'PASS',
                             last_run=meta['publication_timestamp'], records_tested=len(values), failing_rows=0,
                             remediation='Inspect metric trust dimensions and rebuild; never override a failed control.', evidence_reference='#trust-center'))
    for result in contract_results:
        controls.append(dict(control_id='CONTRACT-'+result['source'], name=result['source']+' contract',category='contract',
                             severity='BLOCKING', asset=result['source'], owner=result['owner'],logic='governance/contracts.py',
                             threshold='Exact columns, types, keys, nullability, categories, version',blocking=True,status=result['status'],
                             records_tested=result['records_tested'], failing_rows=None,last_run=meta['publication_timestamp'],
                             remediation='Review drift; restore schema or version the producer and consumer together.',evidence_reference='#contracts'))
    products=[]
    for domain in dict.fromkeys(m['domain'] for m in registry['metrics']):
        selected=[m for m in registry['metrics'] if m['domain']==domain and m['certification_status']=='CERTIFIED_DEMO']
        ids=[m['metric_id'] for m in selected]
        products.append(dict(product_id=domain.lower(),name=domain+' Intelligence',owner=domain+' owner (demo)',
            description='Approved synthetic '+domain.lower()+' measures with evidence and explicit definitions.',metrics=ids,
            primary_tables=sorted({t for m in selected for t in m['source_tables']}),sensitivity='Internal (synthetic public demo)',
            status='WARNING' if any(decisions[k]['status']=='WARNING' for k in ids) else 'TRUSTED',
            readiness='Conditional' if any(decisions[k]['status']=='WARNING' for k in ids) else 'Ready',
            consumers=['Dashboard','Governed analytical assistant'],contract_status='PASS',business_cutoff=cutoff))
    audit.record('metric_definitions_validated',asset='metric_registry')
    audit.record('lineage_validated',asset='lineage')
    audit.record('trust_decisions_created')
    payload['governance'] = dict(version='2.0.0',registry=registry,values=values,periods=periods,lineage=lineage,
         decisions=decisions,contracts=dict(definitions=contracts,results=contract_results),policy=load_policy(),
         controls=controls,control_registry_version='2.0.0',products=products,equivalence=equivalence,
         version_identity=dict(run_id=meta['build_id'],dataset_version=meta['dataset_id'],schema_version=meta['contract_version'],
            contract_version=contracts['version'],metric_registry_version=registry['version'],code_version=meta['commit'],
            business_cutoff=cutoff,generation_seed=meta['random_seed'],source_hashes=meta['input_sha256'],
            warehouse_hash=hashlib.sha256(warehouse.read_bytes()).hexdigest(),timestamp=meta['publication_timestamp'],
            publication_hash_location='Matching run_manifest.json; excluded from its own hashed bytes'),
         audit=audit.events,implementation=dict(governance='IMPLEMENTED',assistant='IMPLEMENTED: deterministic analytical engine; no LLM',
            rbac='SIMULATED / DEMONSTRATED: public browser role simulation',enterprise='FUTURE: live ERP, SSO, RLS, private API, durable security audit'),
         freshness=dict(max_age_hours=192,basis='Publication timestamp; weekly batch plus one-day grace',business_cutoff=cutoff,
                        historical_scenario=True))
    validate_governance(payload)
    return payload['governance']


def validate_governance(payload):
    g=payload.get('governance')
    if not g or g.get('version')!='2.0.0': raise ValueError('Missing V2 governance contract')
    registry=validate_registry(g['registry'])
    if registry != validate_registry() or g['policy'] != load_policy() or g['contracts']['definitions'] != load_contracts():
        raise ValueError('Published governance metadata differs from approved repository definitions')
    enforce_contracts(g['contracts']['results'])
    validate_lineage(g['lineage'],registry['metrics'])
    if g['lineage'] != build_lineage(registry['metrics'],g['values'],load_contracts()):
        raise ValueError('Lineage differs from query dependencies and loader mappings')
    for metric in registry['metrics']:
        key=metric['metric_id']
        if metric['certification_status']!='CERTIFIED_DEMO': continue
        decision=g['decisions'].get(key,{})
        expected=trust_decision(key,decision.get('controls',{}))
        if decision!=expected or decision['status']=='BLOCKED': raise ValueError('Trust gate blocked '+key)
        value=g['values'].get(key,{}).get('value')
        if key not in g['values'] or g['values'][key]['query']!=metric['sql'] or set(g['values'][key]['dependencies'])!=set(metric['source_columns']):
            raise ValueError('Semantic query/dependency evidence mismatch: '+key)
        if value is not None and (type(value) not in (int,float) or not math.isfinite(value)):
            raise ValueError('Nonfinite governed measure')
        if metric.get('published_path'):
            published=at_path(payload,metric['published_path'])
            if published!=value: raise ValueError('Published semantic value mismatch: '+key)
    if not g['equivalence'] or any(r['status']!='PASS' or
        (r['warehouse'] is not None and abs(r['warehouse']-r['published'])>r['tolerance']) for r in g['equivalence']):
        raise ValueError('Invalid semantic equivalence evidence')
    if g['version_identity']['dataset_version']!=payload['pipeline_metadata']['dataset_id']:
        raise ValueError('Mismatched data version')
    return True
