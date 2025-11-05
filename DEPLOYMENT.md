# EM-CFC-OSINT Deployment Guide

Complete step-by-step guide to deploying the system on free-tier cloud infrastructure.

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] GitHub account
- [ ] Google Cloud account (may need credit card for verification)
- [ ] Streamlit Cloud account (sign up with GitHub)
- [ ] FRED API key
- [ ] 2-3 hours of time

## Phase 0: Foundation Setup (15 minutes)

### Task 0.1: Create GitHub Repository

```bash
# On GitHub.com
1. Click "New repository"
2. Name: em-cfc-osint
3. Visibility: Public (required for Streamlit free tier)
4. Initialize with: README, Python .gitignore
5. Click "Create repository"
```

### Task 0.2: Clone and Add Project Files

```bash
# On your local machine
git clone https://github.com/YOUR_USERNAME/em-cfc-osint.git
cd em-cfc-osint

# Copy all project files into this directory
# (All files from the project structure)

# IMPORTANT: Edit config/settings.py
nano config/settings.py
# Replace YOUR_FRED_API_KEY_HERE with actual key

# Commit and push
git add .
git commit -m "Initial project setup with all OSINT scripts"
git push origin main
```

### Task 0.3: Get API Keys

**FRED API:**
1. Visit: https://fred.stlouisfed.org/docs/api/api_key.html
2. Sign up (free)
3. Copy your API key
4. Paste into `config/settings.py`

**Sentinel Hub (Optional):**
1. Visit: https://scihub.copernicus.eu/
2. Sign up (free)
3. Use username/password in config

## Phase 1: Local Development & Testing (30 minutes)

### Task 1.1: Local Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Task 1.2: Install Local Redis

**macOS:**
```bash
brew install redis
redis-server
```

**Ubuntu/WSL:**
```bash
sudo apt-get update
sudo apt-get install redis-server
redis-server
```

**Windows:**
1. Download Memurai from https://www.memurai.com/
2. Install and start service

**Test Redis:**
```bash
redis-cli ping  # Should return: PONG
```

### Task 1.3: Test Backend Pipeline

```bash
# Run each component
python collectors/data_ingestion.py
python pipelines/data_processing.py
python models/forecasting_engine.py
python engine/simulation_engine.py

# Verify data
redis-cli KEYS "*"
redis-cli GET "alpha_opportunities"
```

### Task 1.4: Test Frontend

```bash
streamlit run app.py
# Browser opens to localhost:8501
# Verify dashboard displays data
```

**✓ Checkpoint:** System works locally

## Phase 2: Backend Cloud Deployment (45 minutes)

### Task 2.1: Provision GCP VM

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project (e.g., "em-cfc-osint")
3. Navigate to: Compute Engine → VM instances
4. Click "Create Instance"

**Configuration:**
- Name: `em-cfc-backend`
- Region: `us-central1` (Iowa)
- Zone: `us-central1-a`
- Machine type: **e2-micro** (0.25-1 vCPU, 1GB RAM)
- Boot disk: 
  - OS: Ubuntu 22.04 LTS
  - Size: 30 GB (free tier includes 30GB)
- Firewall: 
  - ✅ Allow HTTP traffic
  - ✅ Allow HTTPS traffic

5. Click "Create"
6. Wait for VM to start (~60 seconds)

### Task 2.2: Connect to VM

```bash
# Click "SSH" button in GCP console
# A browser terminal opens

# You're now inside the VM!
```

### Task 2.3: Install VM Stack

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Git, Python, Redis
sudo apt-get install -y git python3-pip python3-venv redis-server

# Verify installations
git --version
python3 --version
redis-cli --version
```

### Task 2.4: Clone Project on VM

```bash
# Clone your repository
cd ~
git clone https://github.com/YOUR_USERNAME/em-cfc-osint.git
cd em-cfc-osint

# Create Python environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies (this takes 5-10 minutes on e2-micro)
pip install --no-cache-dir -r requirements.txt

# If installation fails due to memory, install in batches:
pip install --no-cache-dir redis streamlit
pip install --no-cache-dir pandas numpy
pip install --no-cache-dir scikit-learn statsmodels
pip install --no-cache-dir requests python-dotenv pytz
```

### Task 2.5: Configure Redis for Remote Access

```bash
# Edit Redis config
sudo nano /etc/redis/redis.conf

# Find and change these lines:
# 1. Change bind address (line ~69)
bind 127.0.0.1 ::1
# CHANGE TO:
bind 0.0.0.0

# 2. Enable password (line ~507)
# requirepass foobared
# UNCOMMENT AND CHANGE TO:
requirepass YOUR_VERY_STRONG_PASSWORD_HERE
# Example: requirepass Xk9#mP2$vL8@qR5!nW7

# 3. Enable persistence (line ~219 and ~1223)
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfilename "appendonly.aof"

# Save: Ctrl+O, Enter, Ctrl+X

# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server  # Start on boot

# Test Redis with password
redis-cli -a YOUR_VERY_STRONG_PASSWORD_HERE ping
# Should return: PONG
```

### Task 2.6: Update Config with Password

```bash
# On the VM, edit config
cd ~/em-cfc-osint
nano config/settings.py

# Change line:
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
# TO:
REDIS_PASSWORD = "YOUR_VERY_STRONG_PASSWORD_HERE"

# Save and exit
```

### Task 2.7: Test Backend on VM

```bash
# Activate venv
cd ~/em-cfc-osint
source venv/bin/activate

# Run pipeline
python collectors/data_ingestion.py
python pipelines/data_processing.py
python models/forecasting_engine.py
python engine/simulation_engine.py

# Verify
redis-cli -a YOUR_PASSWORD GET "alpha_opportunities"
# Should show JSON data
```

**✓ Checkpoint:** Backend works on GCP VM

### Task 2.8: Get VM Public IP

```bash
# In GCP Console, VM instances page
# Find "External IP" column
# Copy this IP (e.g., 34.123.45.67)
# You'll need this for Streamlit
```

## Phase 3: Frontend Cloud Deployment (20 minutes)

### Task 3.1: Configure Firewall

1. GCP Console → VPC network → Firewall
2. Click "Create Firewall Rule"

**Configuration:**
- Name: `allow-redis-external`
- Direction: Ingress
- Action on match: Allow
- Targets: All instances in network
- Source filter: IP ranges
- Source IP ranges: `0.0.0.0/0` ⚠️ (temporarily open)
- Protocols and ports: 
  - ☑️ TCP
  - Port: `6379`

3. Click "Create"

### Task 3.2: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"

**Configuration:**
- Repository: `YOUR_USERNAME/em-cfc-osint`
- Branch: `main`
- Main file path: `app.py`

4. Click "Advanced settings"
5. In the "Secrets" box, paste:

```toml
VM_PUBLIC_IP = "YOUR_VM_EXTERNAL_IP"
REDIS_PASSWORD = "YOUR_VERY_STRONG_PASSWORD_HERE"
```

6. Click "Deploy!"

**Wait 2-3 minutes for deployment...**

### Task 3.3: Verify Frontend

1. Streamlit will give you a URL (e.g., `your-app.streamlit.app`)
2. Visit the URL
3. Check sidebar: Should show "✓ Cloud Backend Connected"
4. Dashboard should display data

**✓ Checkpoint:** Full system deployed and operational

## Phase 4: Automation & Monitoring (15 minutes)

### Task 4.1: Set Up Cron Automation

```bash
# SSH back into VM
cd ~/em-cfc-osint

# Get your username
echo $USER  # Note this down

# Edit crontab
crontab -e
# If asked, select nano (option 1)

# Paste this (replace YOUR_USERNAME with actual username):
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Data collection at :00
0 * * * * cd /home/YOUR_USERNAME/em-cfc-osint && source venv/bin/activate && python collectors/data_ingestion.py >> /tmp/collector.log 2>&1 || echo "$(date): Collector failed" >> /tmp/errors.log

# Processing at :05
5 * * * * cd /home/YOUR_USERNAME/em-cfc-osint && source venv/bin/activate && python pipelines/data_processing.py >> /tmp/processing.log 2>&1 || echo "$(date): Processing failed" >> /tmp/errors.log

# Forecasting at :10
10 * * * * cd /home/YOUR_USERNAME/em-cfc-osint && source venv/bin/activate && python models/forecasting_engine.py >> /tmp/forecasting.log 2>&1 || echo "$(date): Forecasting failed" >> /tmp/errors.log

# Simulation at :15
15 * * * * cd /home/YOUR_USERNAME/em-cfc-osint && source venv/bin/activate && python engine/simulation_engine.py >> /tmp/simulation.log 2>&1 || echo "$(date): Simulation failed" >> /tmp/errors.log

# Health check at :20
20 * * * * cd /home/YOUR_USERNAME/em-cfc-osint && source venv/bin/activate && python utils/health_check.py >> /tmp/health.log 2>&1

# Log rotation daily at 3 AM
0 3 * * * find /tmp -name "*.log" -size +10M -delete

# Save: Ctrl+O, Enter, Ctrl+X

# Verify cron is scheduled
crontab -l
```

### Task 4.2: Test Cron (Optional)

```bash
# Manually trigger to test
cd ~/em-cfc-osint
source venv/bin/activate
python collectors/data_ingestion.py >> /tmp/collector.log 2>&1

# Check log
cat /tmp/collector.log
```

### Task 4.3: Monitoring Commands

```bash
# View logs in real-time
tail -f /tmp/collector.log
tail -f /tmp/errors.log

# Check Redis keys
redis-cli -a YOUR_PASSWORD KEYS "*"

# Check system health
cd ~/em-cfc-osint
source venv/bin/activate
python utils/health_check.py

# Check cron status
sudo systemctl status cron
```

## 🔒 Security Hardening (Optional but Recommended)

### Restrict Firewall to Streamlit IPs

Streamlit Cloud uses these egress IPs (as of 2024):
- `34.86.38.245`
- `34.86.176.66`
- `35.247.103.123`

```bash
# Update your firewall rule:
# 1. Go to GCP Console → VPC network → Firewall
# 2. Edit "allow-redis-external"
# 3. Change Source IP ranges from 0.0.0.0/0 to:
34.86.38.245/32,34.86.176.66/32,35.247.103.123/32
# 4. Save
```

### Additional Security

```bash
# 1. Enable UFW firewall on VM
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow from 34.86.38.245 to any port 6379
sudo ufw allow from 34.86.176.66 to any port 6379
sudo ufw allow from 35.247.103.123 to any port 6379
sudo ufw enable

# 2. Keep system updated
sudo apt-get update && sudo apt-get upgrade -y

# 3. Monitor Redis logs
sudo tail -f /var/log/redis/redis-server.log
```

## 🐛 Troubleshooting

### Issue: Frontend Can't Connect

**Symptoms:** "Backend Connection Failed" in Streamlit

**Solutions:**
```bash
# 1. Check VM is running
# GCP Console → Compute Engine → VM instances
# Status should be green/running

# 2. Check firewall rule exists
# GCP Console → VPC network → Firewall
# Verify "allow-redis-external" is there

# 3. Test Redis from external
# On your LOCAL machine:
redis-cli -h YOUR_VM_IP -a YOUR_PASSWORD ping
# Should return PONG

# 4. Check Streamlit secrets
# Verify VM_PUBLIC_IP and REDIS_PASSWORD in Streamlit settings
```

### Issue: Cron Not Running

```bash
# Check cron service
sudo systemctl status cron

# Check cron logs
sudo tail -f /var/log/syslog | grep CRON

# Check error log
cat /tmp/errors.log

# Manually run to test
cd ~/em-cfc-osint
source venv/bin/activate
python collectors/data_ingestion.py
```

### Issue: Out of Memory

```bash
# e2-micro has only 1GB RAM
# Monitor memory
free -h

# If pipelines fail, reduce iterations in config:
nano config/settings.py
# Change MONTE_CARLO_ITERATIONS from 1000 to 500
```

### Issue: Redis Data Lost After Reboot

```bash
# Check persistence is enabled
redis-cli -a YOUR_PASSWORD CONFIG GET save
redis-cli -a YOUR_PASSWORD CONFIG GET appendonly

# Should show save rules and appendonly yes
# If not, repeat Task 2.5
```

## 📊 Monitoring Dashboard

Access your system:
- **Frontend:** `https://your-app.streamlit.app`
- **VM Console:** GCP Console → Compute Engine
- **Logs:** SSH into VM → `tail -f /tmp/*.log`

## 🎉 Success Checklist

After deployment, verify:

- [ ] Streamlit app loads without errors
- [ ] "✓ Cloud Backend Connected" shows in sidebar
- [ ] Alpha Opportunities section shows data
- [ ] Economic Indicators populated
- [ ] Entity Monitoring shows entities
- [ ] System Status shows recent timestamps
- [ ] Cron jobs running (check after 1 hour)
- [ ] Health check passes: `python utils/health_check.py`

## 💰 Cost Verification

Confirm you're on free tier:
- GCP: Compute Engine → VM instances → Check "Machine type" is e2-micro
- Streamlit: Always free for public repos
- GitHub: Free tier sufficient

Expected cost: **$0.00/month** ✅

## 🔄 Maintenance

### Weekly
```bash
# SSH into VM
sudo apt-get update && sudo apt-get upgrade -y
```

### Monthly
```bash
# Check disk space
df -h

# Clean old logs
sudo find /tmp -name "*.log" -mtime +30 -delete

# Update project
cd ~/em-cfc-osint
git pull origin main
pip install --no-cache-dir -r requirements.txt
```

### As Needed
```bash
# Update API keys
nano ~/em-cfc-osint/config/settings.py
# Restart cron jobs (they'll pick up new config)

# Add new entities
nano ~/em-cfc-osint/config/settings.py
# Add to MONITORED_ENTITIES list
```

## 🚀 Next Steps

1. **Add More Data Sources:** Integrate Twitter sentiment, shipping data, etc.
2. **Improve Models:** Replace linear regression with LSTM/XGBoost
3. **Add Alerts:** Email notifications for high-alpha opportunities
4. **Scale Up:** Upgrade to larger VM if needed (exits free tier)
5. **Add Authentication:** Secure dashboard with Streamlit auth

---

**Congratulations! Your system is deployed and autonomous.** 🎉

Questions? Open an issue on GitHub.
