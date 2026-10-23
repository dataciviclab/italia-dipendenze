-- clean.sql: Comext DS-045409 oil products — Italy by CN8 group and partner.

SELECT
    cast_int(year) AS year,
    normalize_string(product_group) AS product_group,
    normalize_string(flow) AS flow,
    normalize_string(flow_label) AS flow_label,
    normalize_string(partner_code) AS partner_code,
    normalize_string(partner_name) AS partner_name,
    cast_double(value_eur) AS value_eur,
    cast_double(quantity_100kg) AS quantity_100kg,
    cast_double(unit_value_eur_per_kg) AS unit_value_eur_per_kg,
    normalize_string(source) AS source,
    normalize_string(method) AS method,
    normalize_string(data_quality) AS data_quality
FROM raw_input
WHERE year IS NOT NULL
  AND product_group IS NOT NULL
  AND flow IN ('1', '2')
  AND partner_code IS NOT NULL
