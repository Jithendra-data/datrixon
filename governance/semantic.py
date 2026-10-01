"""One SQL implementation per certified metric; no arbitrary SQL input API."""
import sqlite3
from contextlib import closing
from governance.registry import validate_registry
from utils.business_rules import RULES


class SemanticLayer:
    def __init__(self, warehouse, cutoff, registry=None):
        self.warehouse = warehouse
        self.cutoff = cutoff
        self.registry = validate_registry(registry)
        self.metrics = {m['metric_id']: m for m in self.registry['metrics']}

    def get_metric(self, metric_id, year=None):
        metric = self.metrics.get(metric_id)
        if not metric or metric['certification_status'] != 'CERTIFIED_DEMO':
            raise ValueError('Metric is unknown or not certified')
        if year is not None and (type(year) is not int or not 2020 <= year <= 2035 or not metric.get('period_support')):
            raise ValueError('Unsupported period for metric')
        params = dict(cutoff=self.cutoff, start=f'{year}-01-01' if year else '2020-01-01',
                      end=min(self.cutoff, f'{year}-12-31') if year else self.cutoff, **RULES)
        reads = set()
        def authorize(action, table, column, database, trigger):
            if action == sqlite3.SQLITE_READ and column: reads.add((table, column))
            if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE):
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY
        with closing(sqlite3.connect(f'{self.warehouse.resolve().as_uri()}?mode=ro', uri=True)) as db:
            db.set_authorizer(authorize)
            result = db.execute(metric['sql'], params).fetchone()[0]
            db.set_authorizer(None)
            # SQLite can omit USING join keys from authorizer callbacks. The reviewed
            # dependency contract includes those keys and is checked against real DDL.
            for dependency in metric['source_columns']:
                table, column = dependency.split('.')
                if table not in metric['source_tables'] or column not in {r[1] for r in db.execute(f'PRAGMA table_info("{table}")')}:
                    raise ValueError('Invalid declared SQL dependency: ' + dependency)
                reads.add((table,column))
            if not {f'{t}.{c}' for t,c in reads} <= set(metric['source_columns']):
                raise ValueError('SQL has undeclared metric dependencies')
        return dict(metric_id=metric_id, value=float(result) if result is not None else None,
                    year=year, query=metric['sql'], dependencies=[f'{t}.{c}' for t, c in sorted(reads)])

    def export(self):
        return {key: self.get_metric(key) for key, metric in self.metrics.items()
                if metric['certification_status'] == 'CERTIFIED_DEMO'}
