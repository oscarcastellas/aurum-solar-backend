-- NYC Spatial and Geographic Optimization for 5/5 Rating
-- Advanced spatial indexes and geographic optimizations

-- =============================================
-- SPATIAL DATA OPTIMIZATION
-- =============================================

-- Enable PostGIS extension for advanced spatial operations
CREATE EXTENSION IF NOT EXISTS postgis;

-- Add spatial columns to NYC zip codes
ALTER TABLE nyc_zip_codes ADD COLUMN IF NOT EXISTS geom geometry(POINT, 4326);
ALTER TABLE nyc_zip_codes ADD COLUMN IF NOT EXISTS bbox geometry(POLYGON, 4326);

-- Update spatial data from lat/lng
UPDATE nyc_zip_codes 
SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
WHERE longitude IS NOT NULL AND latitude IS NOT NULL;

-- Create bounding box for each zip code (approximate)
UPDATE nyc_zip_codes 
SET bbox = ST_MakeEnvelope(
    longitude - 0.01, latitude - 0.01,
    longitude + 0.01, latitude + 0.01,
    4326
)
WHERE longitude IS NOT NULL AND latitude IS NOT NULL;

-- =============================================
-- ADVANCED SPATIAL INDEXES
-- =============================================

-- Primary spatial index for point queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nyc_zip_spatial_point 
ON nyc_zip_codes USING GIST (geom);

-- Bounding box spatial index for area queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nyc_zip_spatial_bbox 
ON nyc_zip_codes USING GIST (bbox);

-- Spatial index for distance queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nyc_zip_spatial_distance 
ON nyc_zip_codes USING GIST (geom) 
WHERE geom IS NOT NULL;

-- =============================================
-- GEOGRAPHIC OPTIMIZATION FUNCTIONS
-- =============================================

-- Function to find nearby zip codes within radius
CREATE OR REPLACE FUNCTION find_nearby_zip_codes(
    target_zip VARCHAR(10),
    radius_km FLOAT DEFAULT 5.0
) RETURNS TABLE (
    zip_code VARCHAR(10),
    distance_km FLOAT,
    borough VARCHAR(50),
    solar_potential_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        nzc.zip_code,
        ST_Distance(
            nzc.geom::geography,
            target.geom::geography
        ) / 1000.0 as distance_km,
        nzc.borough,
        nzc.solar_potential_score
    FROM nyc_zip_codes nzc
    CROSS JOIN (
        SELECT geom FROM nyc_zip_codes WHERE zip_code = target_zip
    ) target
    WHERE nzc.zip_code != target_zip
    AND ST_DWithin(
        nzc.geom::geography,
        target.geom::geography,
        radius_km * 1000
    )
    ORDER BY distance_km;
END;
$$ LANGUAGE plpgsql;

-- Function to find zip codes in polygon area
CREATE OR REPLACE FUNCTION find_zip_codes_in_area(
    area_geom GEOMETRY
) RETURNS TABLE (
    zip_code VARCHAR(10),
    borough VARCHAR(50),
    solar_potential_score FLOAT,
    conversion_rate FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        nzc.zip_code,
        nzc.borough,
        nzc.solar_potential_score,
        nzc.conversion_rate
    FROM nyc_zip_codes nzc
    WHERE ST_Intersects(nzc.geom, area_geom)
    ORDER BY nzc.solar_potential_score DESC;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- ADVANCED NYC MARKET INTELLIGENCE INDEXES
-- =============================================

-- NYC market clustering index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nyc_market_clusters 
ON nyc_zip_codes(borough, solar_potential_score, conversion_rate, median_household_income) 
WHERE solar_potential_score > 0;

-- NYC competition density index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nyc_competition_density 
ON nyc_zip_codes(borough, solar_installers_count, market_saturation, competition_intensity) 
WHERE solar_installers_count > 0;

-- NYC incentive availability index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nyc_incentive_availability 
ON nyc_zip_codes(zip_code, state_incentives_available, local_incentives_available, net_metering_available) 
WHERE state_incentives_available = true OR local_incentives_available = true;

-- =============================================
-- NYC DEMOGRAPHIC OPTIMIZATION
-- =============================================

-- NYC demographic analysis index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nyc_demographic_analysis 
ON nyc_demographics(zip_code_id, environmental_concern_score, green_energy_adoption_rate, data_year) 
WHERE environmental_concern_score > 0;

-- NYC housing characteristics index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nyc_housing_characteristics 
ON nyc_zip_codes(zip_code, average_home_value, homeownership_rate, average_home_age) 
WHERE average_home_value > 0;

-- =============================================
-- NYC ELECTRIC RATES OPTIMIZATION
-- =============================================

-- NYC electric rates optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nyc_electric_rates_optimized 
ON nyc_electric_rates(zip_code_id, utility_company, total_rate_per_kwh, effective_date) 
WHERE is_active = true;

-- NYC solar-specific rates index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nyc_solar_rates 
ON nyc_electric_rates(zip_code_id, net_metering_rate, solar_credit_rate, net_metering_credits_expire) 
WHERE net_metering_rate > 0;

-- =============================================
-- NYC MARKET INTELLIGENCE VIEWS
-- =============================================

-- High-value NYC zip codes view
CREATE OR REPLACE VIEW nyc_high_value_zips AS
SELECT 
    zip_code,
    borough,
    neighborhood,
    solar_potential_score,
    conversion_rate,
    median_household_income,
    average_home_value,
    solar_installers_count,
    market_saturation,
    geom
FROM nyc_zip_codes
WHERE high_value_zip_code = true
AND solar_potential_score > 70
AND conversion_rate > 0.15
ORDER BY solar_potential_score DESC, conversion_rate DESC;

-- NYC market opportunity analysis view
CREATE OR REPLACE VIEW nyc_market_opportunities AS
SELECT 
    borough,
    COUNT(*) as total_zips,
    AVG(solar_potential_score) as avg_solar_potential,
    AVG(conversion_rate) as avg_conversion_rate,
    AVG(median_household_income) as avg_income,
    SUM(solar_installers_count) as total_installers,
    AVG(market_saturation) as avg_market_saturation,
    ST_Collect(geom) as borough_geometry
FROM nyc_zip_codes
WHERE geom IS NOT NULL
GROUP BY borough
ORDER BY avg_solar_potential DESC;

-- NYC competition analysis view
CREATE OR REPLACE VIEW nyc_competition_analysis AS
SELECT 
    zip_code,
    borough,
    solar_installers_count,
    market_saturation,
    competition_intensity,
    solar_potential_score,
    conversion_rate,
    CASE 
        WHEN competition_intensity = 'low' AND solar_potential_score > 80 THEN 'High Opportunity'
        WHEN competition_intensity = 'medium' AND solar_potential_score > 70 THEN 'Medium Opportunity'
        WHEN competition_intensity = 'high' AND solar_potential_score > 60 THEN 'Competitive Market'
        ELSE 'Low Opportunity'
    END as market_opportunity
FROM nyc_zip_codes
WHERE solar_installers_count > 0
ORDER BY solar_potential_score DESC;

-- =============================================
-- NYC PERFORMANCE MONITORING
-- =============================================

-- NYC zip code performance monitoring
CREATE OR REPLACE VIEW nyc_zip_performance AS
SELECT 
    nzc.zip_code,
    nzc.borough,
    nzc.solar_potential_score,
    nzc.conversion_rate,
    nzc.lead_volume_per_month,
    nzc.average_lead_value,
    COUNT(l.id) as actual_leads,
    AVG(l.lead_score) as avg_lead_score,
    SUM(l.total_revenue_earned) as total_revenue
FROM nyc_zip_codes nzc
LEFT JOIN leads l ON nzc.zip_code = l.zip_code
WHERE l.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY nzc.zip_code, nzc.borough, nzc.solar_potential_score, 
         nzc.conversion_rate, nzc.lead_volume_per_month, nzc.average_lead_value
ORDER BY total_revenue DESC;

-- =============================================
-- NYC CACHE OPTIMIZATION
-- =============================================

-- Create materialized view for frequently accessed NYC data
CREATE MATERIALIZED VIEW nyc_zip_cache AS
SELECT 
    zip_code,
    borough,
    neighborhood,
    latitude,
    longitude,
    median_household_income,
    average_home_value,
    solar_potential_score,
    solar_adoption_rate,
    average_electric_rate_per_kwh,
    conversion_rate,
    high_value_zip_code,
    solar_installers_count,
    market_saturation,
    competition_intensity,
    state_incentives_available,
    local_incentives_available,
    net_metering_available,
    geom
FROM nyc_zip_codes
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- Create index on materialized view
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nyc_zip_cache_zip 
ON nyc_zip_cache(zip_code);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nyc_zip_cache_spatial 
ON nyc_zip_cache USING GIST (geom);

-- Function to refresh NYC cache
CREATE OR REPLACE FUNCTION refresh_nyc_zip_cache()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY nyc_zip_cache;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- NYC DATA QUALITY MONITORING
-- =============================================

-- NYC data quality monitoring view
CREATE OR REPLACE VIEW nyc_data_quality AS
SELECT 
    'nyc_zip_codes' as table_name,
    COUNT(*) as total_records,
    COUNT(geom) as records_with_geometry,
    COUNT(*) - COUNT(geom) as missing_geometry,
    AVG(solar_potential_score) as avg_solar_potential,
    COUNT(CASE WHEN solar_potential_score > 0 THEN 1 END) as records_with_solar_data,
    MAX(last_updated) as last_updated
FROM nyc_zip_codes
UNION ALL
SELECT 
    'nyc_incentives' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN is_active = true THEN 1 END) as active_incentives,
    COUNT(CASE WHEN is_active = false THEN 1 END) as inactive_incentives,
    AVG(incentive_amount) as avg_incentive_amount,
    COUNT(CASE WHEN incentive_amount > 0 THEN 1 END) as records_with_amounts,
    MAX(updated_at) as last_updated
FROM nyc_incentives;

-- =============================================
-- UPDATE STATISTICS
-- =============================================

-- Update statistics for all NYC tables
ANALYZE nyc_zip_codes;
ANALYZE nyc_incentives;
ANALYZE nyc_demographics;
ANALYZE nyc_electric_rates;
ANALYZE nyc_zip_cache;
