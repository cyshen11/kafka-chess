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
from datetime import datetime

st.set_page_config(page_title="Chess Analytics", page_icon="♟️", layout="wide")

st.title("♟️ Chess Web App Analytics")
st.write("Built with Streamlit and PyFlink")

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
          if result[1] != 'dummy':
            moves.append(result)
          df = pd.DataFrame(moves, columns=['Game ID', 'Player', 'Move', 'Move Timestamp']) # exclude first dummy record (initialized to avoid null object)
          df = df.style.map(color_player_ai, subset=["Player"])
          yield(df)

def get_quick_stats(table_env):
    with table_env.execute_sql(
        """
          WITH stats_1 AS (
            SELECT COALESCE(ROUND(AVG(game_length)), 0) avg_game_length
            FROM (
              SELECT 
                t1.game_id
                ,COALESCE(COUNT(move_id), 0) game_length
              FROM games t1
              LEFT JOIN moves t2 ON t1.game_id = t2.game_id
              WHERE YEAR(end_time) = 1970
              AND player <> 'dummy'
              GROUP BY t1.game_id
            )
          ),

          stats_2 AS (
            SELECT 
              HOUR(start_time) peak_hour
              ,COUNT(*)
            FROM games 
            GROUP BY HOUR(start_time)
            ORDER BY COUNT(*) DESC
            LIMIT 1
          )

          SELECT * FROM stats_1, stats_2
        """
      ).collect() as results:
      for result in results:
          yield(result)

def query(table_env):
    with table_env.execute_sql(
        """
          WITH moves_result AS (
            SELECT game_id, player, move, move_time FROM moves
          ),

          game_stats AS (
            SELECT 
              SUM(CASE WHEN record_count = 1 THEN 1 ELSE 0 END) active_game_count
              ,SUM(CASE WHEN record_count = 2 THEN 1 ELSE 0 END) completed_game_count
            FROM (
              SELECT game_id, COUNT(*) record_count FROM games 
              GROUP BY game_id
            )
          ),

          stats_avg_game_length AS (
            SELECT COALESCE(ROUND(AVG(game_length)), 0) avg_game_length
            FROM (
              SELECT 
                t1.game_id
                ,COALESCE(COUNT(move_id), 0) game_length
              FROM games t1
              LEFT JOIN moves t2 ON t1.game_id = t2.game_id
              WHERE YEAR(end_time) = 1970
              GROUP BY t1.game_id
            )
          ),

          stats_peak_hour AS (
            SELECT 
              HOUR(start_time) peak_hour
            FROM games 
            GROUP BY HOUR(start_time)
            ORDER BY COUNT(*) DESC
            LIMIT 1
          )
          
          SELECT *
          FROM moves_result, game_stats, stats_avg_game_length, stats_peak_hour
        """
      ).collect() as results:
      moves = []
      for result in results:
          moves.append(result[0:4])
          # df = pd.DataFrame(results_2, columns=['Game ID', 'Player', 'Move', 'Move Timestamp', 'Active Game Count', 'Completed Game Count', 'Average Game Length', 'Peak Hour']) # exclude first dummy record (initialized to avoid null object)
          # df = df.style.map(color_player_ai, subset=["Player"])
          yield(moves, result[4], result[5], result[6], result[7])

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
              self.target.container().dataframe(chunk, height=400)

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
                  st.write(f"**Most Active Hour:** {int(chunk[1]) > 12 and f'{int(chunk[1]) - 12} PM' or f'{int(chunk[1])} AM'}")

class WorkerThread4(Thread):
    def __init__(self, delay, target):
        super().__init__()
        self.delay = delay
        self.target = target

    def run(self):
        time.sleep(self.delay)
        while True:
            self.target.write("**Last Updated:** " + datetime.now().strftime("%H:%M:%S"))

class WorkerThread5(Thread):
    def __init__(self, delay, col1, col2, col3, col4, table_env):
        super().__init__()
        self.delay = delay
        self.col1 = col1
        self.col2 = col2
        self.col3 = col3
        self.col4 = col4
        self.table_env = table_env

    def run(self):
        time.sleep(self.delay)
        stream = query(self.table_env)
        for moves, active_game_count, completed_game_count, avg_game_length, peak_hour in stream:
             df = pd.DataFrame(moves, columns=['Game ID', 'Player', 'Move', 'Move Timestamp'])
             df.drop_duplicates(inplace=True)
             df = df.style.map(color_player_ai, subset=["Player"])
             self.col2.container().dataframe(df, height=400)
             with self.col1.container():
                st.metric("Active Games", active_game_count)
                st.metric("Total Players", active_game_count)
                st.metric("Games Completed Today", completed_game_count)
             
             with self.col3.container():
                st.write(f"**Average Game Length:** {avg_game_length} moves")
                # st.write(f"**Most Active Hour:** {int(peak_hour) > 12 and f'{int(peak_hour) - 12} PM' or f'{int(peak_hour)} AM'}")

col1, col2 = st.columns([1, 2])
col1.subheader("📊 Game Statistics")
col2.subheader("🔄 Recent Moves")

st.markdown("---")

col3, col4 = st.columns([1, 2])

with col3:
    st.subheader("🎯 Quick Stats")

with col4:
    st.subheader("⚡ Live Updates")


try:
  threads = [
     WorkerThread1(1.2, col1.empty(), table_env)
    , WorkerThread2(1.1, col2.empty(), table_env)
    , WorkerThread3(1, col3.empty(), table_env)
    , WorkerThread4(1.3, col4.empty())
  ]

  for thread in threads:
      add_script_run_ctx(thread, get_script_run_ctx())
      thread.start()

  for thread in threads:
    thread.join()
except:
    st.info("Unable to fetch live data.")



