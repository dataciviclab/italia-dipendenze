-- mart_trade_balance.sql: Trade balance (export - import) per resource × year.

WITH imports AS (
    SELECT year, resource, SUM(primary_value_usd) AS import_value_usd
    FROM clean_input
    WHERE flow = 'M' AND primary_value_usd > 0
    GROUP BY year, resource
),
exports AS (
    SELECT year, resource, SUM(primary_value_usd) AS export_value_usd
    FROM clean_input
    WHERE flow = 'X' AND primary_value_usd > 0
    GROUP BY year, resource
)
SELECT
    COALESCE(i.year, e.year) AS year,
    COALESCE(i.resource, e.resource) AS resource,
    ROUND(COALESCE(i.import_value_usd, 0), 0) AS import_value_usd,
    ROUND(COALESCE(e.export_value_usd, 0), 0) AS export_value_usd,
    ROUND(COALESCE(e.export_value_usd, 0) - COALESCE(i.import_value_usd, 0), 0) AS balance_usd,
    CASE
        WHEN COALESCE(e.export_value_usd, 0) - COALESCE(i.import_value_usd, 0) > 0 THEN 'net_exporter'
        WHEN COALESCE(e.export_value_usd, 0) - COALESCE(i.import_value_usd, 0) < 0 THEN 'net_importer'
        ELSE 'balanced'
    END AS trade_position,
    ROUND(
        CASE
            WHEN COALESCE(i.import_value_usd, 0) > 0
            THEN COALESCE(e.export_value_usd, 0) / i.import_value_usd * 100
            ELSE NULL
        END, 1
    ) AS export_coverage_pct,
    'un_comtrade_derived' AS source,
    'derived' AS method,
    'verified' AS data_quality
FROM imports i
FULL OUTER JOIN exports e ON i.year = e.year AND i.resource = e.resource
WHERE COALESCE(i.year, e.year) IS NOT NULL
ORDER BY year, resource
