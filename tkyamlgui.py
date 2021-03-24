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
if useruemel: yaml = yaml.YAML()

# Map some strings to types
typemap={}
typemap['str']   = str
typemap['bool']  = bool
typemap['int']   = int
typemap['float'] = float

#
# See https://stackoverflow.com/questions/58045626/scrollbar-in-tkinter-notebook-frames
class YScrolledFrame(Tk.Frame, object):
    def __init__(self, parent, *args, **kwargs):
        super(YScrolledFrame, self).__init__(parent, *args, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas = canvas = Tk.Canvas(self, relief='raised', 
                                         width=400, height=450)
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

class testApp(Tk.Tk, object):
    def __init__(self):
        super(App, self).__init__()

        notebook = Notebook(self, ['Page 1', 'Page 2', 'Page 3'])
        notebook.grid(row=0, column=0, sticky='nsew')

        # Fill content, to see scroll action
        tab = notebook.tab('Page 1')
        for n in range(10):
            label = Tk.Label(tab, text='Page 1 - Label {}'.format(n))
            label.grid()

def tkextractval(inputtype, tkvar, tkentry, optionlist=[]):
    if inputtype is bool:
        val = bool(tkvar.get())
    elif (inputtype is str) and len(optionlist)>0:
        val = str(tkvar.get())
    elif (inputtype is str):
        val = str(tkentry.get())
    elif (inputtype is int):
        val = int(float(tkentry.get()))
    else: # float 
        val = float(tkentry.get())
    return val

class inputwidget:
    def __init__(self, frame, row, inputtype, name, label, 
                 defaultval=None, optionlist=[], ctrlframe=None,
                 labelonly=False):
        defaultw       = 12
        self.name      = name
        self.label     = label
        self.labelonly = labelonly
        self.inputtype = inputtype
        self.var       = None
        self.optionlist= optionlist
        self.ctrlframe = ctrlframe
        self.tklabel   = Tk.Label(frame, text=label)
        #self.tklabel.grid(row=row, column=0, sticky='w')
        if row is None:  self.tklabel.grid(column=0, sticky='w', padx=5)
        else:            self.tklabel.grid(row=row, column=0, sticky='w', padx=5)
        if labelonly: return None

        if inputtype is bool:
            # create a checkvar
            self.var       = Tk.IntVar()
            if defaultval is not None: self.var.set(defaultval)
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
            if defaultval is not None: self.var.set(defaultval)
        elif (inputtype is str):
            self.var       = Tk.StringVar()
            self.tkentry   = Tk.Entry(master=frame, width=defaultw) 
            self.tkentry.insert(0, repr(defaultval))
        elif (isinstance(inputtype, list)):
            # Handle list inputs
            N              = len(inputtype)
            self.var       = []
            self.tkentry   = []
            for i in range(N):
                self.var.append(None)
                self.tkentry.append(Tk.Entry(master=frame, width=defaultw))
                self.tkentry[i].insert(0, repr(defaultval[i]))
        else:
            self.tkentry   = Tk.Entry(master=frame, width=defaultw) 
            self.tkentry.insert(0, repr(defaultval))
        # Add the entry to the frame
        if row is None: row=self.tklabel.grid_info()['row']
        if (isinstance(inputtype, list)):
            for i in range(len(inputtype)):
                self.tkentry[i].grid(row=row, column=1+i, sticky='w')
        else:
            self.tkentry.grid(row=row, column=1, sticky='w')
        return

    def getval(self):
        """Return the value"""
        try:
            if isinstance(self.inputtype, list):
                val = []
                for i in range(len(self.inputtype)):
                    ival = tkextractval(self.inputtype[i], 
                                        self.var[i], 
                                        self.tkentry[i])
                    val.append(ival)
            else:
                val = tkextractval(self.inputtype, self.var, self.tkentry,
                                   optionlist=self.optionlist)
        except:
            print("Error in "+self.name)
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
    
    @classmethod
    def fromdict(cls, frame, d, allframes=None):        
        # Parse the dict
        name                        = d['name']
        if 'row' in d:        row   = d['row']
        else:                 row   = None
        if 'label' in d:      label = d['label']
        else:                 label = ''
        if 'defaultval' in d: defaultval = d['defaultval']
        else:                 defaultval = None
        if 'optionlist' in d: optionlist = d['optionlist']
        else:                 optionlist = []
        if 'labelonly' in d:  labelonly  = d['labelonly']
        else:                 labelonly = False
        # Set the control frame (for booleans)
        ctrlframe = None
        if ('ctrlframe' in d) and (allframes is not None):
            ctrlframe = allframes[d['ctrlframe']]
        # Get the input type
        if 'inputtype' in d:  yamlinputtype    = d['inputtype']
        else:                 yamlinputtype    = 'str'
        if isinstance(yamlinputtype, list):
            inputtype = [typemap[x.lower()] for x in yamlinputtype]
        else:
            inputtype = typemap[yamlinputtype.lower()]
        return cls(frame, row, inputtype, name, label,
                   defaultval=defaultval, optionlist=optionlist,
                   ctrlframe=ctrlframe, labelonly=labelonly)
# -- Done inputwidget --

def donothing(toproot):
    filewin = Tk.Toplevel(toproot)
    button = Tk.Button(filewin, text="Do nothing button")
    button.pack()

def pullvals(inputs, statuslabel=None):
    for key, inp in inputs.items():
        if inp.labelonly is False:
            #print(inp)
            print(inp.name+": "+repr(inp.getval()))
    if statuslabel is not None: statuslabel.config(text='Pulled values')
    print("--- pulled values ---")
    return

def dummyMenu(root):
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


class App(Tk.Tk, object):
    def __init__(self, menufunc=None, configyaml='default.yaml', 
                 title='TK Yaml GUI',
                 *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)

        self.wm_title(title)

        # Set up the menu bar
        if menufunc is not None:   menufunc(self)
        else:                      dummyMenu(self)

        # Set up the status bar
        self.statusbar = Tk.Label(self, text="%200s"%" ", 
                             bd=1, relief=Tk.SUNKEN, anchor=Tk.W)
        self.statusbar.grid(row=1, columnspan=2, sticky='w')

        # Get the drawing window
        self.center = Tk.Frame(self, padx=5)
        self.center.grid(row=0, column=1)
        #self.fig = Figure(figsize=(5, 4), dpi=100, facecolor='white')    
        self.fig = Figure(dpi=100, facecolor='white')    
        t   = np.arange(0, 3, .01)
        self.fig.add_subplot(111) # .plot(t, 2 * np.sin(2 * np.pi * t))
        figcanvas = FigureCanvasTkAgg(self.fig, master=self.center)  # A tk.DrawingArea.
        figcanvas.draw()
        # Add toolbar to figcanvas
        toolbar = NavigationToolbar2TkAgg(figcanvas, self.center)
        toolbar.update()
        toolbar.pack(side=Tk.BOTTOM, fill=Tk.X, expand=1)
        figcanvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

        # The input frame is leftframe
        self.leftframe=Tk.Frame(self, width=450)
        self.leftframe.grid(row=0, column=0, sticky='nsew')
        self.leftframe.grid_propagate(0)

        # Load the yaml input file
        with open(configyaml) as fp:
            yamldict = yaml.load(fp)

        # -- Set up the tabs --
        #alltabslist = ['Tab 1','Tab 2', 'Tab 3']
        self.alltabslist = yamldict['tabs']
        self.notebook = Notebook(self.leftframe, self.alltabslist)
        self.notebook.grid(row=0, column=0, sticky='nsew')

        # -- Set up the frames --
        self.subframes = OrderedDict()
        if 'frames' in yamldict:
            for frame in yamldict['frames']:
                name = frame['name']
                tab  = self.notebook.tab(frame['tab'])
                self.subframes[name] = Tk.LabelFrame(tab)
                if 'row' in frame:
                    self.subframes[name].grid(column=0, row=frame['row'],
                                              padx=10,pady=10, 
                                              columnspan=4, sticky='w')
                else:
                    self.subframes[name].grid(column=0, padx=10,pady=10,
                                              columnspan=4, sticky='w') 
                if 'title' in frame:
                    Tk.Label(self.subframes[name], 
                             text=frame['title']).grid(row=0, column=0, 
                                                       columnspan=4,
                                                       sticky='w')
                #print('Done with frame '+name)

        # -- Set up the input widgets --
        self.inputvars = OrderedDict()
        for widget in yamldict['inputwidgets']:
            name  = widget['name']
            frame = self.tabframeselector(widget)
            iwidget = inputwidget.fromdict(frame, widget,
                                          allframes=self.subframes)
            self.inputvars[name] = iwidget
        

        # tab = self.notebook.tab('Tab 1')
        # Tk.Label(tab, text='Inputs').grid(row=0, column=0, sticky='w')
        # self.allinputs = []
        # self.allinputs.append(
        #     inputwidget(tab, None, float, "input0", "Test input 0", 
        #                 defaultval=1.0))
        # self.allinputs.append(
        #     inputwidget(tab, None, int,   "input1", "Test input 1"))
        # self.allinputs.append(
        #     inputwidget(tab, None, bool,  "input2", "Test input 2"))
        # self.allinputs.append(
        #     inputwidget(tab, None, str,   "input3", "Test input 3",
        #                 optionlist=['option1','option2']))
        # self.allinputs.append(
        #     inputwidget(tab, None, [float, int, str], 
        #                 "input4", "Test input vec"))
        # self.allinputs.append(
        #     inputwidget(tab, None, str, "input5", "Test str"))

        button = Tk.Button(master=self.notebook.tab('Tab 1'), text="Pullvals", 
                           command=partial(pullvals, self.inputvars, 
                                           statuslabel=self.statusbar))
        button.grid(column=0, padx=5, sticky='w')

        exitbutton = Tk.Button(master=self.notebook.tab('Tab 1'), 
                               text="Quit", command=self.quit)
        exitbutton.grid(row=8, column=0, padx=5, sticky='w')

        # tabframe  = self.notebook.tab('Tab 2') #alltabsdict['Tab 2']
        # for n in range(30):
        #     label = Tk.Label(tabframe, text='Page 1 - Label {}'.format(n))
        #     label.grid()

        # tabframe  = self.notebook.tab('Tab 3') #alltabsdict['Tab 3']
        # testframe = Tk.LabelFrame(tabframe)
        # testframe.grid(column=0,row=1,padx=10,pady=10)
        # Tk.Label(testframe, text='Frame stuff').grid(row=0, column=0, sticky='w')
        # self.allinputs.append(
        #     inputwidget(testframe, 1, [float, float], "inputB", "Test input B"))
        # Tk.Label(testframe, text='Explanation').grid(row=2, column=0, sticky='w')

        # self.allinputs.append(inputwidget(tabframe, 0, bool,  
        #                                   "inputA", "activate tab3", 
        #                                   ctrlframe=testframe))
        self.formatgridrows()
        return

    def tabframeselector(self, d):
        if 'frame' in d:  return self.subframes[d['frame']]
        else:             return self.notebook.tab(d['tab'])

    def formatgridrows(self, minsize=25):
        for tabname in self.alltabslist:
            tab = self.notebook.tab(tabname)
            col_count, row_count = tab.grid_size()
            for n in range(row_count): 
                tab.grid_rowconfigure(n, minsize=minsize)
        

if __name__ == "__main__":
    App().mainloop()
    #doGUI()
    #doGUI2()
