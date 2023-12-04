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
    news = requests.get(get_route("news"))
    return news.text

def join_game():
    """
    Called when user starts a game
    Used to track how many games are played each day
    """
    requests.get(get_route("join_game"))

def get_latest_version():
    news = requests.get(get_route("latest_version"))
    return news.text

def get_info():
    """
    Gets the credits info and parses it into a dict
    """
    info = requests.get(get_route("info"))
    info = info.text
    data = {}
    for i in info.split("\n"):
        i = i.split(": ")
        data[i[0]] = i[1]
    return data
