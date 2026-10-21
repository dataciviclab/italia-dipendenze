-- mart_energy_balance.sql: Italy energy balance by product x year.
--
-- Dependency is measured on DOMESTIC SUPPLY, using the official Eurostat GIC
-- (gross inland consumption) when available. The previous formula used
-- PPRD + IMP - EXP - STK_CHG, which inverted the stock-change sign:
-- Eurostat's STK_CHG is positive for a stock draw, so the identity is
--   GIC = PPRD + IMP - EXP + STK_CHG.
--
--   gic_computed_ktoe = PPRD + IMP - EXP + STK_CHG   (audit, when GIC missing)
--   gic_ktoe          = COALESCE(GIC reported, gic_computed_ktoe)
--   supply_ktoe       = gic_ktoe                       (primary / aggregate)
--                     = gic_ktoe + TO                  (secondary products)
--   net_import_dependency_pct   = (IMP - EXP) / supply * 100  (headline)
--   gross_import_dependency_pct = IMP / supply * 100          (gross flows)
--   domestic_share_pct          = (PPRD + TO) / supply * 100
--
-- Why TO: electricity, gas oil, motor gasoline, LPG, jet fuel, fuel oil and
-- coke are SECONDARY products. Their domestic supply is refinery / power
-- transformation output (TO), not primary production. Using GIC alone gives
-- nonsense (e.g. electricity "100% dependent" while most power is domestic).
-- For primary products and aggregates TO is not added: it would double-count
-- the crude / fuel input already embedded in GIC.

WITH pivoted AS (
    SELECT
        year,
        product,
        product_label,
        MAX(CASE WHEN indicator = 'PPRD' THEN value_ktoe END) AS production_ktoe,
        MAX(CASE WHEN indicator = 'IMP' THEN value_ktoe END) AS imports_ktoe,
        MAX(CASE WHEN indicator = 'EXP' THEN value_ktoe END) AS exports_ktoe,
        MAX(CASE WHEN indicator = 'STK_CHG' THEN value_ktoe END) AS stock_change_ktoe,
        MAX(CASE WHEN indicator = 'GIC' THEN value_ktoe END) AS gic_reported_ktoe,
        MAX(CASE WHEN indicator = 'TO' THEN value_ktoe END) AS domestic_output_ktoe,
        MAX(CASE WHEN data_quality = 'partial' THEN 1 ELSE 0 END) AS has_flagged_data
    FROM clean_input
    GROUP BY year, product, product_label
),
classified AS (
    SELECT
        *,
        CASE
            WHEN product IN (
                'E7000', 'H8000', 'C0311', 'O4630', 'O4640',
                'O4652XR5210B', 'O4671XR5220B', 'O4661XR5230B', 'O4680'
            ) THEN 'secondary'
            WHEN product IN (
                'TOTAL', 'O4000XBIO', 'C0000X0350-0370', 'RA000', 'BIOE'
            ) THEN 'aggregate'
            ELSE 'primary'
        END AS product_kind
    FROM pivoted
),
with_metrics AS (
    SELECT
        year,
        product,
        product_label,
        product_kind,
        COALESCE(production_ktoe, 0) AS production_ktoe,
        COALESCE(imports_ktoe, 0) AS imports_ktoe,
        COALESCE(exports_ktoe, 0) AS exports_ktoe,
        stock_change_ktoe,
        gic_reported_ktoe,
        COALESCE(domestic_output_ktoe, 0) AS domestic_output_ktoe,
        has_flagged_data,
        COALESCE(production_ktoe, 0) + COALESCE(imports_ktoe, 0) - COALESCE(exports_ktoe, 0)
            AS apparent_consumption_ktoe,
        COALESCE(production_ktoe, 0) + COALESCE(imports_ktoe, 0) - COALESCE(exports_ktoe, 0)
            + COALESCE(stock_change_ktoe, 0) AS gic_computed_ktoe,
        COALESCE(
            gic_reported_ktoe,
            COALESCE(production_ktoe, 0) + COALESCE(imports_ktoe, 0) - COALESCE(exports_ktoe, 0)
                + COALESCE(stock_change_ktoe, 0)
        ) AS gic_ktoe,
        COALESCE(
            gic_reported_ktoe,
            COALESCE(production_ktoe, 0) + COALESCE(imports_ktoe, 0) - COALESCE(exports_ktoe, 0)
                + COALESCE(stock_change_ktoe, 0)
        ) + CASE WHEN product_kind = 'secondary' THEN COALESCE(domestic_output_ktoe, 0) ELSE 0 END
            AS supply_ktoe
    FROM classified
),
calculated AS (
    SELECT
        *,
        CASE
            WHEN supply_ktoe > 0 THEN ROUND(imports_ktoe / supply_ktoe * 100, 1)
            ELSE NULL
        END AS gross_import_dependency_pct,
        CASE
            WHEN supply_ktoe > 0 THEN ROUND((imports_ktoe - exports_ktoe) / supply_ktoe * 100, 1)
            ELSE NULL
        END AS net_import_dependency_pct,
        CASE
            WHEN supply_ktoe > 0
            THEN ROUND(
                (production_ktoe + CASE WHEN product_kind = 'secondary' THEN domestic_output_ktoe ELSE 0 END)
                / supply_ktoe * 100,
                1
            )
            ELSE NULL
        END AS domestic_share_pct,
        CASE
            WHEN imports_ktoe > 0
            THEN ROUND(
                (production_ktoe + CASE WHEN product_kind = 'secondary' THEN domestic_output_ktoe ELSE 0 END)
                / imports_ktoe,
                2
            )
            ELSE NULL
        END AS import_coverage_ratio
    FROM with_metrics
)
SELECT
    year,
    product,
    product_label,
    product_kind,
    production_ktoe,
    imports_ktoe,
    exports_ktoe,
    stock_change_ktoe,
    domestic_output_ktoe,
    apparent_consumption_ktoe,
    gic_computed_ktoe,
    gic_reported_ktoe,
    gic_ktoe,
    supply_ktoe,
    gross_import_dependency_pct,
    net_import_dependency_pct,
    domestic_share_pct,
    import_coverage_ratio,
    'eurostat_nrg_bal_c' AS source,
    'net_import_dependency' AS metric_type,
    'observed' AS method,
    CASE WHEN has_flagged_data = 1 THEN 'partial' ELSE 'verified' END AS data_quality
FROM calculated
ORDER BY year, product
