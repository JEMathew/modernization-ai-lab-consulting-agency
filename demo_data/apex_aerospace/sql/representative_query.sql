-- Synthetic Oracle SQL representative of the Apex customer analytics workload.
-- This file is display-only input in Sprint 1; no conversion is performed.
SELECT
    c.customer_id,
    c.customer_name,
    TRUNC(o.order_date, 'MM') AS order_month,
    COUNT(DISTINCT o.order_id) AS order_count,
    SUM(o.net_amount) AS net_revenue,
    MAX(s.event_timestamp) AS latest_service_event
FROM customer_dim c
JOIN order_fact o
    ON o.customer_key = c.customer_key
LEFT JOIN service_event_fact s
    ON s.customer_key = c.customer_key
WHERE o.order_date >= ADD_MONTHS(TRUNC(SYSDATE, 'MM'), -12)
  AND c.customer_status = 'ACTIVE'
GROUP BY
    c.customer_id,
    c.customer_name,
    TRUNC(o.order_date, 'MM')
ORDER BY
    order_month DESC,
    net_revenue DESC;
