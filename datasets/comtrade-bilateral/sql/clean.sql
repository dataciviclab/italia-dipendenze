-- clean.sql: comtrade_bilateral — bilateral trade by HS6.
-- Reads CSV produced by fetch_comtrade.py script.

SELECT
    cast_int(year) AS year,
    normalize_string(hs_code) AS hs_code,
    cast_int(reporter_code) AS reporter_code,
    cast_int(partner_code) AS partner_code,
    normalize_string(flow) AS flow,
    cast_double(net_wgt_kg) AS net_wgt_kg,
    cast_double(primary_value_usd) AS primary_value_usd,
    normalize_string(classification) AS classification,
    normalize_string(resource) AS resource,
    normalize_string(hs_code_name) AS hs_code_name,
    normalize_string(partner_name) AS partner_name,
    normalize_string(flow_label) AS flow_label
FROM raw_input
WHERE year IS NOT NULL
  AND hs_code IS NOT NULL
  AND flow IN ('M', 'X')
