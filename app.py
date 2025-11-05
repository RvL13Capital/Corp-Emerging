"""
Streamlit Frontend Dashboard
Displays alpha opportunities and system status
"""
import streamlit as st
import redis
from redis.exceptions import ConnectionError, TimeoutError
import json
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Page config
st.set_page_config(
    page_title="EM-CFC OSINT Alpha Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


def get_redis_client():
    """Initialize Redis with retry logic and secrets support"""
    
    # Check if running on Streamlit Cloud (secrets available)
    if hasattr(st, 'secrets') and 'VM_PUBLIC_IP' in st.secrets:
        host = st.secrets["VM_PUBLIC_IP"]
        password = st.secrets["REDIS_PASSWORD"]
        connection_type = "Cloud Backend"
    else:
        # Local development
        host = "localhost"
        password = None
        connection_type = "Local Redis"
    
    try:
        client = redis.Redis(
            host=host,
            port=6379,
            db=0,
            password=password,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )
        client.ping()
        return client, None, connection_type
    except (ConnectionError, TimeoutError) as e:
        return None, f"Connection timeout: {str(e)}", connection_type
    except Exception as e:
        return None, f"Error: {str(e)}", connection_type


class Dashboard:
    """Main dashboard application"""
    
    def __init__(self):
        """Initialize dashboard"""
        self.cache, error, conn_type = get_redis_client()
        
        if error:
            st.sidebar.error(f"❌ Backend: {error}")
            st.error("### Backend Connection Failed")
            st.info("""
            **Troubleshooting:**
            - Ensure Redis is running
            - Check firewall rules (port 6379)
            - Verify credentials in Streamlit secrets
            - Check VM is running (for cloud deployment)
            """)
            st.stop()
        else:
            st.sidebar.success(f"✓ {conn_type} Connected")
    
    def load_data(self, key):
        """Load and parse JSON data from Redis"""
        try:
            data = self.cache.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            st.error(f"Error loading {key}: {str(e)}")
            return None
    
    def render_header(self):
        """Render dashboard header"""
        st.title("📊 EM-CFC OSINT Alpha Dashboard")
        st.markdown("**Emerging Markets Commodity-Finance Complex Intelligence System**")
        
        # System status
        col1, col2, col3, col4 = st.columns(4)
        
        # Last collection
        collection_meta = self.load_data("raw:metadata:last_collection")
        with col1:
            if collection_meta:
                ts = collection_meta.get("timestamp", "N/A")
                st.metric("Last Data Collection", 
                         datetime.fromisoformat(ts).strftime("%H:%M") if ts != "N/A" else "N/A")
            else:
                st.metric("Last Data Collection", "No data")
        
        # Last processing
        processing_meta = self.load_data("processed:metadata:last_processing")
        with col2:
            if processing_meta:
                ts = processing_meta.get("timestamp", "N/A")
                st.metric("Last Processing", 
                         datetime.fromisoformat(ts).strftime("%H:%M") if ts != "N/A" else "N/A")
            else:
                st.metric("Last Processing", "No data")
        
        # Last forecast
        forecast_meta = self.load_data("forecasts:metadata:last_forecast")
        with col3:
            if forecast_meta:
                ts = forecast_meta.get("timestamp", "N/A")
                st.metric("Last Forecast", 
                         datetime.fromisoformat(ts).strftime("%H:%M") if ts != "N/A" else "N/A")
            else:
                st.metric("Last Forecast", "No data")
        
        # System health
        with col4:
            if collection_meta and processing_meta and forecast_meta:
                st.metric("System Status", "✓ Operational", delta="Healthy")
            else:
                st.metric("System Status", "⚠ Partial", delta="Check logs")
        
        st.markdown("---")
    
    def render_opportunities(self):
        """Render alpha opportunities section"""
        st.header("🎯 Alpha Opportunities")
        
        opps_data = self.load_data("alpha_opportunities")
        
        if not opps_data:
            st.warning("No opportunity data available. Run the simulation engine.")
            return
        
        opportunities = opps_data.get("opportunities", [])
        threshold = opps_data.get("threshold_pct", 15)
        
        if not opportunities:
            st.info(f"No opportunities above {threshold}% threshold found.")
            
            # Show all evaluations instead
            all_evals = opps_data.get("all_evaluations", [])
            if all_evals:
                st.subheader("All Entity Evaluations")
                df = pd.DataFrame(all_evals)
                df = df[["entity_name", "expected_return_pct", "sharpe_ratio", 
                        "confidence", "risk_level", "rating"]]
                df = df.sort_values("expected_return_pct", ascending=False)
                st.dataframe(df, use_container_width=True)
            return
        
        # Display opportunities
        st.success(f"Found {len(opportunities)} opportunities above {threshold}% threshold")
        
        for i, opp in enumerate(opportunities):
            with st.expander(f"🔥 #{i+1}: {opp['entity_name']} - {opp['expected_return_pct']:.1f}% Expected Return", 
                           expanded=(i==0)):
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Expected Return", f"{opp['expected_return_pct']:.1f}%")
                    st.metric("Alpha Score", f"{opp['alpha_score']:.1f}")
                
                with col2:
                    st.metric("Sharpe Ratio", f"{opp['sharpe_ratio']:.2f}")
                    st.metric("Prob. Positive", f"{opp['probability_positive']:.1f}%")
                
                with col3:
                    st.metric("Risk Level", opp['risk_level'].upper())
                    st.metric("Confidence", opp['confidence'].upper())
                
                # Percentile distribution
                st.markdown("**Return Distribution (Monte Carlo)**")
                perc = opp['percentiles']
                dist_df = pd.DataFrame({
                    "Percentile": ["P5 (Worst Case)", "P50 (Median)", "P95 (Best Case)"],
                    "Value": [perc['p5'], perc['p50'], perc['p95']]
                })
                st.dataframe(dist_df, use_container_width=True)
                
                # Additional context
                st.markdown(f"""
                **Analysis:**
                - Rating: {opp['rating'].upper()}
                - Volatility: {opp['volatility_pct']:.1f}%
                - Job Momentum: {opp['job_momentum']:.1f}%
                - Last Updated: {opp['timestamp'][:19]}
                """)
    
    def render_economic_indicators(self):
        """Render economic indicators section"""
        st.header("📈 Economic Indicators")
        
        indicators = self.load_data("processed:economic_indicators")
        
        if not indicators:
            st.warning("No economic data available.")
            return
        
        features = indicators.get("features", {})
        
        if not features:
            st.info("No indicator features processed yet.")
            return
        
        # Create DataFrame
        data = []
        for name, values in features.items():
            data.append({
                "Indicator": name.replace("_", " ").title(),
                "Current": f"{values['current']:.2f}",
                "Change %": f"{values['change_pct']:+.2f}%",
                "vs 30d Avg": f"{values['vs_30d_avg']:+.2f}%",
                "Trend": values['trend'].upper()
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    
    def render_entity_status(self):
        """Render entity monitoring status"""
        st.header("🏢 Entity Monitoring")
        
        entities = self.load_data("processed:entity_vectors")
        
        if not entities:
            st.warning("No entity data available.")
            return
        
        entity_data = entities.get("entities", {})
        
        if not entity_data:
            st.info("No entities processed yet.")
            return
        
        # Create DataFrame
        data = []
        for name, entity_info in entity_data.items():
            features = entity_info.get("features", {})
            data.append({
                "Entity": name,
                "Activity": f"{features.get('activity_current', 0):.1f}",
                "Activity Trend": f"{features.get('activity_trend', 0):+.1f}",
                "Jobs (Current)": int(features.get('jobs_current', 0)),
                "Jobs Trend": f"{features.get('jobs_trend', 0):+.0f}",
                "Composite Score": f"{features.get('composite_score', 0):.1f}"
            })
        
        df = pd.DataFrame(data)
        df = df.sort_values("Composite Score", ascending=False)
        st.dataframe(df, use_container_width=True)
    
    def render_sidebar(self):
        """Render sidebar with controls and info"""
        st.sidebar.title("⚙️ Controls")
        
        if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 System Info")
        
        # Count keys
        try:
            raw_keys = len(self.cache.keys("raw:*"))
            processed_keys = len(self.cache.keys("processed:*"))
            forecast_keys = len(self.cache.keys("forecasts:*"))
            
            st.sidebar.metric("Raw Data Keys", raw_keys)
            st.sidebar.metric("Processed Keys", processed_keys)
            st.sidebar.metric("Forecast Keys", forecast_keys)
        except:
            st.sidebar.info("Metrics unavailable")
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ℹ️ About")
        st.sidebar.info("""
        **EM-CFC-OSINT System**
        
        An autonomous intelligence system for emerging markets analysis.
        
        **Data Sources:**
        - FRED Economic Data
        - Satellite Imagery
        - Job Postings
        
        **Pipeline:**
        1. Data Collection
        2. Feature Engineering  
        3. Forecasting
        4. Monte Carlo Simulation
        """)
    
    def run(self):
        """Run the dashboard"""
        self.render_header()
        self.render_sidebar()
        
        # Main content tabs
        tab1, tab2, tab3 = st.tabs(["🎯 Opportunities", "📈 Economics", "🏢 Entities"])
        
        with tab1:
            self.render_opportunities()
        
        with tab2:
            self.render_economic_indicators()
        
        with tab3:
            self.render_entity_status()
        
        # Footer
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: gray;'>"
            "EM-CFC-OSINT v1.0 | Free Tier Hybrid Cloud Architecture"
            "</div>",
            unsafe_allow_html=True
        )


if __name__ == "__main__":
    dashboard = Dashboard()
    dashboard.run()
