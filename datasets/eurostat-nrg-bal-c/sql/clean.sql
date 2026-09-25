-- clean.sql: NRG_BAL_C — Italy energy balance from script-fetched CSV.

SELECT
    cast_int(year) AS year,
    normalize_string(product) AS product,
    normalize_string(product_name) AS product_label,
    normalize_string(indicator) AS indicator,
    normalize_string(indicator_name) AS indicator_label,
    cast_double(value) AS value_ktoe,
    normalize_string(unit) AS unit,
    normalize_string(geo) AS geo,
    normalize_string(source) AS source,
    normalize_string(method) AS method,
    normalize_string(data_quality) AS data_quality
FROM raw_input
WHERE year IS NOT NULL
  AND value IS NOT NULL
  AND indicator IN ('PPRD', 'IMP', 'EXP', 'STK_CHG')
