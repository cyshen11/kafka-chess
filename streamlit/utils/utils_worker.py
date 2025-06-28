import time
from threading import Thread
import streamlit as st
from datetime import datetime
# Import Streamlit context utilities for thread management
from streamlit.runtime.scriptrunner_utils.script_run_context import (
    add_script_run_ctx,
    get_script_run_ctx,
)

class WorkerThread1(Thread):
    """Worker thread for displaying game statistics metrics."""
    
    def __init__(self, delay, target, table_env):
        """Initialize worker thread for game stats.
        
        Args:
            delay (float): Initial delay before starting work
            target: Streamlit container target for output
            table_env: Table environment for data queries
        """
        super().__init__()
        self.delay = delay
        self.target = target
        self.table_env = table_env

    def run(self):
        """Execute the worker thread to display game statistics."""
        # Initial delay to stagger thread startup
        time.sleep(self.delay)
        # Stream game statistics from table environment
        stream = self.table_env.get_games_stats()
        for chunk in stream:
            with self.target.container():
                # Display metrics for active games, total players, and completed games
                st.metric("Active Games", chunk[0])
                st.metric("Total Players", chunk[0])  # Note: Same as active games
                st.metric("Games Completed Today", chunk[1])


class WorkerThread2(Thread):
    """Worker thread for displaying chess moves data table."""
    
    def __init__(self, delay, target, table_env):
        """Initialize worker thread for moves display.
        
        Args:
            delay (float): Initial delay before starting work
            target: Streamlit container target for output
            table_env: Table environment for data queries
        """
        super().__init__()
        self.delay = delay
        self.target = target
        self.table_env = table_env

    def run(self):
        """Execute the worker thread to display moves data."""
        # Initial delay to stagger thread startup
        time.sleep(self.delay)
        # Stream chess moves data from table environment
        stream = self.table_env.get_moves()

        for chunk in stream:
            # Display moves data as a scrollable dataframe
            self.target.container().dataframe(chunk, height=400)


class WorkerThread3(Thread):
    """Worker thread for displaying quick statistics (currently disabled)."""
    
    def __init__(self, delay, target, table_env):
        """Initialize worker thread for quick stats.
        
        Args:
            delay (float): Initial delay before starting work
            target: Streamlit container target for output
            table_env: Table environment for data queries
        """
        super().__init__()
        self.delay = delay
        self.target = target
        self.table_env = table_env

    def run(self):
        """Execute the worker thread to display quick statistics."""
        # Initial delay to stagger thread startup
        time.sleep(self.delay)
        # Stream quick statistics from table environment
        stream = self.table_env.get_quick_stats()
        for chunk in stream:
            with self.target.container():
                # Display average game length in moves
                st.write(f"**Average Game Length:** {chunk[0]} moves")
                # Format and display most active hour with AM/PM conversion
                st.write(
                    f"**Most Active Hour:** {int(chunk[1]) > 12 and f'{int(chunk[1]) - 12} PM' or f'{int(chunk[1])} AM'}"
                )


class WorkerThread4(Thread):
    """Worker thread for displaying real-time timestamp updates."""
    
    def __init__(self, delay, target):
        """Initialize worker thread for timestamp display.
        
        Args:
            delay (float): Initial delay before starting work
            target: Streamlit container target for output
        """
        super().__init__()
        self.delay = delay
        self.target = target

    def run(self):
        """Execute the worker thread to continuously update timestamp."""
        # Initial delay to stagger thread startup
        time.sleep(self.delay)
        # Continuously update the last updated timestamp
        while True:
            self.target.write(
                "**Last Updated:** " + datetime.now().strftime("%H:%M:%S")
            )

def run_workers(col1, col2, col3, col4, table_env):
    """Initialize and start all worker threads for the Streamlit dashboard.
    
    Args:
        col1: Streamlit column for game statistics
        col2: Streamlit column for moves data table
        col3: Streamlit column for quick stats (currently unused)
        col4: Streamlit column for timestamp updates
        table_env: Table environment instance for data queries
    """
    # Create worker threads with staggered delays to avoid startup conflicts
    threads = [
        WorkerThread1(1.2, col1.empty(), table_env),  # Game stats
        WorkerThread2(1.1, col2.empty(), table_env),  # Moves table
        # WorkerThread3(1, col3.empty(), table_env),  # Quick stats (disabled)
        WorkerThread4(1.3, col4.empty()),             # Timestamp updates
    ]

    # Start all threads with proper Streamlit context
    for thread in threads:
        # Add Streamlit script context to enable UI updates from threads
        add_script_run_ctx(thread, get_script_run_ctx())
        thread.start()

    # Wait for all threads to complete (blocking operation)
    for thread in threads:
        thread.join()