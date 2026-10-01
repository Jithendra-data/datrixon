"""Rebuild an enforced SQLite reference warehouse from validated staging files."""
from pathlib import Path
import sqlite3
from contextlib import closing
import pandas as pd
from utils.config import ROOT

def load_warehouse(source: Path, target: Path) -> dict:
    target.parent.mkdir(parents=True, exist_ok=True)
    candidate = target.with_suffix('.candidate.sqlite')
    candidate.unlink(missing_ok=True)
    read = lambda name: pd.read_csv(source / f'{name}.csv')
    with closing(sqlite3.connect(candidate)) as db:
        db.executescript((ROOT/'sql/sqlite/warehouse.sql').read_text())
        def insert(table, frame):
            clean = frame.astype(object).where(frame.notna(), None)
            columns = ','.join(f'"{c}"' for c in clean.columns)
            db.executemany(f'INSERT INTO {table} ({columns}) VALUES ({",".join("?" for _ in clean.columns)})', clean.itertuples(index=False, name=None))
        for name, columns in {
            'Customer':['CustomerID','CustomerName','Region'],
            'Product':['ProductID','ProductName','CategoryName','UnitCost'],
            'Warehouse':['WarehouseID','WarehouseName'],
            'Vendor':['VendorID','VendorName'], 'SalesRep':['SalesRepID','SalesRepName']
        }.items(): insert('Dim'+name, read(name)[columns])
        dates = pd.date_range('2020-01-01','2035-12-31')
        insert('DimDate', pd.DataFrame({'DateKey':dates.strftime('%Y-%m-%d'),'YearMonth':dates.strftime('%Y-%m')}))
        insert('OrderService', read('SalesOrderHeader')[['SalesOrderID','OrderDate','ActualShipDate','RequestedShipDate','OrderStatus']])
        sales = read('InvoiceLine').merge(read('InvoiceHeader')[['InvoiceID','InvoiceDate','CustomerID','InvoiceStatus']], on='InvoiceID', validate='many_to_one')
        sales = sales.merge(read('SalesOrderHeader')[['SalesOrderID','WarehouseID','SalesRepID']], on='SalesOrderID', validate='many_to_one')
        insert('FactSales',sales.rename(columns={'InvoiceDate':'DateKey'})[['InvoiceID','LineNumber','DateKey','CustomerID','ProductID','WarehouseID','SalesRepID','SalesOrderID','InvoiceStatus','Quantity','Revenue','COGS','DiscountAmount','GrossProfit']])
        insert('FactInventory',read('InventoryTransaction').rename(columns={'TransactionDate':'DateKey'})[['InventoryTransactionID','ProductID','WarehouseID','DateKey','Quantity','TransactionType','ReferenceNumber','UnitCost']])
        po=read('PurchaseOrderLine').merge(read('PurchaseOrderHeader')[['PONumber','VendorID','WarehouseID','CreatedDate','ExpectedDeliveryDate']],on='PONumber',validate='many_to_one')
        insert('FactPurchasing',po.rename(columns={'CreatedDate':'DateKey'})[['PONumber','LineNumber','ProductID','VendorID','WarehouseID','DateKey','ExpectedDeliveryDate','OrderedQuantity','ReceivedQuantity','RemainingQuantity','UnitCost']])
        insert('FactReturns',read('CustomerReturn').rename(columns={'ReturnDate':'DateKey'})[['ReturnID','CustomerID','ProductID','DateKey','InvoiceID','InvoiceLineNumber','ReturnReason','ReturnQuantity','ReturnAmount']])
        insert('PurchaseReceiptEvent',read('PurchaseReceipt').rename(columns={'ReceiptDate':'DateKey'})[['ReceiptID','PONumber','LineNumber','DateKey','QuantityReceived']])
        violations = db.execute('PRAGMA foreign_key_check').fetchall()
        if violations: raise ValueError(f'Warehouse foreign key violations: {violations[:3]}')
        counts={name:db.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0] for name in ['FactSales','FactInventory','FactPurchasing','FactReturns']}
        db.commit()
    candidate.replace(target)
    return counts
