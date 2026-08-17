import os
import streamlit as st
from dotenv import load_dotenv
from models import FieldSpec
from monitor import check_health
from healer import demo_repair
load_dotenv()

st.set_page_config(page_title="ScrapeShield AI",page_icon="🛡️",layout="wide")
st.title("🛡️ ScrapeShield AI")
st.caption("Self-healing web scraper reliability layer")

schema=[FieldSpec("product_name","Product name"),FieldSpec("price","Current price"),FieldSpec("stock","Availability")]
healthy=[
 {"product_name":"Laptop A","price":"₹59,999","stock":"In stock"},
 {"product_name":"Laptop B","price":"₹74,999","stock":"In stock"},
 {"product_name":"Laptop C","price":"₹89,999","stock":"Out of stock"}]
broken=[
 {"product_name":"Laptop A","stock":"In stock","_recovered_price":"₹59,999"},
 {"product_name":"Laptop B","stock":"In stock","_recovered_price":"₹74,999"},
 {"product_name":"Laptop C","stock":"Out of stock","_recovered_price":"₹89,999"}]

if "rows" not in st.session_state: st.session_state.rows=healthy
health=check_health(st.session_state.rows,schema)
real=bool(os.getenv("BRIGHT_DATA_API_TOKEN") and os.getenv("BRIGHT_DATA_COLLECTOR_ID"))

a,b,c,d=st.columns(4)
a.metric("Health","HEALTHY" if health.healthy else "BROKEN")
b.metric("Rows",health.row_count)
c.metric("Missing",len(health.missing_fields))
d.metric("Mode","REAL" if real else "DEMO")

url=st.text_input("Public page URL","https://ecommerce-shop-brd.vercel.app/product/echo-portable-speaker")
x,y=st.columns(2)

with x:
    if st.button("▶ Run Bright Data collector",use_container_width=True):
        if not real: st.warning("Add Bright Data credentials first.")
        else:
            try:
                from brightdata import BrightDataClient
                with st.spinner("Collecting..."):
                    rows,sid=BrightDataClient().collect([{"url":url}])
                st.session_state.rows=rows
                st.session_state.snapshot=sid
                st.rerun()
            except Exception as e: st.error(str(e))

with y:
    if st.button("🧪 Simulate website redesign",use_container_width=True):
        st.session_state.rows=broken
        st.rerun()

st.divider()
if health.healthy:
    st.success(health.message)
else:
    st.error(health.message)
    prompt=f"The latest collection is missing: {', '.join(health.missing_fields)}. Repair the extraction, preserve the output schema, prefer stable semantic/data-test selectors, and validate the result."
    st.code(prompt)
    p,q=st.columns(2)
    with p:
        if st.button("🤖 Self-heal in Bright Data",use_container_width=True):
            if not real: st.warning("Real Self-Healing requires Bright Data credentials.")
            else:
                try:
                    from brightdata import BrightDataClient
                    with st.spinner("Starting Self-Healing..."):
                        result=BrightDataClient().self_heal(prompt)
                    st.success("Self-Healing job started.")
                    st.json(result)
                except Exception as e: st.error(str(e))
    with q:
        if st.button("⚡ Apply demo repair",use_container_width=True):
            st.session_state.rows=demo_repair(st.session_state.rows,health.missing_fields)
            st.rerun()

st.divider()
st.subheader("Structured output")
st.dataframe([{k:v for k,v in r.items() if not k.startswith("_")} for r in st.session_state.rows],use_container_width=True)
