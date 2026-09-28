"""Versioned publication contract. Append IDs; never recycle their meanings."""
CONTROL_VERSION = 2
CONTRACT_VERSION = 4
NAMES = (
    'Duplicate InvoiceID', 'Duplicate SalesOrderID', 'Duplicate PONumber',
    'Orphan invoice lines', 'Invoices without sales orders', 'Orphan order lines',
    'Missing invoice customers', 'Missing invoice products', 'Duplicate PO lines',
    'Missing PO vendors', 'PO received above ordered', 'Negative invoice quantity',
    'Missing or nonpositive product cost', 'Invalid InvoiceHeader dates',
    'Invalid SalesOrderHeader dates', 'Invalid PurchaseOrderHeader dates',
    'Invalid InventoryTransaction dates', 'Invalid CustomerReturn dates',
    'Invalid inventory warehouse', 'Negative ending on-hand',
    'Orders before customer creation', 'Sales before product availability',
    'Invoices before product availability', 'Invalid return chronology',
    'Shipment inventory consistency', 'Invalid shipment chronology',
    'Invoice posting eligibility', 'Invoice financial arithmetic', 'PO remaining arithmetic',
    'Finite source numeric values', 'Return quantity consistency', 'Receipt line relationships',
    'Receipt quantity reconciliation', 'Receipt inventory consistency', 'Return inventory consistency',
    'Business cutoff coverage', 'Source key integrity',
)
CONTROL_IDS = {name: f'C{i:03}' for i, name in enumerate(NAMES, 1)}


def summarize(rows):
    passed = sum(r['Status'] == 'PASS' for r in rows)
    return dict(total_tests=len(rows), passed_tests=passed,
                failed_tests=len(rows)-passed,
                failed_records=sum(r['FailedRecords'] for r in rows),
                quality_percent=round(100*passed/len(rows), 2) if rows else None)
