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

from typing import List
from copy import deepcopy
from itertools import chain

def solve(grid: List[List[int]]) -> [int, List[str]]:
    """
    Use BFS to get the optimal moves to solve the sliding puzzle
    """
    cache: str = {"placeholder"} # set of past grids
    store: List[list] = [[[grid, [""], (None, None)]]] # [[[grid1,last_move,moves]], [[grid1_1,last_move,moves], [grid1_2,last_move,moves]]]
    
    def bfs(grid: List[List[int]], moves: List[str], x: int, y: int) -> [int, List[str], tuple[int | None]]:
        """
        Breadth first search algorithm
        """
        # Boundary condition (no solution found -> num_moves > 31)
        if len(moves) > 31: # max moves is 31 (+ 1 empty string inserted)
            return "not found"
        
        # Most efficient way i know to flatten a nested list of integers (i'm sorry)
        grid_str: str = f"{grid[0][0]}{grid[0][1]}{grid[0][2]}{grid[1][0]}{grid[1][1]}{grid[1][2]}{grid[2][0]}{grid[2][1]}{grid[2][2]}"
        if grid_str in cache:
            return
        else:
            cache.add(grid_str)
        
        
        # Locate empty tile (x and y)
        if x is None: # check if finding the empty tile is needed (for first bfs layer)
            for y, row in enumerate(grid):
                for x, item in enumerate(row):
                    if item == -1: break
                if item == -1: break

        # Remove previous moves from possible moves
        opposite_move_list = ["up", "down", "up", "left", "right", "left"]
        to_move = ["up", "down", "left", "right"]
        last_move = moves[-1]

        if last_move != "":
            to_move.remove(opposite_move_list[opposite_move_list.index(last_move)+1])

        # Move tile and store it(excluding the last_move)
        original_coords = x, y
        for move in to_move:
            new_grid = deepcopy(grid)
            x, y = original_coords
            if move == "up" and y != 0:
                new_grid[y][x], new_grid[y-1][x] = new_grid[y-1][x], new_grid[y][x]
                y -= 1
            elif move == "down" and y != 2:
                new_grid[y][x], new_grid[y+1][x] = new_grid[y+1][x], new_grid[y][x]
                y += 1
            elif move == "left" and x != 0:
                new_grid[y][x], new_grid[y][x-1] = new_grid[y][x-1], new_grid[y][x]
                x -= 1
            elif move == "right" and x != 2:
                new_grid[y][x], new_grid[y][x+1] = new_grid[y][x+1], new_grid[y][x]
                x += 1
            else:
                continue
            
            store[-1].append([new_grid, moves + [move], (x, y)])
            
            if new_grid == [[1,2,3], [4,5,6], [7,8,-1]]: # func: check_win(grid); Check if new grid is correct ([[1,2,3], [4,5,6], [7,8,-1]])
                return "found"

    status = None
    if store[0][0][0] == [[1,2,3], [4,5,6], [7,8,-1]]:
        return store[0][0]
    
    while status is None:
        store.append([])
        for i in store[-2]:
            status = bfs(i[0], i[1], i[2][0], i[2][1])
            if status != None:
                break

    return store[-1][-1] if status == "found" else "not found"

"""
# Used to test efficiency
import time

s=time.time()
print(len(solve([[1,8,7],[4,2,-1],[5,3,6]])[-2] ))
print(time.time()-s)
#18742-1536
"""