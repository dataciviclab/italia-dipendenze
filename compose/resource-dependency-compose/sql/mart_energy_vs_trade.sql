-- mart_energy_vs_trade.sql: Compare physical ID with supplier concentration.
-- Only includes products that have BOTH energy balance AND bilateral trade data.

WITH energy AS (
    SELECT
        year,
        product,
        product_label,
        gross_import_dependency_pct AS physical_id_pct,
        apparent_consumption_ktoe,
        production_ktoe,
        imports_ktoe
    FROM read_parquet('{support.energy.mart.mart_energy_balance}')
    WHERE product IN ('G3000', 'C0000X0350-0370', 'O4630', 'E7000')
),
trade AS (
    SELECT
        year,
        resource,
        hhi,
        concentration_level,
        top1_supplier,
        top1_share_pct,
        top3_share_pct,
        num_suppliers
    FROM read_parquet('{support.trade.mart.mart_trade_concentration}')
),
resource_map AS (
    SELECT 'G3000' AS product, 'gas' AS resource
    UNION ALL SELECT 'C0000X0350-0370', 'carbone'
    UNION ALL SELECT 'O4630', 'prodotti_petroliferi'
    UNION ALL SELECT 'E7000', 'elettricita'
)
SELECT
    e.year,
    e.product,
    e.product_label,
    rm.resource,
    ROUND(e.physical_id_pct, 1) AS physical_id_pct,
    ROUND(e.apparent_consumption_ktoe, 0) AS apparent_consumption_ktoe,
    ROUND(e.production_ktoe, 0) AS production_ktoe,
    ROUND(e.imports_ktoe, 0) AS imports_ktoe,
    ROUND(t.hhi, 1) AS trade_hhi,
    t.concentration_level AS trade_concentration,
    t.top1_supplier,
    t.top1_share_pct,
    t.top3_share_pct,
    t.num_suppliers,
    CASE
        WHEN e.physical_id_pct > 90 AND t.hhi > 2500 THEN 'critical_high_concentration'
        WHEN e.physical_id_pct > 90 AND t.hhi <= 2500 THEN 'critical_diversified'
        WHEN e.physical_id_pct BETWEEN 50 AND 90 AND t.hhi > 2500 THEN 'moderate_high_concentration'
        WHEN e.physical_id_pct BETWEEN 50 AND 90 THEN 'moderate_diversified'
        ELSE 'low_dependency'
    END AS risk_profile,
    'compose' AS source,
    'derived' AS method,
    'verified' AS data_quality
FROM energy e
LEFT JOIN resource_map rm ON e.product = rm.product
LEFT JOIN trade t ON e.year = t.year AND rm.resource = t.resource
ORDER BY e.year, e.product
