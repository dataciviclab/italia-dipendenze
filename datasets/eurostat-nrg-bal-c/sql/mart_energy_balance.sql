-- mart_energy_balance.sql: Italy energy balance pivoted by product x year.

WITH pivoted AS (
    SELECT
        year,
        product,
        product_label,
        MAX(CASE WHEN indicator = 'PPRD' THEN value_ktoe END) AS production_ktoe,
        MAX(CASE WHEN indicator = 'IMP' THEN value_ktoe END) AS imports_ktoe,
        MAX(CASE WHEN indicator = 'EXP' THEN value_ktoe END) AS exports_ktoe,
        MAX(CASE WHEN indicator = 'STK_CHG' THEN value_ktoe END) AS stock_change_ktoe
    FROM clean_input
    WHERE indicator IN ('PPRD', 'IMP', 'EXP', 'STK_CHG')
    GROUP BY year, product, product_label
),
with_metrics AS (
    SELECT
        year,
        product,
        product_label,
        COALESCE(production_ktoe, 0) AS production_ktoe,
        COALESCE(imports_ktoe, 0) AS imports_ktoe,
        COALESCE(exports_ktoe, 0) AS exports_ktoe,
        stock_change_ktoe,
        COALESCE(production_ktoe, 0) + COALESCE(imports_ktoe, 0) - COALESCE(exports_ktoe, 0)
            AS apparent_consumption_ktoe,
        CASE
            WHEN COALESCE(production_ktoe, 0) + COALESCE(imports_ktoe, 0) - COALESCE(exports_ktoe, 0) > 0
            THEN ROUND(
                imports_ktoe / (production_ktoe + imports_ktoe - exports_ktoe) * 100,
                1
            )
            ELSE NULL
        END AS gross_import_dependency_pct,
        CASE
            WHEN COALESCE(production_ktoe, 0) + COALESCE(imports_ktoe, 0) - COALESCE(exports_ktoe, 0) > 0
            THEN ROUND(
                production_ktoe / (production_ktoe + imports_ktoe - exports_ktoe) * 100,
                1
            )
            ELSE NULL
        END AS domestic_share_pct,
        CASE
            WHEN imports_ktoe > 0
            THEN ROUND(production_ktoe / imports_ktoe, 2)
            ELSE NULL
        END AS import_coverage_ratio
    FROM pivoted
)
SELECT
    year, product, product_label,
    production_ktoe, imports_ktoe, exports_ktoe,
    stock_change_ktoe,
    apparent_consumption_ktoe,
    gross_import_dependency_pct, domestic_share_pct,
    import_coverage_ratio,
    'eurostat_nrg_bal_c' AS source,
    'gross_import_dependency' AS metric_type,
    'observed' AS method,
    'verified' AS data_quality
FROM with_metrics
ORDER BY year, product
