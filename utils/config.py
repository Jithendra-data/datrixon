"""Central project configuration. Paths are resolved from the repository root."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
WEB_DATA_DIR = ROOT / "web" / "data"
NUM_CUSTOMERS = 5_000
NUM_PRODUCTS = 2_000
NUM_VENDORS = 150
NUM_SALES_REPS = 25
NUM_SALES_ORDERS = 75_000
NUM_PURCHASE_ORDERS = 10_000
START_DATE = "2023-01-01"
AS_OF_DATE = os.getenv("DATRIXON_AS_OF_DATE", "2025-12-31")
from datetime import date
if not date.fromisoformat(START_DATE) <= date.fromisoformat(AS_OF_DATE) <= date(2035,12,31):
    raise ValueError("Business as-of date must be within scenario/date-dimension range")
END_DATE = AS_OF_DATE
# Set DATRIXON_RANDOM_SEED for a new, traceable synthetic scenario. Keeping a
# default preserves reproducibility for local development.
RANDOM_SEED = int(os.getenv("DATRIXON_RANDOM_SEED", os.getenv("NORTHSTAR_RANDOM_SEED", "73041")))
