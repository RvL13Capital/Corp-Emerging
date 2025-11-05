"""
Data Processing Pipeline
Transforms raw data into engineered features and entity vectors
Stores processed data in Redis with 'processed:' prefix
"""
import redis
import json
import sys
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import (
    REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB,
    MONITORED_ENTITIES, NORMALIZATION_METHOD
)


class DataProcessor:
    """Processes and engineers features from raw data"""
    
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
    
    def load_raw_data(self, pattern):
        """Load all keys matching pattern"""
        keys = self.redis.keys(pattern)
        data = {}
        for key in keys:
            try:
                data[key] = json.loads(self.redis.get(key))
            except:
                pass
        return data
    
    def process_fred_indicators(self):
        """Create economic indicator features"""
        print("\n[1/3] Processing Economic Indicators...")
        
        fred_data = self.load_raw_data("raw:fred:*")
        
        if not fred_data:
            print("  ✗ No FRED data found")
            return None
        
        features = {}
        
        for key, data in fred_data.items():
            if "error" in data:
                continue
                
            indicator_name = key.split(":")[-1]
            observations = data.get("observations", [])
            
            if len(observations) < 2:
                continue
            
            # Extract values
            values = [float(obs.get("value", 0)) for obs in observations if obs.get("value") != "."]
            
            if len(values) < 2:
                continue
            
            # Calculate features
            current = values[-1]
            prev = values[-2] if len(values) > 1 else current
            avg_30 = np.mean(values[-30:]) if len(values) >= 30 else current
            
            features[indicator_name] = {
                "current": current,
                "change_pct": ((current - prev) / prev * 100) if prev != 0 else 0,
                "vs_30d_avg": ((current - avg_30) / avg_30 * 100) if avg_30 != 0 else 0,
                "trend": "up" if current > prev else "down",
                "volatility": float(np.std(values[-30:])) if len(values) >= 30 else 0
            }
            
            print(f"  ✓ {indicator_name}: {current:.2f} ({features[indicator_name]['change_pct']:+.2f}%)")
        
        # Store processed indicators
        self.redis.set("processed:economic_indicators", json.dumps({
            "features": features,
            "timestamp": datetime.now().isoformat()
        }))
        
        return features
    
    def process_entity_data(self):
        """Create entity-level feature vectors"""
        print("\n[2/3] Processing Entity Vectors...")
        
        entity_vectors = {}
        
        for entity in MONITORED_ENTITIES:
            name = entity['name']
            
            try:
                # Load satellite data
                sat_key = f"raw:satellite:{name}"
                sat_data = json.loads(self.redis.get(sat_key) or "{}")
                
                # Load job data
                job_key = f"raw:jobs:{name}"
                job_data = json.loads(self.redis.get(job_key) or "{}")
                
                # Calculate features
                features = {}
                
                # Satellite features
                if "observations" in sat_data:
                    obs = sat_data["observations"]
                    activity_scores = [o["activity_score"] for o in obs]
                    
                    features["activity_current"] = activity_scores[-1]
                    features["activity_trend"] = activity_scores[-1] - activity_scores[0]
                    features["activity_volatility"] = float(np.std(activity_scores))
                    features["activity_avg_7d"] = float(np.mean(activity_scores[-7:]))
                else:
                    features["activity_current"] = 50
                    features["activity_trend"] = 0
                    features["activity_volatility"] = 0
                    features["activity_avg_7d"] = 50
                
                # Job posting features
                if "job_postings" in job_data:
                    postings = job_data["job_postings"]
                    counts = [p["count"] for p in postings]
                    
                    features["jobs_current"] = counts[0]
                    features["jobs_trend"] = counts[0] - counts[-1]
                    features["jobs_avg_3m"] = float(np.mean(counts[:3]))
                else:
                    features["jobs_current"] = 0
                    features["jobs_trend"] = 0
                    features["jobs_avg_3m"] = 0
                
                # Composite score
                features["composite_score"] = (
                    features["activity_current"] * 0.4 +
                    features["jobs_current"] * 2.0 +  # Scale jobs up
                    features["activity_trend"] * 0.3
                )
                
                entity_vectors[name] = {
                    "entity": entity,
                    "features": features,
                    "timestamp": datetime.now().isoformat()
                }
                
                print(f"  ✓ {name}: Composite={features['composite_score']:.1f}")
                
            except Exception as e:
                print(f"  ✗ {name}: {str(e)}")
        
        # Store entity vectors
        self.redis.set("processed:entity_vectors", json.dumps({
            "entities": entity_vectors,
            "timestamp": datetime.now().isoformat()
        }))
        
        return entity_vectors
    
    def create_feature_matrix(self, econ_features, entity_vectors):
        """Combine all features into a normalized matrix"""
        print("\n[3/3] Creating Feature Matrix...")
        
        if not econ_features or not entity_vectors:
            print("  ✗ Insufficient data for feature matrix")
            return
        
        matrix = {}
        
        for entity_name, entity_data in entity_vectors.items():
            features = entity_data["features"].copy()
            
            # Add macro economic context
            for indicator, values in econ_features.items():
                features[f"macro_{indicator}"] = values["current"]
                features[f"macro_{indicator}_change"] = values["change_pct"]
            
            # Normalize if needed
            if NORMALIZATION_METHOD == "zscore":
                # Simple z-score normalization
                vals = list(features.values())
                mean = np.mean(vals)
                std = np.std(vals) if np.std(vals) > 0 else 1
                normalized = {k: (v - mean) / std for k, v in features.items()}
            else:
                normalized = features
            
            matrix[entity_name] = {
                "raw_features": features,
                "normalized_features": normalized,
                "feature_count": len(features)
            }
            
            print(f"  ✓ {entity_name}: {len(features)} features")
        
        # Store feature matrix
        self.redis.set("processed:feature_matrix", json.dumps({
            "matrix": matrix,
            "timestamp": datetime.now().isoformat(),
            "normalization": NORMALIZATION_METHOD
        }))
        
        return matrix
    
    def run(self):
        """Execute processing pipeline"""
        print("="*60)
        print("DATA PROCESSING STARTED")
        print("="*60)
        
        start_time = datetime.now()
        
        econ_features = self.process_fred_indicators()
        entity_vectors = self.process_entity_data()
        self.create_feature_matrix(econ_features, entity_vectors)
        
        # Store processing metadata
        self.redis.set("processed:metadata:last_processing", json.dumps({
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "status": "success"
        }))
        
        print("="*60)
        print(f"PROCESSING COMPLETE ({(datetime.now() - start_time).total_seconds():.1f}s)")
        print("="*60)


if __name__ == "__main__":
    try:
        processor = DataProcessor()
        processor.run()
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {str(e)}")
        sys.exit(1)
