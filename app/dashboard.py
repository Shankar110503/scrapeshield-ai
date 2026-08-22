import sys
import os

# Root directory ko Python path me add karein
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from app.healer import AutoHealer

import streamlit as st
from app.healer import AutoHealer

st.set_page_config(page_title="ScrapeShield AI", page_icon="🛡️", layout="wide")

st.title("🛡️ ScrapeShield AI — Self-Healing Scraper Engine")
st.caption("Powered by Bright Data Scraper Studio & CLI")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("⚙️ Target Setup")
    target_url = st.text_input("Target URL", "https://example.com/products")
    collector_id = st.text_input("Collector ID", "c_8f2a91xxxxxx")
    required_fields = st.text_input("Expected Fields (comma separated)", "title, price, availability")
    
    fields_list = [f.strip() for f in required_fields.split(",") if f.strip()]

    if st.button("🚀 Run Scraper Pipeline", type="primary"):
        st.info("Executing Scraper and Validating Extraction...")
        healer = AutoHealer()
        result = healer.auto_repair_loop(collector_id, target_url, fields_list)
        st.session_state['last_result'] = result

with col2:
    st.subheader("📊 Execution & Health Status")
    
    if 'last_result' in st.session_state:
        res = st.session_state['last_result']
        status = res.get("status", "UNKNOWN")
        
        if status == "HEALTHY":
            st.success("Engine Status: HEALTHY 🟢")
        elif status == "REPAIRED":
            st.warning("Engine Status: SELF-HEALED ⚡")
        else:
            st.error("Engine Status: FAILED 🔴")
            
        st.markdown("---")
        st.subheader("📄 Extracted JSON Data")
        st.json(res.get("data", {}))
    else:
        st.info("Pipeline run karne ke liye URL aur Collector ID दर्ज करें।")
        
