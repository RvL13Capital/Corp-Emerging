# EM-CFC-OSINT: Emerging Markets Intelligence System

![Status](https://img.shields.io/badge/status-production-green)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

An autonomous OSINT-driven intelligence system for emerging markets analysis, running entirely on free-tier cloud infrastructure ($0/month operational cost).

## 🎯 What This Does

This system:
- **Collects** economic data (FRED API), satellite observations, and alternative data
- **Processes** raw data into engineered features
- **Forecasts** entity activity using statistical models
- **Simulates** thousands of scenarios via Monte Carlo
- **Identifies** alpha opportunities with quantified risk/return profiles

## 🏗️ Architecture

```
┌─────────────────────┐         ┌──────────────────────┐
│   BACKEND (GCP VM)  │         │  FRONTEND (Streamlit)│
│                     │◄───────►│                      │
│  • Redis Database   │         │  • Dashboard UI      │
│  • Python Scripts   │         │  • Visualizations    │
│  • Cron Scheduler   │         │                      │
└─────────────────────┘         └──────────────────────┘
         ▲                               ▲
         │                               │
         └───────────┬───────────────────┘
                     │
              ┌──────▼──────┐
              │   GitHub    │
              │ (Code Repo) │
              └─────────────┘
```

## 📁 Project Structure

```
em-cfc-osint/
├── config/
│   └── settings.py          # Configuration & API keys
├── collectors/
│   └── data_ingestion.py    # Fetches raw data
├── pipelines/
│   └── data_processing.py   # Feature engineering
├── models/
│   └── forecasting_engine.py # Predictions
├── engine/
│   └── simulation_engine.py  # Monte Carlo & opportunities
├── utils/
│   └── health_check.py      # System monitoring
├── app.py                   # Streamlit dashboard
├── requirements.txt         # Dependencies
├── .gitignore
├── README.md               # This file
└── DEPLOYMENT.md           # Detailed deployment guide
```

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.9+
- Redis installed locally
- API keys (see below)

### 1. Get API Keys (Free)

```bash
# FRED API
Visit: https://fred.stlouisfed.org/docs/api/api_key.html

# Copernicus Sentinel (optional for this demo)
Visit: https://scihub.copernicus.eu/
```

### 2. Clone & Setup

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/em-cfc-osint.git
cd em-cfc-osint

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Edit config with your API keys
nano config/settings.py
```

### 3. Start Local Redis

```bash
# macOS
brew install redis
redis-server

# Ubuntu/WSL
sudo apt-get install redis-server
redis-server

# Windows
# Download Memurai from memurai.com
```

### 4. Run the Pipeline

```bash
# Collect data
python collectors/data_ingestion.py

# Process data
python pipelines/data_processing.py

# Generate forecasts
python models/forecasting_engine.py

# Run simulations
python engine/simulation_engine.py

# Verify data in Redis
redis-cli KEYS "*"
```

### 5. Launch Dashboard

```bash
streamlit run app.py
```

Open browser to `http://localhost:8501` 🎉

## ☁️ Cloud Deployment

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for complete cloud deployment instructions.

**Summary:**
1. Deploy backend to GCP e2-micro VM (free tier)
2. Configure Redis with persistence
3. Deploy frontend to Streamlit Cloud (free)
4. Set up cron automation (hourly updates)

## 📊 Dashboard Features

- **Alpha Opportunities**: Ranked investment opportunities with Monte Carlo-derived risk/return
- **Economic Indicators**: Real-time macro data from FRED
- **Entity Monitoring**: Activity scores for tracked entities
- **System Health**: Pipeline status and data freshness

## 🔧 Configuration

Key settings in `config/settings.py`:

```python
# Economic indicators to track
ECONOMIC_INDICATORS = {
    "unemployment": "UNRATE",
    "gdp": "GDP",
    # ... add more
}

# Entities to monitor
MONITORED_ENTITIES = [
    {"name": "VALE", "type": "mining", "lat": -19.9167, "lon": -43.9345},
    # ... add more
]

# Simulation parameters
MONTE_CARLO_ITERATIONS = 1000
OPPORTUNITY_THRESHOLD = 0.15  # 15% minimum expected return
```

## 🛠️ Troubleshooting

### Redis Connection Failed
```bash
# Check Redis is running
redis-cli ping  # Should return PONG

# Check connection
redis-cli -h YOUR_VM_IP -a YOUR_PASSWORD ping
```

### Data Not Updating
```bash
# Check cron logs
cat /tmp/collector.log
cat /tmp/errors.log

# Check Redis keys
redis-cli -a YOUR_PASSWORD KEYS "*"

# Run health check
python utils/health_check.py
```

### Streamlit Cloud Connection Issues
- Verify VM public IP in secrets
- Check GCP firewall allows port 6379
- Confirm Redis password matches

## 📈 System Monitoring

```bash
# Health check
python utils/health_check.py

# View logs
tail -f /tmp/collector.log
tail -f /tmp/processing.log
tail -f /tmp/forecasting.log
tail -f /tmp/simulation.log
tail -f /tmp/errors.log

# Redis stats
redis-cli INFO stats
```

## 🔐 Security Notes

- Never commit API keys to Git
- Use strong Redis passwords in production
- Restrict firewall to Streamlit IPs (see DEPLOYMENT.md)
- Enable Redis AUTH
- Use HTTPS for all connections

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📞 Support

- **Issues**: Open a GitHub issue
- **Docs**: See DEPLOYMENT.md for detailed setup
- **Community**: [GitHub Discussions](https://github.com/YOUR_USERNAME/em-cfc-osint/discussions)

## 🎓 Learn More

- [Streamlit Docs](https://docs.streamlit.io)
- [Redis Documentation](https://redis.io/docs)
- [GCP Free Tier](https://cloud.google.com/free)
- [FRED API](https://fred.stlouisfed.org/docs/api/)

---

**Built with ❤️ using free-tier cloud services**
