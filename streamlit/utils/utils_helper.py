import time

def current_milli_time():
    """
    Get the current time in milliseconds with a 5-second offset.
    
    Returns:
        int: Current timestamp in milliseconds minus 5000ms
    """
    return round(time.time() * 1000) - 5000

def color_player_ai(value):
    """
    Apply styling for AI vs human players in the UI.
    
    Args:
        value (str): Player type - "AI" or other
        
    Returns:
        str: CSS styling string with background and text colors
    """
    return (
        f"background-color: #333; color: #f0f0f0;"
        if value == "AI"
        else "background-color: #f0f0f0; color: #333;"
    )