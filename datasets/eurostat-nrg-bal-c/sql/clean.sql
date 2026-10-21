-- clean.sql: NRG_BAL_C — Italy energy balance from Eurostat SDMX.
--
-- Contract: raw is the toolkit sdmx output
--   [freq, nrg_bal, siec, unit, geo, year, value, flag]
-- Labels come from the SIEC / NRG_BAL codelists, never from a hardcoded map:
-- Eurostat reuses code names across releases, and a wrong label silently
-- corrupts every downstream product analysis.

SELECT
    cast_int(r.year) AS year,
    normalize_string(r.siec) AS product,
    COALESCE(normalize_string(s.label_en), normalize_string(r.siec)) AS product_label,
    normalize_string(r.nrg_bal) AS indicator,
    COALESCE(normalize_string(n.label_en), normalize_string(r.nrg_bal)) AS indicator_label,
    cast_double(r.value) AS value_ktoe,
    normalize_string(r.unit) AS unit,
    normalize_string(r.geo) AS geo,
    normalize_string(r.freq) AS freq,
    normalize_string(r.flag) AS flag,
    normalize_string(fl.label_en) AS flag_label,
    'eurostat_nrg_bal_c' AS source,
    'observed' AS method,
    CASE
        WHEN normalize_string(r.flag) IS NULL THEN 'verified'
        ELSE 'partial'
    END AS data_quality
FROM raw_input r
LEFT JOIN read_parquet('{support.siec.path}') s ON r.siec = s.code
LEFT JOIN read_parquet('{support.nrg_bal.path}') n ON r.nrg_bal = n.code
LEFT JOIN read_parquet('{support.flag.path}') fl ON r.flag = fl.code
WHERE cast_int(r.year) BETWEEN 1990 AND 2024
  AND cast_double(r.value) IS NOT NULL
