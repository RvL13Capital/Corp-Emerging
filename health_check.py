"""
Health Check Utility
Monitors system health and writes status to Redis
"""
import redis
import json
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB


def check_pipeline_health():
    """Check if all pipeline stages are healthy"""
    
    try:
        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True
        )
        r.ping()
    except Exception as e:
        print(f"✗ Redis connection failed: {str(e)}")
        return False
    
    health_status = {
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    all_healthy = True
    
    # Check 1: Data collection
    try:
        meta = r.get("raw:metadata:last_collection")
        if meta:
            data = json.loads(meta)
            last_update = datetime.fromisoformat(data["timestamp"])
            age = (datetime.now() - last_update).total_seconds() / 3600
            
            if age < 2:  # Should update every hour
                health_status["checks"]["collection"] = "✓ OK"
                print(f"✓ Collection: OK ({age:.1f}h ago)")
            else:
                health_status["checks"]["collection"] = f"⚠ Stale ({age:.1f}h)"
                print(f"⚠ Collection: Stale ({age:.1f}h ago)")
                all_healthy = False
        else:
            health_status["checks"]["collection"] = "✗ No data"
            print("✗ Collection: No data")
            all_healthy = False
    except Exception as e:
        health_status["checks"]["collection"] = f"✗ Error: {str(e)}"
        print(f"✗ Collection check failed: {str(e)}")
        all_healthy = False
    
    # Check 2: Processing
    try:
        meta = r.get("processed:metadata:last_processing")
        if meta:
            data = json.loads(meta)
            last_update = datetime.fromisoformat(data["timestamp"])
            age = (datetime.now() - last_update).total_seconds() / 3600
            
            if age < 2:
                health_status["checks"]["processing"] = "✓ OK"
                print(f"✓ Processing: OK ({age:.1f}h ago)")
            else:
                health_status["checks"]["processing"] = f"⚠ Stale ({age:.1f}h)"
                print(f"⚠ Processing: Stale ({age:.1f}h ago)")
                all_healthy = False
        else:
            health_status["checks"]["processing"] = "✗ No data"
            print("✗ Processing: No data")
            all_healthy = False
    except Exception as e:
        health_status["checks"]["processing"] = f"✗ Error: {str(e)}"
        print(f"✗ Processing check failed: {str(e)}")
        all_healthy = False
    
    # Check 3: Forecasting
    try:
        meta = r.get("forecasts:metadata:last_forecast")
        if meta:
            data = json.loads(meta)
            last_update = datetime.fromisoformat(data["timestamp"])
            age = (datetime.now() - last_update).total_seconds() / 3600
            
            if age < 2:
                health_status["checks"]["forecasting"] = "✓ OK"
                print(f"✓ Forecasting: OK ({age:.1f}h ago)")
            else:
                health_status["checks"]["forecasting"] = f"⚠ Stale ({age:.1f}h)"
                print(f"⚠ Forecasting: Stale ({age:.1f}h ago)")
                all_healthy = False
        else:
            health_status["checks"]["forecasting"] = "✗ No data"
            print("✗ Forecasting: No data")
            all_healthy = False
    except Exception as e:
        health_status["checks"]["forecasting"] = f"✗ Error: {str(e)}"
        print(f"✗ Forecasting check failed: {str(e)}")
        all_healthy = False
    
    # Check 4: Simulation
    try:
        meta = r.get("simulation:metadata:last_run")
        if meta:
            data = json.loads(meta)
            last_update = datetime.fromisoformat(data["timestamp"])
            age = (datetime.now() - last_update).total_seconds() / 3600
            
            if age < 2:
                health_status["checks"]["simulation"] = "✓ OK"
                print(f"✓ Simulation: OK ({age:.1f}h ago)")
            else:
                health_status["checks"]["simulation"] = f"⚠ Stale ({age:.1f}h)"
                print(f"⚠ Simulation: Stale ({age:.1f}h ago)")
                all_healthy = False
        else:
            health_status["checks"]["simulation"] = "✗ No data"
            print("✗ Simulation: No data")
            all_healthy = False
    except Exception as e:
        health_status["checks"]["simulation"] = f"✗ Error: {str(e)}"
        print(f"✗ Simulation check failed: {str(e)}")
        all_healthy = False
    
    # Overall status
    health_status["overall"] = "healthy" if all_healthy else "degraded"
    
    # Write to Redis
    r.set("system:health_status", json.dumps(health_status))
    
    print(f"\n{'='*60}")
    print(f"Overall Status: {health_status['overall'].upper()}")
    print(f"{'='*60}")
    
    return all_healthy


if __name__ == "__main__":
    try:
        healthy = check_pipeline_health()
        sys.exit(0 if healthy else 1)
    except Exception as e:
        print(f"✗ Health check failed: {str(e)}")
        sys.exit(1)
