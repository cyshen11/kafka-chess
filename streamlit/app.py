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

table_env.execute_sql(f"""
    CREATE TABLE moves (
        move_id VARCHAR
        ,game_id VARCHAR
        ,player VARCHAR
        ,move VARCHAR
        ,move_time TIMESTAMP(0)
    ) WITH (
        'connector' = 'kafka',
        'topic' = 'moves',
        'properties.bootstrap.servers' = 'localhost:9092',
        'scan.startup.mode' = 'timestamp',
        'scan.startup.timestamp-millis' = '{current_milli_time()}',
        'value.format' = 'csv'
    )
""")


def get_games_stats(table_env):
    with table_env.execute_sql(
       """
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

def color_player_ai(value):
    return f"background-color: #333; color: #f0f0f0;" if value == "AI" else "background-color: #f0f0f0; color: #333;"

def get_moves(table_env):
    with table_env.execute_sql("SELECT game_id, player, move, move_time FROM moves").collect() as results:
      moves = []
      for result in results:
          moves.append(result)
          df = pd.DataFrame(moves, columns=['Game ID', 'Player', 'Move', 'Move Timestamp'])
          df = df.style.map(color_player_ai, subset=["Player"])
          yield(df)

def get_quick_stats(table_env):
    with table_env.execute_sql(
        """
          SELECT ROUND(AVG(game_length)) avg_game_length
          FROM (
            SELECT 
              t1.game_id,
              COUNT(move_id) game_length
            FROM games t1
            LEFT JOIN moves t2 ON t1.game_id = t2.game_id
            WHERE YEAR(end_time) > 1970
            GROUP BY t1.game_id
          )
        """
      ).collect() as results:
      for result in results:
          yield(result)

class WorkerThread1(Thread):
    def __init__(self, delay, target, table_env):
        super().__init__()
        self.delay = delay
        self.target = target
        self.table_env = table_env

    def run(self):
        time.sleep(self.delay)
        stream = get_games_stats(self.table_env)
        for chunk in stream:
          with self.target.container():
             st.metric("Active Games", chunk[0])
             st.metric("Total Players", chunk[0])
             st.metric("Games Completed Today", chunk[1])
            #  st.write(f"**Active Games:** {chunk[0]} games")
            #  st.write(f"**Total Players:** {chunk[0]} players")
            #  st.write(f"**Games Completed Today:** {chunk[1]} games") 

class WorkerThread2(Thread):
    def __init__(self, delay, target, table_env):
        super().__init__()
        self.delay = delay
        self.target = target
        self.table_env = table_env

    def run(self):
        time.sleep(self.delay)
        stream = get_moves(self.table_env)

        for chunk in stream:
              self.target.container().dataframe(chunk)

class WorkerThread3(Thread):
    def __init__(self, delay, target, table_env):
        super().__init__()
        self.delay = delay
        self.target = target
        self.table_env = table_env

    def run(self):
        time.sleep(self.delay)
        stream = get_quick_stats(self.table_env)
        for chunk in stream:
              with self.target.container():
                  st.write(f"**Average Game Length:** {chunk[0]} moves")
        
col1, col2 = st.columns([1, 2])
col1.subheader("📊 Game Statistics")
col2.subheader("🔄 Recent Moves")

st.markdown("---")

col3, col4 = st.columns(2)

with col3:
    st.subheader("🎯 Quick Stats")

try:
  threads = [
     WorkerThread1(1.2, col1.empty(), table_env)
    , WorkerThread2(1.1, col2.empty(), table_env)
    , 
    WorkerThread3(1, col3.empty(), table_env)
  ]

  for thread in threads:
      add_script_run_ctx(thread, get_script_run_ctx())
      thread.start()

  for thread in threads:
    thread.join()
except:
    st.info("Unable to fetch live data.")



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
