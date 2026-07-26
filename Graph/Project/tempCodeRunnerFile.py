from tkinter import Tk, Label, Frame, Button, PhotoImage, RIDGE, SUNKEN, N, S, E, W, messagebox
from tkinter import Toplevel, Canvas, Scale, HORIZONTAL, Checkbutton, BooleanVar
from tkinter import font as tkfont
from tkinter import ttk
import math
import heapq
from collections import deque
import time
import threading
try:
	import psutil
except Exception:
	psutil = None
from typing import Dict, Any, Tuple
import sys
import traceback


# small dummy text widget used when tkinter.Text unavailable
class DummyText:
	def insert(self, *args, **kwargs):
		return None
	def see(self, *args, **kwargs):
		return None
	def pack(self, *args, **kwargs):
		return None
	def delete(self, *args, **kwargs):
		return None
	def __init__(self):
		# emulate a minimal internal state for 'state' so cget/config behave
		self._state = 'normal'

	def config(self, *args, **kwargs):
		# allow callers to set a 'state' kwarg similar to tkinter.Text
		try:
			if 'state' in kwargs:
				self._state = kwargs.get('state')
		except Exception:
			pass
		return None

	def cget(self, key):
		# minimal support: return the stored 'state' value when requested
		try:
			if key == 'state':
				return self._state
		except Exception:
			pass
		return None
# The execution visualization (ExecutionWindow) is embedded below in this file.
# We do not import an external execution module to"y" is possibly unbound avoid type conflicts with editors.

# Window setup
window = Tk()
window.title("AI Search Algorithms Visualization")
window.geometry("1920x1080")
# global exception logging: record uncaught exceptions to a file for easier debugging
LOG_PATH = 'gui_exceptions.log'
def _log_exception(exc_type, exc_value, exc_tb):
	try:
		with open(LOG_PATH, 'a') as _f:
			traceback.print_exception(exc_type, exc_value, exc_tb, file=_f)
	except Exception:
		pass
# sys.excepthook for non-tk exceptions
sys.excepthook = _log_exception
# tkinter callback exception hook (called for exceptions raised in tkinter callbacks)
try:
	# Tk exposes report_callback_exception; bind it to our logger
	def _tk_report(exc, val, tb):
		try:
			with open(LOG_PATH, 'a') as _f:
				traceback.print_exception(exc, val, tb, file=_f)
		except Exception:
			pass
	window.report_callback_exception = _tk_report
except Exception:
	pass
# Color palette
WINDOW_BG = "#f7fafc"      # very light
PANEL_BG = "#e6eef6"       # pale blue panels
HEADER_BG = "#2b6cb0"      # deep blue for headings
HEADER_FG = "white"
LABEL_FG = "#063a6f"       # dark blue text for labels
ACCENT_OK = "#2f855a"      # green for Run
# Visualization colors
NODE_BG = '#e7f2ff'
VISITED_COLOR = ACCENT_OK
CURRENT_COLOR = '#ffbf00'   # amber for current node
PATH_COLOR = '#8e44ad'      # special final-path color (purple)
EDGE_BG = '#e6e6e6'         # faint background edges
ALGO_LABELS = {'BFS','DFS','UCS','A*','Beam','IDA*','Greedy','Hill Climbing'}

window.configure(background=WINDOW_BG)
# layout constants for algorithm/control column (right side)
ALGO_BASE_X = 1480
ALGO_FRAME_W = 320
ALGO_FRAME_H = 80

start = None
goal  = None
algorithm = None
currently_dragging = None
original_pos       = {}
widget_names: dict = {}  # Map widgets to their names

#funcions for drag and drop
def drag_start(event):
	global currently_dragging, original_pos, start, goal
	currently_dragging = event.widget
	if currently_dragging not in original_pos:
		original_pos[currently_dragging] = (currently_dragging.winfo_x(), currently_dragging.winfo_y())
	currently_dragging.startX = event.x
	currently_dragging.startY = event.y
	widget_name = widget_names.get(currently_dragging)
	if widget_name and start == widget_name:
		start = None
		try:
			start_value_label.config(text="(none)")
		except Exception:
			pass
	if widget_name and goal == widget_name:
		goal = None
		try:
			goal_value_label.config(text="(none)")
		except Exception:
			pass
	# clear algorithm assignment if dragging the currently placed algorithm
	if widget_name and algorithm == widget_name:
		# allow reassigning algorithm by clearing current value at drag start
		try:
			# assign to global
			globals()['algorithm'] = None
		except Exception:
			pass
		try:
			algo_value_label.config(text="(none)")
		except Exception:
			pass

def drag_motion(event):
	global currently_dragging, start, goal
	if not currently_dragging:
		return
	widget = event.widget
	x = currently_dragging.winfo_x() - currently_dragging.startX + event.x
	y = currently_dragging.winfo_y() - currently_dragging.startY + event.y
	currently_dragging.place(x=x, y=y)

def drop(event):
	global currently_dragging, start, goal, algorithm, original_pos
	if not currently_dragging:
		return

	name = widget_names.get(currently_dragging)
	if not name:
		currently_dragging = None
		return
		
	x_mouse = event.x_root - window.winfo_rootx()
	y_mouse = event.y_root - window.winfo_rooty()
	placed = False

	# helper: get frame bounds (x,y,width,height) relative to main window
	def _frame_bounds(frm):
		sx = frm.winfo_x()
		sy = frm.winfo_y()
		try:
			sw = frm.winfo_width()
			sh = frm.winfo_height()
		except Exception:
			sw, sh = (400, 80)
		return sx, sy, sw, sh

	# compute bounds for start, goal and algorithm frames
	sx_s, sy_s, sw_s, sh_s = _frame_bounds(start_frame)
	sx_g, sy_g, sw_g, sh_g = _frame_bounds(goal_frame)
	sx_a, sy_a, sw_a, sh_a = _frame_bounds(algorithm_frame)

	# START area
	if sx_s <= x_mouse <= sx_s + sw_s and sy_s <= y_mouse <= sy_s + sh_s:
		# treat any algorithm name declared in ALG_MAP as an algorithm
		if name in ALG_MAP:
			# cannot drop algorithm into START
			orig_x, orig_y = original_pos.get(currently_dragging, (0, 0))
			currently_dragging.place(x=orig_x, y=orig_y)
		else:
			if start is None:
				set_start(name)
				try:
					currently_dragging.place(x=sx_s + 10, y=sy_s + 10)
				except Exception:
					pass
				placed = True
			else:
				orig_x, orig_y = original_pos.get(currently_dragging, (0, 0))
				currently_dragging.place(x=orig_x, y=orig_y)

	# GOAL area
	elif sx_g <= x_mouse <= sx_g + sw_g and sy_g <= y_mouse <= sy_g + sh_g:
		if name in ALG_MAP:
			# cannot drop an algorithm into GOAL
			orig_x, orig_y = original_pos.get(currently_dragging, (0, 0))
			currently_dragging.place(x=orig_x, y=orig_y)
		else:
			if goal is None:
				set_goal(name)
				try:
					currently_dragging.place(x=sx_g + 10, y=sy_g + 10)
				except Exception:
					pass
				placed = True
			else:
				orig_x, orig_y = original_pos.get(currently_dragging, (0, 0))
				currently_dragging.place(x=orig_x, y=orig_y)

	# ALGORITHM area
	elif sx_a <= x_mouse <= sx_a + sw_a and sy_a <= y_mouse <= sy_a + sh_a:
		# only algorithms (keys in ALG_MAP) may be placed here
		if name in ALG_MAP:
			if algorithm is None:
				set_algorithm(name)
				try:
					currently_dragging.place(x=sx_a + 10, y=sy_a + 10)
				except Exception:
					pass
				placed = True
			else:
				# already have algorithm placed; reject
				orig_x, orig_y = original_pos.get(currently_dragging, (0, 0))
				currently_dragging.place(x=orig_x, y=orig_y)
		else:
			# reject placing a city into the algorithm area
			orig_x, orig_y = original_pos.get(currently_dragging, (0, 0))
			currently_dragging.place(x=orig_x, y=orig_y)

	# restore original position if not placed
	if not placed:
		orig_x, orig_y = original_pos.get(currently_dragging, (0, 0))
		currently_dragging.place(x=orig_x, y=orig_y)

	currently_dragging = None

import os
_img_path = os.path.join(os.path.dirname(__file__), 'Romania.png')
try:
	photo = PhotoImage(file=_img_path)
	Label(window, image=photo, bg=WINDOW_BG).place(x=506, y=0)
except Exception as _e:
	print(f"Warning: couldn't load image '{_img_path}': {_e}")

# Text display

Start = Label(window, text="START", font=("Arial", 40), relief= RIDGE, bg=HEADER_BG, fg=HEADER_FG)
Start.place(x=160, y=10)
start_frame = Frame(window, width=400, height=80, bg=PANEL_BG, relief=SUNKEN, bd=5)
start_frame.place(x=48, y=140)
# value label inside start_frame
start_value_label = Label(start_frame, font=("Arial", 20), bg=PANEL_BG, fg=LABEL_FG)
start_value_label.place(relx=0.02, rely=0.15)

Goal = Label(window, text="GOAL", font=("Arial", 40), relief= RIDGE, bg=HEADER_BG, fg=HEADER_FG)
Goal.place(x=170, y=270)
goal_frame = Frame(window, width=400, height=80, bg=PANEL_BG, relief=SUNKEN, bd=5)
goal_frame.place(x=48, y=400)
# value label inside goal_frame
goal_value_label = Label(goal_frame, font=("Arial", 20), bg=PANEL_BG, fg=LABEL_FG)
goal_value_label.place(relx=0.02, rely=0.15)

Algorithm = Label(window, text="ALGORITHM:", font=("Arial", 40), relief= RIDGE, bg=HEADER_BG, fg=HEADER_FG)
Algorithm.place(x=1480, y=10)
algorithm_frame = Frame(window, width=400, height=80, bg=PANEL_BG, relief=SUNKEN, bd=5)
algorithm_frame.place(x=1450, y=140)
# value label inside algorithm_frame
algo_value_label = Label(algorithm_frame, font=("Arial", 16), bg=PANEL_BG, fg=LABEL_FG)
algo_value_label.place(relx=0.02, rely=0.2)

def choose_from_list(title, items, callback):
	# simple popup to choose one item from a list
	win = Toplevel(window)
	win.title(title)
	win.geometry("300x400")
	frm = Frame(win)
	frm.pack(fill='both', expand=True)
	# create buttons for each item
	for it in items:
		b = Button(frm, text=it, width=30, command=(lambda v=it: (callback(v), win.destroy())))
		b.pack(pady=2, padx=6)

def on_start_frame_click(event=None):
	# choose from city list
	items = list(graph.keys())
	choose_from_list('Choose START city', items, set_start)

def on_goal_frame_click(event=None):
	items = list(graph.keys())
	choose_from_list('Choose GOAL city', items, set_goal)

def on_algorithm_frame_click(event=None):
	items = list(ALG_MAP.keys())
	choose_from_list('Choose ALGORITHM', items, set_algorithm)

def set_start(name: str):
	global start
	if name in graph:
		start = name
		start_value_label.config(text=name)

def set_goal(name: str):
	global goal
	if name in graph:
		goal = name
		goal_value_label.config(text=name)

def set_algorithm(name: str):
	global algorithm
	if name in ALG_MAP:
		algorithm = name
		algo_value_label.config(text=name)

# allow clicking the frames to choose values
start_frame.bind('<Button-1>', on_start_frame_click)
goal_frame.bind('<Button-1>', on_goal_frame_click)
algorithm_frame.bind('<Button-1>', on_algorithm_frame_click)

def run_all_algorithms():
	global start, goal, algorithm
	if start is None or goal is None:
		messagebox.showwarning("Warning", "Please set START and GOAL before running")
		return
	# Open a single ExecutionWindow and run all algorithms sequentially inside it
	try:
		ew = ExecutionWindow(window, start, goal, None)
		# run the visual sequence in a background thread so the main UI stays responsive
		threading.Thread(target=lambda: ew.run_all_visual(list(ALG_MAP.keys())), daemon=True).start()
	except Exception as e:
		messagebox.showerror('Error', f'Failed to start combined run: {e}')

Run_all = Button(window, text="Run All:", font=("Arial", 40), relief= RIDGE, bg=HEADER_BG, fg=HEADER_FG, command=run_all_algorithms)
Run_all.place(x=1540, y=270)

# Add Run button to launch execution window (uses ExecutionWindow from Graph/GUI.py)
def run_execution():
	global start, goal, algorithm
	if start is None or goal is None:
		messagebox.showwarning("Warning", "Please set START and GOAL before running")
		return
	# Run the single placed algorithm (no checkboxes in this layout)
	if algorithm is None:
		messagebox.showwarning("Warning", "Please set an ALGORITHM before running")
		return
	ExecutionWindow(window, start, goal, algorithm)

run_btn = Button(window, text="Run", font=("Arial", 40), bg=HEADER_BG, fg=HEADER_FG, command=run_execution)
run_btn.place(x=1587, y=400)

#places to choose from
Label(window, text="Places to choose from:", font=("Arial", 40), relief= RIDGE, bg=HEADER_BG, fg=HEADER_FG).place(x=320, y=550)

Arad           = Label(window, text="Arad"          , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Arad.place(x=60, y=625)
widget_names[Arad] = "Arad"
Arad.bind("<Button-1>", drag_start)
Arad.bind("<B1-Motion>", drag_motion)
Arad.bind("<ButtonRelease-1>", drop)

Buchurest      = Label(window, text="Buchurest"     , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Buchurest.place(x=240, y=625)
widget_names[Buchurest] = "Buchurest"
Buchurest.bind("<Button-1>", drag_start)
Buchurest.bind("<B1-Motion>", drag_motion)
Buchurest.bind("<ButtonRelease-1>", drop)

Craiova        = Label(window, text="Craiova"       , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Craiova.place(x=510, y=625)
widget_names[Craiova] = "Craiova"
Craiova.bind("<Button-1>", drag_start)
Craiova.bind("<B1-Motion>", drag_motion)
Craiova.bind("<ButtonRelease-1>", drop)

Dobreta        = Label(window, text="Dobreta"       , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Dobreta.place(x=750, y=625)
widget_names[Dobreta] = "Dobreta"
Dobreta.bind("<Button-1>", drag_start)
Dobreta.bind("<B1-Motion>", drag_motion)
Dobreta.bind("<ButtonRelease-1>", drop)

Eforie         = Label(window, text="Eforie"        , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Eforie.place(x=1010, y=625)
widget_names[Eforie] = "Eforie"
Eforie.bind("<Button-1>", drag_start)
Eforie.bind("<B1-Motion>", drag_motion)
Eforie.bind("<ButtonRelease-1>", drop)

Fargaras       = Label(window, text="Fargaras"      , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Fargaras.place(x=20, y=730)
widget_names[Fargaras] = "Fargaras"
Fargaras.bind("<Button-1>", drag_start)
Fargaras.bind("<B1-Motion>", drag_motion)
Fargaras.bind("<ButtonRelease-1>", drop)

Giurgiu        = Label(window, text="Giurgiu"       , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Giurgiu.place(x=258, y=710)
widget_names[Giurgiu] = "Giurgiu"
Giurgiu.bind("<Button-1>", drag_start)
Giurgiu.bind("<B1-Motion>", drag_motion)
Giurgiu.bind("<ButtonRelease-1>", drop)

Hirsova        = Label(window, text="Hirsova"       , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Hirsova.place(x=510, y=730)
widget_names[Hirsova] = "Hirsova"
Hirsova.bind("<Button-1>", drag_start)
Hirsova.bind("<B1-Motion>", drag_motion)
Hirsova.bind("<ButtonRelease-1>", drop)

Lasi           = Label(window, text="Lasi"          , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Lasi.place(x=785, y=730)
widget_names[Lasi] = "Lasi"
Lasi.bind("<Button-1>", drag_start)
Lasi.bind("<B1-Motion>", drag_motion)
Lasi.bind("<ButtonRelease-1>", drop)

Lugoj          = Label(window, text="Lugoj"         , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Lugoj.place(x=1013, y=730)
widget_names[Lugoj] = "Lugoj"
Lugoj.bind("<Button-1>", drag_start)
Lugoj.bind("<B1-Motion>", drag_motion)
Lugoj.bind("<ButtonRelease-1>", drop)

Mehadia        = Label(window, text="Mehadia"       , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Mehadia.place(x=20, y=835)
widget_names[Mehadia] = "Mehadia"
Mehadia.bind("<Button-1>", drag_start)
Mehadia.bind("<B1-Motion>", drag_motion)
Mehadia.bind("<ButtonRelease-1>", drop)

Neamt          = Label(window, text="Neamt"         , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Neamt.place(x=262, y=835)
widget_names[Neamt] = "Neamt"
Neamt.bind("<Button-1>", drag_start)
Neamt.bind("<B1-Motion>", drag_motion)
Neamt.bind("<ButtonRelease-1>", drop)

Oradea         = Label(window, text="Oradea"        , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Oradea.place(x=510, y=835)
widget_names[Oradea] = "Oradea"
Oradea.bind("<Button-1>", drag_start)
Oradea.bind("<B1-Motion>", drag_motion)
Oradea.bind("<ButtonRelease-1>", drop)

Pitesti        = Label(window, text="Pitesti"       , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Pitesti.place(x=769, y=835)
widget_names[Pitesti] = "Pitesti"
Pitesti.bind("<Button-1>", drag_start)
Pitesti.bind("<B1-Motion>", drag_motion)
Pitesti.bind("<ButtonRelease-1>", drop)

Rimnicu_Vilcea = Label(window, text="Rimnicu Vilcea", font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Rimnicu_Vilcea.place(x=943, y=835)
widget_names[Rimnicu_Vilcea] = "Rimnicu Vilcea"
Rimnicu_Vilcea.bind("<Button-1>", drag_start)
Rimnicu_Vilcea.bind("<B1-Motion>", drag_motion)
Rimnicu_Vilcea.bind("<ButtonRelease-1>", drop)

Sibiu          = Label(window, text="Sibiu"         , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Sibiu.place(x=50, y=940)
widget_names[Sibiu] = "Sibiu"
Sibiu.bind("<Button-1>", drag_start)
Sibiu.bind("<B1-Motion>", drag_motion)
Sibiu.bind("<ButtonRelease-1>", drop)

Timisoara      = Label(window, text="Timisoara"     , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Timisoara.place(x=232, y=940)
widget_names[Timisoara] = "Timisoara"
Timisoara.bind("<Button-1>", drag_start)
Timisoara.bind("<B1-Motion>", drag_motion)
Timisoara.bind("<ButtonRelease-1>", drop)

Urziceni       = Label(window, text="Urziceni"      , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Urziceni.place(x=505, y=940)
widget_names[Urziceni] = "Urziceni"
Urziceni.bind("<Button-1>", drag_start)
Urziceni.bind("<B1-Motion>", drag_motion)
Urziceni.bind("<ButtonRelease-1>", drop)

Vaslui         = Label(window, text="Vaslui"        , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Vaslui.place(x=769, y=940)
widget_names[Vaslui] = "Vaslui"
Vaslui.bind("<Button-1>", drag_start)
Vaslui.bind("<B1-Motion>", drag_motion)
Vaslui.bind("<ButtonRelease-1>", drop)

Zerind         = Label(window, text="Zerind"        , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Zerind.place(x=1010, y=940)
widget_names[Zerind] = "Zerind"
Zerind.bind("<Button-1>", drag_start)
Zerind.bind("<B1-Motion>", drag_motion)
Zerind.bind("<ButtonRelease-1>", drop)


# Algorithms to choose from

Label(window, text="Algorithms to choose from:", font=("Arial", 40), relief= RIDGE, bg=HEADER_BG, fg=HEADER_FG).place(x=1250, y=550)

BFS            = Label(window, text="BFS"           , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
BFS.place(x=1270, y=625)
widget_names[BFS] = "BFS"
BFS.bind("<Button-1>", drag_start)
BFS.bind("<B1-Motion>", drag_motion)
BFS.bind("<ButtonRelease-1>", drop)

DFS            = Label(window, text="DFS"           , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
DFS.place(x=1530, y=625)
widget_names[DFS] = "DFS"
DFS.bind("<Button-1>", drag_start)
DFS.bind("<B1-Motion>", drag_motion)
DFS.bind("<ButtonRelease-1>", drop) 

UCS           = Label(window, text="UCS"           , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
UCS.place(x=1780, y=625)
widget_names[UCS] = "UCS"
UCS.bind("<Button-1>", drag_start)
UCS.bind("<B1-Motion>", drag_motion)
UCS.bind("<ButtonRelease-1>", drop)



AStar          = Label(window, text="A*"            , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
AStar.place(x=1287, y=730)
widget_names[AStar] = "A*"
AStar.bind("<Button-1>", drag_start)    
AStar.bind("<B1-Motion>", drag_motion)
AStar.bind("<ButtonRelease-1>", drop)

Beam         = Label(window, text="Beam"            , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Beam.place(x=1520, y=730)
widget_names[Beam] = "Beam"
Beam.bind("<Button-1>", drag_start)
Beam.bind("<B1-Motion>", drag_motion)
Beam.bind("<ButtonRelease-1>", drop)

IDAStar        = Label(window, text="IDA*"          , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
IDAStar.place(x=1780, y=730)
widget_names[IDAStar] = "IDA*"
IDAStar.bind("<Button-1>", drag_start)
IDAStar.bind("<B1-Motion>", drag_motion)
IDAStar.bind("<ButtonRelease-1>", drop)

Greedy        = Label(window, text="Greedy"        , font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Greedy.place(x=1508, y=835)
widget_names[Greedy] = "Greedy"
Greedy.bind("<Button-1>", drag_start)
Greedy.bind("<B1-Motion>", drag_motion)
Greedy.bind("<ButtonRelease-1>", drop)

Hill_Climbing= Label(window, text="Hill Climbing", font=("Arial", 30), relief= RIDGE, bg=PANEL_BG, fg=LABEL_FG)
Hill_Climbing.place(x=1466, y=940)
widget_names[Hill_Climbing] = "Hill Climbing"
Hill_Climbing.bind("<Button-1>", drag_start)
Hill_Climbing.bind("<B1-Motion>", drag_motion)
Hill_Climbing.bind("<ButtonRelease-1>", drop)

# Main part of the code would go here

# --- Embedded execution window + algorithms (so Run opens here directly) ---

# Minimal Romania graph (weights) and approximate coordinates for heuristics
graph: Dict[str, Dict[str, int]] = {
	'Arad': {'Zerind':75,'Sibiu':140,'Timisoara':118},
	'Zerind': {'Arad':75,'Oradea':71},
	'Oradea': {'Zerind':71,'Sibiu':151},
	'Sibiu': {'Arad':140,'Oradea':151,'Fargaras':99,'Rimnicu Vilcea':80},
	'Timisoara': {'Arad':118,'Lugoj':111},
	'Lugoj': {'Timisoara':111,'Mehadia':70},
	'Mehadia': {'Lugoj':70,'Dobreta':75},
	'Dobreta': {'Mehadia':75,'Craiova':120},
	'Craiova': {'Dobreta':120,'Rimnicu Vilcea':146,'Pitesti':138},
	'Rimnicu Vilcea': {'Sibiu':80,'Craiova':146,'Pitesti':97},
	'Fargaras': {'Sibiu':99,'Buchurest':211},
	'Pitesti': {'Rimnicu Vilcea':97,'Craiova':138,'Buchurest':101},
	'Buchurest': {'Fargaras':211,'Pitesti':101,'Giurgiu':90,'Urziceni':85},
	'Giurgiu': {'Buchurest':90},
	'Urziceni': {'Buchurest':85,'Hirsova':98,'Vaslui':142},
	'Hirsova': {'Urziceni':98,'Eforie':86},
	'Eforie': {'Hirsova':86},
	'Vaslui': {'Urziceni':142,'Lasi':92},
	'Lasi': {'Vaslui':92,'Neamt':87},
	'Neamt': {'Lasi':87},
}

# rough coordinates (for heuristic)
coords: Dict[str, Tuple[int,int]] = {
	'Arad': (91,492), 'Zerind': (108,531), 'Oradea': (171,571), 'Sibiu': (207,500),
	'Timisoara': (92,593), 'Lugoj': (130,600), 'Mehadia': (170,640), 'Dobreta': (190,700),
	'Craiova': (300,700), 'Rimnicu Vilcea': (265,560), 'Fargaras': (310,490), 'Pitesti': (350,650),
	'Buchurest': (420,720), 'Giurgiu': (370,700), 'Urziceni': (520,690), 'Hirsova': (560,720),
	'Eforie': (610,710), 'Vaslui': (640,600), 'Lasi': (700,560), 'Neamt': (720,500)
}

def heuristic(a,b):
	if a not in coords or b not in coords:
		return 0
	(x1,y1),(x2,y2) = coords[a], coords[b]
	return math.hypot(x1-x2,y1-y2)

def bfs_search(start, goal):
	q = deque([start])
	visited = set([start])
	parent = {}
	order = [start]
	while q:
		u = q.popleft()
		if u == goal:
			break
		for v in graph.get(u,{}):
			if v not in visited:
				visited.add(v)
				parent[v]=u
				q.append(v)
				order.append(v)
	return order, parent

def dfs_search(start, goal):
	stack=[start]
	visited=set([start])
	parent={}
	order=[start]
	while stack:
		u = stack.pop()
		if u==goal:
			break
		for v in graph.get(u,{}):
			if v not in visited:
				visited.add(v)
				parent[v]=u
				stack.append(v)
				order.append(v)
	return order, parent

def ucs_search(start, goal):
	pq=[(0,start,None)]
	dist={start:0}
	parent={}
	visited=set()
	order=[]
	while pq:
		d,u,p = heapq.heappop(pq)
		if u in visited: continue
		visited.add(u)
		if p: parent[u]=p
		order.append(u)
		if u==goal: break
		for v,w in graph.get(u,{}).items():
			nd = d + w
			if nd < dist.get(v, 1e12):
				dist[v]=nd
				heapq.heappush(pq,(nd,v,u))
	return order, parent

def greedy_search(start, goal):
	pq=[(heuristic(start,goal), start, None)]
	visited=set()
	parent={}
	order=[]
	while pq:
		_,u,p = heapq.heappop(pq)
		if u in visited: continue
		visited.add(u)
		if p: parent[u]=p
		order.append(u)
		if u==goal: break
		for v in graph.get(u,{}):
			if v not in visited:
				heapq.heappush(pq,(heuristic(v,goal),v,u))
	return order, parent

def astar_search(start, goal):
	pq=[(heuristic(start,goal),0,start,None)]
	dist={start:0}
	parent={}
	visited=set()
	order=[]
	while pq:
		f,g,u,p = heapq.heappop(pq)
		if u in visited: continue
		visited.add(u)
		if p: parent[u]=p
		order.append(u)
		if u==goal: break
		for v,w in graph.get(u,{}).items():
			ng = g + w
			if ng < dist.get(v, 1e12):
				dist[v]=ng
				heapq.heappush(pq,(ng+heuristic(v,goal),ng,v,u))
	return order, parent

def beam_search(start, goal, k=2):
	frontier=[start]
	visited=set([start])
	parent={}
	order=[start]
	while frontier:
		candidates=[]
		for u in frontier:
			if u==goal: return order,parent
			for v in graph.get(u,{}):
				if v not in visited:
					visited.add(v)
					parent[v]=u
					candidates.append((heuristic(v,goal),v))
					order.append(v)
		candidates.sort()
		frontier=[v for _,v in candidates[:k]]
	return order,parent

def hill_climb(start, goal):
	current = start
	parent={}
	order=[start]
	visited=set([start])
	while current!=goal:
		neigh = [(heuristic(n,goal),n) for n in graph.get(current,{}) if n not in visited]
		if not neigh: break
		neigh.sort()
		nxt = neigh[0][1]
		parent[nxt]=current
		visited.add(nxt)
		order.append(nxt)
		current = nxt
	return order,parent

def ida_search(start, goal):
	# Iterative Deepening A* (IDA*)
	# Returns (order, parent)
	def dfs(path, g, bound, parent, order, visited):
		node = path[-1]
		f = g + heuristic(node, goal)
		if f > bound:
			return f, False
		if node == goal:
			return f, True
		min_threshold = float('inf')
		# expand neighbors in heuristic order
		neighbors = list(graph.get(node, {}).items())
		neighbors.sort(key=lambda vw: heuristic(vw[0], goal) + g + vw[1])
		for v, w in neighbors:
			if v in path:
				continue
			parent[v] = node
			order.append(v)
			path.append(v)
			t, found = dfs(path, g + w, bound, parent, order, visited)
			path.pop()
			if found:
				return t, True
			if t < min_threshold:
				min_threshold = t
		# if none found
		return min_threshold, False

	# main IDA* loop
	parent = {}
	order = [start]
	bound = heuristic(start, goal)
	visited = set()
	if start == goal:
		return [start], {}
	while True:
		path = [start]
		t, found = dfs(path, 0, bound, parent, order, visited)
		if found:
			# ensure parent mapping leads to correct path
			return order, parent
		if t == float('inf'):
			# no solution
			return order, parent
		bound = t

ALG_MAP = {
	'BFS': bfs_search,
	'DFS': dfs_search,
	'UCS': ucs_search,
	'Greedy': greedy_search,
	'A*': astar_search,
	'Beam': lambda s,g: beam_search(s,g, k=3),
	'Hill Climbing': hill_climb,
	'IDA*': ida_search,
}

# Attempt to load algorithm implementations from parent Graph/ directory
import ast

def _load_funcs_from_file(path, want_funcs=('graph','coords')):
	"""Parse the file at `path` and exec only Assign nodes for 'graph'/'coords' and
	any FunctionDef nodes. Returns namespace dict with extracted symbols."""
	try:
		src = open(path, 'r', encoding='utf-8').read()
	except Exception:
		return {}
	try:
		tree = ast.parse(src, filename=path)
	except Exception:
		return {}
	nodes = []
	for node in tree.body:
		if isinstance(node, ast.Assign):
			for target in node.targets:
				if isinstance(target, ast.Name) and target.id in want_funcs:
					nodes.append(node)
		elif isinstance(node, ast.FunctionDef):
			nodes.append(node)
	if not nodes:
		return {}
	mod = ast.Module(body=nodes, type_ignores=[])
	ns = {}
	try:
		code = compile(mod, path, 'exec')
		exec(code, ns)
	except Exception:
		return {}
	return ns

def _wrap_external_function(ns, func_candidates):
	"""Return a callable wrapper that calls the first matching function name in ns.
	The wrapper converts common return formats into (order, parent) expected by GUI.
	"""
	fn = None
	for name in func_candidates:
		if name in ns and callable(ns[name]):
			fn = ns[name]
			break
	if fn is None:
		return None

	def wrapper(start, goal):
		try:
			res = fn(start, goal)
		except Exception:
			# if external fails, let caller fallback
			raise
		# common patterns: (path, nodes_expanded, cost) OR (order, parent)
		if isinstance(res, tuple) and len(res) >= 1:
			first = res[0]
			# If first element looks like a path (list of nodes), derive parent/order from it
			if isinstance(first, list):
				path = first
				order = path[:]  # best-effort: show path nodes as visited sequence
				parent = {}
				for i in range(1, len(path)):
					parent[path[i]] = path[i-1]
				return order, parent
			# If returns (order, parent) already
			if len(res) >= 2 and isinstance(res[0], list) and isinstance(res[1], dict):
				return res[0], res[1]
		# unknown format: return empty
		return [start], {}

	return wrapper

# Directory of this file -> parent Graph directory
_this_dir = os.path.dirname(__file__)
_parent_graph = os.path.abspath(os.path.join(_this_dir, '..'))

# mapping: GUI name -> (filename, possible function names in that file)
_external_map = {
	'BFS': ('BFS.py', ['BFS', 'bfs', 'bfs_search']),
	'DFS': ('DFS.py', ['DFS', 'dfs', 'dfs_search']),
	'UCS': ('UCS.py', ['UCS', 'ucs', 'ucs_search']),
	'Greedy': ('Greedy.py', ['Greedy', 'greedy_search', 'greedy']),
	'A*': ('Astar.py', ['A_star', 'Astar', 'astar', 'astar_search', 'astart_search']),
	'Beam': ('Beem.py', ['beam_search', 'Beem', 'beam']),
	'Hill Climbing': ('Hillclimping.py', ['hill_climb', 'HillClimb', 'hill_climbing']),
	'IDA*': ('IDAstar.py', ['IDA_star', 'IDAstar', 'ida_search', 'IDAsearch']),
}

_orig_alg_map = dict(ALG_MAP)
for key, (fname, candidates) in list(_external_map.items()):
	fpath = os.path.join(_parent_graph, fname)
	ns = _load_funcs_from_file(fpath, want_funcs=('graph','coords'))
	if ns:
		wrapped = _wrap_external_function(ns, candidates)
		if wrapped:
			# create a safe wrapper that falls back to the original implementation
			orig_fn = _orig_alg_map.get(key)
			def _safe_wrapper(start, goal, _w=wrapped, _orig=orig_fn, _k=key):
				try:
					return _w(start, goal)
				except Exception as e:
					# log the external error and fallback
					try:
						with open(LOG_PATH, 'a') as _f:
							_f.write(f"External algorithm {_k} failed: {e}\n")
					except Exception:
						pass
					if _orig:
						try:
							return _orig(start, goal)
						except Exception:
							pass
					return [start], {}
			ALG_MAP[key] = _safe_wrapper

class ExecutionWindow:
	def __init__(self, parent, start, goal, algorithm_name):
		# create a full-screen execution window and split canvas + analysis pane
		self.window = Toplevel(parent)
		self.window.title(f"Execution: {algorithm_name} {start} -> {goal}")
		# maximize / fullscreen
		try:
			self.window.state('zoomed')  # Set window to zoomed state
		except Exception:
			try:
				self.window.attributes('-zoomed', True)
			except Exception:
				self.window.attributes('-fullscreen', True)

		screen_w = self.window.winfo_screenwidth()
		screen_h = self.window.winfo_screenheight()
		# store screen width for later layout/scaling decisions
		self.screen_w = screen_w
		# reserve a larger minimum width for the analysis/control panel so it is always readable
		min_ctrl_w = 420
		# prefer ~28% for controls but never below min_ctrl_w
		ctrl_w = max(min_ctrl_w, int(screen_w * 0.28))
		# Force the canvas to occupy the left half of the screen (but keep a minimum)
		# This ensures the graph is constrained to the left half for consistent analysis pane layout
		self.canvas_w = max(300, screen_w // 2)
		# Set canvas height to nearly full screen height (leave small margin for OS bars)
		# Using `screen_h - 40` gives more predictable lower space than a percentage
		self.canvas_h = max(300, screen_h - 40)
		self.canvas = Canvas(self.window, width=self.canvas_w, height=self.canvas_h, bg='white')
		# allow the canvas to expand (especially vertically) so it uses available lower space
		self.canvas.pack(side='left', fill='both', expand=True)
		# ensure drawing is limited to this canvas area and enable scrolling region if needed
		self.canvas.config(scrollregion=(0, 0, self.canvas_w, self.canvas_h))

		# early placeholders so background threads can log before the results box is created
		self.results = {}
		def _noop_append(s):
			return None
		self._append_res = _noop_append

		# right analysis / controls panel
		ctrl = Frame(self.window, width=screen_w - self.canvas_w, bg='#f0f4f8')
		ctrl.pack(side='right', fill='both', expand=True)

		# Controls: Play / Pause / Step + speed
		Button(ctrl, text='Play', command=self.play, width=18).pack(pady=6)
		Button(ctrl, text='Pause', command=self.pause, width=18).pack(pady=2)
		Button(ctrl, text='Step', command=self.step, width=18).pack(pady=2)
		Label(ctrl, text='Speed (ms)', bg=ctrl['bg']).pack(pady=6)
		self.speed = Scale(ctrl, from_=50, to=1000, orient=HORIZONTAL)
		self.speed.set(300)
		self.speed.pack(pady=6)
		# restart running comparisons when user changes animation speed
		try:
			self.speed.bind("<ButtonRelease-1>", lambda e: self.on_speed_change())
		except Exception:
			pass
		# Removed: Show Final Path button (merged into Results display)

		# Stop / Continue for the animation and algorithm runs
		self.stop_event = threading.Event()
		tk_btn_frame = Frame(ctrl, bg=ctrl['bg'])
		tk_btn_frame.pack(pady=6)
		Button(tk_btn_frame, text='Stop', command=self.request_stop, width=10, bg='#FF5555').pack(side='left', padx=4)
		Button(tk_btn_frame, text='Continue', command=self.clear_stop, width=10, bg='#55AA55').pack(side='left', padx=4)
		# Options
		# optionally import tkinter module namespace for widgets
		_tk = None
		try:
			import tkinter as _tk
		except Exception:
			_tk = None
		# Algorithm selection and run controls (adapted from Maze GUI)
		# Algorithm checkboxes
		self.avars = {}
		algos = list(ALG_MAP.keys())
		Label(ctrl, text='Select Algorithms for Compare:', bg=ctrl['bg'], font=('Arial',11,'bold')).pack(anchor='w', padx=6, pady=(6,2))
		cb_frame = Frame(ctrl, bg=ctrl['bg'])
		cb_frame.pack(anchor='w', padx=6)
		for a in algos:
			v = _tk.BooleanVar(value=True) if _tk is not None else BooleanVar(value=True)
			self.avars[a] = v
			try:
				chk = Checkbutton(cb_frame, text=a, variable=v, bg=ctrl['bg'])
				chk.pack(anchor='w')
			except Exception:
				pass

		# Individual algorithm buttons
		Label(ctrl, text='Run Individual Algorithm:', bg=ctrl['bg'], font=('Arial',11,'bold')).pack(anchor='w', padx=6, pady=(8,2))
		algo_btn_frame = Frame(ctrl, bg=ctrl['bg'])
		algo_btn_frame.pack(fill='x', padx=6)
		for a in algos:
			btn = Button(algo_btn_frame, text=a, command=(lambda name=a: threading.Thread(target=self.run_algo_ui, args=(name,), daemon=True).start()), bg='#048989', fg='white')
			btn.pack(side='left', padx=2, pady=2, expand=True, fill='x')

		# Action buttons
		action_frame = Frame(ctrl, bg=ctrl['bg'])
		action_frame.pack(fill='x', padx=6, pady=8)
		Button(action_frame, text='Solve & Run Selected', command=self.run_selected_ui, bg='#2b6cb0', fg='white').pack(side='left', expand=True, fill='x', padx=(0,5))
		Button(action_frame, text='Run All', command=self.run_all_ui, bg='#2b6cb0', fg='white').pack(side='left', expand=True, fill='x')

		# Extra analysis action buttons (Performance / Recommend / Best)
		perf_frame = Frame(ctrl, bg=ctrl['bg'])
		perf_frame.pack(fill='x', padx=6, pady=(6,2))
		Button(perf_frame, text='Performance Comparison', command=self.show_graph, bg='#666', fg='white').pack(side='left', expand=True, fill='x', padx=(0,4))
		Button(perf_frame, text='Show Best', command=self.show_best, bg='#666', fg='white').pack(side='left', expand=True, fill='x', padx=4)
		Button(perf_frame, text='Recommend', command=self.recommend, bg='#666', fg='white').pack(side='left', expand=True, fill='x', padx=(4,0))

		# Fast animation option state is kept for compatibility, but
		# the checkbox widget has been removed from the UI per request.
		self.fast_search_var = _tk.BooleanVar(value=False) if _tk is not None else BooleanVar(value=False)
		# Animate final path option
		self.animate_path_var = _tk.BooleanVar(value=True) if _tk is not None else BooleanVar(value=True)
		try:
			_chk_a = Checkbutton(ctrl, text='Animate Final Path', variable=self.animate_path_var, bg=ctrl['bg'])
			_chk_a.pack(pady=2, padx=6, anchor='w')
		except Exception:
			pass



		func = ALG_MAP.get(algorithm_name)
		if func is None:
			self.order, self.parent = [start], {}
		else:
			# measure memory before
			try:
				self.start_mem = psutil.Process().memory_info().rss / 1024.0 if psutil else 0.0
			except Exception:
				self.start_mem = 0.0
			import time as _t
			t0 = _t.time()
			self.order, self.parent = func(start, goal)

			t1 = _t.time()
			self.elapsed_ms = int((t1 - t0) * 1000)
			# sample memory after
			try:
				self.end_mem = psutil.Process().memory_info().rss / 1024.0 if psutil else 0.0
			except Exception:
				self.end_mem = 0.0

		self.start = start
		self.goal = goal
		self.algorithm_name = algorithm_name

		# Draw all cities so the map always shows every node
		self.nodes = list(graph.keys())
		# scale node font & radii based on canvas width for responsive layout
		scale_factor = max(0.5, min(2.0, float(self.canvas_w) / 1200.0))
		font_size = max(8, min(20, int(12 * scale_factor)))
		self.node_font = tkfont.Font(family='Arial', size=font_size, weight='bold')
		self.node_radius = {}
		min_rad = max(12, int(26 * scale_factor))
		pad = max(6, int(14 * scale_factor))
		for node in self.nodes:
			w = self.node_font.measure(node)
			self.node_radius[node] = max(min_rad, int(w/2) + pad)
		# compute layers based on parent pointers (distance from start)
		self.layers = self.build_layers()
		# Special-case layout requested: if start Arad and goal Buchurest, force specific layers
		if self.start == 'Arad' and self.goal == 'Buchurest':
			# only include nodes that exist in our node set
			spec = {
				0: ['Arad'],
				1: [n for n in ['Sibiu','Timisoara','Zerind'] if n in self.nodes],
				2: [n for n in ['Fargaras','Rimnicu Vilcea'] if n in self.nodes],
				3: [n for n in ['Pitesti','Craiova'] if n in self.nodes],
				4: [n for n in ['Buchurest'] if n in self.nodes],
			}
			# remove empty layers and set
			self.layers = {d:lst for d,lst in spec.items() if lst}
		self.positions = self.compute_positions()

		self.node_items = {}
		self.edge_items = {}

		self.step_index = 0
		self.running = False
		# runtime flags for restart-on-speed-change and single-run reporting
		self._is_running = False
		self._current_algos = None
		self._restart_requested = False
		self._single_running = False
		self._visited_seq = []
		self._step_logs = []

		# draw the static graph now and create the results text box
		try:
			self.draw_static()
		except Exception:
			pass
		# Results / log box (label + Text) - put analysis inside the results text box
		Label(ctrl, text='Results', font=('Arial',12,'bold'), bg=ctrl['bg']).pack(anchor='w', padx=6, pady=(8,2))
		# Use a larger Text box to contain both analysis and tabular results
		self.res_box = DummyText()
		try:
			if _tk is not None and hasattr(_tk, 'Text'):
				self.res_box = _tk.Text(ctrl, height=18)
			else:
				from tkinter import Text as _TkText
				self.res_box = _TkText(ctrl, height=18)
			self.res_box.pack(fill='both', expand=True, padx=6, pady=6)
			self.results = {}
			def _append_res(s):
				try:
					# ensure the text widget is writable (it may be disabled by upd_res)
					was_disabled = False
					try:
						if str(self.res_box.cget('state')) == 'disabled':
							was_disabled = True
					except Exception:
						was_disabled = False
					try:
						self.res_box.config(state='normal')
					except Exception:
						pass
					try:
						self.res_box.insert('end', s + '\n')
						self.res_box.see('end')
					except Exception:
						pass
					# restore disabled state if needed
					try:
						if was_disabled:
							self.res_box.config(state='disabled')
					except Exception:
						pass
				except Exception:
					pass
			self._append_res = _append_res
			# initial summary lines (analysis) go inside the results box
			self._append_res(f"Algorithm: {self.algorithm_name or '(none)'}")
			self._append_res(f"Start: {self.start or '(none)'} | Goal: {self.goal or '(none)'}")
			self._append_res(f"Elapsed (ms): {getattr(self,'elapsed_ms',0)} | Mem delta KB: {int(getattr(self,'end_mem',0)-getattr(self,'start_mem',0))}")
			self._append_res('')
		except Exception:
			self.res_box = DummyText()

	def _report_step(self, node):
		# record and display a concise per-step report for individual runs
		try:
			if node not in self._visited_seq:
				self._visited_seq.append(node)
				# keep a short textual log of steps (last 200)
				# Do NOT include actual node names in the results per user request;
				# only record counts to avoid leaking node identifiers into the results box.
				s = f"Visited count: {len(self._visited_seq)}"
				self._step_logs.append(s)
				if len(self._step_logs) > 500:
					self._step_logs.pop(0)
				# append to results box without clobbering header/table (upd_res will re-render)
				try:
					if hasattr(self, '_append_res'):
						# append only the count (no node names)
						self._append_res(s)
				except Exception:
					pass
		except Exception:
			pass

	def on_speed_change(self, *args):
		# Called when the speed Scale is changed (on release). If a run is in progress,
		# request a restart so comparisons are fair at the new speed.
		try:
			if not (self._is_running or self._single_running):
				return
			self._append_res('Speed changed — restarting current run to apply new speed')
			# request stop of running worker
			self._restart_requested = True
			self.stop_event.set()
			# spawn watcher to restart after current worker stops
			def _watcher():
				# wait until running flag cleared
				while True:
					if not (getattr(self, '_is_running', False) or getattr(self, '_single_running', False)):
						break
					time.sleep(0.05)
				# clear stop flag and restart appropriate run
				try:
					self.stop_event.clear()
				except Exception:
					pass
				# restart the same set of algorithms or single algorithm
				if getattr(self, '_current_algos', None):
					threading.Thread(target=lambda: self.run_all_visual(self._current_algos), daemon=True).start()
				elif getattr(self, '_last_single_name', None):
					# restart individual algorithm run
					threading.Thread(target=lambda: self.run_algo_ui(self._last_single_name), daemon=True).start()
				self._restart_requested = False
			threading.Thread(target=_watcher, daemon=True).start()
		except Exception:
			pass




	def build_layers(self):
		layers = {}
		for n in self.nodes:
			depth = 0
			cur = n
			while cur in self.parent:
				depth += 1
				cur = self.parent[cur]
				if cur==self.start:
					break
			layers.setdefault(depth, []).append(n)
		return layers

	def compute_positions(self):
		positions = {}
		# refresh canvas dimensions from the actual widget size so layout uses current available area
		try:
			cw = int(self.canvas.winfo_width())
			ch = int(self.canvas.winfo_height())
			# only update if widget reports a reasonable size
			if cw > 50 and ch > 50:
				self.canvas_w = cw
				self.canvas_h = ch
		except Exception:
			pass
		# Prefer to use map coordinates if available (scale to canvas). Fallback to layered layout.
		coords_nodes = [n for n in self.nodes if n in coords]
		if coords_nodes:
			# compute bounding box of provided coords
			xs = [coords[n][0] for n in coords_nodes]
			ys = [coords[n][1] for n in coords_nodes]
			min_x, max_x = min(xs), max(xs)
			min_y, max_y = min(ys), max(ys)
			# reduce margin proportional to canvas size so layout can shrink more on narrow views
			scale_factor = max(0.4, min(1.2, float(self.canvas_w) / 1600.0))
			margin = max(20, int(60 * scale_factor))
			width_avail = max(100, self.canvas_w - 2 * margin)
			height_avail = max(100, self.canvas_h - 2 * margin)
			range_x = max(1, max_x - min_x)
			range_y = max(1, max_y - min_y)
			scale_x = width_avail / range_x
			scale_y = height_avail / range_y
			for n in self.nodes:
				if n in coords:
					x0,y0 = coords[n]
					x = int((x0 - min_x) * scale_x) + margin
					y = int((y0 - min_y) * scale_y) + margin
					# clamp
					rad = self.node_radius.get(n, 26)
					x = min(self.canvas_w - rad - 8, max(rad + 8, x))
					y = min(self.canvas_h - rad - 8, max(rad + 8, y))
					positions[n] = (x,y)
				else:
					# will place remaining nodes using layered layout later
					positions[n] = None
		# For any nodes without coords, compute layered positions
		# Tree layout: organize by depth (Y), spread horizontally (X)
		for depth, nodes in self.layers.items():
			n = len(nodes)
			# Increase vertical spacing slightly for DFS to emphasize depth
			vert_space = 140 if self.algorithm_name == 'DFS' else 120
			y = 80 + depth * vert_space
			# Horizontal spacing: spread nodes across canvas width
			if n == 1:
				x_positions = [self.canvas_w // 2]
			else:
				spacing = min(200, (self.canvas_w - 100) // max(1, n - 1))
				start_x = self.canvas_w // 2 - (spacing * (n - 1)) // 2
				x_positions = [start_x + i * spacing for i in range(n)]
			for i, node in enumerate(nodes):
				# if already placed via coords, skip
				if positions.get(node):
					continue
				x = x_positions[i]
				# clamp positions so node circle stays inside the canvas
				rad = self.node_radius.get(node, 26)
				min_x = rad + 8
				max_x = self.canvas_w - rad - 8
				min_y = rad + 8
				max_y = self.canvas_h - rad - 8
				x = min(max_x, max(min_x, x))
				y = min(max_y, max(min_y, y))
				positions[node] = (x, y)
		# Resolve overlaps (simple nudge) so closely placed cities (e.g., Lugoj/Timisoara)
		# don't draw on top of each other. Do a few relaxation passes.
		all_nodes = list(self.nodes)
		for _pass in range(8):
			moved = False
			for i in range(len(all_nodes)):
				a = all_nodes[i]
				xa, ya = positions.get(a, (0,0))
				ra = self.node_radius.get(a, 26)
				for j in range(i+1, len(all_nodes)):
					b = all_nodes[j]
					xb, yb = positions.get(b, (0,0))
					rb = self.node_radius.get(b, 26)
					dx = xa - xb
					dy = ya - yb
					d = math.hypot(dx, dy)
					min_sep = (ra + rb) * 1.1
					if d > 0 and d < min_sep:
						over = (min_sep - d) / 2.0
						nx = dx / d
						ny = dy / d
						xa += nx * over
						ya += ny * over
						xb -= nx * over
						yb -= ny * over
						# clamp
						xa = min(self.canvas_w - ra - 8, max(ra + 8, xa))
						ya = min(self.canvas_h - ra - 8, max(ra + 8, ya))
						xb = min(self.canvas_w - rb - 8, max(rb + 8, xb))
						yb = min(self.canvas_h - rb - 8, max(rb + 8, yb))
						positions[a] = (int(xa), int(ya))
						positions[b] = (int(xb), int(yb))
						moved = True
			if not moved:
				break
		# After computing positions, scale the entire layout so it fits within
		# the left half of the screen (so analysis panel remains visible).
		try:
			# choose a margin based on screen size
			margin = max(12, int(self.screen_w * 0.02))
			xs = [positions[n][0] for n in positions]
			ys = [positions[n][1] for n in positions]
			min_x, max_x = min(xs), max(xs)
			min_y, max_y = min(ys), max(ys)
			range_x = max(1, max_x - min_x)
			range_y = max(1, max_y - min_y)
			# desired available area: left half of the SCREEN (not canvas), with margin
			screen_half = max(100, (self.screen_w // 2))
			desired_w = max(100, screen_half - 2 * margin)
			desired_h = max(100, self.canvas_h - 2 * margin)
			scale2 = min(desired_w / range_x, desired_h / range_y, 1.0)
			if scale2 < 1.0:
				for n in list(positions.keys()):
					x, y = positions[n]
					# map into left half of screen (starting at margin)
					nx = int(margin + (x - min_x) * scale2)
					ny = int(margin + (y - min_y) * scale2)
					positions[n] = (nx, ny)
				# shrink node radii and font size accordingly
				try:
					old_size = int(self.node_font.cget('size'))
					new_size = max(6, int(old_size * scale2))
					self.node_font.configure(size=new_size)
				except Exception:
					pass
				for n in list(self.node_radius.keys()):
					self.node_radius[n] = max(6, int(self.node_radius[n] * scale2))
		except Exception:
			# if anything goes wrong with scaling, just return computed positions
			pass

		# Targeted clamp: ensure specific problematic nodes are inside the canvas
		# without changing other nodes' relative positions.
		try:
			forced_nodes = ['Buchurest', 'Giurgiu', 'Hirsova']
			pad = max(12, int(self.canvas_w * 0.02))
			for n in forced_nodes:
				if n in positions and positions[n] is not None:
					x, y = positions[n]
					# clamp to visible area
					x = min(self.canvas_w - pad, max(pad, x))
					y = min(self.canvas_h - pad, max(pad, y))
					positions[n] = (int(x), int(y))
		except Exception:
			pass

			# Final safety: if any positions still fall outside the canvas (due to
			# rounding, margins, or unexpected sizes), translate all positions
			# together so they fit inside the visible canvas area. This preserves
			# relative layout while ensuring nothing is drawn off-screen.
			try:
				margin = max(12, int(self.canvas_w * 0.02))
				xs = [positions[n][0] for n in positions]
				ys = [positions[n][1] for n in positions]
				min_x, max_x = min(xs), max(xs)
				min_y, max_y = min(ys), max(ys)
				# compute horizontal shift
				dx = 0
				if min_x < margin:
					dx = margin - min_x
				elif max_x > (self.canvas_w - margin):
					dx = (self.canvas_w - margin) - max_x
				# compute vertical shift
				dy = 0
				if min_y < margin:
					dy = margin - min_y
				elif max_y > (self.canvas_h - margin):
					dy = (self.canvas_h - margin) - max_y
				if dx != 0 or dy != 0:
					for n in list(positions.keys()):
						x,y = positions[n]
						positions[n] = (int(x + dx), int(y + dy))
			except Exception:
				pass

		# Fallback: ensure no position remains None (place any missing nodes evenly)
		try:
			missing = [n for n, p in positions.items() if p is None]
			if missing:
				count = len(missing)
				y = self.canvas_h // 2
				spacing = max(40, (self.canvas_w - 40) // max(1, count))
				start_x = 20
				for i, n in enumerate(missing):
					positions[n] = (start_x + i * spacing, y)
		except Exception:
			pass

		return positions


	def draw_static(self):
		try:
			# draw faint background edges for whole graph first
			seen = set()
			for u, nbrs in graph.items():
				for v in nbrs:
					if (v,u) in seen or (u,v) in seen:
						continue
					x1,y1 = self.positions.get(u,(0,0))
					x2,y2 = self.positions.get(v,(0,0))
					self.canvas.create_line(x1,y1,x2,y2, fill=EDGE_BG, width=1)
					seen.add((u,v))
			# draw parent links (on top)
			for child, parent in self.parent.items():
				x1,y1 = self.positions.get(parent,(0,0))
				x2,y2 = self.positions.get(child,(0,0))
				line = self.canvas.create_line(x1,y1,x2,y2, fill='#999', width=2)
				self.edge_items[(parent,child)] = line
			# draw nodes
			# prepare font for labels and compute size-based radius
			for node,(x,y) in self.positions.items():
				try:
					text_width = self.node_font.measure(node)
					# radius comes from precomputed values (responsive)
					r = self.node_radius.get(node, 26)
					oval = self.canvas.create_oval(x-r,y-r,x+r,y+r, fill=NODE_BG, outline='#2b6cb0', width=2)
					text = self.canvas.create_text(x,y, text=node, fill='#063a6f', font=self.node_font)
					self.node_items[node] = (oval,text)
				except Exception:
					# skip nodes that cannot be drawn and continue
					continue
			# track current highlighted node
			self.current_node = None

			# compute final path (if available) and update analysis
			self.path = self.compute_path()
			self.path_cost = self.compute_path_cost(self.path)
			self.update_info()

			# ensure the canvas scrollregion covers all drawn items so nothing is clipped
			try:
				bbox = self.canvas.bbox("all")
				if bbox:
					# provide extra padding, larger on the vertical axis to avoid bottom clipping
					pad_x = max(24, int(self.canvas_w * 0.03))
					pad_y = max(64, int(self.canvas_h * 0.08))
					self.canvas.config(scrollregion=(bbox[0]-pad_x, bbox[1]-pad_y, bbox[2]+pad_x, bbox[3]+pad_y))
			except Exception:
				pass
		except Exception:
			# log unexpected drawing errors for diagnosis
			try:
				with open(LOG_PATH, 'a') as _f:
					traceback.print_exc(file=_f)
			except Exception:
				pass

	def highlight_node(self, node):
		items = self.node_items.get(node)
		if not items: return
		# restore previous current node to visited color
		if getattr(self, 'current_node', None):
			prev = self.current_node
			if prev in self.node_items:
				p_oval, p_text = self.node_items[prev]
				self.canvas.itemconfig(p_oval, fill=VISITED_COLOR)
				self.canvas.itemconfig(p_text, fill=LABEL_FG)
		# set new current
		oval, text = items
		self.canvas.itemconfig(oval, fill=CURRENT_COLOR)
		self.canvas.itemconfig(text, fill='white')
		self.current_node = node

	def play(self):
		if not self.running:
			self.running = True
			self._run()

	def pause(self):
		self.running = False

	def step(self):
		if self.step_index < len(self.order):
			node = self.order[self.step_index]
			self.highlight_node(node)
			self.step_index += 1
			# if we've finished iterating, auto-display final path
			if self.step_index >= len(self.order):
				self.running = False
				self.path = self.compute_path()
				self.show_path()
				self.update_info()

	def _run(self):
		if not self.running: return
		if self.step_index < len(self.order):
			node = self.order[self.step_index]
			self.highlight_node(node)
			self.step_index += 1
			delay = int(self.speed.get())
			self.window.after(delay, self._run)
		else:
			self.running = False
			# reached end of traversal; automatically highlight final path
			self.path = self.compute_path()
			self.show_path()
			self.update_info()

	def compute_path(self):
		# trace back from goal using parent pointers
		path = []
		cur = self.goal
		if cur == self.start:
			return [self.start]
		while True:
			path.append(cur)
			if cur not in self.parent:
				# no parent known; path incomplete
				return []
			cur = self.parent[cur]
			if cur == self.start:
				path.append(self.start)
				break
		path.reverse()
		return path

	def compute_path_cost(self, path):
		if not path or len(path) < 2:
			return 0
		cost = 0
		for a,b in zip(path, path[1:]):
			cost += graph.get(a,{}).get(b, graph.get(b,{}).get(a, 0))
		return cost

	def show_path(self):
		if not getattr(self, 'path', None):
			return
		# highlight nodes and edges along path
		for i,node in enumerate(self.path):
			items = self.node_items.get(node)
			if not items: continue
			oval, text = items
			self.canvas.itemconfig(oval, fill=PATH_COLOR)
			self.canvas.itemconfig(text, fill='white')
			if i < len(self.path)-1:
				a = node
				b = self.path[i+1]
				edge = self.edge_items.get((a,b)) or self.edge_items.get((b,a))
				if edge:
					self.canvas.itemconfig(edge, fill=PATH_COLOR, width=3)

	def update_info(self):
		# Update analysis fields inside the results text box
		try:
			path_len = len(self.path)-1 if getattr(self,'path',None) else 0
			path_cost = getattr(self,'path_cost',0)
			elapsed = getattr(self,'elapsed_ms',0)
			mem_delta = int(getattr(self,'end_mem',0) - getattr(self,'start_mem',0))
			# rebuild the results text box so analysis appears at top
			if hasattr(self, 'res_box') and hasattr(self.res_box, 'config') and hasattr(self.res_box, 'delete') and hasattr(self.res_box, 'insert'):
				try:
					self.res_box.config(state='normal')
				except Exception:
					pass
				# clear then write analysis header; leave table generation to upd_res
				try:
					self.res_box.delete('1.0', 'end')
					self.res_box.insert('end', f"Algorithm: {self.algorithm_name or '(none)'}\n")
					self.res_box.insert('end', f"Start: {self.start or '(none)'} | Goal: {self.goal or '(none)'}\n")
					self.res_box.insert('end', f"Elapsed (ms): {elapsed} | Mem delta KB: {mem_delta}\n")
					self.res_box.insert('end', f"Nodes Expanded: {len(self.order)} | Path Length: {path_len} | Path Cost: {path_cost}\n\n")
				except Exception:
					pass
				# now append the tabular results
				self.upd_res()
		except Exception:
			pass

	def _should_animate(self):
		"""Return True when visualization/animation should be performed.
		Safely handles missing or non-standard variable types for backward compatibility.
		"""
		v = getattr(self, 'fast_search_var', None)
		try:
			if v is None:
				# no fast-search control present — default to animate
				return True
			# if it's a tkinter BooleanVar or similar, animate when fast_search_var is False
			if hasattr(v, 'get'):
				return not bool(v.get())
			# if it's a plain bool, animate when False
			return not bool(v)
		except Exception:
			return True


	# --- UI-run helpers (adapted from MazeGUI) ---
	def run_algo_ui(self, name):
		# Run a single algorithm in this execution window (thread-safe entry)
		if not self.start or not self.goal:
			messagebox.showwarning("Warning", "Set Start and Goal")
			return
		self._append_res(f"Running {name}...")
		# If a multi-algo comparison is running, request it stop and wait
		try:
			if getattr(self, '_is_running', False):
				self._append_res('Stopping current comparison to run single algorithm')
				self.stop_event.set()
				# wait for the comparison worker to clear its running flag
				while getattr(self, '_is_running', False):
					time.sleep(0.05)
				try:
					self.stop_event.clear()
				except Exception:
					pass
		except Exception:
			pass
		# clear stop and run
		self.stop_event.clear()
		# mark single-run state for reporting/restart
		self._last_single_name = name
		self._single_running = True
		self._visited_seq = []
		self._step_logs = []
		def _run():
			try:
				# reset visual state before running single algorithm
				try:
					for node, items in list(self.node_items.items()):
						oval, text = items
						self.canvas.itemconfig(oval, fill=NODE_BG)
						self.canvas.itemconfig(text, fill=LABEL_FG)
					for e in list(self.edge_items.values()):
						self.canvas.itemconfig(e, fill=EDGE_BG, width=2)
					self.current_node = None
				except Exception:
					pass
				func = ALG_MAP.get(name)
				if func is None:
					self._append_res(f"No implementation for {name}")
					return
				t0 = time.time()
				order, parent = func(self.start, self.goal)
				t1 = time.time()
				elapsed = t1 - t0
				# sample memory if psutil available
				mem_delta = 0.0
				try:
					if psutil:
						mem_delta = psutil.Process().memory_info().rss / 1024.0
				except Exception:
					mem_delta = 0.0
				# record results (include animation/drawing delay if we will animate)
				nodes = len(order) if order else 0
				success = (self.goal in order) or (self.start == self.goal)
				# estimate draw time based on current speed setting (ms)
				try:
					delay_ms = max(10, int(self.speed.get()))
				except Exception:
					delay_ms = 300
				# if we're animating, add schedule window time (last after uses len(order)*delay + 50ms)
				if self._should_animate():
					draw_time = (len(order or []) * delay_ms + 50) / 1000.0
				else:
					# fast mode or unavailable: small UI update time
					draw_time = 0.05
				combined_time = elapsed + draw_time
				self.results[name] = {"time": combined_time, "memory": mem_delta, "nodes": nodes, "path_length": (len(self.compute_path()) if hasattr(self,'parent') else 0), "success": success}
				# also update elapsed_ms used by the info header
				self.elapsed_ms = int(combined_time * 1000)
				# update window state on main thread (show time including draw delay)
				self.window.after(0, lambda: self._append_res(f"{name}: time={combined_time:.3f}s nodes={nodes} success={success}"))
				# set order/parent for visualization
				self.order = order
				self.parent = parent
				# compute final path now that parent pointers are in place
				try:
					self.path = self.compute_path()
					self.path_cost = self.compute_path_cost(self.path)
				except Exception:
					self.path = []
					self.path_cost = 0
				# update stored path length in results without exposing node names
				try:
					pl = (len(self.path)-1) if getattr(self, 'path', None) else 0
					if name in self.results:
						self.results[name]['path_length'] = pl
				except Exception:
					pass
				# self.elapsed_ms was set above (includes draw time)
				# animate or immediately show
				if self._should_animate():
					delay = max(10, int(self.speed.get()))
					# perform synchronous animation for individual run so each visited node is shown
					for i, node in enumerate(self.order or []):
						if self.stop_event.is_set():
							break
						try:
							self.highlight_node(node)
							self._report_step(node)
						except Exception:
							pass
						# force UI refresh and wait according to speed
						try:
							self.window.update()
						except Exception:
							pass
						time.sleep(delay / 1000.0)
					# after traversal, show path and update results/UI
					try:
						# compute and display final path (do not print node list)
						self.path = self.compute_path()
						self.path_cost = self.compute_path_cost(self.path)
						self.show_path()
						self.update_info()
						self.upd_res()
						self._append_res(f"{name} finished. Path length: {len(self.path)-1 if self.path else 0} | Cost: {self.path_cost}")
					except Exception:
						pass
						pass
					# clear single-run flag
					self._single_running = False
				else:
					# fast: don't animate nodes, just compute path and show
					# mark all visited nodes visually so the user can see both visited set and final path
					try:
						for node in (order or []):
							items = self.node_items.get(node)
							if not items:
								continue
							oval, text = items
							self.canvas.itemconfig(oval, fill=VISITED_COLOR)
							self.canvas.itemconfig(text, fill=LABEL_FG)
					except Exception:
						pass
					# compute and show final path
					self.path = self.compute_path()
					self.path_cost = self.compute_path_cost(self.path)
					self.window.after(0, lambda: (self.show_path(), self.update_info(), self.upd_res(), setattr(self, '_single_running', False)))
			except Exception as e:
				# bind exception text into default arg so it's available when after() runs
				self.window.after(0, (lambda exc=e: self._append_res(f"{name} error: {exc}")))
			finally:
				# ensure single-running flag cleared even on error
				try:
					self._single_running = False
				except Exception:
					pass
		# run in background thread
		threading.Thread(target=_run, daemon=True).start()

	def run_selected_ui(self):
		sel = [a for a, v in self.avars.items() if (v.get() if hasattr(v, 'get') else bool(v))]
		if not sel:
			messagebox.showwarning("Warning", "Select algorithm(s)")
			return
		# run selected algorithms visually, one by one
		threading.Thread(target=lambda: self.run_all_visual(algos=sel), daemon=True).start()

	def run_all_ui(self):
		# run all algorithms visually, sequentially
		threading.Thread(target=lambda: self.run_all_visual(), daemon=True).start()

	def run_all_visual(self, algos=None):
		"""
		Run the provided algorithms sequentially in this ExecutionWindow, animating each
		so the user can visually compare them. Respects `self.stop_event`.
		"""
		if algos is None:
			algos = list(ALG_MAP.keys())
		def _worker():
			# mark running state for restart-on-speed-change
			self._is_running = True
			self._current_algos = algos
			for name in algos:
				if self.stop_event.is_set():
					self._append_res(f"Run cancelled before {name}")
					break
				self._append_res(f"Running {name}...")
				# clear previous highlights so each algorithm's run is clean
				try:
					for node, items in list(self.node_items.items()):
						oval, text = items
						self.canvas.itemconfig(oval, fill=NODE_BG)
						self.canvas.itemconfig(text, fill=LABEL_FG)
					for e in list(self.edge_items.values()):
						self.canvas.itemconfig(e, fill=EDGE_BG, width=2)
				except Exception:
					pass
				# show overlay with algorithm name
				try:
					overlay = self.canvas.create_text(self.canvas_w//2, 40, text=name, font=('Arial',18,'bold'), fill='#333', tags=('alg_overlay',))
					self.window.update()
				except Exception:
					overlay = None
				func = ALG_MAP.get(name)
				if func is None:
					self._append_res(f"No implementation for {name}")
					continue
				# run algorithm synchronously to get order/parent
				t0 = time.time()
				order, parent = func(self.start, self.goal)
				t1 = time.time()
				elapsed = t1 - t0
				# sample memory
				mem_delta = 0.0
				try:
					if psutil:
						mem_delta = psutil.Process().memory_info().rss / 1024.0
				except Exception:
					mem_delta = 0.0
				nodes = len(order) if order else 0
				success = (self.goal in order) or (self.start == self.goal)
				# estimate draw time and include it in reported time
				try:
					delay_ms = max(10, int(self.speed.get()))
				except Exception:
					delay_ms = 300
				if getattr(self, 'fast_search_var', None) is None or not self.fast_search_var.get():
					# synchronous animation path: include per-node delay plus a short pause
					draw_time = (len(order or []) * delay_ms) / 1000.0 + 0.6
				else:
					# fast mode: small UI update overhead
					draw_time = 0.2
				combined_time = elapsed + draw_time
				self.results[name] = {"time": combined_time, "memory": mem_delta, "nodes": nodes, "path_length": (len(self.compute_path()) if hasattr(self,'parent') else 0), "success": success}
				# set for visualization
				self.order = order
				self.parent = parent
				# compute final path now that parent pointers are in place
				try:
					self.path = self.compute_path()
					self.path_cost = self.compute_path_cost(self.path)
					pl = (len(self.path)-1) if self.path else 0
					if name in self.results:
						self.results[name]['path_length'] = pl
				except Exception:
					pass
				self.elapsed_ms = int(combined_time * 1000)
				# animate (or fast) and wait until animation completes or stop requested
				if getattr(self, 'fast_search_var', None) is None or not self.fast_search_var.get():
					delay = max(10, int(self.speed.get()))
					# Synchronous deterministic animation: iterate and update the UI
					try:
						self._append_res(f"{name}: animating {len(self.order or [])} nodes (success={success})")
					except Exception:
						pass
					for i, node in enumerate(self.order or []):
						if self.stop_event.is_set():
							break
						try:
							self.highlight_node(node)
						except Exception as e:
							# Log but continue
							try:
								self._append_res(f"{name} highlight error: {e}")
							except Exception:
								pass
						# force UI refresh and wait according to speed
						try:
							self.window.update()
						except Exception:
							pass
						time.sleep(delay / 1000.0)
					# after traversal, show path and update results/UI
					try:
						self.show_path()
						self.update_info()
						self.upd_res()
					except Exception as e:
						try:
							self._append_res(f"{name} show_path/update error: {e}")
						except Exception:
							pass
					# short pause so final path is visible to the user
					try:
						time.sleep(0.6)
					except Exception:
						pass
					# remove overlay
					try:
						self.canvas.delete('alg_overlay')
					except Exception:
						pass
				else:
					# fast: just compute and show
					self.path = self.compute_path()
					self.path_cost = self.compute_path_cost(self.path)
					self.window.after(0, lambda: (self.show_path(), self.update_info(), self.upd_res()))
					# small pause so UI updates and then remove overlay
					self.window.update()
					time.sleep(0.2)
					try:
						self.canvas.delete('alg_overlay')
					except Exception:
						pass
			# finished all
			self._append_res('All algorithms completed')
			# clear running state
			try:
				self._is_running = False
				self._current_algos = None
			except Exception:
				pass
		threading.Thread(target=_worker, daemon=True).start()

	def upd_res(self):
		# refresh the results text box
		try:
			if not hasattr(self, 'res_box'):
				return
			# ensure editable
			try:
				self.res_box.config(state='normal')
			except Exception:
				pass
			# remove previous content and write analysis summary then table
			try:
				self.res_box.delete('1.0', 'end')
			except Exception:
				pass
			# write analysis summary
			try:
				self.res_box.insert('end', f"Algorithm: {self.algorithm_name or '(none)'}\n")
				self.res_box.insert('end', f"Start: {self.start or '(none)'} | Goal: {self.goal or '(none)'}\n")
				self.res_box.insert('end', f"Elapsed (ms): {getattr(self,'elapsed_ms',0)} | Mem delta KB: {int(getattr(self,'end_mem',0)-getattr(self,'start_mem',0))}\n")
				self.res_box.insert('end', f"Nodes Expanded: {len(self.order)} | Path Length: {len(getattr(self,'path',[]))-1 if getattr(self,'path',None) else 0} | Path Cost: {getattr(self,'path_cost',0)}\n\n")
			except Exception:
				pass
			# now table header
			h = f"{'Algo':<14} {'Time(s)':<10} {'Mem(KB)':<12} {'Nodes':<8} {'PathLen':<8} {'OK':<5}\n"
			h += '-' * 70 + '\n'
			try:
				self.res_box.insert('end', h)
			except Exception:
				pass
			for a, s in sorted(self.results.items()):
				mem = s.get('memory', 0.0)
				mem_str = f"{mem:.2f}" if isinstance(mem, float) else str(mem)
				l = f"{a:<14} {s.get('time',0):<10.4f} {mem_str:<12} {s.get('nodes',0):<8} {s.get('path_length',0):<8} {'✓' if s.get('success') else '✗':<5}\n"
				try:
					self.res_box.insert('end', l)
				except Exception:
					pass
			# append per-step logs for the last individual run (if any)
			try:
				if getattr(self, '_step_logs', None):
					self.res_box.insert('end', '\nStep log (most recent):\n')
					for line in self._step_logs[-200:]:
						self.res_box.insert('end', line + '\n')
			except Exception:
				pass
			# make read-only
			try:
				self.res_box.config(state='disabled')
			except Exception:
				pass
		except Exception:
			pass

	def show_graph(self):
		# Simple performance window adapted from MazeGUI
		if not getattr(self, 'results', None):
			messagebox.showinfo('Graph', 'No results to show')
			return
		items = sorted(self.results.items())
		names = [n for n, _ in items]
		nodes = [float(r.get('nodes', 0) or 0) for _, r in items]
		times = [float(r.get('time', 0) or 0) for _, r in items]
		paths = [int(r.get('path_length', -1) if r.get('path_length', -1) is not None else -1) for _, r in items]
		mems = [float(r.get('memory', 0) or 0) for _, r in items]

		win = Toplevel(self.window)
		win.title('Performance Comparison')
		try:
			win.geometry('1000x700')
		except Exception:
			pass
		# top text
		top = Frame(win)
		top.pack(side='top', fill='x', padx=6, pady=6)
		# try to create a Text widget for summary; fall back to Label
		try:
			import tkinter as _tk_local
			info = _tk_local.Text(top, height=10, width=120)
			info.pack(side='left', fill='x', expand=True)
			# compute bests for highlighting
			best_time = min([r.get('time', float('inf')) for _, r in items]) if items else None
			best_nodes = min([r.get('nodes', float('inf')) for _, r in items]) if items else None
			best_mem = min([r.get('memory', float('inf')) for _, r in items]) if items else None
			best_path = min([r.get('path_length', float('inf')) for _, r in items]) if items else None
			info.insert('end', f"{'Algorithm':<18} {'Time(s)':<8} {'Nodes':<8} {'PathLen':<8} {'Memory(KB)':<12} {'Success':<8}\n")
			info.insert('end', '-'*80 + '\n')
			for name, r in items:
				time_s = r.get('time',0)
				nodes_v = r.get('nodes',0)
				path_v = r.get('path_length',-1)
				mem_v = r.get('memory',0)
				succ = '✓' if r.get('success') else '✗'
				mark = ''
				if best_time is not None and time_s == best_time:
					mark += '*'
				if best_nodes is not None and nodes_v == best_nodes:
					mark += '*'
				info.insert('end', f"{name:<18} {time_s:<8.3f} {nodes_v:<8} {path_v:<8} {mem_v:<12.2f} {succ:<8} {mark}\n")
			info.config(state='disabled')
		except Exception:
			lbl = Label(top, text='\n'.join([f"{name}\t{r.get('time',0):.3f}\t{r.get('nodes',0)}\t{r.get('path_length',-1)}\t{r.get('memory',0):.2f}" for name, r in items]))
			lbl.pack(fill='x')
		# Bars canvas
		canvas = Canvas(win, height=max(300, 30 * max(1, len(names))), width=840, bg='white')
		canvas.pack(side='bottom', fill='both', expand=True, padx=6, pady=6)
		# draw bars for multiple metrics with a legend
		name_col = 220
		metrics = ['Nodes', 'Time(s)', 'Path', 'Memory']
		metric_values = [nodes, times, [p if p >= 0 else 0 for p in paths], mems]
		colors = ['#f39c12', '#2ecc71', '#8e44ad', '#7f8c8d']
		max_vals = [max(vals) if vals and max(vals) > 0 else 1 for vals in metric_values]
		cwidth = max(840, canvas.winfo_reqwidth() if canvas.winfo_reqwidth() else 840)
		# leave an explicit gap between each metric block so numeric labels fit
		block_gap = 28
		# compute available area for all metric blocks (subtract gaps between them)
		total_gap = block_gap * (len(metrics) - 1)
		bar_area = max(400, cwidth - name_col - total_gap)
		# allocate width per metric block after accounting for gaps
		metric_width = max(90, (bar_area // len(metrics)))
		row_h = 34
		padding_top = 30
		# legend
		for mi, m in enumerate(metrics):
			canvas.create_rectangle(10 + mi*120, 6, 30 + mi*120, 24, fill=colors[mi], outline='black')
			canvas.create_text(36 + mi*120, 15, anchor='w', text=m, font=("Arial",9))
		for i, name in enumerate(names):
			y = padding_top + i * row_h
			canvas.create_text(10, y + (row_h//4), anchor='w', text=name, font=("Arial",10))
			for mi, vals in enumerate(metric_values):
				v = vals[i]
				maxv = max_vals[mi]
				# position each metric block with an extra gap so labels don't overlap
				x0 = name_col + mi * (metric_width + block_gap)
				y0 = y
				full_w = metric_width - 8
				w = int((v / maxv) * full_w) if maxv > 0 else 0
				# background bar
				canvas.create_rectangle(x0, y0, x0+full_w, y0 + (row_h//1.2), fill='#f6f7f8', outline='#ddd')
				# value bar
				if w > 0:
					canvas.create_rectangle(x0+2, y0+2, x0+2+w, y0 + (row_h//1.2) -2, fill=colors[mi], outline='black')
				# numeric label
				# rounded to one decimal place for compact display
				val_text = f"{v:.1f}" if isinstance(v, float) else str(v)
				canvas.create_text(x0 + full_w + 10, y + (row_h//6), anchor='w', text=val_text, font=("Arial",9))

	def show_best(self):
		ok = {a: s for a, s in self.results.items() if s.get('success')}
		if not ok:
			messagebox.showinfo('Best', 'No solution found')
			return
		b = min(ok.items(), key=lambda kv: (kv[1]['time'], kv[1]['nodes']))
		messagebox.showinfo('Best', f"{b[0]}\nTime: {b[1]['time']:.4f}s\nMemory: {b[1]['memory']:.2f} KB\nNodes: {b[1]['nodes']}")

	def recommend(self):
		ok = {a: s for a, s in self.results.items() if s.get('success')}
		if not ok:
			messagebox.showinfo('Recommend', 'Run algorithms first')
			return
		def norm(a, v):
			mn, mx = min(a), max(a)
			return 0 if mn == mx else (v - mn) / (mx - mn)
		t = [s['time'] for s in ok.values()]
		m = [s['memory'] for s in ok.values()]
		n = [s['nodes'] for s in ok.values()]
		scores = {a: norm(t, s['time']) + norm(m, s['memory']) + norm(n, s['nodes']) for a, s in ok.items()}
		best = min(scores.items(), key=lambda kv: kv[1])
		messagebox.showinfo('Recommend', f"Best: {best[0]}\nScore: {best[1]:.3f}")

	def request_stop(self):
		try:
			self.stop_event.set()
		except Exception:
			pass
		try:
			if hasattr(self, '_append_res'):
				self._append_res('Stop requested')
			else:
				self.upd_res()
		except Exception:
			pass

	def clear_stop(self):
		try:
			self.stop_event.clear()
		except Exception:
			pass
		try:
			self.upd_res()
		except Exception:
			pass

# Ensure the local ExecutionWindow overrides any imported value
ExecutionWindow = ExecutionWindow


window.mainloop()