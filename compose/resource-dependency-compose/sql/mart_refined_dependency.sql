-- mart_refined_dependency.sql: refined products with BOTH physical dependency
-- (NRG_BAL_C) and supplier concentration (Comext CN8) in one row.
--
-- This is the product-level answer to "how dependent are we, and on whom"
-- for gasolio, jet and fuel oil. It does not replace mart_resource_dependency
-- (which keeps the HS6 Comtrade aggregate); it adds the CN8 detail.

WITH energy AS (
    SELECT
        year,
        CASE product
            WHEN 'O4671XR5220B' THEN 'gasolio'
            WHEN 'O4661XR5230B' THEN 'cherosene'
            WHEN 'O4680' THEN 'olio_combustibile'
        END AS resource,
        product,
        product_label,
        net_import_dependency_pct AS physical_id_pct,
        supply_ktoe,
        imports_ktoe,
        exports_ktoe
    FROM read_parquet('{support.energy.mart.mart_energy_balance}')
    WHERE product IN ('O4671XR5220B', 'O4661XR5230B', 'O4680')
),
comext AS (
    SELECT
        year,
        CASE product_group WHEN 'jet' THEN 'cherosene' ELSE product_group END AS resource,
        total_import_value_eur,
        import_quantity_kg,
        import_unit_value_eur_per_kg,
        hhi,
        concentration_level,
        top1_supplier,
        top1_share_pct,
        top3_share_pct,
        top5_share_pct,
        num_suppliers
    FROM read_parquet('{support.comext.mart.mart_comext_oil_concentration}')
    WHERE product_group IN ('gasolio', 'jet', 'olio_combustibile')
)
SELECT
    e.year,
    e.resource,
    e.product_label,
    ROUND(e.physical_id_pct, 1) AS physical_id_pct,
    ROUND(e.supply_ktoe, 0) AS supply_ktoe,
    ROUND(e.imports_ktoe, 0) AS imports_ktoe,
    ROUND(e.exports_ktoe, 0) AS exports_ktoe,
    ROUND(c.total_import_value_eur, 0) AS import_value_eur,
    ROUND(c.import_quantity_kg, 0) AS import_quantity_kg,
    ROUND(c.import_unit_value_eur_per_kg, 4) AS import_unit_value_eur_per_kg,
    ROUND(c.hhi, 1) AS hhi,
    c.concentration_level,
    c.top1_supplier,
    c.top1_share_pct,
    c.top3_share_pct,
    c.num_suppliers,
    CASE
        WHEN e.physical_id_pct IS NULL AND c.hhi IS NULL THEN 'insufficient_data'
        WHEN e.physical_id_pct > 90 AND c.hhi > 2500 THEN 'critical_high_concentration'
        WHEN e.physical_id_pct > 90 AND c.hhi <= 2500 THEN 'critical_diversified'
        WHEN e.physical_id_pct BETWEEN 50 AND 90 AND c.hhi > 2500 THEN 'moderate_high_concentration'
        WHEN e.physical_id_pct BETWEEN 50 AND 90 AND c.hhi <= 2500 THEN 'moderate_diversified'
        WHEN e.physical_id_pct < 50 AND c.hhi > 2500 THEN 'low_dependency_high_concentration'
        WHEN e.physical_id_pct < 50 AND c.hhi <= 2500 THEN 'low_dependency_diversified'
        ELSE 'low_dependency'
    END AS risk_profile,
    'compose' AS source,
    'derived' AS method,
    'verified' AS data_quality
FROM energy e
LEFT JOIN comext c ON e.year = c.year AND e.resource = c.resource
ORDER BY e.year, e.resource
