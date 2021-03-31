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
import sys, os, re
from enum import Enum

if sys.version_info[0] < 3:
    import Tkinter as Tk
    import ttk
    import tkFileDialog as filedialog
    from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg
else:
    import tkinter as Tk
    from tkinter import ttk
    from tkinter import filedialog as filedialog
    from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as NavigationToolbar2TkAgg

try:
    import ruamel.yaml as yaml
    #print("# Loaded ruamel.yaml")
    useruemel=True
except:
    import yaml as yaml
    #print("# Loaded yaml")
    useruemel=False
if useruemel: yaml = yaml.YAML()

# Helpful function for pulling things out of dicts
getdictval = lambda d, key, default: default if key not in d else d[key]

# Add some additional input types
class moretypes(Enum):
    mergedboollist = 1    
    listbox        = 2
    filename       = 3

# Map some strings to types
typemap={}
typemap['str']   = str
typemap['bool']  = bool
typemap['int']   = int
typemap['float'] = float
typemap['mergedboollist'] = moretypes.mergedboollist
typemap['listbox']        = moretypes.listbox
typemap['filename']       = moretypes.filename

def to_bool(bool_str):
    """Parse the string and return the boolean value encoded or raise an
    exception
    """
    #if isinstance(bool_str, basestring) and bool_str: 
    if isinstance(bool_str, basestring):
        if bool_str.lower() in ['true', 't', '1']: 
            return True
        elif bool_str.lower() in ['false', 'f', '0']: 
            return False
    #if here we couldn't parse it
    raise ValueError("[%s] is not recognized as a boolean value" % bool_str)

#
# See https://stackoverflow.com/questions/58045626/scrollbar-in-tkinter-notebook-frames
class YScrolledFrame(Tk.Frame, object):
    def __init__(self, parent, canvaswidth=500, *args, **kwargs):
        super(YScrolledFrame, self).__init__(parent, *args, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas = canvas = Tk.Canvas(self, relief='raised', 
                                         width=canvaswidth, height=450)
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
    def __init__(self, parent, tab_labels, canvaswidth=500):
        super(Notebook, self).__init__(parent)

        self._tab = {}
        for text in tab_labels:
            self._tab[text] = YScrolledFrame(self, canvaswidth=canvaswidth)
            # layout by .add defaults to fill=Tk.BOTH, expand=True
            self.add(self._tab[text], text=text, compound=Tk.TOP)

    def tab(self, key):
        return self._tab[key].content

# def getMergedBoollist(inp, allvars):
#     val = []
#     for var in inp.mergedboollist:
#         boolvar = var[0]
#         iftrue  = var[1]
#         iffalse = var[2]
#         if allvars[boolvar].getval():    val.append(iftrue)
#         else:                            val.append(iffalse)
#     return val

def tkextractval(inputtype, tkvar, tkentry, optionlist=[]):
    if inputtype is bool:
        val = bool(tkvar.get())
    elif (inputtype is str) and len(optionlist)>0:
        val = str(tkvar.get())
    elif (inputtype is moretypes.listbox):
        val = [tkentry.get(idx) for idx in tkentry.curselection()]
    elif (inputtype is str):
        val = str(tkentry.get())
    elif (inputtype is moretypes.filename):
        val = str(tkentry.get())
    elif (inputtype is int):
        val = int(float(tkentry.get()))
    else: # float 
        val = float(tkentry.get())
    return val

class inputwidget:
    """
    Creates a general-purpose widget for input 
    """
    def __init__(self, frame, row, inputtype, name, label, 
                 defaultval=None, optionlist=[], 
                 listboxopt={},  fileopenopt={},
                 ctrlframe=None, ctrlelem=None,
                 labelonly=False, visible=True, 
                 outputdef={}, mergedboollist=[], allinputs=None):
        defaultw       = 12
        self.name      = name
        self.label     = label
        self.labelonly = labelonly
        self.inputtype = inputtype
        self.var       = None
        self.optionlist= optionlist
        self.listboxopt= listboxopt
        self.ctrlframe = ctrlframe
        self.ctrlelem  = ctrlelem
        self.tklabel   = Tk.Label(frame, text=label)
        self.outputdef = outputdef
        self.visible   = visible
        self.mergedboollist = mergedboollist
        self.button    = None
        self.allinputs = allinputs

        if inputtype == moretypes.mergedboollist: return

        if visible:
            if row is None:  
                self.tklabel.grid(column=0, sticky='nw', padx=5)
            else:            
                self.tklabel.grid(row=row, column=0, sticky='nw', padx=5)
        if labelonly: return None

        if inputtype is bool:
            # create a checkvar
            self.var       = Tk.IntVar()
            if defaultval is not None: self.var.set(defaultval)
            if self.ctrlelem is None:
                self.tkentry   = Tk.Checkbutton(frame, variable=self.var)
            else:
                self.tkentry   = Tk.Checkbutton(frame, variable=self.var, 
                                                command=partial(self.onoffctrlelem, None))
        elif (inputtype is moretypes.listbox):
            height=max(3,len(optionlist))
            self.tkentry   = Tk.Listbox(frame, height=height,
                                        exportselection=False, **listboxopt) 

            for i, option in enumerate(optionlist):
                self.tkentry.insert(i+1, option)
            # Set the default values
            if defaultval is not None:
                if not isinstance(defaultval, list): defaultval = [defaultval]
                for v in defaultval:
                    # set the value to active
                    self.tkentry.selection_set(self.optionlist.index(v))
            if self.ctrlelem is not None:
                self.tkentry.bind("<<ListboxSelect>>", self.onoffctrlelem)
        elif (inputtype is str) and (len(optionlist)>0):
            # create a dropdown menu
            self.var       = Tk.StringVar()
            self.tkentry   = Tk.OptionMenu(frame, self.var, *optionlist)
            if defaultval is not None: self.var.set(defaultval)
        elif (inputtype is str):
            self.var       = Tk.StringVar()
            self.tkentry   = Tk.Entry(master=frame, width=defaultw) 
            self.tkentry.insert(0, repr(defaultval))
        elif (inputtype is moretypes.filename):
            self.var       = Tk.StringVar()
            self.tkentry   = Tk.Entry(master=frame, width=defaultw) 
            if defaultval is not None: 
                self.tkentry.insert(0, repr(defaultval))
            # Add a button to choose filename
            self.button    = Tk.Button(master=frame, 
                                       text="Choose file", 
                                       command=partial(self.choosefile, 
                                                       fileopenopt))
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
        if visible:
            if row is None: row=self.tklabel.grid_info()['row']
            if (isinstance(inputtype, list)):
                for i in range(len(inputtype)):
                    self.tkentry[i].grid(row=row, column=1+i, sticky='w')
            else:
                self.tkentry.grid(row=row, column=1, sticky='w')
            if self.button is not None: 
                self.button.grid(row=row, column=2, sticky='nw')

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
            elif (self.inputtype == moretypes.mergedboollist):
                val = []
                for var in self.mergedboollist:
                    boolvar = var[0]
                    iftrue  = var[1]
                    iffalse = var[2]
                    if self.allinputs[boolvar].getval():    
                        val.append(iftrue)
                    else:                            
                        val.append(iffalse)
            else:
                # Scalar primitive types
                val = tkextractval(self.inputtype, self.var, self.tkentry,
                                   optionlist=self.optionlist)
        except:
            print("Error in "+self.name)
            val = None
        return val

    def setval(self, val, strinput=False, forcechange=False):
        """Update the contents with val"""
        if (isinstance(self.inputtype, list)):
            listval=val
            if strinput: listval = re.split(r'[,; ]+', val)
            # Input a list
            for i in range(len(self.inputtype)):
                itkentry= self.tkentry[i]
                statedisabled= itkentry.cget('state') in ['disable','disabled']
                if statedisabled and forcechange==False:
                    print("CANNOT update: %s use forcechange=True in setval()"
                          %self.name)
                if statedisabled and forcechange:
                    itkentry.config(state='normal')                    
                #print(repr(itkentry.get()))
                itkentry.delete(0, Tk.END)
                itkentry.insert(0, repr(listval[i]).strip("'").strip('"'))
                #self.tkentry[i].insert(0, repr(listval[i]))
                #print(repr(listval[i]), itkentry.get())
                if statedisabled and forcechange: # Reset the state
                    itkentry.config(state='disabled')                    
        else: 
            # Check to see if entry is normal or disabled
            if self.inputtype==moretypes.mergedboollist: 
                statedisabled=False
            else:
                statedisabled=self.tkentry.cget('state') in ['disable','disabled']
            if statedisabled and forcechange==False:
                print("CANNOT update: %s use forcechange=True in setval()"
                      %self.name)
            if statedisabled and forcechange:
                self.tkentry.config(state='normal') 
            # Handle scalars
            if self.inputtype is bool:
                boolval = to_bool(val) if strinput else val
                #print("Set "+self.name+" to "+repr(val))
                self.var.set(boolval)
                if self.ctrlelem is not None: self.onoffctrlelem(None)
            elif (self.inputtype is str) and len(self.optionlist)>0:
                self.var.set(val.strip("'").strip('"'))
            elif self.inputtype==moretypes.listbox:
                listval = val
                if strinput: listval = re.split(r'[,; ]+', val)
                for v in listval:
                    # set the value to active
                    self.tkentry.selection_set(self.optionlist.index(v))
            elif self.inputtype==moretypes.mergedboollist:
                allboolstrs=[item for sublist in self.mergedboollist for item in sublist[1:]]
                listval=val
                if strinput: listval = re.split(r'[,; ]+', val)                
                if '' in allboolstrs:
                    # Could be in any order
                    for boolinput in self.mergedboollist:
                        if boolinput[1] in listval:
                            self.allinputs[boolinput[0]].setval(True)
                        else:
                            self.allinputs[boolinput[0]].setval(False)
                else:
                    # Take it in order
                    for istr, strinput in enumerate(listval):
                        boolinput=self.mergedboollist[istr]
                        if strinput.lower()==boolinput[1].lower():
                            self.allinputs[boolinput[0]].setval(True)
                        elif strinput.lower()==boolinput[2].lower():
                            self.allinputs[boolinput[0]].setval(False)
                        else:
                            raise ValueError("%s is not either %s or %s."%(strinput, boolinput[1], boolinput[2]))
            else:
                # Set a string in the entry
                self.tkentry.delete(0, Tk.END)
                self.tkentry.insert(0, repr(val).strip("'").strip('"'))
            if statedisabled and forcechange: # Reset the state
                self.tkentry.config(state='disabled')                    
        return

    def choosefile(self, optiondict):
        #filewin = Tk.Toplevel()   
        #print(optiondict)
        selecttype = getdictval(optiondict, 'selecttype', 'open')
        if selecttype=='open':
            filename = filedialog.askopenfilename(initialdir = "./",
                                                  title = "Select file")
        elif selecttype=='saveas':
            filename = filedialog.asksaveasfilename(initialdir = "./",
                                                    title = "Select file")
        elif selecttype=='directory':
            filename = filedialog.askdirectory(initialdir = "./",
                                               title = "Select directory")
        self.tkentry.delete(0, Tk.END)
        self.tkentry.insert(0, filename)
        return filename

    def onoffframe(self):
        if self.var.get() == 1:
            for child in self.ctrlframe.winfo_children():
                child.configure(state='normal')
        else:
            for child in self.ctrlframe.winfo_children():
                child.configure(state='disable')
        return

    def onoffctrlelem(self, event):
        currstate = self.getval()
        # Handle the bool option first
        if self.inputtype is bool:
            for ielem, elem in enumerate(self.ctrlelem):
                if 'activewhen' in elem:
                    criteria  = elem['activewhen']
                    condition = criteria[1]
                else:
                    condition = True
                if bool(currstate)==bool(condition):
                    framestate, inputstate = 'normal', 'normal'
                else:
                    framestate, inputstate = 'disable', 'disabled'
                if elem['ctrlframe'] is not None:
                    #print("Set "+elem['frame']+" to "+framestate)
                    for child in elem['ctrlframe'].winfo_children():
                        child.configure(state=framestate)
                if elem['ctrlinput'] is not None:
                    #print("Set "+elem['input']+" to "+inputstate)
                    if isinstance(elem['ctrlinput'].tkentry, list):
                        for entry in elem['ctrlinput'].tkentry:
                            entry.config(state=inputstate)
                    else:
                        elem['ctrlinput'].tkentry.config(state=inputstate)  
        # Handle the listbox option 
        if self.inputtype == moretypes.listbox:
            # Get the current state
            #print("curr state = "+repr(currstate))
            for ielem, elem in enumerate(self.ctrlelem):
                criteria  = elem['activewhen']
                optiontest= criteria[0]
                condition = criteria[1]
                #print("testing "+optiontest+" "+repr(condition))
                if (optiontest in currstate) == bool(condition):
                    # Passes test, let's activate/deactivate
                    framestate, inputstate = 'normal', 'normal'
                else:
                    framestate, inputstate = 'disable', 'disabled'
                if elem['ctrlframe'] is not None:
                    #print("Set "+elem['frame']+" to "+framestate)
                    for child in elem['ctrlframe'].winfo_children():
                        child.configure(state=framestate)
                if elem['ctrlinput'] is not None:
                    #print("Set "+elem['input']+" to "+inputstate)
                    if isinstance(elem['ctrlinput'].tkentry, list):
                        for entry in elem['ctrlinput'].tkentry:
                            entry.config(state=inputstate)
                    else:
                        elem['ctrlinput'].tkentry.config(state=inputstate)
        return

    def linkctrlelem(self, allframes, allinputs):
        """
        Link the ctrl elements to the frames/inputs to control
        """
        for ielem, elem in enumerate(self.ctrlelem):
            #print(self.name)
            # Attach it to the right thing
            if 'frame' in elem:
                self.ctrlelem[ielem]['ctrlframe'] = allframes[elem['frame']]
                self.ctrlelem[ielem]['ctrlinput'] = None
            elif 'input' in elem:
                self.ctrlelem[ielem]['ctrlframe'] = None
                self.ctrlelem[ielem]['ctrlinput'] = allinputs[elem['input']]
            else:
                print("Invalid ctrlelem specification in "+self.name)
        return
    
    @classmethod
    def fromdict(cls, frame, d, allframes=None, allinputs=None): 
        # Parse the dict
        name                        = d['name']
        row        = getdictval(d, 'row',        None)
        label      = getdictval(d, 'label',      '')
        defaultval = getdictval(d, 'defaultval', None)
        optionlist = getdictval(d, 'optionlist', [])
        labelonly  = getdictval(d, 'labelonly',  False)
        visible    = getdictval(d, 'visible',    True)
        # Set the control frame (for booleans)
        ctrlframe = None
        if ('ctrlframe' in d) and (allframes is not None):
            ctrlframe = allframes[d['ctrlframe']]
        ctrlelem      = getdictval(d, 'ctrlelem',   None)
        yamlinputtype = getdictval(d, 'inputtype', 'str')
        if isinstance(yamlinputtype, list):
            inputtype = [typemap[x.lower()] for x in yamlinputtype]
        else:
            inputtype = typemap[yamlinputtype.lower()]
        mergedboollist = getdictval(d, 'mergedboollist', [])
        outputdef  = getdictval(d, 'outputdef', {})
        listboxopt = getdictval(d, 'listboxopt', {})
        fileopenopt= getdictval(d, 'fileopenopt', {})
        # Return the widget
        return cls(frame, row, inputtype, name, label,
                   defaultval=defaultval, optionlist=optionlist,
                   listboxopt=listboxopt, fileopenopt=fileopenopt,
                   ctrlframe=ctrlframe,   ctrlelem=ctrlelem,
                   labelonly=labelonly,
                   outputdef=outputdef, mergedboollist=mergedboollist,
                   allinputs=allinputs, visible=visible)
# -- Done inputwidget --

class popupwindow(Tk.Toplevel, object):
    """
    Creates a pop-up window
    """
    def __init__(self, parent, master, defdict, stored_inputvars, initnew=True):
        self.master = master
        super(popupwindow, self).__init__(parent)

        if 'title' in defdict: self.wm_title(defdict['title'])

        self.stored_inputvars=stored_inputvars
        if not stored_inputvars:
            # Initialize the values
            for widget in defdict['inputwidgets']:
                self.stored_inputvars[widget['name']] = widget['defaultval']

        # populate the window
        self.temp_inputvars = OrderedDict()
        for widget in defdict['inputwidgets']:
            widgetcopy = widget.copy()
            name       = widgetcopy['name']
            widgetcopy['defaultval'] = self.stored_inputvars[name]
            iwidget = inputwidget.fromdict(self, widgetcopy,
                                           allinputs=self.temp_inputvars)
            self.temp_inputvars[name] = iwidget
        # link any widgets necessary
        for key,  inputvar in self.temp_inputvars.items():
            if self.temp_inputvars[key].ctrlelem is not None:
                self.temp_inputvars[key].linkctrlelem(None, self.temp_inputvars)
                self.temp_inputvars[key].onoffctrlelem(None)

        # Add the save button
        row, col = self.grid_size()
        Tk.Button(self,text='Save',command=self.savevals).grid(row=row,column=0)
        # Add the close button
        Tk.Button(self,text='Close',command=self.okclose).grid(row=row,column=1)

    def savevals(self):
        for key, widget in self.stored_inputvars.items():
            val = self.temp_inputvars[key].getval()
            self.stored_inputvars[key] = val

    def okclose(self):
        self.savevals()
        self.destroy()

    def printvals(self):
        for key, widget in self.stored_inputvars.items():
            val = self.stored_inputvars[key]
            print(key+" "+repr(val))
        return

# -- Done popupwindow --

def donothing(toproot):
    filewin = Tk.Toplevel(toproot)
    button = Tk.Button(filewin, text="Do nothing button")
    button.pack()

def pullvals(inputs, statuslabel=None):
    for key, inp in inputs.items():
        if inp.labelonly is False:
            val = inp.getval()
            # if inp.inputtype is moretypes.mergedboollist:
            #     val = getMergedBoollist(inp, inputs)
            # else:
            #     val = inp.getval()
            print(inp.name+' '+repr(val))
    if statuslabel is not None: statuslabel.config(text='Pulled values')
    print("--- pulled values ---")
    return

# def dummyMenu(root):
#     """ 
#     Adds a menu bar to root
#     See https://www.tutorialspoint.com/python/tk_menu.htm
#     """
#     menubar  = Tk.Menu(root)

#     # File menu
#     filemenu = Tk.Menu(menubar, tearoff=0)
#     filemenu.add_command(label="New", command=partial(donothing, root))
#     filemenu.add_command(label="Open", command=partial(donothing, root))
#     filemenu.add_command(label="Save", command=partial(donothing, root))
#     filemenu.add_command(label="Save as...", command=partial(donothing, root))
#     filemenu.add_command(label="Close", command=partial(donothing, root))
#     filemenu.add_separator()
#     filemenu.add_command(label="Exit", command=root.quit)
#     menubar.add_cascade(label="File", menu=filemenu)

#     # Help menu
#     helpmenu = Tk.Menu(menubar, tearoff=0)
#     helpmenu.add_command(label="Help Index", command=partial(donothing, root))
#     helpmenu.add_command(label="About...", command=partial(donothing, root))
#     menubar.add_cascade(label="Help", menu=helpmenu)

#     root.config(menu=menubar)


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
    """
    Creates a Tk app which loads the configuration from a yaml file
    """
    def __init__(self, menufunc=None, configyaml='default.yaml', 
                 title='TK Yaml GUI', leftframew=525,
                 *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)

        self.leftframew = leftframew
        self.wm_title(title)
        self.geometry("1050x575")
        # Set up the menu bar
        if menufunc is not None:   menufunc(self)
        else:                      self.menubar(self)

        # Set up the status bar
        self.statusbar = Tk.Label(self, text="%200s"%" ", 
                                  bd=1, relief=Tk.SUNKEN, anchor=Tk.W)
        self.statusbar.grid(row=1, columnspan=2, sticky='w')

        # Get the drawing window
        self.center = Tk.Frame(self, width=leftframew, height=500)
        self.center.grid(row=0, column=1, sticky='nsew')
        self.dpi=100
        self.fig = Figure(figsize=(leftframew/self.dpi, 500/self.dpi),
                          dpi=self.dpi, facecolor='white')
        #t   = np.arange(0, 3, .01)
        #self.fig.add_subplot(111).plot(t, 2 * np.sin(2 * np.pi * t))
        self.figcanvas = FigureCanvasTkAgg(self.fig, master=self.center)  # A tk.DrawingArea.
        self.figcanvas.draw()
        # Add toolbar to figcanvas
        self.toolbar = NavigationToolbar2TkAgg(self.figcanvas, self.center)
        self.toolbar.update()
        self.toolbar.grid(row=1, column=0, sticky='nsew')
        #toolbar.pack(side=Tk.BOTTOM, fill=Tk.X, expand=1)
        #self.figcanvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1
        self.figcanvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')

        # The input frame is leftframe
        self.leftframe=Tk.Frame(self, width=leftframew)
        self.leftframe.grid(row=0, column=0, sticky='nsew')
        self.leftframe.grid_propagate(0)

        # Load the yaml input file
        with open(configyaml) as fp:
            if useruemel: Loader=yaml.load
            else:         Loader=yaml.safe_load
            yamldict = Loader(fp)
        self.yamldict=yamldict

        # -- Set up the tabs --
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
                                           allframes=self.subframes,
                                           allinputs=self.inputvars)
            self.inputvars[name] = iwidget
        # link any widgets necessary
        for key,  inputvar in self.inputvars.items():
            if self.inputvars[key].ctrlelem is not None:
                self.inputvars[key].linkctrlelem(self.subframes, self.inputvars)
                self.inputvars[key].onoffctrlelem(None)

        self.puwindict={}

        # -- Set up the buttons --
        if 'buttons' in yamldict:
            for button in yamldict['buttons']:
                frame = self.tabframeselector(button)
                text  = button['text']
                cmdstr= button['command']
                if 'col' in button: col=button['col']
                else:               col=0
                b  = Tk.Button(master=frame,text=text,command=eval(cmdstr))
                if 'row' in button:
                    b.grid(row=button['row'], column=col, padx=5, sticky='w')
                else:
                    b.grid(column=col, padx=5, sticky='w')
        
        # -- Button demonstrating pullvals --
        # button = Tk.Button(master=self.notebook.tab('Tab 1'),text="Pullvals", 
        #                    command=partial(pullvals, self.inputvars, 
        #                                    statuslabel=self.statusbar))
        # button.grid(column=0, padx=5, sticky='w')
        
        # -- Button demonstrating update plots --        
        #button = Tk.Button(master=self.notebook.tab('Tab 1'),text="update plt", 
        #                  command=self.updateplot).grid(column=0, padx=5, sticky='w')
        #self.inputvars['mergedbool1'].setval('off1 off2 off3', strinput=True)
        #self.inputvars['input_2'].setval([-143, -3.1, "stuffA"])
        #print(self.getoutputdefdict('AMR-Wind'))
        #print(self.setinputfromdict('AMR-Wind', yamldict['setfromdict']))
        #self.setuppopupwin(yamldict['popupwindow']['popup1'])
        #puwin=popupwindow(self, yamldict['popupwindow']['popup1'], self.puwindict)
        #puwin.printvals()
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

    def mirrorinputs(self, source, target):
        # Get the input 
        val=self.inputvars[source].getval()
        self.inputvars[target].setval(val)

    def getoutputdefdict(self, tag, allinputs=None):
        tagdict = OrderedDict()
        if allinputs is None:
            allinputs=self.inputvars
        for key, inputvar in allinputs.items():
            if tag in inputvar.outputdef:
                outputkey = inputvar.outputdef[tag]
                tagdict[outputkey] = allinputs[key]
        return tagdict

    def setinputfromdict(self, tag, inputdict):
        extradict=inputdict.copy()
        # Get the dictionary
        tagdict = self.getoutputdefdict(tag)
        for key, item in inputdict.items():
            if key in tagdict:
                tagdict[key].setval(item, 
                                    strinput=isinstance(item,str),
                                    forcechange=True)
                extradict.pop(key)
        return extradict  # Return any unused entries
    
    def updateplot(self):
        input1=self.inputvars['input_1'].getval()
        w,h1 = self.winfo_width(), self.winfo_height()
        canvaswidget=self.figcanvas.get_tk_widget()
        cw, ch = canvaswidget.winfo_width(), canvaswidget.winfo_height()
        canvaswidget.configure(width=w-self.leftframew-10, height=h1-75)
        self.fig.clf()
        ax=self.fig.add_subplot(111)
        ax.clear()
        t   = np.arange(0, 3, .01)
        ax.plot(t, t+input1)
        ax.set_title('replot i='+repr(input1))
        #self.figcanvas.draw()
        #self.figcanvas.show()
        return

    def menubar(self, root):
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
        return


    def printpuwindict(self):
        print(self.puwindict)

    def popupwin(self):
        popupwindow(self, self,  self.yamldict['popupwindow']['popup1'], 
                    self.puwindict)

    
if __name__ == "__main__":
    App().mainloop()
