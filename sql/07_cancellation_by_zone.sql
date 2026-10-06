SELECT zone,
       ROUND(100.0 * SUM(CASE WHEN week <= 6 AND status = 'cancelled' THEN 1 ELSE 0 END)
             / SUM(week <= 6), 1) AS cancel_pct_wk1_6,
       ROUND(100.0 * SUM(CASE WHEN week >= 7 AND status = 'cancelled' THEN 1 ELSE 0 END)
             / SUM(week >= 7), 1) AS cancel_pct_wk7_8
FROM orders
GROUP BY zone
ORDER BY cancel_pct_wk7_8 DESC;