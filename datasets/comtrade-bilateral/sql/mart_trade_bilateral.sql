-- mart_trade_bilateral.sql: Bilateral trade pivoted by year × hs_code × partner × flow.

SELECT
    year,
    hs_code,
    hs_code_name,
    resource,
    reporter_code,
    partner_code,
    partner_name,
    flow,
    flow_label,
    net_wgt_kg,
    primary_value_usd,
    classification,
    'un_comtrade' AS source,
    'observed' AS method,
    'verified' AS data_quality
FROM clean_input
ORDER BY year, resource, hs_code, flow, primary_value_usd DESC
