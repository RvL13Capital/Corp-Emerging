"""
Data Ingestion Collector
Fetches economic data from FRED and simulates satellite/OSINT data
Stores raw data in Redis with 'raw:' prefix
"""
import redis
import requests
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import (
    REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB,
    FRED_API_KEY, ECONOMIC_INDICATORS, MONITORED_ENTITIES,
    SENTINEL_LOOKBACK_DAYS
)


class DataCollector:
    """Collects data from multiple OSINT sources"""
    
    def __init__(self):
        """Initialize Redis connection"""
        self.redis = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True
        )
        print(f"✓ Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
    
    def collect_fred_data(self):
        """Fetch economic indicators from FRED API"""
        print("\n[1/3] Collecting FRED Economic Data...")
        
        base_url = "https://api.stlouisfed.org/fred/series/observations"
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # Last year
        
        for indicator_name, series_id in ECONOMIC_INDICATORS.items():
            try:
                params = {
                    "series_id": series_id,
                    "api_key": FRED_API_KEY,
                    "file_type": "json",
                    "observation_start": start_date.strftime("%Y-%m-%d"),
                    "observation_end": end_date.strftime("%Y-%m-%d")
                }
                
                response = requests.get(base_url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                observations = data.get("observations", [])
                
                # Store in Redis
                key = f"raw:fred:{indicator_name}"
                self.redis.set(key, json.dumps({
                    "series_id": series_id,
                    "name": indicator_name,
                    "observations": observations[-90:],  # Last 90 days
                    "timestamp": datetime.now().isoformat(),
                    "source": "FRED"
                }))
                
                print(f"  ✓ {indicator_name}: {len(observations)} observations")
                
            except Exception as e:
                print(f"  ✗ {indicator_name}: {str(e)}")
                # Store error state
                self.redis.set(f"raw:fred:{indicator_name}", json.dumps({
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }))
    
    def collect_satellite_data(self):
        """Simulate satellite/aerial observation data"""
        print("\n[2/3] Simulating Satellite/OSINT Data...")
        
        import numpy as np
        
        for entity in MONITORED_ENTITIES:
            try:
                # Simulate activity metrics (in real system, this would be Sentinel API)
                days = SENTINEL_LOOKBACK_DAYS
                
                # Generate synthetic time series
                baseline = 50 + np.random.randn() * 10
                trend = np.random.randn() * 0.5
                noise = np.random.randn(days) * 5
                
                activity_scores = baseline + trend * np.arange(days) + noise
                activity_scores = np.clip(activity_scores, 0, 100)
                
                # Create observations
                observations = []
                for i in range(days):
                    date = (datetime.now() - timedelta(days=days-i))
                    observations.append({
                        "date": date.strftime("%Y-%m-%d"),
                        "activity_score": float(activity_scores[i]),
                        "cloud_cover": float(np.random.uniform(0, 30)),
                        "confidence": float(np.random.uniform(0.7, 1.0))
                    })
                
                # Store in Redis
                key = f"raw:satellite:{entity['name']}"
                self.redis.set(key, json.dumps({
                    "entity": entity,
                    "observations": observations,
                    "timestamp": datetime.now().isoformat(),
                    "source": "Sentinel-2_Simulation"
                }))
                
                print(f"  ✓ {entity['name']} ({entity['type']}): {days} days")
                
            except Exception as e:
                print(f"  ✗ {entity['name']}: {str(e)}")
    
    def collect_alternative_data(self):
        """Simulate job postings, shipping data, etc."""
        print("\n[3/3] Simulating Alternative Data Sources...")
        
        import numpy as np
        
        for entity in MONITORED_ENTITIES:
            try:
                # Simulate job postings trend
                months = 12
                job_postings = []
                
                for i in range(months):
                    date = (datetime.now() - timedelta(days=30*i))
                    count = max(0, int(np.random.poisson(25) + np.random.randn() * 5))
                    
                    job_postings.append({
                        "month": date.strftime("%Y-%m"),
                        "count": count,
                        "categories": {
                            "engineering": int(count * 0.4),
                            "operations": int(count * 0.3),
                            "management": int(count * 0.2),
                            "other": int(count * 0.1)
                        }
                    })
                
                # Store in Redis
                key = f"raw:jobs:{entity['name']}"
                self.redis.set(key, json.dumps({
                    "entity_name": entity['name'],
                    "job_postings": job_postings,
                    "timestamp": datetime.now().isoformat(),
                    "source": "LinkedIn_Simulation"
                }))
                
                print(f"  ✓ {entity['name']}: {months} months of job data")
                
            except Exception as e:
                print(f"  ✗ {entity['name']}: {str(e)}")
    
    def run(self):
        """Execute all collectors"""
        print("="*60)
        print("DATA COLLECTION STARTED")
        print("="*60)
        
        start_time = datetime.now()
        
        self.collect_fred_data()
        self.collect_satellite_data()
        self.collect_alternative_data()
        
        # Store collection metadata
        self.redis.set("raw:metadata:last_collection", json.dumps({
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "status": "success"
        }))
        
        print("="*60)
        print(f"COLLECTION COMPLETE ({(datetime.now() - start_time).total_seconds():.1f}s)")
        print("="*60)


if __name__ == "__main__":
    try:
        collector = DataCollector()
        collector.run()
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {str(e)}")
        sys.exit(1)
