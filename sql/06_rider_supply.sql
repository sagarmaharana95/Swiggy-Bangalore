-- Q6: Avg active riders per zone-hour, before vs after the drop
SELECT zone,
       ROUND(AVG(CASE WHEN week <= 6 THEN active_riders END), 2) AS avg_riders_wk1_6,
       ROUND(AVG(CASE WHEN week >= 7 THEN active_riders END), 2) AS avg_riders_wk7_8,
       ROUND(100.0 * (AVG(CASE WHEN week >= 7 THEN active_riders END)
             / AVG(CASE WHEN week <= 6 THEN active_riders END) - 1), 1) AS pct_change
FROM rider_shifts
GROUP BY zone
ORDER BY pct_change;
