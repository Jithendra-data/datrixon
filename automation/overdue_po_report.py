"""Overdue commitments using the same business cutoff as the dashboard."""
from etl.operational import purchase_positions
from utils.config import PROCESSED_DIR, RAW_DIR
from utils.helpers import write_csv

def run(source=RAW_DIR, as_of=None):
    rows=purchase_positions(source,as_of)
    return rows[(rows.RemainingQuantity>0)&(rows.DaysLate>0)]

if __name__=='__main__':write_csv(run(),PROCESSED_DIR/'overdue_po_report.csv')
