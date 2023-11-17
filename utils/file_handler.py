import os
import sys

RESOURCE_PATHS = {}

def resource_path(relative_path):
    """
    PyInstaller creates a temp folder and stores path in _MEIPASS
    This function tries to find that path 

    Note: This function is for EXEs. Feel free to remove it when compiling it to APKs.
    """
    if relative_path in RESOURCE_PATHS:
        return RESOURCE_PATHS[relative_path]
    
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    path = os.path.join(base_path, relative_path)
    RESOURCE_PATHS[relative_path] = path # save in memory if not already in
    
    return path

def load_resources():
        """
        Load all the full file paths into memory
        """
        files = [
            "bg/bg.png",
            "bg/frame.png",
            "music/suiteofstrings.mp3",
            "sound_effects/tile_sliding.wav",
            "tiles/button_round.png",
            "tiles/button1.png",
            "tiles/button2.png",
            "tiles/button3.png",
            "tiles/button4.png",
            "tiles/button5.png",
            "tiles/button6.png",
            "tiles/button7.png",
            "tiles/button8.png",
        ]
        for file in files:
            RESOURCE_PATHS[file] = resource_path(file)