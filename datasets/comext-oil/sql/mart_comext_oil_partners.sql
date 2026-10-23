-- mart_comext_oil_partners.sql: partner-level values and shares by oil product
-- group, flow and year.

WITH totals AS (
    SELECT
        year,
        product_group,
        flow,
        SUM(value_eur) AS total_value_eur
    FROM clean_input
    GROUP BY year, product_group, flow
)
SELECT
    c.year,
    c.product_group,
    c.flow,
    c.flow_label,
    c.partner_code,
    c.partner_name,
    ROUND(c.value_eur, 0) AS value_eur,
    ROUND(c.quantity_100kg * 100, 0) AS quantity_kg,
    ROUND(
        CASE
            WHEN c.quantity_100kg > 0
            THEN c.value_eur / (c.quantity_100kg * 100)
            ELSE NULL
        END,
        4
    ) AS unit_value_eur_per_kg,
    ROUND(c.value_eur / t.total_value_eur * 100, 1) AS share_pct,
    'eurostat_comext' AS source,
    'derived' AS method,
    'verified' AS data_quality
FROM clean_input c
JOIN totals t ON c.year = t.year AND c.product_group = t.product_group AND c.flow = t.flow
ORDER BY c.year, c.product_group, c.flow, c.value_eur DESC
