-- mart_resource_dependency.sql: Joins physical balance + bilateral concentration.
--
-- physical_id_pct is the NET import dependency: (imports - exports) / GIC.
-- The old gross ratio (imports / GIC) overstates oil dependency because Italy
-- imports crude and exports refined products.

WITH energy AS (
    SELECT
        year,
        CASE
            WHEN product = 'G3000' THEN 'gas'
            WHEN product = 'C0000X0350-0370' THEN 'carbone'
            WHEN product = 'C0311' THEN 'coke'
            WHEN product = 'E7000' THEN 'elettricita'
            WHEN product = 'H8000' THEN 'calore'
            WHEN product = 'O4100_TOT' THEN 'petrolio_greggio'
            WHEN product = 'O4000XBIO' THEN 'prodotti_petroliferi'
            WHEN product = 'O4630' THEN 'gpl'
            WHEN product = 'O4640' THEN 'nafta'
            WHEN product = 'O4652XR5210B' THEN 'benzina'
            WHEN product = 'O4671XR5220B' THEN 'gasolio'
            WHEN product = 'O4661XR5230B' THEN 'cherosene'
            WHEN product = 'O4680' THEN 'olio_combustibile'
            WHEN product = 'RA000' THEN 'rinnovabili_total'
            WHEN product = 'RA100' THEN 'idroelettrico'
            WHEN product = 'RA200' THEN 'geotermico'
            WHEN product = 'RA300' THEN 'eolico'
            WHEN product = 'RA410' THEN 'solare_termico'
            WHEN product = 'RA420' THEN 'solare_fotovoltaico'
            WHEN product = 'R5110-5150_W6000RI' THEN 'biocombustibili_solidi'
            WHEN product = 'RA600' THEN 'calore_ambiente'
            WHEN product = 'W6100_6220' THEN 'rifiuti_non_rinnovabili'
            WHEN product = 'W6210' THEN 'rifiuti_rinnovabili'
            ELSE product
        END AS resource,
        product,
        product_label,
        net_import_dependency_pct,
        domestic_share_pct,
        supply_ktoe,
        production_ktoe,
        imports_ktoe,
        exports_ktoe,
        data_quality AS energy_data_quality
    FROM read_parquet('{support.energy.mart.mart_energy_balance}')
    -- Exclude aggregates to avoid double-counting in the resource matrix.
    WHERE product NOT IN ('TOTAL', 'BIOE')
),
trade AS (
    SELECT
        year,
        resource,
        total_import_value_usd,
        import_unit_value_usd_per_kg,
        hhi,
        concentration_level,
        top1_supplier,
        top1_share_pct,
        top3_share_pct,
        top5_share_pct,
        num_suppliers,
        data_quality AS trade_data_quality
    FROM read_parquet('{support.trade.mart.mart_trade_concentration}')
),
fertilizer AS (
    SELECT
        year,
        'fertilizzanti' AS resource,
        total_consumption_tonnes,
        data_quality AS fert_data_quality
    FROM read_parquet('{support.fertilizer.mart.mart_fertilizer_consumption}')
),
all_resources AS (
    SELECT
        year,
        resource,
        net_import_dependency_pct AS physical_id_pct,
        domestic_share_pct,
        supply_ktoe AS physical_volume,
        'KTOE' AS physical_unit,
        energy_data_quality
    FROM energy
    WHERE net_import_dependency_pct IS NOT NULL

    UNION ALL

    SELECT
        year,
        resource,
        NULL AS physical_id_pct,
        NULL AS domestic_share_pct,
        total_consumption_tonnes AS physical_volume,
        'TONNES' AS physical_unit,
        fert_data_quality AS energy_data_quality
    FROM fertilizer
),
joined AS (
    SELECT
        COALESCE(a.year, t.year) AS year,
        COALESCE(a.resource, t.resource) AS resource,
        a.physical_id_pct,
        a.domestic_share_pct,
        a.physical_volume,
        a.physical_unit,
        t.total_import_value_usd,
        t.import_unit_value_usd_per_kg,
        t.hhi,
        t.concentration_level,
        t.top1_supplier,
        t.top1_share_pct,
        t.top3_share_pct,
        t.top5_share_pct,
        t.num_suppliers,
        CASE
            WHEN a.energy_data_quality = 'verified' AND t.trade_data_quality = 'verified' THEN 'verified'
            WHEN a.energy_data_quality IS NOT NULL AND t.trade_data_quality IS NOT NULL THEN 'partial'
            ELSE 'constructed'
        END AS data_quality
    FROM all_resources a
    FULL OUTER JOIN trade t ON a.year = t.year AND a.resource = t.resource
)
SELECT
    year,
    resource,
    ROUND(physical_id_pct, 1) AS physical_id_pct,
    ROUND(domestic_share_pct, 1) AS domestic_share_pct,
    ROUND(physical_volume, 0) AS physical_volume,
    physical_unit,
    ROUND(total_import_value_usd, 0) AS total_import_value_usd,
    ROUND(import_unit_value_usd_per_kg, 4) AS import_unit_value_usd_per_kg,
    ROUND(hhi, 1) AS hhi,
    concentration_level,
    top1_supplier,
    top1_share_pct,
    top3_share_pct,
    top5_share_pct,
    num_suppliers,
    CASE
        WHEN total_import_value_usd IS NOT NULL AND physical_id_pct IS NOT NULL THEN 'energy_and_trade'
        WHEN total_import_value_usd IS NOT NULL THEN 'trade_only'
        ELSE 'energy_only'
    END AS data_source,
    data_quality,
    'compose' AS source,
    'derived' AS method
FROM joined
WHERE year IS NOT NULL
ORDER BY year, resource
