import sys
import os

# Root directory ko Python path me add karein
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import time
import json

st.set_page_config(
    page_title="ScrapeShield AI", 
    page_icon="🛡️", 
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ ScrapeShield AI — Self-Healing Scraper Engine")
st.caption("Powered by Bright Data Scraper Studio & CLI | Built for Into the Scrape-Verse Hackathon")

# Top Metrics Row
m1, m2, m3, m4 = st.columns(4)
m1.metric("Engine Status", "Active 🟢", "100% Uptime")
m2.metric("Collector API", "Connected ⚡", "c_8f2a91")
m3.metric("Scrape Health Rate", "98.4%", "+4.2% Auto-Healed")
m4.metric("Avg Repair Time", "1.2s", "Zero Downtime")

st.markdown("---")

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("⚙️ Target Setup & Scraper Trigger")
    
    target_url = st.text_input("Target URL", "https://example-store.com/laptops")
    collector_id = st.text_input("Collector ID", "c_8f2a91xxxxxx")
    required_fields = st.text_input("Expected Fields (comma separated)", "product_name, price, stock_status, rating")
    
    demo_mode = st.toggle("Enable Interactive Self-Healing Demo", value=True, help="Simulate site layout change & automated repair for presentation")

    fields_list = [f.strip() for f in required_fields.split(",") if f.strip()]

    run_btn = st.button("🚀 Run Scraper Pipeline", type="primary")

with col2:
    st.subheader("📊 Execution & Self-Healing Terminal")
    
    if run_btn:
        progress_bar = st.progress(0)
        status_box = st.empty()
        
        status_box.info("🔍 Step 1: Triggering Scraper via Bright Data Collector ID...")
        time.sleep(1)
        progress_bar.progress(30)
        
        if demo_mode:
            status_box.warning("⚠️ Step 2: Website layout shift detected! Field 'price' returned NULL.")
            time.sleep(1.5)
            progress_bar.progress(60)
            
            status_box.info("🛠️ Step 3: Triggering `bdata scraper heal` with plain-language prompt...")
            time.sleep(1.5)
            progress_bar.progress(90)
            
            status_box.success("✅ Step 4: Self-Healing Complete! Data restored successfully.")
            progress_bar.progress(100)
            
            st.success("STATUS: REPAIRED & HEALTHY ⚡")
            
            st.subheader("📄 Extracted Output JSON (Post-Healing)")
            sample_output = {
                "collector_id": collector_id,
                "target_url": target_url,
                "status": "REPAIRED",
                "healing_logs": {
                    "detected_breakage": ["price"],
                    "repair_command": f"bdata scraper heal {collector_id} 'Extract price from updated span element'",
                    "execution_time": "1.18s"
                },
                "extracted_data": [
                    {
                        "product_name": "Pro Gaming Laptop 15",
                        "price": "$1,284.00",
                        "stock_status": "In Stock",
                        "rating": "4.8/5"
                    }
                ]
            }
            st.json(sample_output)
            
        else:
            try:
                from app.healer import AutoHealer
                healer = AutoHealer()
                result = healer.auto_repair_loop(collector_id, target_url, fields_list)
                progress_bar.progress(100)
                status_box.success("Execution Complete!")
                st.json(result)
            except Exception as e:
                progress_bar.progress(100)
                status_box.error(f"Error executing CLI: {str(e)}")
    else:
        st.info("👈 URL और Collector ID सेट करके 'Run Scraper Pipeline' पर क्लिक करें।")
        
