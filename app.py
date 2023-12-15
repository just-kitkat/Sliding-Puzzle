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

from utils.autosolver import solve
from utils.file_handler import resource_path, load_resources
from utils.constants import FRAME_SIZE_MULT, VERSION
from utils.api import get_info, get_latest_version, get_news
from utils.custom_labels import NewsLabel, WinLabel

import random
from copy import deepcopy
import trio
import time

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.config import ConfigParser
from kivy.factory import Factory
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.label import Label 
from kivy.uix.stacklayout import StackLayout
from kivy.animation import Animation


inst = None
sound_effects = True
tile_indication = True
tile_movement = 0
game_stats = None


class WelcomeWindow(Screen):
    pass


class InfoWindow(Screen):
    def on_pre_enter(self):
        self.width, self.height = Window.size
        self.layout = StackLayout(padding=(self.width//10, self.height//10, self.width//10, self.height//10), spacing=10)
        self.text_info = []
        CREDITS = get_info()
        for item in CREDITS:
            text = Label(
                text=f"{item}:\n| {CREDITS[item]}",
                font_size=self.width//20 if self.width < self.height else self.height//40 + self.width//75,
                size_hint=(0.5, 0.2) if self.height > self.width else (0.33, 0.33),
                halign="left",
                valign="center"
            )
            self.text_info.append(text)
            self.layout.add_widget(text)
            
        self.add_widget(self.layout)

    def on_enter(self):
        self.clock = Clock.schedule_interval(self.resize, 0.1)

    def resize(self, dt):
        self.width, self.height = Window.size
        for text in self.text_info:
            text.font_size = self.width//20 if self.width < self.height else self.height//40 + self.width//75
            text.size_hint = (0.5, 0.2) if self.height > self.width else (0.33, 0.33)
            text.text_size = text.size
        self.layout.padding = self.width//10, self.height//10, self.width//10, self.height//10 # left, up, right, down

    def on_leave(self):
        self.remove_widget(self.layout)
    
    def open_news(self):
        Logger.info("Game: Opening news page")
        Factory.register("NewsLabel", cls=NewsLabel)
        content = Factory.NewsLabel(text="Loading news...", pos_hint={"y": 0.5}, size_hint=(1,0.01))
        page = Popup(
            title="News",
            title_align="center",
            title_color="black",
            separator_color="brown",
            content=content,
            size_hint=(0.8, 0.8),
            background=resource_path("assets/bg/bg.png")
        )
        page.open()
        content.text=get_news()
    
    def on_latest_version(self):
        latest_version = get_latest_version()
        return VERSION == latest_version or latest_version is None


class WinWindow(Screen):
    def on_pre_enter(self, *args):
        Factory.register("WinLabel", cls=WinLabel)
        self.stats = Factory.WinLabel(
            text = game_stats
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
        width, height = Window.size
        loading = Label(
            text = "Loading...",
            font_size = height//20 if self.width > self.height else width//20,
            size_hint = (0.4, 0.3),
            pos_hint = {"center_x": 0.5, "center_y": 0.5}
        )
        self.add_widget(loading)
        self.tile_move_sound = SoundLoader.load(resource_path("sound_effects/tile_sliding.wav"))

    def on_enter(self):
        """
        Once in game, load sound effects and clear all widgets (the loading label)
        """
        #self.tile_move_sound.volume = 0.2 # Does not work with android (just throws an error like sound/volume is not defined)
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
        Helper function for is_solvable(puzzle)
        """
        inv_count, empty_value = 0, -1
        for i in range(0, 9):
            for j in range(i + 1, 9):
                if arr[j] != empty_value and arr[i] != empty_value and arr[i] > arr[j]:
                    inv_count += 1

        return inv_count
    
    def is_solvable(self, puzzle: list) -> bool:
        """
        Returns True if the 8 puzzle is solvable and vice versa
        """
        # Count inversions in given 8 puzzle
        inv_count = self.getInvCount([j for sub in puzzle for j in sub])

        # return true if inversion count is even.
        return inv_count % 2 == 0

    def init_game(self, *args):
        """
        Initialises the game
        """
        self.width, self.height = Window.size
        self.font_size = self.width//20
        self.grid = [[], [], []]
        self.btns = [[], [], []]
        self.moves = 0
        self.timer = 0
        self.autosolving = False

        # Add frame to screen
        self.puzzle_frame = Button(
            background_normal = resource_path("assets/bg/frame.png"),
            background_down = resource_path("assets/bg/frame.png"),
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

        # Create Autosolver Button
        self.autosolver_btn = Button(
            text = "Find solution",
            font_size = self.font_size//2.5,
            size_hint = (0.12, 0.1),
            pos_hint = {"center_x": 0.07, "top": 0.98}
        )
        self.autosolver_btn.bind(on_release=self.start_autosolver)
        self.add_widget(self.autosolver_btn)

        # Quit button
        self.quit_btn = Button(
            font_size = self.font_size//1.5,
            size_hint = (None, None),
            size = (
                self.width//9 if self.width < self.height else self.height//12, 
                self.width//9 if self.width < self.height else self.height//12
                ),
            pos = (
                self.width - (self.width//7 if self.width < self.height else self.height//8), 
                (self.width//80 if self.width < self.height else self.height//80)
                ),
            background_normal = "assets/btns/back.png",
            background_down = resource_path("assets/btns/back.png")
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

        self.timer_btn.font_size = self.font_size//1.8 if self.width > self.height else self.font_size
        self.timer_btn.size_hint = (0.12, 0.1) if self.width > self.height else (0.2, 0.07)
        self.timer_btn.pos_hint = {"center_x": 0.93, "top": 0.98} if self.width > self.height else {"center_x": 0.88, "top": 0.98}

        self.autosolver_btn.font_size = self.font_size//2.5 if self.width > self.height else self.font_size//1.5
        self.autosolver_btn.size_hint = (0.12, 0.1) if self.width > self.height else (0.2, 0.07)
        self.autosolver_btn.pos_hint = {"center_x": 0.07, "top": 0.98} if self.width > self.height else {"center_x": 0.12, "top": 0.98}

        self.quit_btn.pos = (
                self.width - (self.width//7 if self.width < self.height else self.height//6), 
                self.width//85 if self.width < self.height else self.height//85
                )
        self.quit_btn.size = (
                self.width//9 if self.width < self.height else self.height//8, 
                self.width//9 if self.width < self.height else self.height//8
                )

        size = self.height//FRAME_SIZE_MULT if self.height < self.width else self.width//FRAME_SIZE_MULT
        # [btn1.pos, btn2.pos, btn3.pos]
        x_pos = [self.width//2 - self.height//4.2, self.width//2, self.width//2 + self.height//4.2] \
                if self.width > self.height else \
                [self.width//2 - self.width//4.2, self.width//2, self.width//2 + self.width//4.2]
        y_pos = [self.height//2 - self.height//4.2, self.height//2, self.height//2 + self.height//4.2] \
                if self.width > self.height else \
                [self.height//2 - self.width//4.2, self.height//2, self.height//2 + self.width//4.2]
        
        for y, row in enumerate(self.btns[::-1]):
            for x, item in enumerate(row):
                item_size = size//3.38
                item.size = item_size, item_size
                # pos = pos - size of tile
                item.pos = (x_pos[x] - item_size//2, y_pos[y] - item_size//2) \
                            if self.width > self.height else \
                            (x_pos[x] - item_size//2, y_pos[y] - item_size//2)
                            
        # This adjusts the size of the frame "holding" the tiles
        self.puzzle_frame.size = size, size
        c = 0.045
        self.puzzle_frame.pos = (self.btns[2][0].pos[0] - c*self.height, self.btns[2][0].pos[1] - c*self.height) \
                                if self.width > self.height else \
                                (self.btns[2][0].pos[0] - c*self.width, self.btns[2][0].pos[1] - c*self.width) #TODO: delete
        self.puzzle_frame.pos_hint = {"center_x": 0.5, "center_y": 0.5}

    def create_grid(self, start: bool=False, move: str=None):
        before = None
        if start: # Start new game
            # Generate grid (3 x 3)
            count = 1
            while True:
                grid = random.sample([1, 2, 3, 4, 5, 6, 7, 8, -1], 9)
                grid = [grid[:3], grid[3:6], grid[6:9]]
                if self.is_solvable(grid):
                    break
                count += 1
            Logger.info(f"Game: Generated puzzle in {count} tries")

            self.grid = grid
            for y, row in enumerate(grid):
                for x, item in enumerate(row):
                    self.btns[y].append(
                        Button(
                            size_hint = (None, None),
                            background_normal = resource_path(f"assets/tiles/button{item}.png"), 
                            background_down = resource_path(f"assets/tiles/button{item}.png"), 
                            opacity = 1,
                            disabled = not item > 0,
                            )
                        )
                    self.btns[y][x].bind(on_press=self.btn_click)
                    self.add_widget(self.btns[y][x])

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
                            background_normal = resource_path(f"assets/tiles/button{self.grid[y][x]}.png"),
                            background_down = resource_path(f"assets/tiles/button{self.grid[y][x]}.png"),
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
                item.background_normal = resource_path(f"assets/tiles/button{self.grid[y][x]}.png")
                item.background_down = resource_path(f"assets/tiles/button{self.grid[y][x]}.png")

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
                inst.root.current = "WinWindow"
                self.manager.transition.direction = "left"

            # Win Game
            global game_stats
            game_stats = f"""
{'You win' if not self.autosolving else 'Puzzle solved'}!

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

    def btn_click(self, instance, autosolving=False):
        """
        Start tile movement when a tile is clicked
        """
        if self.autosolving and not autosolving:
            return
        
        # Find Button from text
        for y in self.grid:
            for x in y:
                if resource_path(f"assets/tiles/button{x}.png") == instance.background_normal or (x == -1 and instance.opacity == 0):
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
        self.autosolving = False
        inst.root.current = "WelcomeWindow"
        self.manager.transition.direction = "right"
    
    def start_autosolver(self, *args):
        """
        Disable tiles, start BFS to find optimal solution and display it
        """
        if self.autosolving:
            return
        
        self.autosolving = True
        self.moves = 0
        self.autosolver_btn.text = "Solving..."
        Logger.info("Game: Starting autosolver")
        inst.nursery.start_soon(self.autosolver)
    
    async def autosolver(self):
        start_time = time.time()
        moves = solve(self.grid)[1][1:]
        self.autosolver_btn.text = f"Solved [{round(time.time() - start_time, 1)}s]" if len(moves) > 0 else "No solution"
        Logger.info(f"Game: Optimal route found ({len(moves)} moves)" if len(moves) > 0 else "No solution found")
        if len(moves) == 0:
            self.autosolving = False
            return
        # Find empty tiles
        for y, row in enumerate(self.grid):
            for x, i in enumerate(row):
                if i == -1:
                    empty = x,y
        x, y = empty

        Logger.info("Game: Displaying solution")
        for move in moves:
            await trio.sleep(0.2)
            if not self.autosolving:
                return
            match move:
                case "left":
                    x -= 1
                    self.btn_click(self.btns[y][x], True)
                case "right":
                    x += 1
                    self.btn_click(self.btns[y][x], True)
                case "up":
                    y -= 1
                    self.btn_click(self.btns[y][x], True)
                case "down":
                    y += 1
                    self.btn_click(self.btns[y][x], True)


class WindowManager(ScreenManager):
    pass


# APP
class PuzzleApp(App):

    def __init__(self, nursery):
        super().__init__()
        self.nursery = nursery
        self.btn_sound = SoundLoader.load(resource_path("sound_effects/tile_sliding.wav"))
    
    def resource_path(self, relative_path):
        """
        Same as the resource_path function above, but this is added so it can be accessed from the kv file.
        """
        return resource_path(relative_path)

    def build(self):
        self.use_kivy_settings = False
        load_resources()
        kv = Builder.load_file(resource_path("slidingpuzzle.kv"))
        return kv

    def on_start(self):
        Window.update_viewport()
        self.title = "Sliding Puzzle by JustKitkat"

        self.songs = ["suiteofstrings"]
        Logger.info("Game: Loading songs")
        self.bg_songs = [SoundLoader.load(resource_path(f"music/{song}.mp3")) for song in self.songs]
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

        p.background = resource_path("assets/bg/bg.png")
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


async def main():
    global inst
    async with trio.open_nursery() as nursery:
        # Start app
        inst = PuzzleApp(nursery)
        await inst.async_run(async_lib="trio")
        nursery.cancel_scope.cancel()

if __name__ == "__main__":
    Logger.info("Game: Starting...")
    trio.run(main)