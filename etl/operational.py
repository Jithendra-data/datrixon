"""Shared operational transformations for dashboard and CSV reports."""
import pandas as pd
from utils.business_rules import business_date, RULES, coverage_risk


def inventory_positions(source, products=None, balances=None, as_of=None):
    cutoff=business_date(as_of)
    tx=pd.read_csv(source/'InventoryTransaction.csv',parse_dates=['TransactionDate'])
    products=pd.read_csv(source/'Product.csv') if products is None else products
    stock=tx.groupby(['ProductID','WarehouseID']).Quantity.sum().rename('AvailableQty').to_frame() if balances is None else balances.set_index(['ProductID','WarehouseID'])[['AvailableQty']]
    shipments=tx[tx.TransactionType.eq('Sales Shipment')].copy()
    shipments['UnitsSold']=shipments.Quantity.abs()
    for days,name in [(30,'Sales30Day'),(RULES['movement_window_days'],'Sales90Day')]:
        selected=shipments[(shipments.TransactionDate>cutoff-pd.Timedelta(days=days)) & (shipments.TransactionDate<=cutoff)]
        stock=stock.join(selected.groupby(['ProductID','WarehouseID']).UnitsSold.sum().rename(name))
    yesterday=shipments[shipments.TransactionDate.eq(cutoff-pd.Timedelta(days=1))].groupby(['ProductID','WarehouseID']).UnitsSold.sum().rename('YesterdayUnitsSold')
    stock=stock.join(yesterday)
    po=pd.read_csv(source/'PurchaseOrderLine.csv').merge(pd.read_csv(source/'PurchaseOrderHeader.csv')[['PONumber','WarehouseID','ExpectedDeliveryDate']],on='PONumber',validate='many_to_one')
    incoming=po[po.RemainingQuantity>0].groupby(['ProductID','WarehouseID']).agg(InboundQty=('RemainingQuantity','sum'),ExpectedPODate=('ExpectedDeliveryDate','min'))
    stock=stock.join(incoming).reset_index()
    for key in ['Sales30Day','Sales90Day','YesterdayUnitsSold','InboundQty']:stock[key]=stock[key].fillna(0)
    stock['DaysOnHand']=stock.AvailableQty.clip(lower=0).div((stock.Sales90Day/RULES['movement_window_days']).where(stock.Sales90Day>0))
    stock['RiskLevel']=[coverage_risk(q,d) for q,d in zip(stock.AvailableQty,stock.DaysOnHand)]
    stock['PercentSold']=stock.YesterdayUnitsSold.div(stock.AvailableQty.where(stock.AvailableQty>0)).fillna(1)
    return stock.merge(products[['ProductID','SKU','ProductName','CategoryName','VendorID','UnitCost']],on='ProductID',validate='many_to_one')


def purchase_positions(source, as_of=None):
    headers=pd.read_csv(source/'PurchaseOrderHeader.csv',parse_dates=['CreatedDate','ExpectedDeliveryDate'])
    lines=pd.read_csv(source/'PurchaseOrderLine.csv')
    vendors=pd.read_csv(source/'Vendor.csv')
    detail=headers.merge(lines,on='PONumber',validate='one_to_many').merge(vendors[['VendorID','VendorName']],on='VendorID',validate='many_to_one')
    detail['RemainingValue']=detail.RemainingQuantity*detail.UnitCost
    detail['DaysLate']=(business_date(as_of)-detail.ExpectedDeliveryDate).dt.days.clip(lower=0)
    return detail
