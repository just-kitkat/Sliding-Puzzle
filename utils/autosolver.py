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
    store: List[list] = [[[grid, [""]]]] # [[[grid1,last_move,moves]], [[grid1_1,last_move,moves], [grid1_2,last_move,moves]]]
    
    def bfs(grid: List[List[int]], moves: List[str]) -> [int, List[str]]:
        """
        Breadth first search algorithm
        """
        # Boundary condition (no solution found -> num_moves > 60)
        if len(moves) > 31: # max moves is 31 (+ 1 empty string inserted)
            return "not found"
        
        grid_str: str = "".join(str(i) for i in list(chain.from_iterable(grid)))
        if grid_str in cache:
            return
        else:
            cache.add(grid_str)
        
        
        # Locate empty tile (x and y)
        #print(f"{grid=}")
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
        for move in to_move:
            new_grid = deepcopy(grid)
            #print(move,to_move,new_grid,moves,store)
            if move == "up" and y != 0:
                new_grid[y][x], new_grid[y-1][x] = new_grid[y-1][x], new_grid[y][x]
            elif move == "down" and y != 2:
                new_grid[y][x], new_grid[y+1][x] = new_grid[y+1][x], new_grid[y][x]
            elif move == "left" and x != 0:
                new_grid[y][x], new_grid[y][x-1] = new_grid[y][x-1], new_grid[y][x]
            elif move == "right" and x != 2:
                new_grid[y][x], new_grid[y][x+1] = new_grid[y][x+1], new_grid[y][x]
            else:
                continue
            
            store[-1].append([new_grid, moves + [move]])
            
            if new_grid == [[1,2,3], [4,5,6], [7,8,-1]]: # func: check_win(grid); Check if new grid is correct ([[1,2,3], [4,5,6], [7,8,-1]])
                return "found"

    status = None
    if store[0][0][0] == [[1,2,3], [4,5,6], [7,8,-1]]:
        return store[0][0]
    while status is None:
        store.append([])
        for i in store[-2]:
            status = bfs(i[0], i[1])
            if status != None:
                break
    return store[-1][-1] if status == "found" else "not found"