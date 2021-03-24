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

try:
    import ruamel.yaml as yaml
    print("# Loaded ruamel.yaml")
    useruemel=True
except:
    import yaml as yaml
    print("# Loaded yaml")
    useruemel=False

#
# See https://stackoverflow.com/questions/58045626/scrollbar-in-tkinter-notebook-frames
class YScrolledFrame(Tk.Frame, object):
    def __init__(self, parent, *args, **kwargs):
        super(YScrolledFrame, self).__init__(parent, *args, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas = canvas = Tk.Canvas(self, relief='raised', 
                                         width=350, height=400)
        canvas.grid(row=0, column=0, sticky='nsew')

        scroll = Tk.Scrollbar(self, command=canvas.yview, orient=Tk.VERTICAL)
        canvas.config(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky='nsew')

        self.content = Tk.Frame(canvas)
        self.canvas.create_window(0, 0, window=self.content, anchor="nw")

        self.bind('<Configure>', self.on_configure)

    def on_configure(self, event):
        bbox = self.content.bbox('ALL')
        self.canvas.config(scrollregion=bbox)

class Notebook(ttk.Notebook, object):
    def __init__(self, parent, tab_labels):
        super(Notebook, self).__init__(parent)

        self._tab = {}
        for text in tab_labels:
            self._tab[text] = YScrolledFrame(self)
            # layout by .add defaults to fill=Tk.BOTH, expand=True
            self.add(self._tab[text], text=text, compound=Tk.TOP)

    def tab(self, key):
        return self._tab[key].content

class App(Tk.Tk, object):
    def __init__(self):
        super(App, self).__init__()

        notebook = Notebook(self, ['Page 1', 'Page 2', 'Page 3'])
        notebook.grid(row=0, column=0, sticky='nsew')

        # Fill content, to see scroll action
        tab = notebook.tab('Page 1')
        for n in range(10):
            label = Tk.Label(tab, text='Page 1 - Label {}'.format(n))
            label.grid()

class inputwidget:
    def __init__(self, frame, row, inputtype, name, label, 
                 defaultval=None, optionlist=[], ctrlframe=None):
        self.name      = name
        self.inputtype = inputtype
        self.label     = label
        self.var       = None
        self.ctrlframe = ctrlframe
        self.tklabel   = Tk.Label(frame, text=label)
        #self.tklabel.grid(row=row, column=0, sticky='w')
        if row is None:  self.tklabel.grid(column=0, sticky='w')
        else:            self.tklabel.grid(row=row, column=0, sticky='w')
        if inputtype is bool:
            # create a checkvar
            self.var       = Tk.IntVar()
            if self.ctrlframe is None:
                self.tkentry   = Tk.Checkbutton(frame, variable=self.var)
            else:
                self.tkentry   = Tk.Checkbutton(frame, variable=self.var, 
                                                command=self.onoffframe)
                self.onoffframe()
        elif (inputtype is str) and (len(optionlist)>0):
            # create a dropdown menu
            self.var       = Tk.StringVar()
            self.tkentry   = Tk.OptionMenu(frame, self.var, *optionlist)
        elif (isinstance(inputtype, list)):
            self.var       = []
        else:
            self.tkentry   = Tk.Entry(master=frame) 
            self.tkentry.insert(0, repr(defaultval))
        if row is None: row=self.tklabel.grid_info()['row']
        self.tkentry.grid(row=row, column=1, sticky='w')
        return

    def getval(self):
        """Return the value"""
        try:
            if self.inputtype is bool:
                val = bool(self.var.get())
            elif (self.inputtype is str):
                val = str(self.var.get())
            elif (self.inputtype is int):
                val = int(self.tkentry.get())
            else:
                val = self.tkentry.get()
        except:
            val = None
        return val

    def onoffframe(self):
        if self.var.get() == 1:
            for child in self.ctrlframe.winfo_children():
                child.configure(state='normal')
            #self.ctrlframe.config(state=ACTIVE)
        else:
            for child in self.ctrlframe.winfo_children():
                child.configure(state='disable')
            #self.ctrlframe.config(state=DISABLED)
        return

def donothing(toproot):
    filewin = Tk.Toplevel(toproot)
    button = Tk.Button(filewin, text="Do nothing button")
    button.pack()

def pullvals(inputs, statuslabel=None):
    for inp in inputs:
        print(inp.name+": "+repr(inp.getval()))
    if statuslabel is not None: statuslabel.config(text='Pulled values')
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
  
    leftframe=Tk.Frame(top, width=400)
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
    #v = Tk.Scrollbar(tabframe)
    #v.pack(side=Tk.RIGHT, fill=Tk.Y)
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

    #ttk.Label(alltabsdict['Tab 2'], 
    #          text ="STUFF HERE").grid(column=0, row=0, padx=30, pady=30) 
    tabframe = alltabsdict['Tab 2']
    testframe = Tk.LabelFrame(tabframe)
    canvas = Tk.Canvas(testframe, width=200, height=400)
    scroll = Tk.Scrollbar(testframe, command=canvas.yview)
    canvas.config(yscrollcommand=scroll.set, scrollregion=(0,0,100,1000))
    canvas.pack(side=Tk.LEFT, fill=Tk.BOTH, expand=True)
    scroll.pack(side=Tk.RIGHT, fill=Tk.Y)
    frame = Tk.Frame(canvas, bg='white', width=200, height=1000)
    canvas.create_window(100, 500, window=frame)

    tabframe = alltabsdict['Tab 3']
    testframe = Tk.LabelFrame(tabframe)
    testframe.grid(column=0,row=1,padx=10,pady=10)
    Tk.Label(testframe, text='Frame stuff').grid(row=0, column=0, sticky='w')
    allinputs.append(inputwidget(testframe, 1, float, "inputB", "Test input B"))
    Tk.Label(testframe, text='Explanation').grid(row=2, column=0, sticky='w')

    allinputs.append(inputwidget(tabframe, 0, bool,  
                                 "inputA", "activate tab3", 
                                 ctrlframe=testframe))

    # Start the main loop
    Tk.mainloop()
    return

# Run all of the gui elements
def doGUI2():

    # GUI stuff
    top  = Tk.Tk()
    #top.geometry("800x600")
    cwd = os.getcwd()
    top.wm_title("Test TK Input: "+cwd)

    doMenu(top)
    
    statusbar = Tk.Label(top, text="", 
                         bd=1, relief=Tk.SUNKEN, anchor=Tk.W)
    statusbar.grid(row=1, columnspan=2, sticky='w')
    #statusbar.pack(side=Tk.BOTTOM, fill=Tk.X)

    # Get the drawing window
    center = Tk.Frame(top, padx=5)
    center.grid(row=0, column=1)
    fig = Figure(figsize=(5, 4), dpi=100, facecolor='white')    
    t   = np.arange(0, 3, .01)
    fig.add_subplot(111).plot(t, 2 * np.sin(2 * np.pi * t))
    canvas = FigureCanvasTkAgg(fig, master=center)  # A tk.DrawingArea.
    canvas.draw()

    # pack_toolbar=False will make it easier to use a layout manager later on.
    toolbar = NavigationToolbar2TkAgg(canvas, center)
    toolbar.update()
    toolbar.pack(side=Tk.BOTTOM, fill=Tk.X, expand=1)
    canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
  
    leftframe=Tk.Frame(top, width=400)
    leftframe.grid(row=0, column=0, sticky='nsew')
    leftframe.grid_propagate(0)

    alltabslist = ['Tab 1','Tab 2', 'Tab 3']

    notebook = Notebook(leftframe, alltabslist)
    notebook.grid(row=0, column=0, sticky='nsew')

    # tabframe = alltabsdict['Tab 1']
    tab = notebook.tab('Tab 1')
    Tk.Label(tab, text='Inputs').grid(row=0, column=0, sticky='w')
    allinputs = []
    allinputs.append(inputwidget(tab, None, float, "input0", "Test input 0"))
    allinputs.append(inputwidget(tab, None, int,   "input1", "Test input 1"))
    allinputs.append(inputwidget(tab, None, bool,  "input2", "Test input 2"))
    allinputs.append(inputwidget(tab, None, str,   "input3", "Test input 3",
                                 optionlist=['option1','option2']))
    
    button = Tk.Button(master=tab, text="Pullvals", 
                       command=partial(pullvals, allinputs, statuslabel=statusbar))
    button.grid(row=5, column=0)

    exitbutton = Tk.Button(master=tab, text="Quit", command=top.quit)
    exitbutton.grid(row=8, column=0)
    col_count, row_count = tab.grid_size()
    for n in range(row_count): tab.grid_rowconfigure(n, minsize=25)

    tabframe  = notebook.tab('Tab 2') #alltabsdict['Tab 2']
    for n in range(30):
        label = Tk.Label(tabframe, text='Page 1 - Label {}'.format(n))
        label.grid()

    tabframe  = notebook.tab('Tab 3') #alltabsdict['Tab 3']
    testframe = Tk.LabelFrame(tabframe)
    testframe.grid(column=0,row=1,padx=10,pady=10)
    Tk.Label(testframe, text='Frame stuff').grid(row=0, column=0, sticky='w')
    allinputs.append(inputwidget(testframe, 1, float, "inputB", "Test input B"))
    Tk.Label(testframe, text='Explanation').grid(row=2, column=0, sticky='w')

    allinputs.append(inputwidget(tabframe, 0, bool,  
                                 "inputA", "activate tab3", 
                                 ctrlframe=testframe))

    # Start the main loop
    Tk.mainloop()
    return

if __name__ == "__main__":
    #App().mainloop()
    #doGUI()
    doGUI2()
