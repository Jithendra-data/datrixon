"""V2 positive and adversarial governance regression; isolates all build artifacts."""
import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
import pandas as pd
from etl.run_pipeline import run
from governance.registry import load_registry, validate_registry, breaking_changes
from governance.contracts import load_contracts, inspect_frame, enforce_contracts
from governance.semantic import SemanticLayer
from governance.lineage import impact, validate_lineage
from governance.trust import trust_decision, DIMENSIONS, authorize, freshness
from governance.build import validate_governance


class MetadataTests(unittest.TestCase):
    def test_registry_valid(self): self.assertEqual(len(validate_registry()['metrics']),19)
    def test_duplicate_metric(self):
        r=load_registry();r['metrics'].append(r['metrics'][0])
        with self.assertRaises(ValueError):validate_registry(r)
    def test_missing_owner(self):
        r=load_registry();r['metrics'][0]['owner']=''
        with self.assertRaises(ValueError):validate_registry(r)
    def test_certified_without_sql(self):
        r=load_registry();r['metrics'][0]['sql']=None
        with self.assertRaises(ValueError):validate_registry(r)
    def test_breaking_definition_requires_version(self):
        before=load_registry();after=copy.deepcopy(before);after['metrics'][0]['calculation']='changed'
        self.assertIn('revenue',breaking_changes(before,after))
        with self.assertRaises(ValueError):validate_registry(after,before)
        after['metrics'][0]['version']='2.0.0';validate_registry(after,before)
    def test_metric_removal_rejected(self):
        r=load_registry();r['metrics'].pop()
        with self.assertRaises(ValueError):validate_registry(r,load_registry())
    def test_sql_mutation_rejected(self):
        r=load_registry();r['metrics'][0]['sql']='DELETE FROM FactSales'
        with self.assertRaises(ValueError):validate_registry(r)
    def test_unknown_control_fails_closed(self):
        self.assertEqual(trust_decision('revenue',{})['status'],'BLOCKED')
    def test_trust_warning_is_conditional(self):
        c=dict.fromkeys(DIMENSIONS,'PASS');c['quality']='WARNING'
        self.assertEqual(trust_decision('inventory',c)['readiness'],'Conditional')
    def test_each_mandatory_control_blocks(self):
        for key in DIMENSIONS:
            c=dict.fromkeys(DIMENSIONS,'PASS');c[key]='FAIL'
            self.assertEqual(trust_decision('revenue',c)['status'],'BLOCKED')
    def test_rbac(self):
        m=next(m for m in load_registry()['metrics'] if m['metric_id']=='gross_profit');d=trust_decision('gross_profit',dict.fromkeys(DIMENSIONS,'PASS'))
        self.assertEqual(authorize(m,d,'Finance')['decision'],'ALLOW')
        self.assertEqual(authorize(m,d,'Sales')['decision'],'DENY')
        self.assertEqual(authorize(m,d,'Unknown')['decision'],'DENY')
    def test_restricted_denied_even_administrator(self):
        m=load_registry()['metrics'][0];m['sensitivity']='Restricted'
        d=trust_decision('revenue',dict.fromkeys(DIMENSIONS,'PASS'))
        self.assertEqual(authorize(m,d,'Administrator')['decision'],'DENY')
    def test_draft_cannot_answer(self):
        m=next(m for m in load_registry()['metrics'] if m['metric_id']=='net_sales')
        self.assertEqual(authorize(m,trust_decision('net_sales',dict.fromkeys(DIMENSIONS,'PASS')),'Finance')['decision'],'DENY')
    def test_freshness(self):
        now=datetime.now(timezone.utc)
        self.assertEqual(freshness(now.isoformat(),now),'PASS')
        self.assertEqual(freshness((now-timedelta(days=9)).isoformat(),now),'FAIL')
        self.assertEqual(freshness('invalid',now),'FAIL')


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.c=next(c for c in load_contracts()['sources'] if c['source']=='InvoiceHeader')
        self.f=pd.DataFrame([dict(InvoiceID='I1',SalesOrderID='S1',CustomerID='C1',InvoiceDate='2025-01-01',InvoiceStatus='Posted')])
    def test_valid(self):self.assertEqual(inspect_frame(self.f,self.c)['status'],'PASS')
    def test_missing_column(self):self.assertEqual(inspect_frame(self.f.drop(columns=['InvoiceID']),self.c)['status'],'FAIL')
    def test_added_column(self):
        self.f['Unexpected']='x';self.assertEqual(inspect_frame(self.f,self.c)['issues'][0]['severity'],'BREAKING')
    def test_type_change(self):
        self.f['InvoiceDate']='not a date';self.assertEqual(inspect_frame(self.f,self.c)['status'],'FAIL')
    def test_duplicate_key(self):self.assertEqual(inspect_frame(pd.concat([self.f,self.f]),self.c)['status'],'FAIL')
    def test_invalid_category(self):
        self.f['InvoiceStatus']='Draft';self.assertEqual(inspect_frame(self.f,self.c)['status'],'FAIL')
    def test_required_null(self):
        self.f['InvoiceID']=None;self.assertEqual(inspect_frame(self.f,self.c)['status'],'FAIL')
    def test_version_mismatch(self):self.assertEqual(inspect_frame(self.f,self.c,'9.0.0')['status'],'FAIL')
    def test_empty_contract_evidence(self):
        with self.assertRaises(ValueError):enforce_contracts([])


class PipelineGovernanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();root=Path(cls.temp.name)
        cls.kwargs=dict(raw_dir=root/'raw',processed_dir=root/'processed',web_dir=root/'web')
        cls.payload=run(True,1000,250,**cls.kwargs)
        cls.layer=SemanticLayer(root/'processed/warehouse.sqlite',cls.payload['pipeline_metadata']['business_as_of_date'])
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_material_metric_equivalence(self):
        for row in self.payload['governance']['equivalence']:
            with self.subTest(metric=row['metric']):
                self.assertAlmostEqual(self.layer.get_metric(row['metric'])['value'],row['published'],delta=row['tolerance'])
    def test_independent_financial_sql(self):
        db=sqlite3.connect(self.layer.warehouse)
        for metric,col in [('revenue','Revenue'),('gross_profit','GrossProfit'),('units','Quantity')]:
            expected=db.execute(f'SELECT SUM({col}) FROM FactSales').fetchone()[0]
            self.assertAlmostEqual(self.layer.get_metric(metric)['value'],expected)
        db.close()
    def test_sql_user_input_rejected(self):
        for key in ['SELECT * FROM FactSales','revenue; DROP TABLE FactSales','net_sales']:
            with self.assertRaises(ValueError):self.layer.get_metric(key)
    def test_year_parameter_rejected(self):
        with self.assertRaises(ValueError):self.layer.get_metric('revenue',"2025 OR 1=1")
    def test_lineage_and_impact(self):
        g=self.payload['governance'];validate_lineage(g['lineage'],g['registry']['metrics'])
        self.assertIn('ai:gross_margin',impact(g['lineage'],'FactSales.GrossProfit'))
        self.assertIn('ai:gross_margin',impact(g['lineage'],'raw:InvoiceLine.COGS'))
    def test_missing_lineage_blocks(self):
        p=copy.deepcopy(self.payload);p['governance']['lineage']=[]
        with self.assertRaises(ValueError):validate_governance(p)
    def test_missing_trust_control_blocks(self):
        p=copy.deepcopy(self.payload);del p['governance']['decisions']['revenue']['controls']['reconciliation']
        with self.assertRaises(ValueError):validate_governance(p)
    def test_altered_semantic_value_blocks(self):
        p=copy.deepcopy(self.payload);p['governance']['values']['revenue']['value']+=100
        with self.assertRaises(ValueError):validate_governance(p)
    def test_policy_tampering_blocks(self):
        p=copy.deepcopy(self.payload);p['governance']['policy']['roles']['Sales'].append('Finance')
        with self.assertRaises(ValueError):validate_governance(p)
    def test_version_metadata_and_publication_hash(self):
        import hashlib
        g=self.payload['governance'];self.assertEqual(g['version_identity']['dataset_version'],self.payload['pipeline_metadata']['dataset_id'])
        manifest=json.loads((self.kwargs['processed_dir']/'run_manifest.json').read_text())
        self.assertEqual(manifest['published_sha256'],hashlib.sha256((self.kwargs['web_dir']/'dashboard.json').read_bytes()).hexdigest())
        self.assertEqual(len(g['version_identity']['warehouse_hash']),64)
    def test_audit_events(self):
        events={e['event'] for e in self.payload['governance']['audit']}
        self.assertTrue({'pipeline_started','source_validated','contracts_validated','warehouse_loaded','reconciliation_executed','publication_approved'}<=events)
    def test_actual_schema_drift_preserves_publication(self):
        source=self.kwargs['raw_dir']/'Customer.csv';original=source.read_bytes()
        public=self.kwargs['web_dir']/'dashboard.json';before=public.read_bytes()
        try:
            f=pd.read_csv(source);f['Unexpected']='x';f.to_csv(source,index=False)
            with self.assertRaisesRegex(ValueError,'contract'):run(False,**self.kwargs)
            self.assertEqual(public.read_bytes(),before)
        finally:source.write_bytes(original)
    def test_governance_failure_preserves_publication(self):
        public=self.kwargs['web_dir']/'dashboard.json';before=public.read_bytes()
        with patch('etl.run_pipeline.build_governance',side_effect=ValueError('Injected governance failure')):
            with self.assertRaises(ValueError):run(False,**self.kwargs)
        self.assertEqual(public.read_bytes(),before)
