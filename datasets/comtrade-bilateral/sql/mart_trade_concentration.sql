-- mart_trade_concentration.sql: Supplier concentration metrics per resource × year.
-- Computes HHI, top-1/3/5 shares from import bilateral data.

WITH imports AS (
    SELECT year, resource, hs_code, partner_name, primary_value_usd
    FROM clean_input
    WHERE flow = 'M'
      AND primary_value_usd > 0
),
partner_totals AS (
    SELECT
        year,
        resource,
        partner_name,
        SUM(primary_value_usd) AS partner_value_usd
    FROM imports
    GROUP BY year, resource, partner_name
),
resource_totals AS (
    SELECT
        year,
        resource,
        SUM(partner_value_usd) AS total_import_value_usd
    FROM partner_totals
    GROUP BY year, resource
),
with_shares AS (
    SELECT
        pt.year,
        pt.resource,
        pt.partner_name,
        pt.partner_value_usd,
        rt.total_import_value_usd,
        pt.partner_value_usd / rt.total_import_value_usd * 100 AS share_pct
    FROM partner_totals pt
    JOIN resource_totals rt ON pt.year = rt.year AND pt.resource = rt.resource
),
ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY year, resource ORDER BY share_pct DESC) AS rank
    FROM with_shares
),
concentration AS (
    SELECT
        year,
        resource,
        total_import_value_usd,
        -- HHI: sum of squared shares
        (SELECT SUM(r2.share_pct * r2.share_pct)
         FROM ranked r2
         WHERE r2.year = r.year AND r2.resource = r.resource) AS hhi,
        -- Top-1
        MAX(CASE WHEN rank = 1 THEN partner_name END) AS top1_supplier,
        MAX(CASE WHEN rank = 1 THEN ROUND(share_pct, 1) END) AS top1_share_pct,
        -- Top-3
        (SELECT SUM(r3.share_pct)
         FROM ranked r3
         WHERE r3.year = r.year AND r3.resource = r.resource AND r3.rank <= 3) AS top3_share_pct,
        -- Top-5
        (SELECT SUM(r5.share_pct)
         FROM ranked r5
         WHERE r5.year = r.year AND r5.resource = r.resource AND r5.rank <= 5) AS top5_share_pct,
        -- Number of suppliers
        (SELECT COUNT(*)
         FROM ranked r4
         WHERE r4.year = r.year AND r4.resource = r.resource) AS num_suppliers
    FROM ranked r
    GROUP BY year, resource, total_import_value_usd
)
SELECT
    year,
    resource,
    ROUND(total_import_value_usd, 0) AS total_import_value_usd,
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
    'un_comtrade_derived' AS source,
    'derived' AS method,
    'verified' AS data_quality
FROM concentration
ORDER BY year, resource
