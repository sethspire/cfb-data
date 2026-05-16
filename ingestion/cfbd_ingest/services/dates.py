from datetime import datetime, timezone

def utc_now_iso() -> str:
    """Returns the current date and time in YYYY-MM-DDTHH-MM-SSZ format"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")

def utc_today() -> str:
    """Returns today's date in YYYY-MM-DD format"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def current_season() -> int:
    """Returns the current season. 
    
    Ex: 2024 season is February 1, 2024 - January 31, 2025"""
    cur = datetime.datetime.now()
    season = cur.year - (cur.month < 2)
    return season