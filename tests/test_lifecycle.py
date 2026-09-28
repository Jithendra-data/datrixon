import unittest
import pandas as pd
from python.generators.generate_master_data import create_master_data
from python.generators.generate_all import build_transactions
from validation.lifecycle import lifecycle_checks


class LifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        masters=create_master_data()
        cls.sources={**masters, **build_transactions(masters, 250, 100)}

    def check(self, sources):
        results={}
        lifecycle_checks(lambda name:sources[name], lambda name,frame,bad,domain:results.update({name:int(bad.sum())}))
        return results

    def test_generated_lifecycle(self):
        self.assertTrue(all(n==0 for n in self.check(self.sources).values()))

    def test_customer_creation(self):
        sources={k:v.copy() for k,v in self.sources.items()}
        sources['Customer']['CreatedDate']='2030-01-01'
        self.assertGreater(self.check(sources)['Orders before customer creation'],0)

    def test_product_availability(self):
        sources={k:v.copy() for k,v in self.sources.items()}
        sources['Product']['LaunchDate']='2030-01-01'
        result=self.check(sources)
        self.assertGreater(result['Sales before product availability'],0)
        self.assertGreater(result['Invoices before product availability'],0)

    def test_returns(self):
        sources={k:v.copy() for k,v in self.sources.items()}
        sources['CustomerReturn']['ReturnDate']=pd.Timestamp('2020-01-01')
        self.assertGreater(self.check(sources)['Invalid return chronology'],0)

    def test_missing_shipment(self):
        sources={k:v.copy() for k,v in self.sources.items()}
        sources['InventoryTransaction']=sources['InventoryTransaction'].loc[lambda f:f.TransactionType.ne('Sales Shipment')]
        self.assertGreater(self.check(sources)['Shipment inventory consistency'],0)

    def test_invalid_shipment_date(self):
        sources={k:v.copy() for k,v in self.sources.items()}
        sources['SalesOrderHeader']['ActualShipDate']=pd.Timestamp('2020-01-01')
        self.assertGreater(self.check(sources)['Invalid shipment chronology'],0)
