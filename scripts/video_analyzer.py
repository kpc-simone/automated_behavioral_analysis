# tkinter_gui.py
# following example from realpython.com/python-gui-tkinter/


import tkinter as tk
import sys,os

sys.path.append(os.path.join(os.path.dirname(__file__),'../src'))
from analyzer_gui import *
#from processes import open_file#, save, edit

GUI = tk.Tk()
AnalysisConfigurer(GUI)
GUI.mainloop()
