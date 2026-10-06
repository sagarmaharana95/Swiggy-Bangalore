"""Shared settings. All paths are relative to project root."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_CSV = ROOT / "data" / "raw" / "messy_orders.csv"
CLEAN_CSV = ROOT / "data" / "processed" / "clean_orders.csv"
RIDERS_CSV = ROOT / "data" / "raw" / "rider_shifts.csv"
FUNNEL_CSV = ROOT / "data" / "raw" / "funnel_events.csv"
DB_PATH = ROOT / "db" / "swiggy.db"
SQL_DIR = ROOT / "sql"

SEED = 42
N_ORDERS = 60_000       # raise to 300_000+ for a bigger dataset
FUNNEL_SESSIONS = 250_000   # app sessions (search -> delivered funnel)
DAYS = 56               # 8 weeks
DROP_DAY = 42           # drop starts in week 7
START = pd.Timestamp("2026-08-03")

ZONES = ["Koramangala", "Indiranagar", "Whitefield", "HSR Layout", "BTM Layout",
         "Jayanagar", "Marathahalli", "Electronic City", "HBR Layout", "Malleshwaram"]
SHORTAGE_ZONES = ["Whitefield", "Marathahalli", "Electronic City"]
