import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os

# Launcher GUI to choose which problem GUI to run (emoji symbols used as icons)
GAMES = [
    {"title": "Grid Editor", "emoji": "🗺️", "desc": "Draw grids and visualize pathfinding\n", "path": os.path.join("Grid", "GUI.py")},
    {"title": "8-Puzzle", "emoji": "🧩", "desc": "Solve the 8-puzzle with search algorithms", "path": os.path.join("Puzzle 8-type", "GUI.py")},
    {"title": "15-Puzzle", "emoji": "🔢", "desc": "Solve the 15-puzzle with search algorithms", "path": os.path.join("Puzzle 15-type", "GUI.py")},
    {"title": "Maze", "emoji": "🧭", "desc": "Generate and solve mazes", "path": os.path.join("Maze", "GUI.py")},
    {"title": "Graph", "emoji": "📈", "desc": "Visualize graph algorithms", "path": os.path.join("Graph", "Project","GUI.py")},
]


def launch_script(script_rel_path):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(root_dir, script_rel_path)
    if not os.path.exists(script_path):
        messagebox.showerror("Not found", f"GUI not found: {script_path}")
        return
    try:
        subprocess.Popen([sys.executable, script_path], cwd=os.path.dirname(script_path))
    except Exception as e:
        messagebox.showerror("Launch error", f"Failed to launch {script_rel_path}: {e}")


def open_file(file_rel_path):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(root_dir, file_rel_path)

    if not os.path.exists(file_path):
        messagebox.showerror("Not found", f"File not found: {file_path}")
        return

    try:
        if os.name == "nt":
            os.startfile(file_path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", file_path])
        else:
            subprocess.Popen(["xdg-open", file_path])
    except Exception as e:
        messagebox.showerror("Open error", f"Failed to open file:\n{e}")


class MainLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Problems applications")

        try:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
        except:
            sw, sh = 1920, 1080
        w = int(min(1200, sw * 0.7))
        h = int(min(760, sh * 0.7))
        self.root.geometry(f"{w}x{h}")

        self.ui_scale = min(max(0.7, sw / 1920.0), 1.4)
        self.sf = lambda s: max(8, int(s * self.ui_scale))

        container = ttk.Frame(root, padding=self.sf(16))
        container.pack(fill=tk.BOTH, expand=True)

        header = ttk.Label(container, text="Choose a Problem", font=("Segoe UI", self.sf(24), "bold"))
        header.pack(pady=(0, self.sf(12)))

        cards_frame = ttk.Frame(container)
        cards_frame.pack(fill=tk.BOTH, expand=True)

        cols = 3
        for c in range(cols):
            cards_frame.columnconfigure(c, weight=1)

        rows = (len(GAMES) + cols - 1) // cols
        for r in range(rows):
            cards_frame.rowconfigure(r, weight=1)

        def set_card_bg(card_widget, color):
            try:
                card_widget.config(bg=color)
            except:
                pass
            for child in card_widget.winfo_children():
                try:
                    cls = child.winfo_class()
                    if cls in ("Label", "Frame", "Canvas", "Text"):
                        child.config(bg=color)
                except:
                    pass


        for idx, game in enumerate(GAMES):
            r = idx // cols
            c = idx % cols
            card = tk.Frame(cards_frame, bd=1, relief='ridge', bg='#FFFFFF')
            card.grid(row=r, column=c, padx=self.sf(10), pady=self.sf(8), sticky='nsew')

            card.bind('<Enter>', lambda e, cw=card: set_card_bg(cw, '#f0fff0'))
            card.bind('<Leave>', lambda e, cw=card: set_card_bg(cw, '#FFFFFF'))
            card.bind('<Button-1>', lambda e, p=game['path']: launch_script(p))

            emoji_lbl = tk.Label(card, text=game['emoji'], font=("Segoe UI Emoji", self.sf(48)), bg=card.cget('bg'))
            emoji_lbl.pack(pady=(self.sf(14), 0))

            title_lbl = tk.Label(card, text=game['title'], font=("Segoe UI", self.sf(18), 'bold'), bg=card.cget('bg'))
            title_lbl.pack(pady=(self.sf(8), 0))

            desc_lbl = tk.Label(card, text=game['desc'], font=("Segoe UI", self.sf(12)), bg=card.cget('bg'),
                                wraplength=self.sf(240))
            desc_lbl.pack(pady=(self.sf(6), self.sf(12)), padx=self.sf(8))

            launch_btn = tk.Button(card, text="Launch", font=("Segoe UI", self.sf(14), 'bold'),
                                   bg='#2E8B57', fg='white', bd=0, cursor='hand2',
                                   command=lambda p=game['path']: launch_script(p))
            launch_btn.pack(pady=(0, self.sf(14)), ipadx=self.sf(10), ipady=self.sf(6))
            # hover effects: slightly darker on enter, restore on leave
            def _btn_enter(e, b=launch_btn):
                try:
                    b.configure(bg="#852406")
                except:
                    pass
            def _btn_leave(e, b=launch_btn):
                try:
                    b.configure(bg='#2E8B57')
                except:
                    pass
            launch_btn.bind('<Enter>', _btn_enter)
            launch_btn.bind('<Leave>', _btn_leave)

        extra_holder = tk.Frame(cards_frame, bg="#FFFFFF", bd=1, relief="ridge")
        extra_holder.grid(row=1, column=2, padx=self.sf(10), pady=self.sf(8), sticky="nsew")

        def make_file_card(parent, title, emoji, file_path):
            card = tk.Frame(parent, bg="#FFFFFF", bd=1, relief="solid")
            card.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

            card.bind("<Enter>", lambda e, cw=card: set_card_bg(cw, "#f0fff0"))
            card.bind("<Leave>", lambda e, cw=card: set_card_bg(cw, "#FFFFFF"))
            card.bind("<Button-1>", lambda e, p=file_path: open_file(p))

            emoji_lbl = tk.Label(card, text=emoji, font=("Segoe UI Emoji", self.sf(26)), bg="#FFFFFF")
            emoji_lbl.pack(pady=(8, 0))

            title_lbl = tk.Label(card, text=title, font=("Segoe UI", self.sf(12), "bold"), bg="#FFFFFF")
            title_lbl.pack(pady=(4, 6))

            open_btn = tk.Button(
                card,
                text="Open",
                font=("Segoe UI", self.sf(11), "bold"),
                bg="#4682B4",
                fg="white",
                bd=0,
                command=lambda p=file_path: open_file(p)
            )
            open_btn.pack(pady=(0, 8), ipadx=10, ipady=4)
            # hover effects for Open button
            def _open_enter(e, b=open_btn):
                try:
                    b.configure(bg="#08753b", cursor='hand2')
                except:
                    pass
            def _open_leave(e, b=open_btn):
                try:
                    b.configure(bg='#4682B4', cursor='')
                except:
                    pass
            open_btn.bind('<Enter>', _open_enter)
            open_btn.bind('<Leave>', _open_leave)

        make_file_card(extra_holder, "Project Report", "📄", "report.pdf")
        make_file_card(extra_holder, "README File", "📘", "README.md")

    
        footer = ttk.Frame(container)
        footer.pack(fill=tk.X, pady=(self.sf(8), 0))

        notes = "you can run any game to try it by just clicking the Launch button of it , enjoy!"
        notes_lbl = ttk.Label(footer, text=notes, font=("Segoe UI", self.sf(10)))
        notes_lbl.pack(side=tk.LEFT, padx=(0, self.sf(8)))

        quit_btn = tk.Button(footer, text="Quit", command=self.root.destroy,
                             font=("Segoe UI", self.sf(14)),
                             bg='#B22222', fg='white', bd=0)
        quit_btn.pack(side=tk.RIGHT)


def main():
    root = tk.Tk()
    app = MainLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()
