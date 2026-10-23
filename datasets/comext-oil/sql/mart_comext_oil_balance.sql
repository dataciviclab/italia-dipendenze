-- mart_comext_oil_balance.sql: import/export value and quantity by oil
-- product group, with unit values and trade position.

WITH imports AS (
    SELECT
        year,
        product_group,
        SUM(value_eur) AS import_value_eur,
        SUM(COALESCE(quantity_100kg, 0)) AS import_quantity_100kg
    FROM clean_input
    WHERE flow = '1' AND value_eur > 0
    GROUP BY year, product_group
),
exports AS (
    SELECT
        year,
        product_group,
        SUM(value_eur) AS export_value_eur,
        SUM(COALESCE(quantity_100kg, 0)) AS export_quantity_100kg
    FROM clean_input
    WHERE flow = '2' AND value_eur > 0
    GROUP BY year, product_group
)
SELECT
    COALESCE(i.year, e.year) AS year,
    COALESCE(i.product_group, e.product_group) AS product_group,
    ROUND(COALESCE(i.import_value_eur, 0), 0) AS import_value_eur,
    ROUND(COALESCE(i.import_quantity_100kg, 0) * 100, 0) AS import_quantity_kg,
    ROUND(
        CASE
            WHEN COALESCE(i.import_quantity_100kg, 0) > 0
            THEN i.import_value_eur / (i.import_quantity_100kg * 100)
            ELSE NULL
        END,
        4
    ) AS import_unit_value_eur_per_kg,
    ROUND(COALESCE(e.export_value_eur, 0), 0) AS export_value_eur,
    ROUND(COALESCE(e.export_quantity_100kg, 0) * 100, 0) AS export_quantity_kg,
    ROUND(
        CASE
            WHEN COALESCE(e.export_quantity_100kg, 0) > 0
            THEN e.export_value_eur / (e.export_quantity_100kg * 100)
            ELSE NULL
        END,
        4
    ) AS export_unit_value_eur_per_kg,
    ROUND(COALESCE(e.export_value_eur, 0) - COALESCE(i.import_value_eur, 0), 0) AS balance_eur,
    CASE
        WHEN COALESCE(e.export_value_eur, 0) - COALESCE(i.import_value_eur, 0) > 0 THEN 'net_exporter'
        WHEN COALESCE(e.export_value_eur, 0) - COALESCE(i.import_value_eur, 0) < 0 THEN 'net_importer'
        ELSE 'balanced'
    END AS trade_position,
    ROUND(
        CASE
            WHEN COALESCE(i.import_value_eur, 0) > 0
            THEN COALESCE(e.export_value_eur, 0) / i.import_value_eur * 100
            ELSE NULL
        END,
        1
    ) AS export_coverage_pct,
    'eurostat_comext' AS source,
    'derived' AS method,
    'verified' AS data_quality
FROM imports i
FULL OUTER JOIN exports e ON i.year = e.year AND i.product_group = e.product_group
WHERE COALESCE(i.year, e.year) IS NOT NULL
ORDER BY year, product_group
