"""Stage 1: generate SIMULATED messy order data -> data/raw/messy_orders.csv
Injected root causes (from DROP_DAY): rider shortage, UPI failures, rain, competitor promo."""
import numpy as np
import pandas as pd
from config import *

rng = np.random.default_rng(SEED)
N = N_ORDERS
HOUR_W = np.array([1, 1, 1, 1, 1, 1, 2, 3, 4, 4, 5, 8, 10, 8, 5, 4, 4, 5, 8, 10, 10, 7, 4, 2], dtype=float)

df = pd.DataFrame({
    "order_id": np.arange(100000, 100000 + N),
    "user_id": rng.integers(1, 15000, N),
    "zone": rng.choice(ZONES, N),
    "day": rng.integers(0, DAYS, N),
    "hour": rng.choice(range(24), N, p=HOUR_W / HOUR_W.sum()),
    "payment_method": rng.choice(["UPI", "Card", "Wallet", "COD"], N, p=[.55, .25, .1, .1]),
    "order_value": np.round(rng.lognormal(5.6, 0.5, N), 0),
    "delivery_mins": np.round(rng.normal(32, 8, N).clip(12, 70), 0),
})
df["order_ts"] = START + pd.to_timedelta(df["day"], unit="D") + pd.to_timedelta(
    df["hour"] * 60 + rng.integers(0, 60, N), unit="m")

# Shock 1: rider shortage (fewer orders in 3 zones) + Shock 2: competitor promo (general dip)
drop = (df["day"] >= DROP_DAY) & df["zone"].isin(SHORTAGE_ZONES) & (rng.random(N) < 0.55)
drop |= (df["day"] >= DROP_DAY) & (rng.random(N) < 0.12)
df = df[~drop].copy()

status = np.where(rng.random(len(df)) < 0.04, "cancelled", "delivered")
# Shock 3: UPI failure spike
upi_fail = (df["payment_method"] == "UPI") & (df["day"] >= DROP_DAY) & (rng.random(len(df)) < 0.22)
status = np.where(upi_fail, "payment_failed", status)
# Shock 4: rain on days 45-46
rain = df["day"].isin([45, 46])
status = np.where(rain & (rng.random(len(df)) < 0.15) & (status == "delivered"), "cancelled", status)
df["delivery_mins"] = np.where(rain, df["delivery_mins"] + 18, df["delivery_mins"])
# Shock 1b: rider shortage also hurts service quality (more cancels, slower deliveries) in shortage zones
rng2 = np.random.default_rng(SEED + 1)   # separate stream so new tables don't change the orders above
short_after = (df["zone"].isin(SHORTAGE_ZONES) & (df["day"] >= DROP_DAY)).to_numpy()
status = np.where(short_after & (rng2.random(len(df)) < 0.12) & (status == "delivered"), "cancelled", status)
df["delivery_mins"] = np.where(short_after, df["delivery_mins"] + 10, df["delivery_mins"])
df["status"] = status
df.loc[df["status"] != "delivered", "delivery_mins"] = np.nan

# ---- make it messy ----
m = df.drop(columns=["day", "hour"]).copy()
n = len(m)

def messy_zone(z):
    r = rng.random()
    if r < .08: return z.upper()
    if r < .16: return z.lower() + " "
    if r < .20: return z[:-1]
    return z
m["zone"] = m["zone"].map(messy_zone)

pm_variants = {"UPI": ["UPI", "upi", "Upi ", "GPay"], "Card": ["Card", "card", "CREDIT CARD", "Debit Card"],
               "Wallet": ["Wallet", "wallet", "Paytm Wallet"], "COD": ["COD", "cod", "Cash"]}
m["payment_method"] = m["payment_method"].map(lambda p: rng.choice(pm_variants[p]) if rng.random() < .3 else p)

ts = m["order_ts"].dt.strftime("%Y-%m-%d %H:%M:%S")
alt = rng.random(n) < .15
m["order_ts"] = pd.Series(np.where(alt, m["order_ts"].dt.strftime("%d/%m/%Y %I:%M %p"), ts), index=m.index)

m.loc[rng.random(n) < .03, "order_value"] = np.nan
m.loc[rng.random(n) < .004, "order_value"] = -m["order_value"].abs()
m.loc[rng.random(n) < .002, "order_value"] = 99999
m.loc[rng.random(n) < .002, "delivery_mins"] = 999
m.loc[rng.random(n) < .01, "user_id"] = np.nan
m = pd.concat([m, m.sample(frac=.02, random_state=1)]).sample(frac=1, random_state=2)

m.to_csv(RAW_CSV, index=False)
print(f"[1/3] Generated {len(m):,} messy rows -> {RAW_CSV.relative_to(ROOT)}")


# =====================================================================
# TABLE 2: rider_shifts  (zone x date x hour -> active riders)
# Shock: shortage zones lose ~40% of riders from DROP_DAY
# =====================================================================
n_rows = DAYS * len(ZONES) * 24
r_days = np.repeat(np.arange(DAYS), len(ZONES) * 24)
r_zone = np.tile(np.repeat(ZONES, 24), DAYS)
r_hour = np.tile(np.arange(24), DAYS * len(ZONES))
base = (HOUR_W[r_hour] / HOUR_W.sum()) * 100 / 1.5       # ~1 rider per 1.5 expected orders/hr
riders = np.maximum(rng2.poisson(base), 1)
short = np.isin(r_zone, SHORTAGE_ZONES) & (r_days >= DROP_DAY)
riders = np.where(short, np.maximum(1, np.round(riders * 0.6)), riders).astype(int)
rs = pd.DataFrame({
    "zone": r_zone,
    "date": (START + pd.to_timedelta(r_days, unit="D")).strftime("%Y-%m-%d"),
    "hour": r_hour,
    "week": r_days // 7 + 1,
    "active_riders": riders,
})
rs.to_csv(RIDERS_CSV, index=False)
print(f"      rider_shifts: {len(rs):,} rows -> {RIDERS_CSV.relative_to(ROOT)}")

# =====================================================================
# TABLE 3: funnel_events  (one row per stage reached per session)
# Stages: search -> cart -> payment_initiated -> payment_success -> fleet_assigned -> delivered
# Shocks (from DROP_DAY): competitor promo lowers cart->payment, UPI payments fail more,
#                         shortage zones fail at fleet_assigned
# =====================================================================
S = FUNNEL_SESSIONS
sd = rng2.integers(0, DAYS, S)
sh = rng2.choice(range(24), S, p=HOUR_W / HOUR_W.sum())
sess = pd.DataFrame({
    "session_id": np.arange(1, S + 1),
    "user_id": rng2.integers(1, 15000, S),
    "zone": rng2.choice(ZONES, S),
    "device": rng2.choice(["Android", "iOS", "Web"], S, p=[.6, .3, .1]),
    "payment_method": rng2.choice(["UPI", "Card", "Wallet", "COD"], S, p=[.55, .25, .1, .1]),
})
sess["ts"] = START + pd.to_timedelta(sd, unit="D") + pd.to_timedelta(sh * 60 + rng2.integers(0, 60, S), unit="m")
sess["week"] = sd // 7 + 1
after = sd >= DROP_DAY
in_short = sess["zone"].isin(SHORTAGE_ZONES).to_numpy()

c1 = rng2.random(S) < 0.35                                                   # search -> cart
c2 = c1 & (rng2.random(S) < np.where(after, 0.64, 0.70))                     # cart -> payment (promo effect)
pay_ok = np.where((sess["payment_method"] == "UPI").to_numpy() & after, 0.74, 0.96)
c3 = c2 & (rng2.random(S) < pay_ok)                                          # payment success
fleet_ok = np.where(after & in_short, 0.72, 0.97)
c4 = c3 & (rng2.random(S) < fleet_ok)                                        # fleet allocated
c5 = c4 & (rng2.random(S) < 0.96)                                            # delivered
depth = 1 + c1.astype(int) + c2 + c3 + c4 + c5                               # stages reached (1-6)

stages = ["search", "cart", "payment_initiated", "payment_success", "fleet_assigned", "delivered"]
offsets = [0, 2, 4, 5, 6, 35]   # minutes after session start
frames = []
for k, stage in enumerate(stages):
    mk = depth > k
    f = sess[mk]
    frames.append(pd.DataFrame({
        "session_id": f["session_id"], "user_id": f["user_id"], "zone": f["zone"], "device": f["device"],
        "stage": stage,
        "payment_method": f["payment_method"] if k >= 2 else None,  # known from payment stage onward
        "event_ts": (f["ts"] + pd.Timedelta(minutes=offsets[k])).dt.strftime("%Y-%m-%d %H:%M:%S"),
        "week": f["week"],
    }))
fe = pd.concat(frames, ignore_index=True)
fe.to_csv(FUNNEL_CSV, index=False)
print(f"      funnel_events: {len(fe):,} rows -> {FUNNEL_CSV.relative_to(ROOT)}")
