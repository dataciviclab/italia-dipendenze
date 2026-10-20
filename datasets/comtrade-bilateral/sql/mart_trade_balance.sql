-- mart_trade_balance.sql: Trade balance (export - import) per resource × year.
-- Unit values are weighted averages: total value / total net weight.

WITH imports AS (
    SELECT
        year,
        resource,
        SUM(primary_value_usd) AS import_value_usd,
        SUM(COALESCE(net_wgt_kg, 0)) AS import_net_wgt_kg
    FROM clean_input
    WHERE flow = 'M' AND primary_value_usd > 0
    GROUP BY year, resource
),
exports AS (
    SELECT
        year,
        resource,
        SUM(primary_value_usd) AS export_value_usd,
        SUM(COALESCE(net_wgt_kg, 0)) AS export_net_wgt_kg
    FROM clean_input
    WHERE flow = 'X' AND primary_value_usd > 0
    GROUP BY year, resource
)
SELECT
    COALESCE(i.year, e.year) AS year,
    COALESCE(i.resource, e.resource) AS resource,
    ROUND(COALESCE(i.import_value_usd, 0), 0) AS import_value_usd,
    ROUND(COALESCE(i.import_net_wgt_kg, 0), 0) AS import_net_wgt_kg,
    ROUND(
        CASE
            WHEN COALESCE(i.import_net_wgt_kg, 0) > 0
                 AND COALESCE(i.resource, e.resource) <> 'elettricita'
            THEN i.import_value_usd / i.import_net_wgt_kg
            ELSE NULL
        END,
        4
    ) AS import_unit_value_usd_per_kg,
    ROUND(COALESCE(e.export_value_usd, 0), 0) AS export_value_usd,
    ROUND(COALESCE(e.export_net_wgt_kg, 0), 0) AS export_net_wgt_kg,
    ROUND(
        CASE
            WHEN COALESCE(e.export_net_wgt_kg, 0) > 0
                 AND COALESCE(i.resource, e.resource) <> 'elettricita'
            THEN e.export_value_usd / e.export_net_wgt_kg
            ELSE NULL
        END,
        4
    ) AS export_unit_value_usd_per_kg,
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
