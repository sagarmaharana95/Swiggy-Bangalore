-- Q4: Anomaly detection - days where a zone's orders fall >2 std-dev below its trailing 28-day mean
-- (SQLite has no STDDEV, so variance = E[x^2] - E[x]^2 and we compare squared distance)
WITH daily AS (
  SELECT zone, order_date, COUNT(*) AS orders
  FROM orders WHERE status = 'delivered'
  GROUP BY zone, order_date
),
stats AS (
  SELECT *,
    AVG(orders) OVER w AS mean_28d,
    AVG(orders * orders) OVER w - AVG(orders) OVER w * AVG(orders) OVER w AS var_28d
  FROM daily
  WINDOW w AS (PARTITION BY zone ORDER BY order_date ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING)
)
SELECT zone, COUNT(*) AS anomaly_days
FROM stats
WHERE var_28d > 0 AND orders < mean_28d AND (orders - mean_28d) * (orders - mean_28d) > 4 * var_28d
GROUP BY zone
ORDER BY anomaly_days DESC;
