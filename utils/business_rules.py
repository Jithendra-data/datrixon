"""Canonical demonstration policies, exported to the browser with each dataset."""
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd
from utils.config import AS_OF_DATE

RULES = dict(valuable_customer_revenue=25000, inactive_days=60,
             at_risk_days=90, long_inactive_days=180, movement_window_days=90,
             critical_coverage_days=7, low_coverage_days=14,
             watch_coverage_days=30, excess_coverage_days=90,
             money_tolerance=0.01, quantity_tolerance=0.000001)


def business_date(value=None):
    return pd.Timestamp(value or AS_OF_DATE).normalize()


def money_round(value):
    return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def customer_segment(days):
    return 'Inactive >180 days' if days>RULES['long_inactive_days'] else 'At Risk' if days>RULES['at_risk_days'] else 'Active'


def inactive_customers(frame):
    return frame[(frame.LifetimeRevenue>=RULES['valuable_customer_revenue']) & (frame.DaysInactive>RULES['inactive_days'])]


def coverage_risk(quantity, days):
    if quantity<0: return 'Negative ledger'
    if pd.isna(days): return 'No Recent Sales'
    for threshold,label in [('critical_coverage_days','Critical'),('low_coverage_days','High Risk'),('watch_coverage_days','Watch')]:
        if days<RULES[threshold]: return label
    return 'Healthy' if days<=RULES['excess_coverage_days'] else 'Excess'
