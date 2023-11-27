"""
Copyright (C) 2022  JustKitkat

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""

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
            "assets/bg/bg.png",
            "assets/bg/frame.png",
            "music/suiteofstrings.mp3",
            "sound_effects/tile_sliding.wav",
            "assets/tiles/button_round.png",
            "assets/tiles/button1.png",
            "assets/tiles/button2.png",
            "assets/tiles/button3.png",
            "assets/tiles/button4.png",
            "assets/tiles/button5.png",
            "assets/tiles/button6.png",
            "assets/tiles/button7.png",
            "assets/tiles/button8.png",
            "assets/btns/back.png",
            "assets/btns/settings.png"
        ]
        for file in files:
            RESOURCE_PATHS[file] = resource_path(file)