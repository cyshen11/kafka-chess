import time

def current_milli_time():
    return round(time.time() * 1000) - 5000

def color_player_ai(value):
    return (
        f"background-color: #333; color: #f0f0f0;"
        if value == "AI"
        else "background-color: #f0f0f0; color: #333;"
    )