"""
Forecasting Engine
Generates forward-looking predictions using statistical models
Stores forecasts in Redis with 'forecasts:' prefix
"""
import redis
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import (
    REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB,
    FORECAST_HORIZON, CONFIDENCE_LEVEL
)


class ForecastingEngine:
    """Generates forecasts for entities and economic indicators"""
    
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
    
    def forecast_entity_activity(self, entity_name, historical_data):
        """
        Forecast entity activity using simple linear regression
        In production, this would use LSTM or more sophisticated models
        """
        try:
            observations = historical_data.get("observations", [])
            
            if len(observations) < 10:
                return None
            
            # Prepare data
            activity_scores = [obs["activity_score"] for obs in observations]
            X = np.arange(len(activity_scores)).reshape(-1, 1)
            y = np.array(activity_scores)
            
            # Fit model
            model = LinearRegression()
            model.fit(X, y)
            
            # Generate forecast
            future_X = np.arange(len(activity_scores), 
                                len(activity_scores) + FORECAST_HORIZON).reshape(-1, 1)
            forecast = model.predict(future_X)
            
            # Calculate confidence intervals (simple ±2 std)
            residuals = y - model.predict(X)
            std_error = np.std(residuals)
            
            forecast_dates = [
                (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
                for i in range(1, FORECAST_HORIZON + 1)
            ]
            
            forecast_data = []
            for i, (date, value) in enumerate(zip(forecast_dates, forecast)):
                forecast_data.append({
                    "date": date,
                    "predicted_activity": float(np.clip(value, 0, 100)),
                    "lower_bound": float(np.clip(value - 2*std_error, 0, 100)),
                    "upper_bound": float(np.clip(value + 2*std_error, 0, 100)),
                    "confidence": float(CONFIDENCE_LEVEL)
                })
            
            # Calculate trend strength
            current_avg = np.mean(activity_scores[-7:])
            forecast_avg = np.mean(forecast[:7])
            trend_strength = ((forecast_avg - current_avg) / current_avg * 100) if current_avg > 0 else 0
            
            return {
                "forecast": forecast_data,
                "current_value": float(activity_scores[-1]),
                "forecast_mean": float(np.mean(forecast)),
                "trend_strength": float(trend_strength),
                "model_r2": float(model.score(X, y))
            }
            
        except Exception as e:
            print(f"    Error forecasting {entity_name}: {str(e)}")
            return None
    
    def forecast_job_growth(self, entity_name, job_data):
        """Forecast job posting trends"""
        try:
            postings = job_data.get("job_postings", [])
            
            if len(postings) < 6:
                return None
            
            counts = [p["count"] for p in postings]
            
            # Simple moving average forecast
            ma_3 = np.mean(counts[:3])
            ma_6 = np.mean(counts[:6])
            
            # Momentum indicator
            momentum = (ma_3 - ma_6) / ma_6 * 100 if ma_6 > 0 else 0
            
            return {
                "current_postings": counts[0],
                "ma_3_month": float(ma_3),
                "ma_6_month": float(ma_6),
                "momentum_pct": float(momentum),
                "trend": "expansion" if momentum > 5 else "contraction" if momentum < -5 else "stable"
            }
            
        except Exception as e:
            print(f"    Error forecasting jobs for {entity_name}: {str(e)}")
            return None
    
    def generate_all_forecasts(self):
        """Generate forecasts for all entities"""
        print("\n[1/1] Generating Forecasts...")
        
        all_forecasts = {}
        
        # Get processed entity vectors
        entity_vectors_raw = self.redis.get("processed:entity_vectors")
        if not entity_vectors_raw:
            print("  ✗ No processed entity data found")
            return
        
        entity_vectors = json.loads(entity_vectors_raw)
        entities = entity_vectors.get("entities", {})
        
        for entity_name in entities.keys():
            print(f"  Processing {entity_name}...")
            
            # Load raw data
            sat_data = self.redis.get(f"raw:satellite:{entity_name}")
            job_data = self.redis.get(f"raw:jobs:{entity_name}")
            
            entity_forecast = {
                "entity_name": entity_name,
                "timestamp": datetime.now().isoformat()
            }
            
            # Activity forecast
            if sat_data:
                sat_json = json.loads(sat_data)
                activity_forecast = self.forecast_entity_activity(entity_name, sat_json)
                if activity_forecast:
                    entity_forecast["activity"] = activity_forecast
                    print(f"    ✓ Activity: trend={activity_forecast['trend_strength']:+.1f}%")
            
            # Job forecast
            if job_data:
                job_json = json.loads(job_data)
                job_forecast = self.forecast_job_growth(entity_name, job_json)
                if job_forecast:
                    entity_forecast["jobs"] = job_forecast
                    print(f"    ✓ Jobs: {job_forecast['trend']} ({job_forecast['momentum_pct']:+.1f}%)")
            
            # Calculate composite outlook score
            if "activity" in entity_forecast and "jobs" in entity_forecast:
                composite = (
                    entity_forecast["activity"]["trend_strength"] * 0.6 +
                    entity_forecast["jobs"]["momentum_pct"] * 0.4
                )
                entity_forecast["composite_outlook"] = float(composite)
                entity_forecast["rating"] = (
                    "bullish" if composite > 10 else
                    "bearish" if composite < -10 else
                    "neutral"
                )
                print(f"    → Outlook: {entity_forecast['rating'].upper()} ({composite:+.1f})")
            
            all_forecasts[entity_name] = entity_forecast
        
        # Store all forecasts
        self.redis.set("forecasts:all_entities", json.dumps({
            "forecasts": all_forecasts,
            "horizon_days": FORECAST_HORIZON,
            "timestamp": datetime.now().isoformat()
        }))
        
        return all_forecasts
    
    def run(self):
        """Execute forecasting engine"""
        print("="*60)
        print("FORECASTING ENGINE STARTED")
        print("="*60)
        
        start_time = datetime.now()
        
        self.generate_all_forecasts()
        
        # Store metadata
        self.redis.set("forecasts:metadata:last_forecast", json.dumps({
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "status": "success",
            "horizon_days": FORECAST_HORIZON
        }))
        
        print("="*60)
        print(f"FORECASTING COMPLETE ({(datetime.now() - start_time).total_seconds():.1f}s)")
        print("="*60)


if __name__ == "__main__":
    try:
        engine = ForecastingEngine()
        engine.run()
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {str(e)}")
        sys.exit(1)
