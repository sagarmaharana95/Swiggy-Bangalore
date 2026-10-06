# Insight Memo: Bangalore Order Drop (1 page)

**TL;DR:** Delivered orders fell ~40% (about 7,230 to 4,374 per week) from week 7. Four causes explain it: rider shortage in 3 zones (~40%), a platform-wide demand dip (~37%), UPI payment failures (~23%) and a small rain effect. Fixing UPI routing first and adding rider incentives in the 3 constrained zones could recover ~1,470 orders (~Rs 4.4 lakh GMV) per week.

## What happened
- Weekly delivered orders: ~7,230 (weeks 1-6 avg) to ~4,374 (weeks 7-8 avg), a **39.5% fall**.
- ~2,856 orders and ~Rs 8.5 lakh GMV lost per week.
- Data validation: no missing days, no duplicate order IDs, so this is a real drop, not a tracking bug.

## Why (root cause attribution)
| Cause | Evidence | Share of drop |
|---|---|---|
| Rider shortage (Whitefield, Marathahalli, Electronic City) | Riders down 31-37% in these zones; cancellations 3.8% to 14.6%; fleet assignment 97% to ~72% | ~40% |
| Platform-wide demand dip (e.g. competitor promo) | Orders fell in unaffected zones too; cart-to-payment 70% to 64% | ~37% |
| UPI payment failures | UPI failure rate 0% to 22%; other methods flat | ~23% |
| Rain (2 days) | Delivery time 51 vs 34 min; cancellations 17.7% on those days | <1% weekly |

All effects significant (chi-square / Welch t-test, p < 0.001).

## Recommendations (priority order)
| Fix | Effort | Orders recovered / week | GMV recovered / week |
|---|---|---|---|
| UPI fallback routing + retry to backup gateway | Low | ~519 | ~Rs 1.6 lakh |
| Rider incentives / surge pay in the 3 constrained zones | Medium | ~676 | ~Rs 2.0 lakh |
| Targeted win-back promo vs competitor | High | ~267 | ~Rs 0.8 lakh |
| Rain-day surge pay + rider bonus | Low | ~7 | negligible |
| **Total** | | **~1,470 (~51% of drop)** | **~Rs 4.4 lakh** |

## Assumptions & limitations
- Data is **simulated** (Swiggy data is not public); four causes were injected so the method can be checked against ground truth.
- Recovery rates (UPI 80%, rider 60%, promo 25%, rain 50%) are assumptions. In a real project, validate fixes with an A/B test or holdout zones.
- Two methods cross-checked the rider-shortage effect: waterfall attribution (~40%) and counterfactual (~35%).
