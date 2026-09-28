"""Cross-entity lifecycle checks over source records, before normalization."""
import pandas as pd


def lifecycle_checks(read, add):
    sh, sl = read('SalesOrderHeader'), read('SalesOrderLine')
    ih, il = read('InvoiceHeader'), read('InvoiceLine')
    customers, products = read('Customer'), read('Product')
    tx, returns = read('InventoryTransaction'), read('CustomerReturn')
    def date(frame, column):
        return pd.to_datetime(frame[column], errors='coerce')
    orders = sh.merge(customers[['CustomerID', 'CreatedDate']], on='CustomerID', how='left', validate='many_to_one')
    bad = date(orders, 'CreatedDate').isna() | (date(orders, 'OrderDate') < date(orders, 'CreatedDate'))
    add('Orders before customer creation', orders, bad, 'Lifecycle')
    for name, lines, headers, key, event_date in [
        ('Sales before product availability', sl, sh, 'SalesOrderID', 'OrderDate'),
        ('Invoices before product availability', il, ih, 'InvoiceID', 'InvoiceDate'),
    ]:
        joined = lines.merge(headers[[key, event_date]], on=key, how='left', validate='many_to_one').merge(products[['ProductID', 'LaunchDate']], on='ProductID', how='left', validate='many_to_one')
        bad = date(joined, 'LaunchDate').isna() | date(joined, event_date).isna() | (date(joined, event_date) < date(joined, 'LaunchDate'))
        add(name, joined, bad, 'Lifecycle')
    ret = returns.merge(ih[['InvoiceID', 'InvoiceDate']], on='InvoiceID', how='left', validate='many_to_one')
    add('Invalid return chronology', ret, date(ret, 'InvoiceDate').isna() | date(ret, 'ReturnDate').isna() | (date(ret, 'ReturnDate') < date(ret, 'InvoiceDate')), 'Lifecycle')
    shipped = sh[sh.OrderStatus.isin(['Shipped', 'Invoiced'])]
    add('Invalid shipment chronology', shipped, date(shipped, 'ActualShipDate').isna() | (date(shipped, 'ActualShipDate') < date(shipped, 'OrderDate')), 'Lifecycle')
    expected = sl.merge(shipped[['SalesOrderID', 'WarehouseID']], on='SalesOrderID').groupby(['SalesOrderID', 'ProductID', 'WarehouseID']).Quantity.sum()
    actual = tx[tx.TransactionType.eq('Sales Shipment')].rename(columns={'ReferenceNumber': 'SalesOrderID'}).groupby(['SalesOrderID', 'ProductID', 'WarehouseID']).Quantity.sum().mul(-1)
    compare = pd.concat([expected.rename('expected'), actual.rename('actual')], axis=1)
    add('Shipment inventory consistency', compare, compare.isna().any(axis=1) | ((compare.expected-compare.actual).abs() > 0.000001), 'Lifecycle')
