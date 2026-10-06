-- Q5: Funnel conversion (stage-to-stage %) before vs after the drop
WITH f AS (
  SELECT CASE WHEN week <= 6 THEN 'wk1-6' ELSE 'wk7-8' END AS period,
         COUNT(DISTINCT CASE WHEN stage = 'search'            THEN session_id END) AS search,
         COUNT(DISTINCT CASE WHEN stage = 'cart'              THEN session_id END) AS cart,
         COUNT(DISTINCT CASE WHEN stage = 'payment_initiated' THEN session_id END) AS pay_init,
         COUNT(DISTINCT CASE WHEN stage = 'payment_success'   THEN session_id END) AS pay_ok,
         COUNT(DISTINCT CASE WHEN stage = 'fleet_assigned'    THEN session_id END) AS fleet,
         COUNT(DISTINCT CASE WHEN stage = 'delivered'         THEN session_id END) AS delivered
  FROM funnel_events GROUP BY period
)
SELECT period,
       ROUND(100.0 * cart / search, 1)      AS search_to_cart,
       ROUND(100.0 * pay_init / cart, 1)    AS cart_to_payment,
       ROUND(100.0 * pay_ok / pay_init, 1)  AS payment_success,
       ROUND(100.0 * fleet / pay_ok, 1)     AS fleet_assigned,
       ROUND(100.0 * delivered / fleet, 1)  AS delivered
FROM f;
