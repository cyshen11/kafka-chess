import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

st.set_page_config(page_title="Chess Analytics", page_icon="♟️", layout="wide")

st.title("♟️ Chess Web App Analytics")

def fetch_stats():
    try:
        response = requests.get("http://localhost:8000/stats")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching statistics: {e}")
        return None

def fetch_moves():
    try:
        response = requests.get("http://localhost:8000/moves")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching moves: {e}")
        return []

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📊 Game Statistics")
    
    if st.button("Refresh Data"):
        st.rerun()
    
    stats = fetch_stats()
    
    if stats:
        st.metric("Active Games", stats.get('active_games', 0))
        st.metric("Total Players", stats.get('total_players', 0))
        st.metric("Games Completed Today", stats.get('games_today', 0))
    else:
        st.metric("Active Games", 0)
        st.info("Unable to fetch live data. Using demo data.")

with col2:
    st.subheader("🔄 Recent Moves")
    
    moves_data = fetch_moves()
    
    if moves_data:
        df = pd.DataFrame(moves_data)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp', ascending=False).head(20)
            
            st.dataframe(
                df[['game_id', 'player', 'move', 'timestamp']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No moves data available")
    else:
        demo_moves = [
            {"game_id": "game_001", "player": "Player1", "move": "e4", "timestamp": datetime.now()},
            {"game_id": "game_001", "player": "Player2", "move": "e5", "timestamp": datetime.now()},
            {"game_id": "game_002", "player": "Player3", "move": "Nf3", "timestamp": datetime.now()},
        ]
        df = pd.DataFrame(demo_moves)
        st.dataframe(
            df[['game_id', 'player', 'move', 'timestamp']],
            use_container_width=True,
            hide_index=True
        )
        st.info("Showing demo data. Check backend connection.")

st.markdown("---")

col3, col4 = st.columns(2)

with col3:
    st.subheader("🎯 Quick Stats")
    stats = fetch_stats() or {}
    
    if stats:
        avg_game_length = stats.get('avg_game_length', 0)
        st.write(f"**Average Game Length:** {avg_game_length} moves")
        st.write(f"**Most Active Hour:** {stats.get('peak_hour', 'N/A')}")
    else:
        st.write("**Average Game Length:** 25 moves")
        st.write("**Most Active Hour:** 8 PM")

with col4:
    st.subheader("⚡ Live Updates")
    st.write("**Last Updated:** " + datetime.now().strftime("%H:%M:%S"))
    
    if st.checkbox("Auto-refresh (every 10s)"):
        time.sleep(10)
        st.rerun()
