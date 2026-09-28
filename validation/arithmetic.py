"""Business invariants independent of published aggregates."""
import numpy as np
import pandas as pd
from utils.business_rules import RULES, business_date, money_round


def arithmetic_checks(read, add):
    ih,il=read('InvoiceHeader'),read('InvoiceLine')
    pol,receipts=read('PurchaseOrderLine'),read('PurchaseReceipt')
    returns,tx=read('CustomerReturn'),read('InventoryTransaction')
    tol=RULES['money_tolerance']+1e-8
    add('Invoice posting eligibility',ih,ih.InvoiceStatus.ne('Posted'),'Finance')
    expected_revenue=(il.Quantity*il.UnitPrice-il.DiscountAmount).map(money_round)
    expected_cogs=(il.Quantity*il.UnitCost).map(money_round)
    bad=(il.Revenue-expected_revenue).abs()>tol
    bad|=(il.COGS-expected_cogs).abs()>tol
    bad|=(il.GrossProfit-(il.Revenue-il.COGS).map(money_round)).abs()>tol
    add('Invoice financial arithmetic',il,bad,'Finance')
    add('PO remaining arithmetic',pol,(pol.RemainingQuantity != pol.OrderedQuantity-pol.ReceivedQuantity) | (pol.RemainingQuantity<0) | (pol.ReceivedQuantity<0),'Purchasing')
    numeric=[]
    for frame,cols in [(il,['Quantity','UnitPrice','DiscountAmount','Revenue','UnitCost','COGS','GrossProfit']),
                       (pol,['OrderedQuantity','ReceivedQuantity','RemainingQuantity','UnitCost','LineAmount']),
                       (returns,['ReturnQuantity','ReturnAmount']), (tx,['Quantity','UnitCost']),
                       (receipts,['QuantityReceived'])]:
        numeric.extend((~np.isfinite(frame[cols].apply(pd.to_numeric,errors='coerce'))).any(axis=1).tolist())
    flags=pd.Series(numeric,dtype=bool)
    add('Finite source numeric values',flags,flags,'Finance')
    ref=returns.merge(il[['InvoiceID','LineNumber','ProductID','Quantity']],left_on=['InvoiceID','InvoiceLineNumber'],right_on=['InvoiceID','LineNumber'],how='left',validate='many_to_one',suffixes=('','_invoice'))
    bad=ref.Quantity.isna() | (ref.ProductID!=ref.ProductID_invoice) | (ref.ReturnQuantity<=0) | (ref.ReturnQuantity>ref.Quantity)
    total=returns.groupby(['InvoiceID','InvoiceLineNumber']).ReturnQuantity.sum()
    sold=il.set_index(['InvoiceID','LineNumber']).Quantity
    excess=total.gt(sold.reindex(total.index))
    bad|=pd.MultiIndex.from_frame(ref[['InvoiceID','InvoiceLineNumber']]).isin(excess[excess].index)
    add('Return quantity consistency',ref,bad,'Returns')
    link=receipts.merge(pol[['PONumber','LineNumber','ProductID']],on=['PONumber','LineNumber'],how='left',indicator=True,validate='many_to_one',suffixes=('','_line'))
    bad=link['_merge'].ne('both') | link.ProductID.ne(link.ProductID_line) | link.ReceiptID.duplicated(keep=False) | link.ReceiptID.isna() | link.QuantityReceived.le(0)
    add('Receipt line relationships',link,bad,'Purchasing')
    actual=receipts.groupby(['PONumber','LineNumber']).QuantityReceived.sum()
    expected=pol.set_index(['PONumber','LineNumber']).ReceivedQuantity
    compare=pd.concat([expected.rename('expected'),actual.rename('actual')],axis=1).fillna(0)
    add('Receipt quantity reconciliation',compare,(compare.expected-compare.actual).abs()>RULES['quantity_tolerance'],'Purchasing')
    for name,kind,source,key,quantity in [
        ('Receipt inventory consistency','Purchase Receipt',receipts,'ReceiptID','QuantityReceived'),
        ('Return inventory consistency','Customer Return',returns,'ReturnID','ReturnQuantity')]:
        moves=tx[tx.TransactionType.eq(kind)].groupby('ReferenceNumber').Quantity.sum()
        expected=source.set_index(key)[quantity]
        pair=pd.concat([expected.rename('expected'),moves.rename('actual')],axis=1)
        add(name,pair,pair.isna().any(axis=1)|(pair.expected-pair.actual).abs().gt(RULES['quantity_tolerance']),'Inventory')
    flags=[]
    for frame,col in [(ih,'InvoiceDate'),(read('SalesOrderHeader'),'OrderDate'),(tx,'TransactionDate'),(returns,'ReturnDate'),(receipts,'ReceiptDate')]:
        dates=pd.to_datetime(frame[col],errors='coerce')
        flags.extend((dates.isna() | dates.gt(business_date())).tolist())
    flags=pd.Series(flags,dtype=bool)
    add('Business cutoff coverage',flags,flags,'Dates')

    keys={'Customer':['CustomerID'],'Product':['ProductID'],'Vendor':['VendorID'],'Warehouse':['WarehouseID'],'SalesRep':['SalesRepID'],
          'SalesOrderHeader':['SalesOrderID'],'SalesOrderLine':['SalesOrderID','LineNumber'],
          'InvoiceHeader':['InvoiceID'],'InvoiceLine':['InvoiceID','LineNumber'],
          'PurchaseOrderHeader':['PONumber'],'PurchaseOrderLine':['PONumber','LineNumber'],
          'InventoryTransaction':['InventoryTransactionID'],'CustomerReturn':['ReturnID'],'PurchaseReceipt':['ReceiptID']}
    flags=[]
    for table,columns in keys.items():
        frame=read(table)
        flags.extend((frame[columns].isna().any(axis=1)|frame.duplicated(columns,keep=False)).tolist())
    flags=pd.Series(flags,dtype=bool)
    add('Source key integrity',flags,flags,'Keys')
