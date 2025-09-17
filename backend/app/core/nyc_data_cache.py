"""
NYC Market Data Caching System
Redis-based caching for high-frequency NYC market data lookups
Optimized for sub-10ms response times
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import redis.asyncio as redis
from sqlalchemy.orm import Session
from app.models.nyc_data import NYCZipCode, NYCIncentive, NYCDemographic, NYCElectricRate
from app.core.railway_database import get_redis

logger = logging.getLogger(__name__)

class NYCMarketDataCache:
    """Redis-based caching for NYC market data with intelligent invalidation"""
    
    # Cache TTL settings (in seconds)
    ZIP_CODE_TTL = 3600  # 1 hour - relatively static data
    INCENTIVES_TTL = 1800  # 30 minutes - can change more frequently
    DEMOGRAPHICS_TTL = 7200  # 2 hours - very static data
    ELECTRIC_RATES_TTL = 1800  # 30 minutes - can change with rate updates
    
    # Cache key patterns
    ZIP_CODE_KEY = "nyc:zip:{zip_code}"
    BOROUGH_KEY = "nyc:borough:{borough}"
    INCENTIVES_KEY = "nyc:incentives:{zip_code}"
    DEMOGRAPHICS_KEY = "nyc:demographics:{zip_code}"
    ELECTRIC_RATES_KEY = "nyc:electric_rates:{zip_code}"
    
    # Batch operation keys
    ALL_ZIP_CODES_KEY = "nyc:zip_codes:all"
    HIGH_VALUE_ZIPS_KEY = "nyc:zip_codes:high_value"
    BOROUGH_ZIPS_KEY = "nyc:borough:{borough}:zips"
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Redis client"""
        if not self._initialized:
            self.redis_client = await get_redis()
            self._initialized = True
            logger.info("NYC Market Data Cache initialized")
    
    async def get_zip_code_data(self, zip_code: str) -> Optional[Dict[str, Any]]:
        """Get cached zip code data with fallback to database"""
        await self.initialize()
        
        cache_key = self.ZIP_CODE_KEY.format(zip_code=zip_code)
        
        try:
            # Try to get from cache
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                logger.debug(f"Cache hit for zip code {zip_code}")
                return json.loads(cached_data)
            
            logger.debug(f"Cache miss for zip code {zip_code}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving zip code {zip_code} from cache: {e}")
            return None
    
    async def set_zip_code_data(self, zip_code: str, data: Dict[str, Any]):
        """Cache zip code data"""
        await self.initialize()
        
        cache_key = self.ZIP_CODE_KEY.format(zip_code=zip_code)
        
        try:
            await self.redis_client.setex(
                cache_key,
                self.ZIP_CODE_TTL,
                json.dumps(data, default=str)
            )
            logger.debug(f"Cached zip code {zip_code} data")
            
        except Exception as e:
            logger.error(f"Error caching zip code {zip_code} data: {e}")
    
    async def get_borough_data(self, borough: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached borough data"""
        await self.initialize()
        
        cache_key = self.BOROUGH_KEY.format(borough=borough)
        
        try:
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                logger.debug(f"Cache hit for borough {borough}")
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving borough {borough} from cache: {e}")
            return None
    
    async def set_borough_data(self, borough: str, data: List[Dict[str, Any]]):
        """Cache borough data"""
        await self.initialize()
        
        cache_key = self.BOROUGH_KEY.format(borough=borough)
        
        try:
            await self.redis_client.setex(
                cache_key,
                self.ZIP_CODE_TTL,
                json.dumps(data, default=str)
            )
            logger.debug(f"Cached borough {borough} data")
            
        except Exception as e:
            logger.error(f"Error caching borough {borough} data: {e}")
    
    async def get_incentives_data(self, zip_code: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached incentives data for zip code"""
        await self.initialize()
        
        cache_key = self.INCENTIVES_KEY.format(zip_code=zip_code)
        
        try:
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                logger.debug(f"Cache hit for incentives {zip_code}")
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving incentives {zip_code} from cache: {e}")
            return None
    
    async def set_incentives_data(self, zip_code: str, data: List[Dict[str, Any]]):
        """Cache incentives data"""
        await self.initialize()
        
        cache_key = self.INCENTIVES_KEY.format(zip_code=zip_code)
        
        try:
            await self.redis_client.setex(
                cache_key,
                self.INCENTIVES_TTL,
                json.dumps(data, default=str)
            )
            logger.debug(f"Cached incentives {zip_code} data")
            
        except Exception as e:
            logger.error(f"Error caching incentives {zip_code} data: {e}")
    
    async def get_electric_rates_data(self, zip_code: str) -> Optional[Dict[str, Any]]:
        """Get cached electric rates data for zip code"""
        await self.initialize()
        
        cache_key = self.ELECTRIC_RATES_KEY.format(zip_code=zip_code)
        
        try:
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                logger.debug(f"Cache hit for electric rates {zip_code}")
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving electric rates {zip_code} from cache: {e}")
            return None
    
    async def set_electric_rates_data(self, zip_code: str, data: Dict[str, Any]):
        """Cache electric rates data"""
        await self.initialize()
        
        cache_key = self.ELECTRIC_RATES_KEY.format(zip_code=zip_code)
        
        try:
            await self.redis_client.setex(
                cache_key,
                self.ELECTRIC_RATES_TTL,
                json.dumps(data, default=str)
            )
            logger.debug(f"Cached electric rates {zip_code} data")
            
        except Exception as e:
            logger.error(f"Error caching electric rates {zip_code} data: {e}")
    
    async def get_high_value_zip_codes(self) -> Optional[List[str]]:
        """Get cached list of high-value zip codes"""
        await self.initialize()
        
        try:
            cached_data = await self.redis_client.get(self.HIGH_VALUE_ZIPS_KEY)
            
            if cached_data:
                logger.debug("Cache hit for high-value zip codes")
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving high-value zip codes from cache: {e}")
            return None
    
    async def set_high_value_zip_codes(self, zip_codes: List[str]):
        """Cache high-value zip codes list"""
        await self.initialize()
        
        try:
            await self.redis_client.setex(
                self.HIGH_VALUE_ZIPS_KEY,
                self.ZIP_CODE_TTL,
                json.dumps(zip_codes)
            )
            logger.debug("Cached high-value zip codes")
            
        except Exception as e:
            logger.error(f"Error caching high-value zip codes: {e}")
    
    async def invalidate_zip_code_cache(self, zip_code: str):
        """Invalidate all cache entries for a specific zip code"""
        await self.initialize()
        
        keys_to_delete = [
            self.ZIP_CODE_KEY.format(zip_code=zip_code),
            self.INCENTIVES_KEY.format(zip_code=zip_code),
            self.DEMOGRAPHICS_KEY.format(zip_code=zip_code),
            self.ELECTRIC_RATES_KEY.format(zip_code=zip_code),
        ]
        
        try:
            await self.redis_client.delete(*keys_to_delete)
            logger.info(f"Invalidated cache for zip code {zip_code}")
            
        except Exception as e:
            logger.error(f"Error invalidating cache for zip code {zip_code}: {e}")
    
    async def invalidate_borough_cache(self, borough: str):
        """Invalidate all cache entries for a specific borough"""
        await self.initialize()
        
        try:
            # Get all keys matching borough pattern
            pattern = f"nyc:borough:{borough}*"
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                await self.redis_client.delete(*keys)
                logger.info(f"Invalidated cache for borough {borough}")
            
        except Exception as e:
            logger.error(f"Error invalidating cache for borough {borough}: {e}")
    
    async def warm_cache(self, db: Session, zip_codes: List[str] = None):
        """Warm cache with frequently accessed data"""
        await self.initialize()
        
        logger.info("Starting cache warming process")
        
        try:
            # Get high-value zip codes if not provided
            if not zip_codes:
                high_value_zips = db.query(NYCZipCode.zip_code).filter(
                    NYCZipCode.high_value_zip_code == True
                ).all()
                zip_codes = [zip_code[0] for zip_code in high_value_zips]
            
            # Warm cache for each zip code
            for zip_code in zip_codes:
                await self._warm_zip_code_cache(db, zip_code)
            
            # Warm borough data
            boroughs = ['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island']
            for borough in boroughs:
                await self._warm_borough_cache(db, borough)
            
            logger.info(f"Cache warming completed for {len(zip_codes)} zip codes")
            
        except Exception as e:
            logger.error(f"Error during cache warming: {e}")
    
    async def _warm_zip_code_cache(self, db: Session, zip_code: str):
        """Warm cache for a specific zip code"""
        
        # Zip code data
        zip_data = db.query(NYCZipCode).filter(NYCZipCode.zip_code == zip_code).first()
        if zip_data:
            zip_dict = {
                'zip_code': zip_data.zip_code,
                'borough': zip_data.borough,
                'neighborhood': zip_data.neighborhood,
                'latitude': zip_data.latitude,
                'longitude': zip_data.longitude,
                'median_household_income': zip_data.median_household_income,
                'average_home_value': zip_data.average_home_value,
                'solar_potential_score': zip_data.solar_potential_score,
                'solar_adoption_rate': zip_data.solar_adoption_rate,
                'average_electric_rate_per_kwh': zip_data.average_electric_rate_per_kwh,
                'conversion_rate': zip_data.conversion_rate,
                'high_value_zip_code': zip_data.high_value_zip_code,
            }
            await self.set_zip_code_data(zip_code, zip_dict)
        
        # Incentives data
        incentives = db.query(NYCIncentive).filter(
            NYCIncentive.zip_code_id == zip_data.id if zip_data else None
        ).all()
        
        if incentives:
            incentives_data = []
            for incentive in incentives:
                incentives_data.append({
                    'incentive_name': incentive.incentive_name,
                    'incentive_type': incentive.incentive_type,
                    'incentive_amount': incentive.incentive_amount,
                    'is_active': incentive.is_active,
                    'start_date': incentive.start_date.isoformat() if incentive.start_date else None,
                    'end_date': incentive.end_date.isoformat() if incentive.end_date else None,
                })
            await self.set_incentives_data(zip_code, incentives_data)
        
        # Electric rates data
        electric_rates = db.query(NYCElectricRate).filter(
            NYCElectricRate.zip_code_id == zip_data.id if zip_data else None
        ).first()
        
        if electric_rates:
            rates_data = {
                'utility_company': electric_rates.utility_company,
                'total_rate_per_kwh': electric_rates.total_rate_per_kwh,
                'net_metering_rate': electric_rates.net_metering_rate,
                'effective_date': electric_rates.effective_date.isoformat() if electric_rates.effective_date else None,
            }
            await self.set_electric_rates_data(zip_code, rates_data)
    
    async def _warm_borough_cache(self, db: Session, borough: str):
        """Warm cache for a specific borough"""
        
        zip_codes = db.query(NYCZipCode).filter(NYCZipCode.borough == borough).all()
        
        borough_data = []
        for zip_code in zip_codes:
            borough_data.append({
                'zip_code': zip_code.zip_code,
                'neighborhood': zip_code.neighborhood,
                'median_household_income': zip_code.median_household_income,
                'solar_potential_score': zip_code.solar_potential_score,
                'conversion_rate': zip_code.conversion_rate,
                'high_value_zip_code': zip_code.high_value_zip_code,
            })
        
        await self.set_borough_data(borough, borough_data)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        await self.initialize()
        
        try:
            info = await self.redis_client.info('memory')
            
            return {
                'redis_memory_used': info.get('used_memory_human', '0B'),
                'redis_memory_peak': info.get('used_memory_peak_human', '0B'),
                'redis_keys_count': await self.redis_client.dbsize(),
                'cache_hit_rate': 0,  # Would need to implement hit/miss tracking
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}

# Global cache instance
nyc_cache = NYCMarketDataCache()

# Convenience functions
async def get_zip_code_data(zip_code: str) -> Optional[Dict[str, Any]]:
    """Get zip code data from cache"""
    return await nyc_cache.get_zip_code_data(zip_code)

async def get_borough_data(borough: str) -> Optional[List[Dict[str, Any]]]:
    """Get borough data from cache"""
    return await nyc_cache.get_borough_data(borough)

async def get_incentives_data(zip_code: str) -> Optional[List[Dict[str, Any]]]:
    """Get incentives data from cache"""
    return await nyc_cache.get_incentives_data(zip_code)

async def get_electric_rates_data(zip_code: str) -> Optional[Dict[str, Any]]:
    """Get electric rates data from cache"""
    return await nyc_cache.get_electric_rates_data(zip_code)

async def warm_nyc_cache(db: Session, zip_codes: List[str] = None):
    """Warm NYC market data cache"""
    await nyc_cache.warm_cache(db, zip_codes)
