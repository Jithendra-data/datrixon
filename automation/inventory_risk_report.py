"""Shared ledger/coverage rules; not an available-to-promise calculation."""
from etl.operational import inventory_positions
from utils.config import PROCESSED_DIR, RAW_DIR
from utils.helpers import write_csv

def run(source=RAW_DIR):
    rows=inventory_positions(source)
    rows=rows[(rows.PercentSold>.1)|rows.RiskLevel.isin(['Negative ledger','Critical','High Risk'])]
    return rows.rename(columns={'AvailableQty':'AvailableInventory','InboundQty':'InboundQuantity'})

if __name__=='__main__':write_csv(run(),PROCESSED_DIR/'inventory_risk_report.csv')
