import streamlit as st
from utils.utils_table_env import TableEnvCustomized
from utils.utils_worker import *

st.set_page_config(page_title="Chess Analytics", page_icon="♟️", layout="wide")
st.title("♟️ Chess Web App Analytics")
st.write("Built with Streamlit and PyFlink")
col1, col2 = st.columns([1, 2])
col1.subheader("📊 Game Statistics")
col2.subheader("🔄 Recent Moves")

st.markdown("---")

col3, col4 = st.columns([1, 2])

with col3:
    st.subheader("🎯 Quick Stats")

with col4:
    st.subheader("⚡ Live Updates")


table_env = TableEnvCustomized()
table_env.create_source_tables()
table_env.insert_dummy_record()

try:
    run_workers(col1, col2, col3, col4, table_env)
except:
    st.info("Unable to fetch live data.")
