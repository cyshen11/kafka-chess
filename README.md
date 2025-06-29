# ℹ️ About

`kafka-chess` is a project that builds a **web-based chess game** with _real-time analytics_. Players interact with an _interactive chessboard_ via a web application, where every move and game event is published to a _Kafka event bus_. An _Apache Flink engine_ continuously processes these events to calculate live game statistics, which are then displayed on a dynamic _Streamlit dashboard_.

## Tech Stack

- Frontend: Flask, Streamlit
- Database: Kafka
- Analytics Engine: Flink

## Getting Started

1. Clone the source repository: `git clone https://github.com/cyshen11/kafka-chess.git`.
2. Create a python environment and install the requirements.txt.
3. Run `flask --app flaskr run --debug` to run the interactive chessboard and navigate to 127.0.0.1:5000 to view it.
4. Change directory to Kafka `cd kafka` and run `docker compose up` to run the Kafka server in Docker container.
5. Change directory to parent level `cd ../`.
6. Run `streamlit run streamlit/app.py` to run the analytics dashboard and navigate to 127.0.0.1:8501 to view it.

---

Developed by Vincent Cheng  
<a href="https://www.linkedin.com/in/yun-sheng-cheng-86094a143/" target="_blank">
<img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" alt="LinkedIn" style="height:30px; width:30px;filter: grayscale(100%);">
</a>
