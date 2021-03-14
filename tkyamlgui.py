#!/usr/bin/env python

import numpy as np
import matplotlib
matplotlib.use('TkAgg')

# For help see:
# https://matplotlib.org/stable/gallery/user_interfaces/embedding_in_tk_sgskip.html
# https://stackoverflow.com/questions/59536002/how-do-i-align-something-to-the-bottom-left-in-tkinter-using-either-grid-or
# https://www.delftstack.com/howto/python-tkinter/how-to-pass-arguments-to-tkinter-button-command/
#
# For tabs with widgets
# https://www.geeksforgeeks.org/creating-tabbed-widget-with-python-tkinter/

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# implement the default mpl key bindings
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from functools import partial
from collections import OrderedDict 
import sys, os

if sys.version_info[0] < 3:
    import Tkinter as Tk
    import ttk
    from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg
else:
    import tkinter as Tk
    from tkinter import ttk
    from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as NavigationToolbar2TkAgg

class inputwidget:
    def __init__(self, frame, row, inputtype, name, label, 
                 startval=None, optionlist=[]):
        self.name      = name
        self.inputtype = inputtype
        self.label     = label
        self.var       = None
        self.tklabel   = Tk.Label(frame, text=label)
        self.tklabel.grid(row=row, column=0, sticky='w')
        if inputtype is bool:
            # create a checkvar
            self.var       = Tk.IntVar()
            self.tkentry   = Tk.Checkbutton(frame, variable=self.var)
        elif (inputtype is str) and (len(optionlist)>0):
            # create a dropdown menu
            self.var       = Tk.StringVar()
            self.tkentry   = Tk.OptionMenu(frame, self.var, *optionlist)
        else:
            self.tkentry   = Tk.Entry(master=frame) 
            self.tkentry.insert(0, repr(startval))
        self.tkentry.grid(row=row, column=1, sticky='w')
        return

    def getval(self):
        """Return the value"""
        if self.inputtype is bool:
            val = bool(self.var.get())
        elif (self.inputtype is str):
            val = str(self.var.get())
        elif (self.inputtype is int):
            val = int(self.tkentry.get())
        else:
            val = self.tkentry.get()
        return val

def donothing(toproot):
    filewin = Tk.Toplevel(toproot)
    button = Tk.Button(filewin, text="Do nothing button")
    button.pack()

def pullvals(inputs):
    for inp in inputs:
        print(inp.name+": "+repr(inp.getval()))
    return

def doMenu(root):
    """ 
    Adds a menu bar to root
    See https://www.tutorialspoint.com/python/tk_menu.htm
    """
    menubar  = Tk.Menu(root)

    # File menu
    filemenu = Tk.Menu(menubar, tearoff=0)
    filemenu.add_command(label="New", command=partial(donothing, root))
    filemenu.add_command(label="Open", command=partial(donothing, root))
    filemenu.add_command(label="Save", command=partial(donothing, root))
    filemenu.add_command(label="Save as...", command=partial(donothing, root))
    filemenu.add_command(label="Close", command=partial(donothing, root))
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=filemenu)

    # Help menu
    helpmenu = Tk.Menu(menubar, tearoff=0)
    helpmenu.add_command(label="Help Index", command=partial(donothing, root))
    helpmenu.add_command(label="About...", command=partial(donothing, root))
    menubar.add_cascade(label="Help", menu=helpmenu)

    root.config(menu=menubar)


# Run all of the gui elements
def doGUI():

    # GUI stuff
    top  = Tk.Tk()
    #top.geometry("800x600")
    cwd = os.getcwd()
    top.wm_title("Test TK Input: "+cwd)

    doMenu(top)

    center = Tk.Frame(top)
    center.grid(row=0, column=1)
    #center.pack(side=Tk.RIGHT)

    fig = Figure(figsize=(5, 4), dpi=100, facecolor='white')
    
    t = np.arange(0, 3, .01)
    fig.add_subplot(111).plot(t, 2 * np.sin(2 * np.pi * t))
    canvas = FigureCanvasTkAgg(fig, master=center)  # A tk.DrawingArea.
    canvas.draw()
    # pack_toolbar=False will make it easier to use a layout manager later on.
    toolbar = NavigationToolbar2TkAgg(canvas, center)
    toolbar.update()
    toolbar.pack(side=Tk.BOTTOM, fill=Tk.X, expand=1)
    canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
  
    leftframe=Tk.Frame(top, width=300)
    leftframe.grid(row=0, column=0, sticky='nsew')
    leftframe.grid_propagate(0)

    alltabslist = ['Tab 1','Tab 2', 'Tab 3']
    alltabsdict = OrderedDict()

    tabControl = ttk.Notebook(leftframe) 
    for tab in alltabslist:
        alltabsdict[tab] = ttk.Frame(tabControl) 
        tabControl.add(alltabsdict[tab], text = tab) 
    #tab1 = ttk.Frame(tabControl) 
    #tab2 = ttk.Frame(tabControl)     
    #tabControl.add(tab1, text ='Tab 1') 
    #tabControl.add(tab2, text ='Tab 2') 
    tabControl.pack(expand = 1, fill ="both") 

    #leftframe.pack(side=Tk.LEFT)
    #for i in range(10): leftframe.rowconfigure(1, weight=1)
    #for i in range(2): leftframe.columnconfigure(i, weight=1)

    tabframe = alltabsdict['Tab 1']
    Tk.Label(tabframe, text='Inputs').grid(row=0, column=0, sticky='w')
    allinputs = []
    allinputs.append(inputwidget(tabframe, 1, float, "input0", "Test input 0"))
    allinputs.append(inputwidget(tabframe, 2, int,   "input1", "Test input 1"))
    allinputs.append(inputwidget(tabframe, 3, bool,  "input2", "Test input 2"))
    allinputs.append(inputwidget(tabframe, 4, str,   "input3", "Test input 3",
                                 optionlist=['option1','option2']))

    button = Tk.Button(master=tabframe, text="Pullvals", 
                       command=partial(pullvals, allinputs))
    button.grid(row=5, column=0)

    exitbutton = Tk.Button(master=tabframe, text="Quit", command=top.quit)
    exitbutton.grid(row=6,column=0)

    ttk.Label(alltabsdict['Tab 2'], 
              text ="STUFF HERE").grid(column=0, row=0, padx=30, pady=30) 

    # Start the main loop
    Tk.mainloop()
    return


if __name__ == "__main__":
    doGUI()
    #doGUI2()
