import unittest
from python.generators.generate_master_data import create_master_data
from python.generators.generate_all import build_transactions
from validation.arithmetic import arithmetic_checks
from utils.business_rules import business_date, money_round, coverage_risk


class ArithmeticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        masters=create_master_data()
        cls.sources={**masters,**build_transactions(masters,250,100)}

    def checks(self, sources):
        results={}
        arithmetic_checks(lambda name:sources[name],lambda name,frame,bad,domain:results.update({name:int(bad.sum())}))
        return results

    def test_valid_generated_arithmetic_and_partial_receipts(self):
        self.assertTrue(all(v==0 for v in self.checks(self.sources).values()))
        self.assertGreater(self.sources['PurchaseReceipt'].duplicated(['PONumber','LineNumber']).sum(),0)

    def test_financial_corruption(self):
        sources={k:v.copy() for k,v in self.sources.items()}
        sources['InvoiceLine'].loc[0,'Revenue']+=100
        self.assertGreater(self.checks(sources)['Invoice financial arithmetic'],0)

    def test_posting_status(self):
        sources={k:v.copy() for k,v in self.sources.items()}
        sources['InvoiceHeader'].loc[0,'InvoiceStatus']='Draft'
        self.assertEqual(self.checks(sources)['Invoice posting eligibility'],1)

    def test_receipt_reference_and_quantity(self):
        sources={k:v.copy() for k,v in self.sources.items()}
        sources['PurchaseReceipt'].loc[0,'LineNumber']=999
        result=self.checks(sources)
        self.assertGreater(result['Receipt line relationships'],0)
        self.assertGreater(result['Receipt quantity reconciliation'],0)

    def test_return_quantity(self):
        sources={k:v.copy() for k,v in self.sources.items()}
        sources['CustomerReturn'].loc[0,'ReturnQuantity']=100000
        self.assertGreater(self.checks(sources)['Return quantity consistency'],0)

    def test_finite_values(self):
        sources={k:v.copy() for k,v in self.sources.items()}
        sources['InvoiceLine'].loc[0,'Revenue']=float('nan')
        self.assertGreater(self.checks(sources)['Finite source numeric values'],0)

    def test_rounding_and_date_policy(self):
        self.assertEqual(money_round('1.005'),1.01)
        self.assertEqual(money_round('-1.005'),-1.01)
        self.assertEqual(str(business_date('2024-06-30').date()),'2024-06-30')
        self.assertEqual(coverage_risk(-1,0),'Negative ledger')

    def test_duplicate_source_grain(self):
        import pandas as pd
        sources={k:v.copy() for k,v in self.sources.items()}
        sources['InvoiceLine']=pd.concat([sources['InvoiceLine'],sources['InvoiceLine'].iloc[[0]]],ignore_index=True)
        # The return join rejects ambiguous invoice lines even before key reporting.
        with self.assertRaises(pd.errors.MergeError):self.checks(sources)
