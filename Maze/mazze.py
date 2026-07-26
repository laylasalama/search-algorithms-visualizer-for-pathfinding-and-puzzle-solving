
import tkinter as tk
import random
import threading
from typing import Dict, Tuple

# Minimal maze visualizer: generates maze from scratch and shows two disabled buttons

# Directions (dx, dy, name)
DIRECTIONS = [(0, -1, 'N'), (0, 1, 'S'), (1, 0, 'E'), (-1, 0, 'W')]

# Visual constants
CELL_SIZE = 10
WALL_COLOR = 'black'
VISITED_COLOR = '#cfefff'
EMPTY_COLOR = 'white'
START_COLOR = 'green'
GOAL_COLOR = 'red'


class MazeGenerator:
	def __init__(self, w, h):
		self.w = w
		self.h = h
		# initialize as empty mapping to satisfy static analyzers
		self.maze: Dict[Tuple[int, int], Dict[str, bool]] = {}

	def generate(self, callback=None, update_every=1):
		# Initialize all walls present
		self.maze = {(x, y): {'N': True, 'S': True, 'E': True, 'W': True}
					 for y in range(self.h) for x in range(self.w)}

		visited = set()
		stack = []
		x, y = random.randint(0, self.w - 1), random.randint(0, self.h - 1)
		visited.add((x, y))
		stack.append((x, y))
		steps = 0

		while stack:
			x, y = stack[-1]
			neighbors = []
			for dx, dy, dname in DIRECTIONS:
				nx, ny = x + dx, y + dy
				if 0 <= nx < self.w and 0 <= ny < self.h and (nx, ny) not in visited:
					neighbors.append((dname, nx, ny))

			if neighbors:
				d, nx, ny = random.choice(neighbors)
				# remove wall between
				opp = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}[d]
				self.maze[(x, y)][d] = False
				self.maze[(nx, ny)][opp] = False
				visited.add((nx, ny))
				stack.append((nx, ny))
				steps += 1
				if callback and (steps % update_every == 0):
					callback(self.maze, list(visited))
			else:
				stack.pop()

		# final callback
		if callback:
			callback(self.maze, list(visited))


class SimpleMazeGUI:
	def __init__(self, master, width=50, height=50):
		self.master = master
		self.width = width
		self.height = height
		self.cell = CELL_SIZE
		self.canvas = tk.Canvas(master,
								width=self.width * self.cell,
								height=self.height * self.cell,
								bg=EMPTY_COLOR)
		self.canvas.pack(padx=10, pady=10)

		self.info = tk.Label(master, text='Click "Generate" to create a maze')
		self.info.pack()

		btn_frame = tk.Frame(master)
		btn_frame.pack(pady=6)

		self.gen_btn = tk.Button(btn_frame, text='Generate New Maze', command=self.generate)
		self.gen_btn.pack(side=tk.LEFT, padx=6)

		# Non-functional buttons (intentionally not wired)
		self.compare_btn = tk.Button(btn_frame, text='Show Comparison', state=tk.DISABLED)
		self.compare_btn.pack(side=tk.LEFT, padx=6)

		self.back_btn = tk.Button(btn_frame, text='Go Back', state=tk.DISABLED)
		self.back_btn.pack(side=tk.LEFT, padx=6)

		# For setting start/goal visually (optional)
		self.start = None
		self.goal = None
		# initialize as empty mapping so type-checkers know it's iterable
		self.maze: Dict[Tuple[int, int], Dict[str, bool]] = {}

		# incremental update bookkeeping
		self._last_visited = set()
		self._pending_maze = None
		self._pending_visited = None
		self._scheduled = False
		self.canvas.bind('<Button-1>', self.on_click)

	def generate(self):
		self.info.config(text='Generating...')
		self.canvas.delete('all')
		self.start = None
		self.goal = None
		gen = MazeGenerator(self.width, self.height)

		def cb(maze, visited):
			# called from generator thread; schedule main-thread update
			self._pending_maze = maze
			self._pending_visited = visited
			if not self._scheduled:
				self._scheduled = True
				# schedule processing on main thread
				self.master.after(1, self._process_pending)

		# choose update frequency based on maze size to reduce UI overhead
		total = max(1, self.width * self.height)
		update_every = max(1, total // 150)

		# run generator in thread to keep UI responsive
		t = threading.Thread(target=gen.generate, args=(cb, update_every), daemon=True)
		t.start()


	def _process_pending(self):
		# run on main thread
		maze = self._pending_maze
		visited = list(self._pending_visited) if self._pending_visited is not None else []
		self._pending_maze = None
		self._pending_visited = None
		self._scheduled = False

		if not maze:
			return
		self.maze = maze
		visited_set = set(visited)
		new = visited_set - self._last_visited

		for (x, y) in new:
			x1 = x * self.cell
			y1 = y * self.cell
			x2 = x1 + self.cell
			y2 = y1 + self.cell
			self.canvas.create_rectangle(x1, y1, x2, y2, fill=VISITED_COLOR, width=0)

		self._last_visited.update(new)

		# if generation finished (all cells visited) draw final walls cleanly
		if len(visited_set) >= self.width * self.height:
			self.draw_full()
			self.info.config(text='Generation complete')

		self.master.update_idletasks()

	def on_click(self, event):
		# let user set start/goal for future features; mark visually
		cx = event.x // self.cell
		cy = event.y // self.cell
		if not self.maze:
			return
		if self.start is None:
			self.start = (cx, cy)
			self.canvas.create_rectangle(cx * self.cell, cy * self.cell,
										 (cx + 1) * self.cell, (cy + 1) * self.cell,
										 fill=START_COLOR, width=0)
			self.info.config(text=f'Start set at {self.start}')
		elif self.goal is None:
			if (cx, cy) == self.start:
				return
			self.goal = (cx, cy)
			self.canvas.create_rectangle(cx * self.cell, cy * self.cell,
										 (cx + 1) * self.cell, (cy + 1) * self.cell,
										 fill=GOAL_COLOR, width=0)
			self.info.config(text=f'Ready. Start: {self.start} Goal: {self.goal}')
		else:
			# reset start/goal
			self.start = (cx, cy)
			self.goal = None
			self.draw_full()
			self.canvas.create_rectangle(cx * self.cell, cy * self.cell,
										 (cx + 1) * self.cell, (cy + 1) * self.cell,
										 fill=START_COLOR, width=0)

	def draw_full(self):
		# redraw full maze background + walls
		if not self.maze:
			return
		self.canvas.delete('all')
		for (x, y), cell in self.maze.items():
			x1 = x * self.cell
			y1 = y * self.cell
			x2 = x1 + self.cell
			y2 = y1 + self.cell
			self.canvas.create_rectangle(x1, y1, x2, y2, fill=EMPTY_COLOR, width=0)
		for (x, y), cell in self.maze.items():
			x1 = x * self.cell
			y1 = y * self.cell
			x2 = x1 + self.cell
			y2 = y1 + self.cell
			if cell['N']:
				self.canvas.create_line(x1, y1, x2, y1, fill=WALL_COLOR)
			if cell['S']:
				self.canvas.create_line(x1, y2, x2, y2, fill=WALL_COLOR)
			if cell['E']:
				self.canvas.create_line(x2, y1, x2, y2, fill=WALL_COLOR)
			if cell['W']:
				self.canvas.create_line(x1, y1, x1, y2, fill=WALL_COLOR)


def main():
	root = tk.Tk()
	root.title('Maze Generator - Simple Visualizer')
	app = SimpleMazeGUI(root, width=50, height=50)
	root.mainloop()


if __name__ == '__main__':
	main()

