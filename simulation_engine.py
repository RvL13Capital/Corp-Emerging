"""
Simulation Engine
Runs Monte Carlo simulations and identifies alpha opportunities
Stores opportunities in Redis
"""
import redis
import json
import sys
from datetime import datetime
from pathlib import Path
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import (
    REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB,
    MONTE_CARLO_ITERATIONS, RISK_FREE_RATE, OPPORTUNITY_THRESHOLD
)


class SimulationEngine:
    """Identifies alpha opportunities using simulation"""
    
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
    
    def monte_carlo_simulation(self, current_value, trend_strength, volatility, days=30):
        """
        Run Monte Carlo simulation for expected returns
        
        Args:
            current_value: Current activity/metric value
            trend_strength: % change expected
            volatility: Historical volatility
            days: Simulation horizon
            
        Returns:
            dict with simulation results
        """
        np.random.seed(None)  # Ensure randomness
        
        # Convert to daily parameters
        daily_return = trend_strength / 100 / days
        daily_vol = volatility / np.sqrt(days) if volatility > 0 else 0.01
        
        # Run simulations
        final_values = []
        
        for _ in range(MONTE_CARLO_ITERATIONS):
            value = current_value
            
            for _ in range(days):
                shock = np.random.normal(daily_return, daily_vol)
                value *= (1 + shock)
            
            final_values.append(value)
        
        final_values = np.array(final_values)
        
        # Calculate statistics
        expected_return = (np.mean(final_values) - current_value) / current_value * 100
        std_dev = np.std(final_values) / current_value * 100
        
        # Percentiles
        p5 = np.percentile(final_values, 5)
        p50 = np.percentile(final_values, 50)
        p95 = np.percentile(final_values, 95)
        
        # Sharpe-like metric
        excess_return = expected_return - (RISK_FREE_RATE * 100)
        sharpe = excess_return / std_dev if std_dev > 0 else 0
        
        return {
            "expected_return_pct": float(expected_return),
            "volatility_pct": float(std_dev),
            "sharpe_ratio": float(sharpe),
            "percentile_5": float(p5),
            "percentile_50": float(p50),
            "percentile_95": float(p95),
            "probability_positive": float(np.sum(final_values > current_value) / MONTE_CARLO_ITERATIONS * 100)
        }
    
    def evaluate_opportunity(self, entity_name, forecast_data):
        """Evaluate if an entity presents an alpha opportunity"""
        try:
            # Extract key metrics
            if "activity" not in forecast_data:
                return None
            
            activity = forecast_data["activity"]
            jobs = forecast_data.get("jobs", {})
            
            current = activity["current_value"]
            trend = activity["trend_strength"]
            
            # Estimate volatility from forecast spread
            forecast_values = [f["predicted_activity"] for f in activity["forecast"][:7]]
            volatility = float(np.std(forecast_values))
            
            # Run simulation
            sim_results = self.monte_carlo_simulation(
                current_value=current,
                trend_strength=trend,
                volatility=volatility,
                days=30
            )
            
            # Combine with job data
            job_signal = jobs.get("momentum_pct", 0) if jobs else 0
            
            # Calculate composite alpha score
            alpha_score = (
                sim_results["expected_return_pct"] * 0.5 +
                job_signal * 0.3 +
                sim_results["sharpe_ratio"] * 10 * 0.2
            )
            
            # Determine confidence
            confidence = "high" if sim_results["probability_positive"] > 70 else \
                        "medium" if sim_results["probability_positive"] > 55 else "low"
            
            # Risk rating
            risk = "low" if sim_results["volatility_pct"] < 10 else \
                   "medium" if sim_results["volatility_pct"] < 20 else "high"
            
            opportunity = {
                "entity_name": entity_name,
                "alpha_score": float(alpha_score),
                "expected_return_pct": sim_results["expected_return_pct"],
                "sharpe_ratio": sim_results["sharpe_ratio"],
                "volatility_pct": sim_results["volatility_pct"],
                "probability_positive": sim_results["probability_positive"],
                "job_momentum": float(job_signal),
                "confidence": confidence,
                "risk_level": risk,
                "percentiles": {
                    "p5": sim_results["percentile_5"],
                    "p50": sim_results["percentile_50"],
                    "p95": sim_results["percentile_95"]
                },
                "rating": forecast_data.get("rating", "neutral"),
                "timestamp": datetime.now().isoformat()
            }
            
            return opportunity
            
        except Exception as e:
            print(f"    Error evaluating {entity_name}: {str(e)}")
            return None
    
    def identify_opportunities(self):
        """Identify all alpha opportunities"""
        print("\n[1/1] Running Simulations & Identifying Opportunities...")
        
        # Load forecasts
        forecasts_raw = self.redis.get("forecasts:all_entities")
        if not forecasts_raw:
            print("  ✗ No forecasts found")
            return
        
        forecasts_data = json.loads(forecasts_raw)
        forecasts = forecasts_data.get("forecasts", {})
        
        opportunities = []
        
        for entity_name, forecast in forecasts.items():
            print(f"  Evaluating {entity_name}...")
            
            opp = self.evaluate_opportunity(entity_name, forecast)
            
            if opp:
                opportunities.append(opp)
                
                # Only flag as "opportunity" if meets threshold
                if opp["expected_return_pct"] > OPPORTUNITY_THRESHOLD * 100:
                    print(f"    ✓ OPPORTUNITY: {opp['expected_return_pct']:.1f}% expected return")
                    print(f"      Sharpe={opp['sharpe_ratio']:.2f}, Risk={opp['risk_level']}, Confidence={opp['confidence']}")
                else:
                    print(f"    • Monitored: {opp['expected_return_pct']:.1f}% expected return")
        
        # Sort by alpha score
        opportunities.sort(key=lambda x: x["alpha_score"], reverse=True)
        
        # Filter for top opportunities
        top_opportunities = [opp for opp in opportunities 
                           if opp["expected_return_pct"] > OPPORTUNITY_THRESHOLD * 100]
        
        # Store results
        self.redis.set("alpha_opportunities", json.dumps({
            "opportunities": top_opportunities,
            "all_evaluations": opportunities,
            "threshold_pct": OPPORTUNITY_THRESHOLD * 100,
            "timestamp": datetime.now().isoformat(),
            "monte_carlo_iterations": MONTE_CARLO_ITERATIONS
        }))
        
        print(f"\n  → Found {len(top_opportunities)} opportunities above threshold")
        print(f"  → Evaluated {len(opportunities)} total entities")
    
    def run(self):
        """Execute simulation engine"""
        print("="*60)
        print("SIMULATION ENGINE STARTED")
        print("="*60)
        
        start_time = datetime.now()
        
        self.identify_opportunities()
        
        # Store metadata
        self.redis.set("simulation:metadata:last_run", json.dumps({
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "status": "success"
        }))
        
        print("="*60)
        print(f"SIMULATION COMPLETE ({(datetime.now() - start_time).total_seconds():.1f}s)")
        print("="*60)


if __name__ == "__main__":
    try:
        engine = SimulationEngine()
        engine.run()
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {str(e)}")
        sys.exit(1)
