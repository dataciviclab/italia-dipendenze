-- mart_fertilizer_consumption.sql: Italy fertilizer consumption time series.

SELECT
    year,
    country,
    total_consumption_tonnes,
    source,
    method,
    data_quality
FROM clean_input
ORDER BY year
