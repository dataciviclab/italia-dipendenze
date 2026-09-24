-- clean.sql: fao_fertilizer_consumption — FAO fertilizer data for Italy.

SELECT
    cast_int(year) AS year,
    normalize_string(country) AS country,
    cast_int(country_code) AS country_code,
    cast_double(total_fertilizer_consumption_tonnes) AS total_consumption_tonnes,
    normalize_string(source) AS source,
    normalize_string(method) AS method,
    normalize_string(data_quality) AS data_quality
FROM raw_input
WHERE year IS NOT NULL
  AND CAST(total_fertilizer_consumption_tonnes AS DOUBLE) > 0
