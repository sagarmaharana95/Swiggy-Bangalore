"""Stage 4: export small, dashboard-ready CSVs -> dashboard/data/
Run after run_pipeline.py:  python src/04_export_for_powerbi.py"""
import sqlite3
import numpy as np
import pandas as pd
from config import *

OUT = ROOT / "dashboard" / "data"
OUT.mkdir(parents=True, exist_ok=True)
con = sqlite3.connect(DB_PATH)

orders = pd.read_sql("SELECT * FROM orders", con)
riders = pd.read_sql("SELECT * FROM rider_shifts", con)
orders["period"] = np.where(orders.week <= 6, "Wk 1-6 (normal)", "Wk 7-8 (drop)")
orders["gmv_delivered"] = np.where(orders.status == "delivered", orders.order_value, 0)
orders["delivery_orders"] = orders.delivery_mins.notna().astype(int)
orders["delivery_mins"] = orders.delivery_mins.fillna(0)

# 1) daily_zone.csv  (grain: date x zone x payment_method)
daily = orders.groupby(["order_date", "week", "period", "zone", "payment_method"]).agg(
    placed=("order_id", "size"),
    delivered=("status", lambda s: (s == "delivered").sum()),
    cancelled=("status", lambda s: (s == "cancelled").sum()),
    payment_failed=("status", lambda s: (s == "payment_failed").sum()),
    gmv_delivered=("gmv_delivered", "sum"),
    delivery_mins_sum=("delivery_mins", "sum"),
    delivery_orders=("delivery_orders", "sum"),
).reset_index()
daily.to_csv(OUT / "daily_zone.csv", index=False)

# 2) funnel.csv  (grain: zone x period x stage)
funnel = pd.read_sql("""
    SELECT zone,
           CASE WHEN week <= 6 THEN 'Wk 1-6 (normal)' ELSE 'Wk 7-8 (drop)' END AS period,
           stage, COUNT(DISTINCT session_id) AS sessions
    FROM funnel_events GROUP BY 1, 2, 3""", con)
funnel["stage_order"] = funnel.stage.map({"search": 1, "cart": 2, "payment_initiated": 3,
                                          "payment_success": 4, "fleet_assigned": 5, "delivered": 6})
funnel.to_csv(OUT / "funnel.csv", index=False)

# 3) riders_zone.csv
r = riders.assign(period=np.where(riders.week <= 6, "base", "drop")).groupby(["zone", "period"]).active_riders.mean().unstack()
r["riders_pct_change"] = (r["drop"] / r["base"] - 1) * 100
r = r.rename(columns={"base": "avg_riders_base", "drop": "avg_riders_drop"}).reset_index()
r["constrained_zone"] = np.where(r.riders_pct_change < -20, "Yes", "No")
r.round(2).to_csv(OUT / "riders_zone.csv", index=False)
SHORT = r.loc[r.constrained_zone == "Yes", "zone"].tolist()

# 4) zone_impact.csv  (weekly averages, base vs drop)
w = {"base": 6, "drop": 2}
orders["p"] = np.where(orders.week <= 6, "base", "drop")
zi = orders.groupby(["zone", "p"]).agg(
    placed=("order_id", "size"),
    delivered=("status", lambda s: (s == "delivered").sum()),
    cancelled=("status", lambda s: (s == "cancelled").sum()),
    gmv=("gmv_delivered", "sum")).unstack()
out = pd.DataFrame({"zone": zi.index})
out["delivered_per_wk_base"] = (zi[("delivered", "base")] / 6).values
out["delivered_per_wk_drop"] = (zi[("delivered", "drop")] / 2).values
out["orders_lost_per_wk"] = out.delivered_per_wk_base - out.delivered_per_wk_drop
aov = (zi[("gmv", "base")] / zi[("delivered", "base")]).values
out["gmv_lost_per_wk"] = out.orders_lost_per_wk * aov
out["orders_pct_change"] = (out.delivered_per_wk_drop / out.delivered_per_wk_base - 1) * 100
out["cancel_pct_base"] = (zi[("cancelled", "base")] / zi[("placed", "base")] * 100).values
out["cancel_pct_drop"] = (zi[("cancelled", "drop")] / zi[("placed", "drop")] * 100).values
out = out.merge(r[["zone", "riders_pct_change", "constrained_zone"]], on="zone")
out.round(2).sort_values("gmv_lost_per_wk", ascending=False).to_csv(OUT / "zone_impact.csv", index=False)

# 5) waterfall.csv  (same accounting as the notebook: delivered = placed - cancelled - payment_failed)
orders["short"] = orders.zone.isin(SHORT)
g = orders.groupby(["p", "short"]).agg(
    placed=("order_id", "size"),
    cancelled=("status", lambda s: (s == "cancelled").sum()),
    pay_failed=("status", lambda s: (s == "payment_failed").sum()),
    delivered=("status", lambda s: (s == "delivered").sum()))
g = g.div([w[p] for p, _ in g.index], axis=0)
v = lambda p, s, c: g.loc[(p, s), c]
dip = 1 - v("drop", False, "placed") / v("base", False, "placed")
steps = [
    ("1 General demand dip (competitor promo)", (v("base", True, "placed") + v("base", False, "placed")) * dip),
    ("2 Rider shortage: fewer orders", v("base", True, "placed") * (1 - dip) - v("drop", True, "placed")),
    ("3 Rider shortage: more cancellations", v("drop", True, "cancelled") - v("base", True, "cancelled")),
    ("4 UPI payment failures", g.xs("drop", level=0).pay_failed.sum() - g.xs("base", level=0).pay_failed.sum()),
    ("5 Rain & other cancellations", v("drop", False, "cancelled") - v("base", False, "cancelled")),
]
wf = pd.DataFrame(steps, columns=["cause", "orders_lost_per_wk"])
wf["share_pct"] = wf.orders_lost_per_wk / wf.orders_lost_per_wk.sum() * 100
wf.round(1).to_csv(OUT / "waterfall.csv", index=False)

print(f"[4/4] Exported 5 CSVs to {OUT.relative_to(ROOT)}")
for f in sorted(OUT.glob("*.csv")):
    print(f"   {f.name:18s} {len(pd.read_csv(f)):>5} rows")
print("\nwaterfall.csv:\n", wf.round(1).to_string(index=False))
