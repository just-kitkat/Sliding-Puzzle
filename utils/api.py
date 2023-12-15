from utils.constants import INFO_REPLACE
import requests

def get_route(path: str) -> str:
    """
    Helper function to format URL
    """
    return f"https://just-kitkat.github.io/api/slidingpuzzle/{path}"

def get_news() -> str:
    """
    Return announcements e.g. new updates/features
    """
    try:
        news = requests.get(get_route("news"))
        return news.text
    except Exception:
        return "News not available!\nAre you connected to the internet?"

def join_game():
    """
    Called when user starts a game
    Used to track how many games are played each day
    """
    try:
        requests.get(get_route("join_game"))
    except Exception:
        pass

def get_latest_version():
    try:
        news = requests.get(get_route("latest_version"))
        return news.text
    except Exception:
        return None

def get_info():
    """
    Gets the credits info and parses it into a dict
    """
    data = {}
    try:
        info = requests.get(get_route("info"))
        info = info.text
        for i in info.split("\n"):
            i = i.split(": ")
            data[i[0]] = i[1] if i[1] not in INFO_REPLACE else INFO_REPLACE[i[1]]
    except Exception:
        data = {"Error": "No internet connection"}

    return data
