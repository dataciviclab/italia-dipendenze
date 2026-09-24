-- mart_resource_dependency.sql: Joins physical balance + bilateral concentration.

WITH energy AS (
    SELECT
        year,
        CASE
            WHEN product = 'G3000' THEN 'gas'
            WHEN product = 'C0000X0350-0370' THEN 'carbone'
            ELSE product
        END AS resource,
        product,
        product_label,
        gross_import_dependency_pct,
        domestic_share_pct,
        apparent_consumption_ktoe,
        data_quality AS energy_data_quality
    FROM read_parquet('{support.energy.mart.mart_energy_balance}')
),
trade AS (
    SELECT
        year,
        resource,
        total_import_value_usd,
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
        year, resource,
        gross_import_dependency_pct AS physical_id_pct,
        domestic_share_pct,
        apparent_consumption_ktoe AS physical_volume,
        'KTOE' AS physical_unit,
        energy_data_quality
    FROM energy
    WHERE gross_import_dependency_pct IS NOT NULL

    UNION ALL

    SELECT
        year, resource,
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
    ROUND(hhi, 1) AS hhi,
    concentration_level,
    top1_supplier,
    top1_share_pct,
    top3_share_pct,
    top5_share_pct,
    num_suppliers,
    data_quality,
    'compose' AS source,
    'derived' AS method
FROM joined
WHERE year IS NOT NULL
ORDER BY year, resource
