"""Lineage from SQL authorizer reads plus reviewed loader mappings, never invented paths."""
import json
from governance.registry import ROOT


def build_lineage(metrics, values, contracts):
    mapping = json.loads((ROOT / 'governance/lineage/warehouse_mapping.json').read_text())
    source_columns = {f"{c['source']}.{col}" for c in contracts['sources'] for col in c['columns']}
    edges = []
    def edge(upstream, downstream, transform, module, metric, kind):
        edges.append(dict(upstream_asset=upstream, downstream_asset=downstream,
                          transformation=transform, module=module, metric=metric, dependency_type=kind))
    for metric in metrics:
        key = metric['metric_id']
        if key not in values: continue
        if key in ('gross_profit','gross_margin'):
            for field in ('COGS','Revenue'):
                source='InvoiceLine.'+field
                edge('raw:'+source,'staging:'+source,'Trim strings and normalize dates','etl/clean_data.py',key,'column')
                edge('staging:'+source,'FactSales.'+field,'Enforced invoice-line load','etl/warehouse.py',key,'column')
            edge('FactSales.COGS','FactSales.GrossProfit','Validated identity: GrossProfit = Revenue - COGS',
                 'validation/arithmetic.py',key,'validated_derivation')
            edge('FactSales.Revenue','FactSales.GrossProfit','Validated identity: GrossProfit = Revenue - COGS',
                 'validation/arithmetic.py',key,'validated_derivation')
        for dep in values[key]['dependencies']:
            source = mapping.get(dep)
            if source not in source_columns: raise ValueError('Unmapped SQL lineage: ' + dep)
            edge('raw:' + source, 'staging:' + source, 'Trim strings and normalize dates', 'etl/clean_data.py', key, 'column')
            edge('staging:' + source, dep, 'Enforced key load; joins described in warehouse loader', 'etl/warehouse.py', key, 'column')
            edge(dep, 'metric:' + key, metric['calculation'], 'governance/semantic.py', key, 'calculation')
        for consumer in metric['downstream_consumers']:
            edge('metric:' + key, consumer, 'Approved semantic value or certified reporting series', 'web/js/governance.js', key, 'consumer')
        edge('metric:' + key, 'ai:' + key, 'Governed operation after trust and role checks', 'web/js/governed-ai.js', key, 'answer')
    return edges


def impact(edges, asset):
    found = set(); pending = [asset]
    while pending:
        current = pending.pop()
        for edge in edges:
            target = edge['downstream_asset']
            if edge['upstream_asset'] == current and target not in found:
                found.add(target); pending.append(target)
    return sorted(found)


def validate_lineage(edges, metrics):
    for metric in metrics:
        if metric['certification_status'] != 'CERTIFIED_DEMO': continue
        key = metric['metric_id']; selected = [e for e in edges if e['metric'] == key]
        raw = [e['upstream_asset'] for e in selected if e['upstream_asset'].startswith('raw:')]
        if not raw or not all('ai:' + key in impact(selected, r) for r in raw):
            raise ValueError('Incomplete lineage: ' + key)
    return True
