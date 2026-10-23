-- mart_comext_oil_concentration.sql: supplier concentration for Italy oil
-- products (CN8 groups) by year, on Comext import value.
--
-- Unit value: total import value / total quantity (quantity is in 100 kg).

WITH imports AS (
    SELECT year, product_group, partner_name, value_eur, quantity_100kg
    FROM clean_input
    WHERE flow = '1'
      AND value_eur > 0
),
partner_totals AS (
    SELECT
        year,
        product_group,
        partner_name,
        SUM(value_eur) AS partner_value_eur,
        SUM(COALESCE(quantity_100kg, 0)) AS partner_quantity_100kg
    FROM imports
    GROUP BY year, product_group, partner_name
),
group_totals AS (
    SELECT
        year,
        product_group,
        SUM(partner_value_eur) AS total_import_value_eur,
        SUM(partner_quantity_100kg) AS total_quantity_100kg
    FROM partner_totals
    GROUP BY year, product_group
),
with_shares AS (
    SELECT
        pt.year,
        pt.product_group,
        pt.partner_name,
        pt.partner_value_eur,
        pt.partner_quantity_100kg,
        gt.total_import_value_eur,
        gt.total_quantity_100kg,
        pt.partner_value_eur / gt.total_import_value_eur * 100 AS share_pct
    FROM partner_totals pt
    JOIN group_totals gt ON pt.year = gt.year AND pt.product_group = gt.product_group
),
ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY year, product_group ORDER BY share_pct DESC) AS rank
    FROM with_shares
),
concentration AS (
    SELECT
        year,
        product_group,
        total_import_value_eur,
        total_quantity_100kg,
        (SELECT SUM(r2.share_pct * r2.share_pct)
         FROM ranked r2
         WHERE r2.year = r.year AND r2.product_group = r.product_group) AS hhi,
        MAX(CASE WHEN rank = 1 THEN partner_name END) AS top1_supplier,
        MAX(CASE WHEN rank = 1 THEN ROUND(share_pct, 1) END) AS top1_share_pct,
        (SELECT SUM(r3.share_pct)
         FROM ranked r3
         WHERE r3.year = r.year AND r3.product_group = r.product_group AND r3.rank <= 3) AS top3_share_pct,
        (SELECT SUM(r5.share_pct)
         FROM ranked r5
         WHERE r5.year = r.year AND r5.product_group = r.product_group AND r5.rank <= 5) AS top5_share_pct,
        (SELECT COUNT(*)
         FROM ranked r4
         WHERE r4.year = r.year AND r4.product_group = r.product_group) AS num_suppliers
    FROM ranked r
    GROUP BY year, product_group, total_import_value_eur, total_quantity_100kg
)
SELECT
    year,
    product_group,
    ROUND(total_import_value_eur, 0) AS total_import_value_eur,
    ROUND(total_quantity_100kg * 100, 0) AS import_quantity_kg,
    ROUND(
        CASE
            WHEN total_quantity_100kg > 0
            THEN total_import_value_eur / (total_quantity_100kg * 100)
            ELSE NULL
        END,
        4
    ) AS import_unit_value_eur_per_kg,
    ROUND(hhi, 1) AS hhi,
    CASE
        WHEN hhi < 1500 THEN 'low'
        WHEN hhi < 2500 THEN 'medium'
        ELSE 'high'
    END AS concentration_level,
    top1_supplier,
    top1_share_pct,
    ROUND(top3_share_pct, 1) AS top3_share_pct,
    ROUND(top5_share_pct, 1) AS top5_share_pct,
    num_suppliers,
    'eurostat_comext' AS source,
    'derived' AS method,
    'verified' AS data_quality
FROM concentration
ORDER BY year, product_group
