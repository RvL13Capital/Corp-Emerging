"""
Configuration settings for EM-CFC-OSINT System
Replace placeholders with your actual API keys
"""
import os
from datetime import datetime, timedelta

# ============================================
# API KEYS (REPLACE WITH YOUR ACTUAL KEYS)
# ============================================

# FRED API (Federal Reserve Economic Data)
FRED_API_KEY = "YOUR_FRED_API_KEY_HERE"  # Get from: https://fred.stlouisfed.org/docs/api/api_key.html

# Copernicus Sentinel Hub
SENTINEL_USERNAME = "YOUR_SENTINEL_USERNAME"  # Get from: https://scihub.copernicus.eu/
SENTINEL_PASSWORD = "YOUR_SENTINEL_PASSWORD"

# ============================================
# REDIS CONFIGURATION
# ============================================

# Local development
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)  # None for local, set for production
REDIS_DB = 0

# ============================================
# DATA COLLECTION SETTINGS
# ============================================

# Economic indicators to track (FRED series IDs)
ECONOMIC_INDICATORS = {
    "unemployment": "UNRATE",
    "gdp": "GDP",
    "inflation": "CPIAUCSL",
    "fed_funds": "FEDFUNDS",
    "industrial_production": "INDPRO",
    "retail_sales": "RSXFS",
    "housing_starts": "HOUST",
    "consumer_sentiment": "UMCSENT"
}

# Entities to monitor (example: mining companies, energy firms)
MONITORED_ENTITIES = [
    {"name": "VALE", "type": "mining", "lat": -19.9167, "lon": -43.9345},  # Vale HQ
    {"name": "BHP", "type": "mining", "lat": -37.8136, "lon": 144.9631},   # BHP Melbourne
    {"name": "RIO", "type": "mining", "lat": 51.5074, "lon": -0.1278},     # Rio Tinto London
    {"name": "EXXON", "type": "energy", "lat": 32.7767, "lon": -96.7970},  # Exxon Dallas
    {"name": "CHEVRON", "type": "energy", "lat": 37.7749, "lon": -122.4194} # Chevron SF
]

# Satellite data parameters
SENTINEL_CLOUD_COVER_MAX = 20  # Maximum cloud cover percentage
SENTINEL_LOOKBACK_DAYS = 30    # Days to look back for imagery

# ============================================
# PROCESSING SETTINGS
# ============================================

# Feature engineering
TECHNICAL_INDICATORS = ["SMA_5", "SMA_20", "RSI_14", "MACD"]
NORMALIZATION_METHOD = "zscore"  # or "minmax"

# ============================================
# FORECASTING SETTINGS
# ============================================

FORECAST_HORIZON = 30  # Days ahead to forecast
CONFIDENCE_LEVEL = 0.95
MIN_HISTORICAL_DAYS = 90  # Minimum data required

# ============================================
# SIMULATION ENGINE SETTINGS
# ============================================

MONTE_CARLO_ITERATIONS = 1000
RISK_FREE_RATE = 0.045  # 4.5% annual
OPPORTUNITY_THRESHOLD = 0.15  # 15% expected return minimum

# ============================================
# LOGGING
# ============================================

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ============================================
# SYSTEM METADATA
# ============================================

SYSTEM_VERSION = "1.0.0"
LAST_UPDATED = datetime.now().isoformat()
