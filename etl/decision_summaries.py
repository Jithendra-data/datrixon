"""Decision evidence computed before browser extracts are capped."""
import pandas as pd
from utils.business_rules import business_date, RULES


def add_decision_summaries(payload, stock, customers, sales, orders, receipts):
    shipped=orders.dropna(subset=['ActualShipDate']).copy()
    shipped['OnTime']=shipped.ActualShipDate <= pd.to_datetime(shipped.RequestedShipDate)
    service=shipped.groupby('WarehouseID').agg(
        MedianShipDays=('OrderToShipDays','median'),
        P90ShipDays=('OrderToShipDays',lambda s:s.quantile(.9)),
        OnTimeOrders=('OnTime','sum'), OnTimeRate=('OnTime','mean'))
    for row in payload['warehouse_performance']:
        if row['WarehouseID'] in service.index:
            row.update(service.loc[row['WarehouseID']].to_dict())
    vendor=receipts.groupby('VendorID').agg(ReceiptEvents=('ActualLeadDays','size'),
        MeanLeadDays=('ActualLeadDays','mean'),MedianLeadDays=('ActualLeadDays','median'),
        P90LeadDays=('ActualLeadDays',lambda s:s.quantile(.9)))
    for row in payload['vendor_performance']:
        if row['VendorID'] in vendor.index: row.update(vendor.loc[row['VendorID']].to_dict())
    categories=payload['sales_by_category']
    positive=stock.AvailableQty.clip(lower=0)*stock.UnitCost
    cutoff=business_date();year=cutoff.year
    comparable=sales[(sales.InvoiceDate.dt.year.eq(year)) | (sales.InvoiceDate<=cutoff-pd.DateOffset(years=1))]
    customer_year=comparable.assign(Year=sales.InvoiceDate.dt.year).groupby(['CustomerID','Year']).Revenue.sum().unstack(fill_value=0)
    prior=customer_year.get(year-1,pd.Series(0,index=customer_year.index))
    current=customer_year.get(year,pd.Series(0,index=customer_year.index))
    payload['decision_evidence']={
        'sales':{'strongest_category':max(categories,key=lambda r:r['GrossMarginPct']),
                 'weakest_category':min(categories,key=lambda r:r['GrossMarginPct'])},
        'customers':{'comparison_year':year,'prior_year':year-1,'comparison_through':str(cutoff.date()),
                     'declining_accounts':int(((current<prior)&(prior>0)).sum()),
                     'prior_active_accounts':int((prior>0).sum())},
        'inventory':{'negative_positions':int((stock.AvailableQty<0).sum()),
                     'no_shipments_positions':int(((stock.AvailableQty>0)&(stock.Sales90Day==0)).sum()),
                     'excess_positions':int((pd.to_numeric(stock.DaysOnHand)>RULES["excess_coverage_days"]).sum()),
                     'low_coverage_positions':int(((stock.AvailableQty>=0)&(stock.Sales90Day>0)&(pd.to_numeric(stock.DaysOnHand)<RULES["low_coverage_days"])).sum()),
                     'positions':len(stock)},
        'purchasing':{'receipt_events':len(receipts),
                      'ordered_units':sum(r['OrderedQuantity'] for r in payload['vendor_performance']),
                      'received_units':sum(r['ReceivedQuantity'] for r in payload['vendor_performance'])},
        'operations':{'shipped_orders':len(shipped),'on_time_orders':int(shipped.OnTime.sum()),
                      'mean_days':float(shipped.OrderToShipDays.mean()),
                      'median_days':float(shipped.OrderToShipDays.median()),
                      'p90_days':float(shipped.OrderToShipDays.quantile(.9))}}
