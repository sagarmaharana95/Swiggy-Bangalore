-- Q2: Payment failure rate by method, before vs after the drop (week 1-6 vs 7-8)
SELECT payment_method,
       ROUND(100.0 * SUM(CASE WHEN week <= 6 AND status = 'payment_failed' THEN 1 ELSE 0 END)
             / SUM(week <= 6), 1) AS fail_pct_wk1_6,
       ROUND(100.0 * SUM(CASE WHEN week >= 7 AND status = 'payment_failed' THEN 1 ELSE 0 END)
             / SUM(week >= 7), 1) AS fail_pct_wk7_8
FROM orders
GROUP BY payment_method;
