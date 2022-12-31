"""
Copyright (C) 2022  kitkat3141

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

import random
import os
import sys
import asyncio, time
from copy import deepcopy
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.config import ConfigParser
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.label import Label 
from kivy.animation import Animation
from kivy.graphics import Rectangle

def resource_path(relative_path):
    """
    PyInstaller creates a temp folder and stores path in _MEIPASS
    This function tries to find that path 

    Note: This function is for EXEs. Feel free to remove it when compiling it to APKs.
    """

    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

inst = None
sound_effects = True
tile_indication = True
tile_movement = 0
game_stats = None

class WelcomeWindow(Screen):
    pass

class InfoWindow(Screen):

    # Credits section. Wierd spacing makes text inline in the game itself :/
    info_text = """
                      Creator                     kitkat3141
                      Art                             Klaide9021
                      Language                Python 3.10.5
                      Main Code               616 Lines
                      Music                        @blueqmusic (yt)
                      
In the case of a bug, contact kitkat3141#0422 on discord.
"""

class WinWindow(Screen):
    def on_pre_enter(self, *args):
        self.stats = Label(
            text = game_stats,
            font_size = Window.width//20,
            size_hint = (0.3, 0.2),
            pos_hint = {"center_x": 0.5, "y": 0.6}
        )
        self.add_widget(self.stats)
    
    def on_leave(self):
        self.remove_widget(self.stats)

class GameWindow(Screen):
    """
    This is the game screen.
    """

    tile_moving = None

    def on_pre_enter(self):
        """
        Clear all items on screen and display the loading label before the window shows
        """
        self.clear_widgets()
        width, _ = Window.size
        loading = Label(
            text = "Loading...",
            font_size = width//20,
            size_hint = (0.4, 0.3),
            pos_hint = {"center_x": 0.5, "center_y": 0.5}
        )
        self.add_widget(loading)

    def on_enter(self):
        """
        Once in game, load sound effects and clear all widgets (the loading label)
        """
        self.tile_move_sound = SoundLoader.load(resource_path("sound_effects/tile_sliding.wav"))
        #self.tile_move_sound.volume = 0.2
        self.clear_widgets()
        self.init_game()

    
    def remove_anim_widget(self, anim, widget):
        """
        Called when an animation finishes
        This function removes the animated widget from the screen
        """
        item = self.tile_moving
        y = (self.btns[0]+self.btns[1]+self.btns[2]).index(self.tile_moving) // 3
        x = self.btns[y].index(self.tile_moving)
        if [[1,2,3], [4,5,6], [7,8,-1]][y][x] == int(item.background_normal[-5]) or not tile_indication:
            item.opacity = 1
        else:
            item.opacity = 0.8
        self.remove_widget(widget)

    def anim_in_progress(self, anim, widget, progress):
        """
        Called when animation is in progress
        This function ensures the opacity of moving tile (not the animated) opacity is 0
        """
        self.tile_moving.opacity = 0

    def getInvCount(self, arr: list):
        """
        Helper function for isSolvable(puzzle)
        """
        inv_count = 0
        empty_value = -1
        for i in range(0, 9):
            for j in range(i + 1, 9):
                if arr[j] != empty_value and arr[i] != empty_value and arr[i] > arr[j]:
                    inv_count += 1
        return inv_count
    
    def isSolvable(self, puzzle: list) -> bool:
        """
        Returns True if the 8 puzzle is solvable and vice versa
        """
        # Count inversions in given 8 puzzle
        inv_count = self.getInvCount([j for sub in puzzle for j in sub])
        # return true if inversion count is even.
        return (inv_count % 2 == 0)

    def init_game(self, *args):
        """
        Initialises the game
        """
        self.width, self.height = Window.size
        self.font_size = self.width//20
        self.grid = [[] for _ in range(3)]
        self.btns = [[] for _ in range(3)]
        self.config = ConfigParser()
        self.moves = 0
        self.timer = 0

        # Add frame to screen
        self.puzzle_frame = Button(
            background_normal = resource_path("bg/frame.png"),
            background_down = resource_path("bg/frame.png"),
            size_hint = (None, None)
        )
        self.add_widget(self.puzzle_frame)

        # Start Timer
        self.timer_btn = Button(
            text = "0.0s",
            font_size = self.font_size//1.5,
            size_hint = (0.15, 0.1),
            pos_hint = {"center_x": 0.9, "top": 0.98}
        )
        self.add_widget(self.timer_btn)

        # Quit button
        self.quit_btn = Button(
            text = "Quit",
            font_size = self.font_size//1.5,
            size_hint = (0.2, 0.1),
            pos_hint = {"center_x": 0.9, "bottom": 0.05}
        )
        self.quit_btn.bind(on_release=self.quit_game)
        self.add_widget(self.quit_btn)

        try:
            self.clock.cancel()
        except Exception:
            pass
        self.clock = Clock.schedule_interval(self.timer_callback, 0.1)

        # Starts the game
        self.create_grid(True)

    def timer_callback(self, dt):
        """
        A function to update the timer and game objects sizes (in case screen gets resized)
        This ensures the tiles are squares and fit in the screen
        """
        if self.moves > 0:
            self.timer += 0.1
            self.timer_btn.text = f"{round(self.timer, 1)}s"
        self.width, self.height = Window.size
        self.font_size = self.width//20
        self.timer_btn.font_size = self.font_size//1.5
        self.quit_btn.font_size = self.font_size//2
        size = (self.height / 4, self.height / 4) if self.height < self.width else (self.width / 4, self.width / 4)
        x_pos = [self.width/2 - self.height/3.8, self.width/2, self.width/2 + self.height/3.8] \
                if self.width > self.height else \
                [self.width/2 - self.width/3.8, self.width/2, self.width/2 + self.width/3.8]
        y_pos = [self.height/2 - self.height/3.8, self.height/2, self.height/2 + self.height/3.8] \
                if self.width > self.height else \
                [self.height/2 - self.width/3.8, self.height/2, self.height/2 + self.width/3.8]
        for y, row in enumerate(self.btns[::-1]):
            for x, item in enumerate(row):
                item.size = size
                item.pos = (x_pos[x] - self.width/8, y_pos[y] - self.height/8) \
                            if self.width > self.height else \
                            (x_pos[x] - self.width/8, y_pos[y] - self.width/8)
                            
        # This adjusts the size of the frame "holding" the tiles
        self.puzzle_frame.size = (size[0]*3.45, size[1]*3.45)
        c = 0.045
        self.puzzle_frame.pos = (self.btns[2][0].pos[0] - c*self.height, self.btns[2][0].pos[1] - c*self.height) \
                                if self.width > self.height else \
                                (self.btns[2][0].pos[0] - c*self.width, self.btns[2][0].pos[1] - c*self.width)

    def create_grid(self, start: bool=False, move: str=None):
        before = None
        if start: # Start new game
            # Generate grid (3 x 3)
            while True:
                grid = random.sample([1, 2, 3, 4, 5, 6, 7, 8, -1], 9)
                grid = [grid[:3], grid[3:6], grid[6:9]]
                if self.isSolvable(grid):
                    break
            self.grid = grid
            for x, row in enumerate(grid):
                for y, item in enumerate(row):
                    self.btns[x].append(
                        Button(
                            size_hint = (None, None),
                            background_normal = resource_path(f"tiles/button{item}.png"), 
                            background_down = resource_path(f"tiles/button{item}.png"), 
                            opacity = 1,
                            disabled = not item > 0,
                            )
                        )
                    self.btns[x][y].bind(on_press=self.btn_click)
                    self.add_widget(self.btns[x][y])
        else:
            before = deepcopy(self.grid)
            self.grid = self.checker(self.grid, move)
            self.moves += 1
            
            # Play tile moving sound effect
            if sound_effects:
                self.tile_move_sound.play()

        # Tile animation
        if before is not None:
            for y, row in enumerate(before):
                for x, value in enumerate(row):
                    if before[y][x] != self.grid[y][x] and self.grid[y][x] != -1:
                        self.tile_moving = self.btns[y][x]
                        ty = (self.grid[0]+self.grid[1]+self.grid[2]).index(-1) // 3
                        tx = self.grid[ty].index(-1)
                        temp_btn = Button(
                            background_normal = resource_path(f"tiles/button{self.grid[y][x]}.png"),
                            background_down = resource_path(f"tiles/button{self.grid[y][x]}.png"),
                            opacity = 0.8 if tile_indication else 1,
                            size = self.btns[0][0].size,
                            size_hint = self.btns[0][0].size_hint,
                            pos = self.btns[ty][tx].pos
                        )

                        ty = (self.grid[0]+self.grid[1]+self.grid[2]).index(self.grid[y][x]) // 3
                        tx = self.grid[ty].index(self.grid[y][x])

                        self.add_widget(temp_btn)
                        bx, by = self.btns[ty][tx].pos # tempy and tempx
                        anim = Animation(x=bx, y=by, duration=tile_movement)
                        anim.bind(
                            on_progress = self.anim_in_progress,
                            on_complete = self.remove_anim_widget
                            )
                        anim.start(temp_btn)

        # Updating buttons
        for y, row in enumerate(self.btns):
            for x, item in enumerate(row):
                item.background_normal = resource_path(f"tiles/button{self.grid[y][x]}.png")
                item.background_down = resource_path(f"tiles/button{self.grid[y][x]}.png")
                if item != self.tile_moving and item.background_normal[-6:-4] != "-1":
                    """
                    Checks if the tile is the current moving one or the empty tile
                    """
                    if [[1,2,3], [4,5,6], [7,8,-1]][y][x] == int(item.background_normal[-5]) or not tile_indication:
                        item.opacity = 1
                    else:
                        item.opacity = 0.8
                else:
                    item.opacity = 0
                item.disabled = item.background_normal[-6:-4] == "-1" # disable button if button is empty tile
        
        if self.check_win(self.grid):
            def show_win_window(dt):
                global inst
                inst.root.current = "WinWindow"
                self.manager.transition.direction = "left"
            # Win Game
            global game_stats
            game_stats = f"""
You win!

Time taken: {round(self.timer, 2)}s 
Moves: {self.moves}
"""
            Clock.schedule_once(show_win_window, 0.4)
    
    def checker(self, puzzle: list, move: str):
        for i in range(3):
            try:
                c = puzzle[i].index(-1)
            
                if move == "up" and i > 0:
                    puzzle[i][c] = puzzle[i-1][c]
                    puzzle[i-1][c] = -1
                    break
                elif move == "down":
                    puzzle[i][c] = puzzle[i+1][c]
                    puzzle[i+1][c] = -1
                    break
                
                elif move == "left" and c > 0:
                    puzzle[i][c] = puzzle[i][c-1]
                    puzzle[i][c-1] = -1
                    break
                elif move == "right":
                    puzzle[i][c] = puzzle[i][c+1]
                    puzzle[i][c+1] = -1
                    break
            except Exception as e:
                pass
        return puzzle

    def btn_click(self, instance):
        # instance.text
        # Find Button from text
        for y in self.grid:
            for x in y:
                if resource_path(f"tiles/button{x}.png") == instance.background_normal or (x == -1 and instance.opacity == 0):
                    pressed = self.grid.index(y), y.index(x)

        y, x = pressed
        for i in range(4):
            try:
                if i == 0 and self.grid[y][x+1] == -1:
                    self.create_grid(False, "left"); break
                if i == 1 and self.grid[y][x-1] == -1 and x-1 != -1:
                    self.create_grid(False, "right"); break
                if i == 2 and self.grid[y+1][x] == -1:
                    self.create_grid(False, "up"); break
                if i == 3 and self.grid[y-1][x] == -1 and y-1 != -1:
                    self.create_grid(False, "down"); break
            except Exception:
                pass

    def check_win(self, puzzle: list):
        return puzzle == [[1, 2, 3], [4, 5, 6], [7, 8, -1]]

    def quit_game(self, *args):
        global inst
        inst.root.current = "WelcomeWindow"
        self.manager.transition.direction = "right"
        self.init_game()

class WindowManager(ScreenManager):
    pass



class PuzzleApp(App):

    btn_sound = SoundLoader.load(resource_path("sound_effects/tile_sliding.wav"))
    
    def resource_path(self, relative_path):
        """
        Same as the resource path above, but this is added so it can be accessed from the kv file.
        """
        return resource_path(relative_path)

    def build(self):
        self.use_kivy_settings = False
        kv = Builder.load_file(resource_path("slidingpuzzle.kv"))
        return kv

    def on_start(self):
        Window.update_viewport()
        self.title = "Sliding Puzzle by kitkat3141"
        self.songs = ["Suite Of Strings"]
        self.bg_songs = [SoundLoader.load(resource_path(f"music/{song}.wav")) for song in self.songs]
        self.current = 0
        for song in self.bg_songs:
            song.bind(on_stop=self.play_song)
            #song.volume = 0.1
        self.music_state = int(self.config.get("Audio", "music"))
        self.play_song()
        
        global sound_effects
        global tile_indication
        global tile_movement
        sound_effects = int(self.config.get("Audio", "sound_effects"))
        tile_indication = int(self.config.get("Graphics", "tile_indication"))
        tile_movement = float(self.config.get("Graphics", "tile_movement").split(" ")[0])

    def build_config(self, config):
        config.setdefaults(
            "Audio", {
                "music": 1,
                "sound_effects": 1,
            }
        )
        config.setdefaults(
            "Graphics", {
                "tile_indication": 1,
                "tile_movement": "0.15 (recommended)"
            }
        )

    def build_settings(self, settings):
        settings.add_json_panel(
            "Settings",
            self.config,
            filename=resource_path("puzzle_settings.json")
        )

    def display_settings(self, settings):
        try:
            p = self.settings_popup
        except AttributeError:
            self.settings_popup = Popup(
                content=settings,
                title='Settings',
                size_hint=(0.8, 0.8))
            p = self.settings_popup
        if p.content is not settings:
            p.content = settings
        p.background = resource_path("bg/bg.png")
        p.title_color = (0, 0, 0, 1)
        p.open()

    def close_settings(self, *args):
        try:
            p = self.settings_popup
            p.dismiss()
        except AttributeError:
            pass # Settings popup doesn't exist

    def on_config_change(self, config, section, key, value):
        if key == "music": 
            self.music_state = int(value)
            self.play_song()
        if key == "sound_effects":
            global sound_effects
            sound_effects = int(value)
        if key == "tile_indication":
            global tile_indication
            tile_indication = int(value)
        if key == "tile_movement":
            global tile_movement
            tile_movement = float(value.split(" ")[0])
        
    def play_song(self, *args):
        if self.music_state:
            if self.current >= len(self.songs) - 1:
                self.current = 0
            else:
                self.current += 1
            self.bg_songs[self.current].play()
        else:
            self.bg_songs[self.current].stop()

    def play_btn_sound(self):
        if sound_effects: 
            self.btn_sound.play()

if __name__ == "__main__":
    print("The game is starting! :D")
    inst = PuzzleApp()
    inst.run()