import sys, runpy, traceback
# Create a minimal fake tkinter module to allow headless execution of the GUI script
import types
_fake = types.SimpleNamespace()

class DummyVar:
    def __init__(self, value=False):
        self._v = value
    def get(self):
        return self._v
    def set(self, v):
        self._v = v

class DummyWidget:
    def __init__(self, *args, **kwargs):
        pass
    def place(self, *a, **k): pass
    def pack(self, *a, **k): pass
    def bind(self, *a, **k): pass
    def config(self, *a, **k): pass
    def insert(self, *a, **k): pass
    def see(self, *a, **k): pass
    def create_line(self, *a, **k): return None
    def create_text(self, *a, **k): return None
    def create_rectangle(self, *a, **k): return None
    def create_oval(self, *a, **k): return None
    def itemconfig(self, *a, **k): pass
    def after(self, *a, **k): pass
    def pack_forget(self): pass

class DummyFont:
    def __init__(self, family='Arial', size=12, weight=''):
        self._size = size
    def measure(self, s):
        return max(10, len(str(s)) * 7)

class DummyPhotoImage:
    def __init__(self, file=None):
        pass

class DummyMessageBox:
    @staticmethod
    def showwarning(title, msg):
        print(f"MESSAGEBOX WARNING: {title}: {msg}")
    @staticmethod
    def showinfo(title, msg):
        print(f"MESSAGEBOX INFO: {title}: {msg}")

class DummyTk(DummyWidget):
    def __init__(self):
        pass
    def title(self, *a, **k): pass
    def geometry(self, *a, **k): pass
    def configure(self, *a, **k): pass
    def state(self, *a, **k): pass
    def attributes(self, *a, **k): pass
    def winfo_screenwidth(self): return 1200
    def winfo_screenheight(self): return 800
    def winfo_rootx(self): return 0
    def winfo_rooty(self): return 0
    def mainloop(self): pass

class DummyToplevel(DummyTk):
    pass

# Build fake tkinter module
fake_tk = types.ModuleType('tkinter')
for name in ['Tk','Toplevel','Label','Frame','Button','PhotoImage','Canvas','Scale','Checkbutton','BooleanVar']:
    setattr(fake_tk, name, DummyWidget)
setattr(fake_tk, 'Tk', DummyTk)
setattr(fake_tk, 'Toplevel', DummyToplevel)
setattr(fake_tk, 'PhotoImage', DummyPhotoImage)
setattr(fake_tk, 'messagebox', DummyMessageBox)
# constants
for c in ['RIDGE','SUNKEN','N','S','E','W','HORIZONTAL']:
    setattr(fake_tk, c, c)
# font submodule
font_mod = types.SimpleNamespace(Font=DummyFont)
setattr(fake_tk, 'font', font_mod)
# BooleanVar backed by DummyVar
def _boolvar(value=False):
    return DummyVar(value)
setattr(fake_tk, 'BooleanVar', DummyVar)
setattr(fake_tk, 'Checkbutton', DummyWidget)
setattr(fake_tk, 'Scale', DummyWidget)
setattr(fake_tk, 'Canvas', DummyWidget)

# Insert into sys.modules to shadow the real tkinter
sys.modules['tkinter'] = fake_tk
# also insert subnames typically imported
sys.modules['tkinter.font'] = font_mod

# Now attempt to run the GUI.py via runpy to capture any runtime exceptions
path = '/home/amrmaarouf/My_Space/ME/Projects/University/Level_One/1st_semester/AI/Codes/Graph/Project /GUI.py'
print('Running GUI script (headless) ->', path)
try:
    runpy.run_path(path, run_name='__main__')
    print('Execution finished without uncaught exceptions.')
except Exception:
    traceback.print_exc()
    print('Execution raised an exception (see traceback above).')

# cleanup
del sys.modules['tkinter']
del sys.modules['tkinter.font']
