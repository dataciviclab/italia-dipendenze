-- mart_energy_vs_trade.sql: Compare physical ID with supplier concentration.
--
-- physical_id_pct is the NET import dependency from mart_energy_balance.
-- Coal has no bilateral trade resource in Comtrade: it stays in the table on
-- purpose, so a missing HHI is declared as "trade missing", not as low risk.
-- Naphtha is included because its GIC is non-positive (secondary product):
-- it exercises the dual-null branch and must stay "insufficient_data".

WITH energy AS (
    SELECT
        year,
        product,
        product_label,
        net_import_dependency_pct AS physical_id_pct,
        apparent_consumption_ktoe,
        gic_ktoe,
        production_ktoe,
        imports_ktoe
    FROM read_parquet('{support.energy.mart.mart_energy_balance}')
    WHERE product IN ('G3000', 'C0000X0350-0370', 'E7000', 'O4640', 'O4100_TOT', 'O4000XBIO')
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
    UNION ALL SELECT 'E7000', 'elettricita'
    UNION ALL SELECT 'O4640', 'nafta'
    UNION ALL SELECT 'O4100_TOT', 'petrolio_greggio'
    UNION ALL SELECT 'O4000XBIO', 'prodotti_petroliferi'
)
SELECT
    e.year,
    e.product,
    e.product_label,
    rm.resource,
    ROUND(e.physical_id_pct, 1) AS physical_id_pct,
    ROUND(e.apparent_consumption_ktoe, 0) AS apparent_consumption_ktoe,
    ROUND(e.gic_ktoe, 0) AS gic_ktoe,
    ROUND(e.production_ktoe, 0) AS production_ktoe,
    ROUND(e.imports_ktoe, 0) AS imports_ktoe,
    ROUND(t.hhi, 1) AS trade_hhi,
    t.concentration_level AS trade_concentration,
    t.top1_supplier,
    t.top1_share_pct,
    t.top3_share_pct,
    t.num_suppliers,
    -- NULL ≠ bassa dipendenza: se manca un lato (o entrambi), lo dichiariamo.
    CASE
        WHEN e.physical_id_pct IS NULL AND t.hhi IS NULL THEN 'insufficient_data'
        WHEN e.physical_id_pct > 90 AND t.hhi > 2500 THEN 'critical_high_concentration'
        WHEN e.physical_id_pct > 90 AND t.hhi <= 2500 THEN 'critical_diversified'
        WHEN e.physical_id_pct BETWEEN 50 AND 90 AND t.hhi > 2500 THEN 'moderate_high_concentration'
        WHEN e.physical_id_pct BETWEEN 50 AND 90 AND t.hhi <= 2500 THEN 'moderate_diversified'
        WHEN e.physical_id_pct > 90 AND t.hhi IS NULL THEN 'high_dependency_trade_missing'
        WHEN e.physical_id_pct BETWEEN 50 AND 90 AND t.hhi IS NULL THEN 'moderate_dependency_trade_missing'
        WHEN e.physical_id_pct < 50 AND t.hhi IS NULL THEN 'low_dependency_trade_missing'
        WHEN e.physical_id_pct IS NULL AND t.hhi > 2500 THEN 'trade_high_concentration_only'
        WHEN e.physical_id_pct IS NULL AND t.hhi IS NOT NULL THEN 'trade_only'
        WHEN e.physical_id_pct < 50 AND t.hhi > 2500 THEN 'low_dependency_high_concentration'
        WHEN e.physical_id_pct < 50 AND t.hhi <= 2500 THEN 'low_dependency_diversified'
        ELSE 'low_dependency'
    END AS risk_profile,
    'compose' AS source,
    'derived' AS method,
    'verified' AS data_quality
FROM energy e
LEFT JOIN resource_map rm ON e.product = rm.product
LEFT JOIN trade t ON e.year = t.year AND rm.resource = t.resource
ORDER BY e.year, e.product
