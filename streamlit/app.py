# Chess Analytics Web Application
# A Streamlit app for real-time chess game analytics using PyFlink

import streamlit as st
from utils.utils_table_env import TableEnvCustomized
from utils.utils_worker import *

# Configure the Streamlit page layout and metadata
st.set_page_config(page_title="Chess Analytics", page_icon="♟️", layout="wide")
st.title("♟️ Chess Web App Analytics")
st.write("Built with Streamlit and PyFlink")

# Create main content columns - col1 for stats, col2 for moves (2x wider)
col1, col2 = st.columns([1, 2])
col1.subheader("📊 Game Statistics")
col2.subheader("🔄 Recent Moves")

# Add visual separator
st.markdown("---")

# Create secondary content columns - col4 for live updates, col3 unused
col4, col3 = st.columns([1, 2])

with col4:
    st.subheader("⚡ Live Updates")

# Initialize PyFlink table environment for data processing
table_env = TableEnvCustomized()
table_env.create_source_tables()  # Set up Kafka source tables
table_env.insert_dummy_record()   # Insert initial test data

# Start the data processing workers with error handling
try:
    run_workers(col1, col2, col3, col4, table_env)
except Exception:
    st.info("Unable to fetch live data.")
