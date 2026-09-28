import copy
import unittest

from validation.registry import CONTROL_IDS, CONTROL_VERSION
from validation.publication import enforce_controls


def valid_controls():
    return [dict(ControlID=i, ControlVersion=CONTROL_VERSION, TestName=n,
                 RecordsChecked=10, FailedRecords=0, PassedRecords=10,
                 PassRate=1.0, Status='PASS') for n, i in CONTROL_IDS.items()]


class RegistryTests(unittest.TestCase):
    def test_complete_registry(self):
        enforce_controls(valid_controls())

    def test_missing(self):
        with self.assertRaises(ValueError): enforce_controls(valid_controls()[1:])

    def test_duplicate(self):
        rows=valid_controls(); rows[-1]=copy.deepcopy(rows[0])
        with self.assertRaises(ValueError): enforce_controls(rows)

    def test_unknown_replacement(self):
        rows=valid_controls(); rows[-1]['ControlID']='arbitrary'
        with self.assertRaises(ValueError): enforce_controls(rows)

    def test_malformed(self):
        for field,value in [('Status','WARNING'),('FailedRecords',-1),('PassedRecords',9),('ControlVersion',999),('PassRate',0.5),('PassRate',float('nan')),('Severity','EXPECTED_SCENARIO')]:
            with self.subTest(field=field):
                rows=valid_controls(); rows[0][field]=value
                with self.assertRaises(ValueError): enforce_controls(rows)

    def test_blocking_failure(self):
        rows=valid_controls(); rows[0].update(Status='FAIL',FailedRecords=1,PassedRecords=9,PassRate=0.9)
        with self.assertRaises(ValueError): enforce_controls(rows)
