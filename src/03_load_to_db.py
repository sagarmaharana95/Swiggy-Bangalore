"""Stage 3: load clean CSV into SQLite and run every .sql file in /sql"""
import sqlite3
import pandas as pd
from config import *

con = sqlite3.connect(DB_PATH)
pd.read_csv(CLEAN_CSV).to_sql("orders", con, if_exists="replace", index=False)
con.execute("CREATE INDEX IF NOT EXISTS idx_zone ON orders(zone)")
con.execute("CREATE INDEX IF NOT EXISTS idx_week ON orders(week)")
pd.read_csv(RIDERS_CSV).to_sql("rider_shifts", con, if_exists="replace", index=False)
pd.read_csv(FUNNEL_CSV, low_memory=False).to_sql("funnel_events", con, if_exists="replace", index=False)
con.execute("CREATE INDEX IF NOT EXISTS idx_rs ON rider_shifts(zone, week)")
con.execute("CREATE INDEX IF NOT EXISTS idx_fe ON funnel_events(week, stage)")
con.execute("CREATE INDEX IF NOT EXISTS idx_fe_zone ON funnel_events(zone, stage)")
print(f"[3/3] Loaded orders, rider_shifts, funnel_events into {DB_PATH.relative_to(ROOT)}")

for f in sorted(SQL_DIR.glob("*.sql")):
    print(f"\n=== {f.name} ===")
    print(pd.read_sql(f.read_text(), con).to_string(index=False))
con.close()
