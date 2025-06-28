import time
from threading import Thread
import streamlit as st
from datetime import datetime
from streamlit.runtime.scriptrunner_utils.script_run_context import (
    add_script_run_ctx,
    get_script_run_ctx,
)

class WorkerThread1(Thread):
    def __init__(self, delay, target, table_env):
        super().__init__()
        self.delay = delay
        self.target = target
        self.table_env = table_env

    def run(self):
        time.sleep(self.delay)
        stream = self.table_env.get_games_stats()
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
        stream = self.table_env.get_moves()

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
        stream = self.table_env.get_quick_stats()
        for chunk in stream:
            with self.target.container():
                st.write(f"**Average Game Length:** {chunk[0]} moves")
                st.write(
                    f"**Most Active Hour:** {int(chunk[1]) > 12 and f'{int(chunk[1]) - 12} PM' or f'{int(chunk[1])} AM'}"
                )


class WorkerThread4(Thread):
    def __init__(self, delay, target):
        super().__init__()
        self.delay = delay
        self.target = target

    def run(self):
        time.sleep(self.delay)
        while True:
            self.target.write(
                "**Last Updated:** " + datetime.now().strftime("%H:%M:%S")
            )

def run_workers(col1, col2, col3, col4, table_env):
    threads = [
        WorkerThread1(1.2, col1.empty(), table_env),
        WorkerThread2(1.1, col2.empty(), table_env),
        # WorkerThread3(1, col3.empty(), table_env),
        WorkerThread4(1.3, col4.empty()),
    ]

    for thread in threads:
        add_script_run_ctx(thread, get_script_run_ctx())
        thread.start()

    for thread in threads:
        thread.join()