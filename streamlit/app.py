import streamlit as st
import pandas as pd
import time
from pyflink.table import EnvironmentSettings, TableEnvironment
from pyflink.table import (EnvironmentSettings, TableEnvironment)
from threading import Thread
from streamlit.runtime.scriptrunner_utils.script_run_context import (
    add_script_run_ctx,
    get_script_run_ctx,
)

st.set_page_config(page_title="Chess Analytics", page_icon="♟️", layout="wide")

st.title("♟️ Chess Web App Analytics")

# 1. create a TableEnvironment
table_env = TableEnvironment.create(EnvironmentSettings.in_streaming_mode())
table_env.get_config().set("parallelism.default", "1")
table_env.get_config().set("pipeline.jars", "file:////Users/vincentcheng/Documents/data_engineering/kafka-chess/streamlit/flink-sql-connector-kafka-4.0.0-2.0.jar")


def current_milli_time():
    return round(time.time() * 1000)

# # 2. create source Table
table_env.execute_sql(f"""
    CREATE TABLE games (
        game_id VARCHAR
        ,start_time TIMESTAMP(3)
        ,end_time TIMESTAMP(3)
    ) WITH (
        'connector' = 'kafka',
        'topic' = 'games',
        'properties.bootstrap.servers' = 'localhost:9092',
        'scan.startup.mode' = 'timestamp',
        'scan.startup.timestamp-millis' = '{current_milli_time()}',
        'value.format' = 'csv'
    )
""")

# table_env.execute_sql("""
#     CREATE TABLE moves (
#         ts TIMESTAMP_LTZ(3) METADATA FROM 'timestamp'
#         ,game_id VARCHAR
#         ,type VARCHAR
#         ,move VARCHAR
#         ,WATERMARK FOR ts AS ts
#     ) WITH (
#         'connector' = 'kafka',
#         'topic' = 'moves',
#         'properties.bootstrap.servers' = 'localhost:9092',
#         'scan.startup.mode' = 'earliest-offset',
#         'value.format' = 'json'
#     )
# """)


def get_games_count(table_env):
    with table_env.execute_sql(
       """
       /*
        SELECT TUMBLE_START(start_time, INTERVAL '1' HOUR) time_window, COUNT(DISTINCT game_id) game_count
        FROM games
        GROUP BY TUMBLE(start_time, INTERVAL '1' HOUR)

        SELECT NULLIF(COUNT(*), 0) FROM
      (SELECT DISTINCT game_id FROM games
      WHERE YEAR(end_time) = 1970)
      */
      
      SELECT 
        SUM(CASE WHEN record_count = 1 THEN 1 ELSE 0 END) active_game_count
        ,SUM(CASE WHEN record_count = 2 THEN 1 ELSE 0 END) completed_game_count
      FROM (
        SELECT game_id, COUNT(*) record_count FROM games 
        GROUP BY game_id
      )
      """
    ).collect() as results:
      for result in results:
        yield(result)

# def get_moves(table_env):
#     with table_env.execute_sql("SELECT * FROM moves").collect() as results:
#       for result in results:
#         yield('#' + str(result.get_fields_by_names('game_id')[1]))

class WorkerThread1(Thread):
    def __init__(self, delay, target, table_env):
        super().__init__()
        self.delay = delay
        self.target = target
        self.table_env = table_env

    def run(self):
        time.sleep(self.delay)
        stream = get_games_count(self.table_env)
        for chunk in stream:
          with self.target.container():
             st.metric("Active Games", chunk[0])
             st.metric("Total Players", chunk[0])
             st.metric("Games Completed Today", chunk[1])

class WorkerThread2(Thread):
    def __init__(self, delay, target, table_env):
        super().__init__()
        self.delay = delay
        self.target = target
        self.table_env = table_env

    def run(self):
        time.sleep(self.delay)
        stream = get_games_count(self.table_env)
        for chunk in stream:
          self.target.metric("Total Players", chunk)


col1, col2 = st.columns([1, 2])

containers = [
   
]

with col1:
    st.subheader("📊 Game Statistics")
    # threads = [
    #     WorkerThread1(1.1, st.empty(), table_env)
    #     ,WorkerThread2(1, st.empty(), table_env)
    # ]

    try:
      threads = [
          WorkerThread1(1.1, st.empty(), table_env)
          # ,WorkerThread2(1, st.empty(), table_env)
      ]

      for thread in threads:
          add_script_run_ctx(thread, get_script_run_ctx())
          thread.start()

      for thread in threads:
        thread.join()
    except:
       st.metric("Active Games", 0)
       st.info("Unable to fetch live data.")

# with col2:
#     st.subheader("🔄 Recent Moves")
    
#     moves_data = fetch_moves()
    
#     if moves_data:
#         df = pd.DataFrame(moves_data)
#         if not df.empty:
#             df['timestamp'] = pd.to_datetime(df['timestamp'])
#             df = df.sort_values('timestamp', ascending=False).head(20)
            
#             st.dataframe(
#                 df[['game_id', 'player', 'move', 'timestamp']],
#                 use_container_width=True,
#                 hide_index=True
#             )
#         else:
#             st.info("No moves data available")
#     else:
#         demo_moves = [
#             {"game_id": "game_001", "player": "Player1", "move": "e4", "timestamp": datetime.now()},
#             {"game_id": "game_001", "player": "Player2", "move": "e5", "timestamp": datetime.now()},
#             {"game_id": "game_002", "player": "Player3", "move": "Nf3", "timestamp": datetime.now()},
#         ]
#         df = pd.DataFrame(demo_moves)
#         st.dataframe(
#             df[['game_id', 'player', 'move', 'timestamp']],
#             use_container_width=True,
#             hide_index=True
#         )
#         st.info("Showing demo data. Check backend connection.")

# st.markdown("---")

# col3, col4 = st.columns(2)

# with col3:
#     st.subheader("🎯 Quick Stats")
#     stats = fetch_stats() or {}
    
#     if stats:
#         avg_game_length = stats.get('avg_game_length', 0)
#         st.write(f"**Average Game Length:** {avg_game_length} moves")
#         st.write(f"**Most Active Hour:** {stats.get('peak_hour', 'N/A')}")
#     else:
#         st.write("**Average Game Length:** 25 moves")
#         st.write("**Most Active Hour:** 8 PM")

# with col4:
#     st.subheader("⚡ Live Updates")
#     st.write("**Last Updated:** " + datetime.now().strftime("%H:%M:%S"))
    
#     if st.checkbox("Auto-refresh (every 10s)"):
#         time.sleep(10)
#         st.rerun()
