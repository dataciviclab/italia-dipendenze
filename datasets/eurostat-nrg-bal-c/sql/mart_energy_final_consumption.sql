-- mart_energy_final_consumption.sql: final energy consumption by product
-- and sector, Italy, annual.
--
-- Units: KTOE. Sectors follow the Eurostat NRG_BAL_C FC_* indicators.
-- This table answers "how much oil does transport / industry / households use?"
-- without mixing it with the import-dependency question.

WITH pivoted AS (
    SELECT
        year,
        product,
        product_label,
        MAX(CASE WHEN indicator = 'FC_E' THEN value_ktoe END) AS final_consumption_total_ktoe,
        MAX(CASE WHEN indicator = 'FC_IND_E' THEN value_ktoe END) AS final_consumption_industry_ktoe,
        MAX(CASE WHEN indicator = 'FC_TRA_E' THEN value_ktoe END) AS final_consumption_transport_ktoe,
        MAX(CASE WHEN indicator = 'FC_TRA_ROAD_E' THEN value_ktoe END) AS final_consumption_transport_road_ktoe,
        MAX(CASE WHEN indicator = 'FC_OTH_HH_E' THEN value_ktoe END) AS final_consumption_households_ktoe,
        MAX(CASE WHEN indicator = 'FC_OTH_CP_E' THEN value_ktoe END) AS final_consumption_commercial_public_ktoe,
        MAX(CASE WHEN indicator = 'FC_OTH_AF_E' THEN value_ktoe END) AS final_consumption_agriculture_forestry_ktoe,
        MAX(CASE WHEN indicator = 'FC_OTH_FISH_E' THEN value_ktoe END) AS final_consumption_fishing_ktoe,
        MAX(CASE WHEN indicator = 'FC_OTH_NSP_E' THEN value_ktoe END) AS final_consumption_other_ktoe,
        MAX(CASE WHEN indicator = 'FC_NE' THEN value_ktoe END) AS final_consumption_non_energy_ktoe,
        MAX(CASE WHEN data_quality = 'partial' THEN 1 ELSE 0 END) AS has_flagged_data
    FROM clean_input
    WHERE indicator LIKE 'FC%'
    GROUP BY year, product, product_label
)
SELECT
    year,
    product,
    product_label,
    final_consumption_total_ktoe,
    final_consumption_industry_ktoe,
    final_consumption_transport_ktoe,
    final_consumption_transport_road_ktoe,
    final_consumption_households_ktoe,
    final_consumption_commercial_public_ktoe,
    final_consumption_agriculture_forestry_ktoe,
    final_consumption_fishing_ktoe,
    final_consumption_other_ktoe,
    final_consumption_non_energy_ktoe,
    'eurostat_nrg_bal_c' AS source,
    'observed' AS method,
    CASE WHEN has_flagged_data = 1 THEN 'partial' ELSE 'verified' END AS data_quality
FROM pivoted
WHERE final_consumption_total_ktoe IS NOT NULL
ORDER BY year, product
