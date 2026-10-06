"""Stage 2: clean messy data -> data/processed/clean_orders.csv"""
import numpy as np
import pandas as pd
from config import *

c = pd.read_csv(RAW_CSV)
rows_before = len(c)

print("--- Data quality report (BEFORE) ---")
print("rows            :", rows_before)
print("duplicate ids   :", c.duplicated(subset="order_id").sum())
print("nulls           :", c.isna().sum()[c.isna().sum() > 0].to_dict())
print("unique zones    :", c["zone"].nunique(), "| payment variants:", c["payment_method"].nunique())

# 1. duplicates
c = c.drop_duplicates(subset="order_id")

# 2. zone names
c["zone"] = c["zone"].str.strip().str.title()
c["zone"] = c["zone"].replace({z[:-1].title(): z for z in ZONES})
c["zone"] = c["zone"].replace({"Hsr Layout": "HSR Layout", "Btm Layout": "BTM Layout", "Hbr Layout": "HBR Layout"})

# 3. payment methods
pm_map = {"upi": "UPI", "gpay": "UPI", "card": "Card", "credit card": "Card", "debit card": "Card",
          "wallet": "Wallet", "paytm wallet": "Wallet", "cod": "COD", "cash": "COD"}
c["payment_method"] = c["payment_method"].str.strip().str.lower().map(pm_map)

# 4. timestamps: parse each known format explicitly (format="mixed" can silently mis-read dd/mm vs mm/dd)
t1 = pd.to_datetime(c["order_ts"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
t2 = pd.to_datetime(c["order_ts"], format="%d/%m/%Y %I:%M %p", errors="coerce")
c["order_ts"] = t1.fillna(t2)
c = c.dropna(subset=["order_ts"])

# 5. values
c["order_value"] = c["order_value"].abs()
cap = c["order_value"].quantile(.99)
c.loc[c["order_value"] > cap, "order_value"] = np.nan
c["order_value"] = c["order_value"].fillna(c.groupby("zone")["order_value"].transform("median"))
c.loc[c["delivery_mins"] > 120, "delivery_mins"] = np.nan
c["user_id"] = c["user_id"].fillna(-1).astype(int)   # -1 = unknown user

# 6. derived columns
c["week"] = (c["order_ts"] - START).dt.days // 7 + 1
c["order_date"] = c["order_ts"].dt.strftime("%Y-%m-%d")
c["order_ts"] = c["order_ts"].dt.strftime("%Y-%m-%d %H:%M:%S")

# 7. validation checks (fail loudly if cleaning is wrong)
assert c["order_id"].is_unique
assert c["zone"].nunique() == len(ZONES), "zone cleaning incomplete"
assert c["payment_method"].notna().all(), "unmapped payment method"
assert c["week"].between(1, DAYS // 7).all(), "week numbers out of range - check date parsing"

c.to_csv(CLEAN_CSV, index=False)
print(f"[2/3] Cleaned: {rows_before:,} -> {len(c):,} rows -> {CLEAN_CSV.relative_to(ROOT)}")
