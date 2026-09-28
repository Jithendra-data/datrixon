import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from etl.run_pipeline import run
from validation.publication import validate_contract


class FailureStageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        root=Path(cls.temp.name)
        cls.kwargs=dict(raw_dir=root/'raw',processed_dir=root/'processed',web_dir=root/'web')
        cls.payload=run(True,1000,250,**cls.kwargs)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_failed_stages_preserve_publication_and_diagnostics(self):
        public=self.kwargs['web_dir']/'dashboard.json'
        initial=hashlib.sha256(public.read_bytes()).hexdigest()
        for target,stage in [('validate','source_validation'),('clean_file','staging'),('load_warehouse','warehouse'),('reconcile','reconciliation'),('validate_contract','publication_contract')]:
            with self.subTest(stage=stage):
                with patch('etl.run_pipeline.'+target,side_effect=ValueError('Injected failure')):
                    with self.assertRaises(ValueError):run(False,**self.kwargs)
                self.assertEqual(hashlib.sha256(public.read_bytes()).hexdigest(),initial)
                diagnostic=json.loads((self.kwargs['processed_dir']/'failure.json').read_text())
                self.assertEqual(diagnostic['stage'],stage)

    def test_lifecycle_failure_preserves_publication(self):
        import pandas as pd
        path=self.kwargs['raw_dir']/'Customer.csv';original=path.read_bytes()
        public=self.kwargs['web_dir']/'dashboard.json';before=public.read_bytes()
        try:
            rows=pd.read_csv(path);rows['CreatedDate']='2030-01-01';rows.to_csv(path,index=False)
            with self.assertRaisesRegex(ValueError,'Orders before customer creation'):run(False,**self.kwargs)
            self.assertEqual(public.read_bytes(),before)
        finally:path.write_bytes(original)

    def test_corrupted_reconciliation(self):
        payload=copy.deepcopy(self.payload)
        payload['reconciliation'][0]['FactValue']+=100
        with self.assertRaises(ValueError):validate_contract(payload)

    def test_summary_mismatch(self):
        payload=copy.deepcopy(self.payload);payload['data_quality']['summary']['passed_tests']+=1
        with self.assertRaises(ValueError):validate_contract(payload)

    def test_omitted_control(self):
        payload=copy.deepcopy(self.payload);payload['data_quality']['results'].pop()
        with self.assertRaises(ValueError):validate_contract(payload)

    def test_nonfinite_series(self):
        payload=copy.deepcopy(self.payload);payload['sales_trend'][0]['Revenue']=float('nan')
        with self.assertRaises(ValueError):validate_contract(payload)
