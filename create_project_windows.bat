@echo off
REM Windows Batch Script to Create EM-CFC-OSINT Project
REM This script recreates all project files locally

echo ========================================
echo  Creating EM-CFC-OSINT Project Files
echo ========================================
echo.

REM Create directory structure
mkdir em-cfc-osint
cd em-cfc-osint
mkdir config collectors pipelines models engine utils

echo Creating project files...

REM Create requirements.txt
(
echo pandas==2.1.4
echo numpy==1.26.3
echo redis==5.0.1
echo streamlit==1.29.0
echo scikit-learn==1.3.2
echo requests==2.31.0
echo python-dotenv==1.0.0
) > requirements.txt

echo ✓ requirements.txt created

REM Create .gitignore
(
echo __pycache__/
echo *.pyc
echo venv/
echo .env
echo .DS_Store
echo *.log
) > .gitignore

echo ✓ .gitignore created

REM Create README.md
(
echo # EM-CFC-OSINT Intelligence System
echo.
echo Production-ready financial intelligence system for emerging markets.
echo.
echo ## Features
echo - Data collection from FRED, satellite, and alternative sources
echo - 30-day statistical forecasting
echo - Monte Carlo simulation ^(1000 iterations^)
echo - Real-time Streamlit dashboard
echo - Zero-cost deployment
echo.
echo ## Quick Start
echo ```bash
echo pip install -r requirements.txt
echo streamlit run app.py
echo ```
echo.
echo ## Documentation
echo - DEPLOYMENT.md - Cloud deployment guide
echo - See full docs in repository
echo.
echo ## Cost
echo $0/month operational cost using GCP free tier + Streamlit Cloud
) > README.md

echo ✓ README.md created

echo.
echo ========================================
echo  Core files created!
echo ========================================
echo.
echo Next: Download the full Python files from the chat
echo Then run the git push commands
echo.
pause
