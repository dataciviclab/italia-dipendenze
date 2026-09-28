-- mart_concentration_trend.sql: HHI trend and year-over-year changes.
-- Recomputes HHI from bilateral import data, then adds YoY deltas.

WITH imports AS (
    SELECT year, resource, hs_code, partner_name, primary_value_usd
    FROM clean_input
    WHERE flow = 'M'
      AND primary_value_usd > 0
),
partner_totals AS (
    SELECT year, resource, partner_name, SUM(primary_value_usd) AS partner_value_usd
    FROM imports
    GROUP BY year, resource, partner_name
),
resource_totals AS (
    SELECT year, resource, SUM(partner_value_usd) AS total_import_value_usd
    FROM partner_totals
    GROUP BY year, resource
),
with_shares AS (
    SELECT
        pt.year, pt.resource, pt.partner_name,
        pt.partner_value_usd, rt.total_import_value_usd,
        pt.partner_value_usd / rt.total_import_value_usd * 100 AS share_pct
    FROM partner_totals pt
    JOIN resource_totals rt ON pt.year = rt.year AND pt.resource = rt.resource
),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY year, resource ORDER BY share_pct DESC) AS rank
    FROM with_shares
),
concentration AS (
    SELECT
        year, resource, total_import_value_usd,
        (SELECT SUM(r2.share_pct * r2.share_pct)
         FROM ranked r2 WHERE r2.year = r.year AND r2.resource = r.resource) AS hhi,
        MAX(CASE WHEN rank = 1 THEN partner_name END) AS top1_supplier,
        MAX(CASE WHEN rank = 1 THEN ROUND(share_pct, 1) END) AS top1_share_pct,
        (SELECT COUNT(*) FROM ranked r4
         WHERE r4.year = r.year AND r4.resource = r.resource) AS num_suppliers
    FROM ranked r
    GROUP BY year, resource, total_import_value_usd
),
lagged AS (
    SELECT
        year, resource,
        ROUND(hhi, 1) AS hhi,
        CASE WHEN hhi < 1500 THEN 'low' WHEN hhi < 2500 THEN 'medium' ELSE 'high' END AS concentration_level,
        top1_supplier,
        ROUND(top1_share_pct, 1) AS top1_share_pct,
        ROUND(total_import_value_usd, 0) AS total_import_value_usd,
        num_suppliers,
        LAG(ROUND(hhi, 1)) OVER (PARTITION BY resource ORDER BY year) AS hhi_prev,
        LAG(ROUND(top1_share_pct, 1)) OVER (PARTITION BY resource ORDER BY year) AS top1_prev,
        LAG(ROUND(total_import_value_usd, 0)) OVER (PARTITION BY resource ORDER BY year) AS import_prev
    FROM concentration
)
SELECT
    year,
    resource,
    hhi,
    concentration_level,
    top1_supplier,
    top1_share_pct,
    total_import_value_usd,
    num_suppliers,
    ROUND(hhi - hhi_prev, 1) AS hhi_change,
    ROUND(
        CASE WHEN hhi_prev > 0 THEN (hhi - hhi_prev) / hhi_prev * 100 ELSE NULL END,
        1
    ) AS hhi_change_pct,
    ROUND(top1_share_pct - top1_prev, 1) AS top1_share_change,
    ROUND(total_import_value_usd - import_prev, 0) AS import_value_change,
    CASE
        WHEN hhi > 2500 AND hhi_prev <= 2500 THEN 'newly_concentrated'
        WHEN hhi <= 2500 AND hhi_prev > 2500 THEN 'newly_diversified'
        WHEN hhi > 2500 AND (hhi - hhi_prev) > 100 THEN 'concentration_increasing'
        WHEN hhi > 2500 AND (hhi - hhi_prev) < -100 THEN 'concentration_decreasing'
        WHEN hhi <= 2500 AND (hhi - hhi_prev) > 100 THEN 'diversification_reversing'
        WHEN hhi <= 2500 AND (hhi - hhi_prev) < -100 THEN 'diversification_improving'
        ELSE 'stable'
    END AS trend_status,
    'un_comtrade_derived' AS source,
    'derived' AS method,
    'verified' AS data_quality
FROM lagged
WHERE year IS NOT NULL
ORDER BY year, resource
