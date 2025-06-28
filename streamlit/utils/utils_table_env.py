from pyflink.table import EnvironmentSettings, TableEnvironment
import pandas as pd
from utils.utils_helper import *
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


class TableEnvCustomized:
    """
    Custom wrapper for PyFlink TableEnvironment configured for Kafka streaming.
    Handles chess game data processing from Kafka topics.
    """
    
    def __init__(self):
        """Initialize streaming table environment with Kafka connector configuration."""
        # Create streaming table environment
        self.table_env = TableEnvironment.create(
            EnvironmentSettings.in_streaming_mode()
        )
        # Set single parallelism for consistent processing
        self.table_env.get_config().set("parallelism.default", "1")
        # Add Kafka connector JAR from environment variable
        self.table_env.get_config().set(
            "pipeline.jars",
            f"file:////{os.getenv('ABSOLUTE_PATH_TO_JAR_FILE')}",
        )

    def create_source_tables(self):
        """Create Kafka source tables for games and moves data."""
        # Create games table - contains game metadata
        self.table_env.execute_sql(
            f"""
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
    """
        )

        # Create moves table - contains individual chess moves
        self.table_env.execute_sql(
            f"""
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
    """
        )

    def insert_dummy_record(self):
        """Insert dummy records to initialize tables and avoid null pointer exceptions."""
        # Insert dummy game record
        self.table_env.execute_sql(
            f"""
      INSERT INTO games
      VALUES ('dummy', CURRENT_TIMESTAMP(), TIMESTAMP '1970-01-01 00:00:00')
      """
        )

        # Insert dummy move record
        self.table_env.execute_sql(
            f"""
      INSERT INTO moves
      VALUES ('dummy', 'dummy', 'dummy', 'dummy', CURRENT_TIMESTAMP())
    """
        )

    def get_games_stats(self):
        """
        Get count of active and completed games.
        Active games have 1 record (start only), completed games have 2 records (start + end).
        
        Yields:
            tuple: (active_game_count, completed_game_count)
        """
        with self.table_env.execute_sql(
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
                yield (result)

    def get_moves(self):
        """
        Get all chess moves data formatted for display.
        
        Yields:
            pandas.DataFrame: Styled DataFrame with moves data, excluding dummy records
        """
        with self.table_env.execute_sql(
            "SELECT game_id, player, move, move_time FROM moves"
        ).collect() as results:
            moves = []
            for result in results:
                # Filter out dummy records used for initialization
                if result[1] != "dummy":
                    moves.append(result)
                df = pd.DataFrame(
                    moves, columns=["Game ID", "Player", "Move", "Move Timestamp"]
                )
                # Apply styling to differentiate AI vs human players
                df = df.style.map(color_player_ai, subset=["Player"])
                yield (df)

    def get_quick_stats(self):
        """
        Get aggregated statistics including average game length and peak gaming hour.
        Only includes active games (end_time year = 1970 indicates game in progress).
        
        Yields:
            tuple: (avg_game_length, peak_hour, peak_hour_count)
        """
        with self.table_env.execute_sql(
            """
          WITH stats_1 AS (
            SELECT COALESCE(ROUND(AVG(game_length)), 0) avg_game_length
            FROM (
              SELECT 
                t1.game_id
                ,COALESCE(COUNT(move_id), 0) game_length
              FROM games t1
              LEFT JOIN moves t2 ON t1.game_id = t2.game_id
              WHERE YEAR(end_time) = 1970  -- Filter for active games only
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
                yield (result)
