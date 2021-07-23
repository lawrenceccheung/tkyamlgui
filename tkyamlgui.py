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
    import collections as collectionsabc
else:
    import tkinter as Tk
    from tkinter import ttk
    from tkinter import filedialog as filedialog
    from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as NavigationToolbar2TkAgg
    import collections.abc as collectionsabc

try:
    import ruamel.yaml as yaml
    #print("# Loaded ruamel.yaml")
    useruemel=True
    try:
        yaml = yaml.YAML()
    except:
        pass
except:
    import yaml as yaml
    #print("# Loaded yaml")
    useruemel=False
#if useruemel: yaml = yaml.YAML()

# Helpful function for pulling things out of dicts
getdictval = lambda d, key, default: default if key not in d else d[key]

verbose = False

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
    if isinstance(bool_str, str):
        if bool_str.lower() in ['true', 't', '1']: 
            return True
        elif bool_str.lower() in ['false', 'f', '0']: 
            return False
    #if here we couldn't parse it
    raise ValueError("[%s] is not recognized as a boolean value" % bool_str)

class ToggledFrame(Tk.Frame):
    """
    Create a toggled/expandable frame
    """
    # See https://stackoverflow.com/questions/13141259/expandable-and-contracting-frame-in-tkinter
    def __init__(self, parent, text="", initstate=1, *args, **options):
        Tk.Frame.__init__(self, parent, *args, **options)

        self.show = Tk.IntVar()
        self.show.set(initstate)

        self.title_frame = ttk.LabelFrame(parent) #ttk.Frame(self)

        self.header_frame = Tk.Frame(self.title_frame)
        self.header_frame.grid(row=0, column=0, sticky='w')
        defaultwidth=20
        w=max(len(text)+2, defaultwidth)
        ttk.Label(self.header_frame, text=" "+text, width=w).grid(row=0, column=1,
                                                              sticky='w')

        self.toggle_button = ttk.Checkbutton(self.header_frame, width=5, 
                                             text='[show]', 
                                             command=self.toggle,
                                             variable=self.show, 
                                             style='Demo.TButton') #'Toolbutton')
        self.toggle_button.grid(row=0, column=0)

        self.sub_frame = Tk.Frame(self.title_frame, #relief="sunken",
                                  borderwidth=1)
        self.toggle()

    def toggle(self):
        if bool(self.show.get()):
            self.sub_frame.grid(row=1)
            self.toggle_button.configure(text='[hide]')
        else:
            self.sub_frame.grid_forget()
            self.toggle_button.configure(text='[show]')

    def setstate(self, state):
        self.show.set(state)
        self.toggle()

class VerticalScrolledFrame:
    """
    A vertically scrolled Frame that can be treated like any other Frame
    ie it needs a master and layout and it can be a master.
    :width:, :height:, :bg: are passed to the underlying Canvas
    :bg: and all other keyword arguments are passed to the inner Frame
    note that a widget layed out in this frame will have a self.master 3 layers deep,
    (outer Frame, Canvas, inner Frame) so 
    if you subclass this there is no built in way for the children to access it.
    You need to provide the controller separately.
    """
    # See https://gist.github.com/novel-yet-trivial/3eddfce704db3082e38c84664fc1fdf8
    def __init__(self, master, extraconfigfunc=None, **kwargs):
        width = kwargs.pop('width', None)
        height = kwargs.pop('height', None)
        bg = kwargs.pop('bg', kwargs.pop('background', None))
        self.outer = Tk.Frame(master, **kwargs)
        self.extraconfigfunc = extraconfigfunc;

        self.vsb = Tk.Scrollbar(self.outer, orient=Tk.VERTICAL)
        self.vsb.pack(fill=Tk.Y, side=Tk.RIGHT)
        self.canvas = Tk.Canvas(self.outer, highlightthickness=0, width=width, height=height, bg=bg)
        self.canvas.pack(side=Tk.LEFT, fill=Tk.BOTH, expand=True)
        self.canvas['yscrollcommand'] = self.vsb.set
        # mouse scroll does not seem to work with just "bind"; You have
        # to use "bind_all". Therefore to use multiple windows you have
        # to bind_all in the current widget
        self.canvas.bind("<Enter>", self._bind_mouse)
        self.canvas.bind("<Leave>", self._unbind_mouse)
        self.vsb['command'] = self.canvas.yview

        self.inner = Tk.Frame(self.canvas, bg=bg)
        # pack the inner Frame into the Canvas with the topleft corner 4 pixels offset
        self.canvas.create_window(4, 4, window=self.inner, anchor='nw')
        self.inner.bind("<Configure>", self._on_frame_configure)

        self.outer_attr = set(dir(Tk.Widget))

    def __getattr__(self, item):
        if item in self.outer_attr:
            # geometry attributes etc (eg pack, destroy, tkraise) are passed on to self.outer
            return getattr(self.outer, item)
        else:
            # all other attributes (_w, children, etc) are passed to self.inner
            return getattr(self.inner, item)

    def _on_frame_configure(self, event=None):
        x1, y1, x2, y2 = self.canvas.bbox("all")
        height = self.canvas.winfo_height()
        try:
            self.canvas.config(scrollregion = (0,0, x2, max(y2, height)))
            if self.extraconfigfunc is not None:
                self.extraconfigfunc()
        except:
            pass

    def _bind_mouse(self, event=None):
        self.canvas.bind_all("<4>", self._on_mousewheel)
        self.canvas.bind_all("<5>", self._on_mousewheel)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mouse(self, event=None):
        self.canvas.unbind_all("<4>")
        self.canvas.unbind_all("<5>")
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        """Linux uses event.num; Windows / Mac uses event.delta"""
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units" )
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units" )

    def __str__(self):
        return str(self.outer)

#
# See https://stackoverflow.com/questions/58045626/scrollbar-in-tkinter-notebook-frames
class YScrolledFrame(Tk.Frame, object):
    def __init__(self, parent, canvaswidth=500,canvasheight=500,*args,**kwargs):
        super(YScrolledFrame, self).__init__(parent, *args, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas = canvas = Tk.Canvas(self, relief='raised', 
                                         width=canvaswidth, height=canvasheight)
        canvas.grid(row=0, column=0, sticky='nsew')

        scroll = Tk.Scrollbar(self, command=canvas.yview, orient=Tk.VERTICAL)
        canvas.config(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky='nsew')
        self.yscroll = scroll

        self.content = Tk.Frame(canvas)
        self.window = self.canvas.create_window(0, 0, window=self.content, anchor="nw")

        self.canvas.bind('<Configure>', self.on_configure)
        self.content.bind('<Configure>', self.reset_scrollregion)
        
    def on_configure(self, event):
        bbox = self.content.bbox('ALL')
        self.canvas.config(scrollregion=bbox)

    def reset_scrollregion(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def onCanvasConfigure(self, event):
        #Resize the inner frame to match the canvas
        minWidth = self.content.winfo_reqwidth()
        minHeight = self.content.winfo_reqheight()

        newWidth = self.winfo_width()
        newHeight = event.height
        #self.canvas.itemconfig(self.window, height=minHeight)
        self.config(width=newWidth, height=newHeight)
        bbox = self.content.bbox('ALL')
        self.canvas.config(scrollregion=bbox)


class Notebook(ttk.Notebook, object):
    def __init__(self, parent, tab_labels, canvaswidth=500, canvasheight=500):
        super(Notebook, self).__init__(parent)

        self._tab = {}
        for text in tab_labels:
            #self._tab[text] = YScrolledFrame(self, canvaswidth=canvaswidth)
            self._tab[text] = VerticalScrolledFrame(self, 
                                                    width=canvaswidth, 
                                                    height=canvasheight)
            self._tab[text].pack(fill=Tk.BOTH, expand=True)
            # layout by .add defaults to fill=Tk.BOTH, expand=True
            self.add(self._tab[text], text=text, compound=Tk.TOP)

    def tab(self, key):
        return self._tab[key] #.content

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

class ToolTip(object):
    """
    Creates a mouse-over tool tip show additional context
    """
    # See https://stackoverflow.com/questions/20399243/display-message-when-hovering-over-something-with-mouse-cursor-in-python
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() +27
        self.tipwindow = tw = Tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = Tk.Label(tw, text=self.text, justify=Tk.LEFT,
                         background="#ffffe0", relief=Tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def CreateToolTip(widget, text):
    """
    Binds a ToolTip to widget with text
    """
    toolTip = ToolTip(widget)
    def enter(event):
        toolTip.showtip(text)
    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)

class inputwidget:
    """
    Creates a general-purpose widget for input 
    """
    def __init__(self, frame, row, inputtype, name, label,
                 parent=None,
                 defaultval=None, optionlist=[], 
                 listboxopt={},  fileopenopt={},
                 ctrlframe=None, ctrlelem=None,
                 labelonly=False, visible=True, entryopt={},
                 outputdef={}, mergedboollist=[], allinputs=None):
        defaultw       = 12
        self.name      = name
        self.label     = label
        self.parent    = parent
        self.labelonly = labelonly
        self.inputtype = inputtype
        self.var       = None
        self.optionlist= optionlist
        self.listboxopt= listboxopt
        self.ctrlframe = ctrlframe
        self.ctrlelem  = ctrlelem
        self.visible   = visible
        self.outputdef = outputdef
        self.mergedboollist = mergedboollist
        self.button    = None
        self.allinputs = allinputs
        if visible:
            self.tklabel   = Tk.Label(frame, text=label) 
        else:
            self.tklabel   = None
        if 'width' not in entryopt:  entryopt['width'] = defaultw
        self.entryopt  = entryopt
        if inputtype == moretypes.mergedboollist: return

        if visible:
            cspan=3 if labelonly else 1
            if row is None:  
                self.tklabel.grid(column=0, columnspan=cspan,sticky='nw',padx=5)
            else:            
                self.tklabel.grid(row=row, columnspan=cspan,
                                  column=0, sticky='nw', padx=5)
            if 'help' in self.outputdef:
                CreateToolTip(self.tklabel, text=self.outputdef['help'])

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
            allopts = eval(optionlist) if isinstance(optionlist,str) else optionlist
            height=max(3,len(allopts))
            if 'height' not in listboxopt: listboxopt['height'] = height
            self.yscroll   = Tk.Scrollbar(frame, orient=Tk.VERTICAL)
            if visible and (row is None): row=self.tklabel.grid_info()['row']
            self.yscroll.grid(row=row, column=2, sticky=Tk.NW+Tk.S)
            self.tkentry   = Tk.Listbox(frame, #height=height,
                                        exportselection=False,
                                        yscrollcommand=self.yscroll.set, 
                                        **listboxopt) 

            for i, option in enumerate(allopts):
                self.tkentry.insert(i+1, option)
            self.yscroll['command'] = self.tkentry.yview
            # Set the default values
            if defaultval is not None:
                if not isinstance(defaultval, list): defaultval = [defaultval]
                for v in defaultval:
                    # set the value to active
                    if v in self.optionlist:
                        self.tkentry.selection_set(self.optionlist.index(v))
            if self.ctrlelem is not None:
                self.tkentry.bind("<<ListboxSelect>>", self.onoffctrlelem)
        elif (inputtype is str) and (len(optionlist)>0):
            # create a dropdown menu
            self.var       = Tk.StringVar()
            optlist = eval(optionlist) if isinstance(optionlist,str) else optionlist
            if len(optlist)==0: optlist=['']
            self.tkentry   = Tk.OptionMenu(frame, self.var, *optlist)
            #self.tkentry.config(**self.entryopt)
            if defaultval is not None: self.var.set(defaultval)
        elif (inputtype is str):
            self.var       = Tk.StringVar()
            self.tkentry   = Tk.Entry(master=frame, **self.entryopt) 
            self.tkentry.insert(0, repr(defaultval).strip("'").strip('"'))
        elif (inputtype is moretypes.filename):
            self.var       = Tk.StringVar()
            self.tkentry   = Tk.Entry(master=frame, **self.entryopt) 
            if defaultval is not None: 
                self.tkentry.insert(0, repr(defaultval).strip("'").strip('"'))
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
                self.tkentry.append(Tk.Entry(master=frame, **self.entryopt))
                if defaultval is not None:
                    self.tkentry[i].insert(0, repr(defaultval[i]).strip("'").strip('"'))
        else:
            self.tkentry   = Tk.Entry(master=frame, **self.entryopt) 
            self.tkentry.insert(0, repr(defaultval).strip("'").strip('"'))
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
            if verbose: print("getval(): Error in "+self.name)
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
                itkentry.delete(0, Tk.END)
                if i < len(listval):
                    itkentry.insert(0, repr(listval[i]).strip("'").strip('"'))
                else:
                    print("WARNING: cannot set %s entry i=%i"%(self.name, i))
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
                self.tkentry.selection_clear(0, Tk.END)
                for v in listval:
                    # set the value to active
                    allopts = eval(self.optionlist) if isinstance(self.optionlist,str) else self.optionlist
                    self.tkentry.selection_set(allopts.index(v))
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

    def isactive(self):
        if self.labelonly: return False
        if self.inputtype==moretypes.mergedboollist: return True
        if isinstance(self.tkentry, list): 
            state = self.tkentry[0].cget('state')
        else:  
            state = self.tkentry.cget('state')
        isnormalstate = (state=='normal')
        hasdata       = False
        if isnormalstate: 
            hasdata = (str(self.getval())!='')
        return (isnormalstate and hasdata)

    def choosefile(self, optiondict):
        #filewin = Tk.Toplevel()   
        selecttype = getdictval(optiondict, 'selecttype', 'open')
        kwargs     = getdictval(optiondict, 'kwargs', {})
        if 'filetypes' in kwargs:
            kwargs['filetypes'] = [(g[0], g[1]) for g in kwargs['filetypes']]
        if selecttype=='open':
            filename = filedialog.askopenfilename(initialdir = "./",
                                                  title = "Select file", 
                                                  **kwargs)
        elif selecttype=='saveas':
            filename = filedialog.asksaveasfilename(initialdir = "./",
                                                    title = "Select file",
                                                    **kwargs)
        elif selecttype=='directory':
            filename = filedialog.askdirectory(initialdir = "./",
                                               title = "Select directory",
                                               **kwargs)
        self.tkentry.delete(0, Tk.END)
        self.tkentry.insert(0, filename)
        return filename

    # DELETE THIS!  OBSOLETE!
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
                        try:    child.configure(state=framestate)
                        except: None
                if elem['ctrlinput'] is not None:
                    #print("Set "+elem['input']+" to "+inputstate)
                    if isinstance(elem['ctrlinput'].tkentry, list):
                        for entry in elem['ctrlinput'].tkentry:
                            try:    entry.config(state=inputstate)
                            except: None
                    else:
                        try: elem['ctrlinput'].tkentry.config(state=inputstate)
                        except: None
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
                        try:    child.configure(state=framestate)
                        except: None
                if elem['ctrlinput'] is not None:
                    #print("Set "+elem['input']+" to "+inputstate)
                    if isinstance(elem['ctrlinput'].tkentry, list):
                        for entry in elem['ctrlinput'].tkentry:
                            try:    
                                entry.config(state=inputstate)
                            except: 
                                None
                    else:
                        try: elem['ctrlinput'].tkentry.config(state=inputstate)
                        except: None
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
    def fromdict(cls, frame, d, parent=None, allframes=None, allinputs=None): 
        # Parse the dict
        name       = d['name']
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
        entryopt   = getdictval(d, 'entryopt', {})

        # Return the widget
        return cls(frame, row, inputtype, name, label, parent=parent,
                   defaultval=defaultval, optionlist=optionlist,
                   listboxopt=listboxopt, fileopenopt=fileopenopt,
                   ctrlframe=ctrlframe,   ctrlelem=ctrlelem,
                   labelonly=labelonly,   entryopt=entryopt,
                   outputdef=outputdef, mergedboollist=mergedboollist,
                   allinputs=allinputs, visible=visible)
# -- Done inputwidget --

class popupwindow(Tk.Toplevel, object):
    """
    Creates a pop-up window
    """
    def __init__(self, parent, master, defdict, stored_inputvars, 
                 extraclosefunc=None, savebutton=True, 
                 savebtxt='Save', closebtxt='Close', entrynum=None,
                 quitafterinit=False, popupgui=True, hidden=False):
        self.scrollframe=scrollframe=True
        if popupgui:
            super(popupwindow, self).__init__(parent)
            if 'title' in defdict: self.wm_title(defdict['title'])
            if scrollframe:
                width  = getdictval(defdict, 'width', 500)
                height = getdictval(defdict, 'height', 500)
                self.scrolledframe = VerticalScrolledFrame(self, 
                                                           width=width,
                                                           height=height)
                self.scrolledframe.pack(fill=Tk.BOTH, expand=True) # fill window


        self.parent = parent
        self.master = master
        self.extraclosefunc = extraclosefunc
        self.datakeyname    = getdictval(defdict, 'datakeyname', None)
        self.stored_inputvars=stored_inputvars

        self.drawframe = self
        if scrollframe and popupgui:
            self.drawframe = self.scrolledframe

        # Initialize the values if stored_inputvars is empty
        if not stored_inputvars:
            for widget in defdict['inputwidgets']:
                if getdictval(widget, 'labelonly', False) == False:
                    self.stored_inputvars[widget['name']] = widget['defaultval']
        if quitafterinit: return
        if popupgui==False: print("Initiating no gui")
        if hidden: self.withdraw()

        # Add some frames to the pop-up window
        self.popup_subframes     = OrderedDict()
        self.popup_toggledframes = OrderedDict()
        if 'frames' in defdict:
            for frame in defdict['frames']:
                toggled = True if (('toggled' in frame) and frame['toggled']) else False
                name = frame['name']
                if toggled:
                    title = '' if ('title' not in frame) else frame['title']
                    state = 0 if ('initstate' not in frame) else frame['initstate']
                    self.popup_toggledframes[name] = ToggledFrame(self.drawframe,
                                                            text=title, 
                                                            relief="raised", 
                                                            initstate=state,
                                                            borderwidth=1)
                    self.popup_subframes[name] = self.popup_toggledframes[name].sub_frame
                    subframelayout = self.popup_toggledframes[name].title_frame
                else:
                    self.popup_subframes[name] = Tk.LabelFrame(self.drawframe)
                    subframelayout = self.popup_subframes[name]
                # Put frame on grid
                kwargs = {}
                if 'row' in frame: kwargs['row'] = frame['row']
                subframelayout.grid(column=0, padx=10,pady=10, 
                                    columnspan=4, sticky='w',
                                    **kwargs)
                if ('title' in frame) and (not toggled):
                    Tk.Label(self.popup_subframes[name], 
                             text=frame['title']).grid(row=0, column=0, 
                                                       columnspan=4,
                                                       sticky='w')
        
        # populate the window
        self.temp_inputvars = OrderedDict()
        for widget in defdict['inputwidgets']:
            widgetcopy = widget.copy()
            name       = widgetcopy['name']
            #widgetcopy['visible']    = popupgui
            if getdictval(widget, 'labelonly', False) is False: 
                widgetcopy['defaultval'] = self.stored_inputvars[name]
            widgetframe = getdictval(widget, 'frame', None)
            targetframe = self.drawframe if widgetframe is None else self.popup_subframes[widgetframe]
            iwidget = inputwidget.fromdict(targetframe, #self.drawframe, 
                                           widgetcopy, parent=parent,
                                           allinputs=self.temp_inputvars)
            self.temp_inputvars[name] = iwidget
        # link any widgets necessary
        for key,  inputvar in self.temp_inputvars.items():
            if self.temp_inputvars[key].ctrlelem is not None:
                self.temp_inputvars[key].linkctrlelem(None, self.temp_inputvars)
                self.temp_inputvars[key].onoffctrlelem(None)

        # Append an entry number to name (if necessary)
        if entrynum is not None:
            name=self.temp_inputvars[self.datakeyname].getval()
            self.temp_inputvars[self.datakeyname].setval(name+repr(entrynum))
        
        if popupgui:
        # -- Set up the buttons --
            Nbuttons = 0
            if 'buttons' in defdict:
                Nbuttons = len(defdict['buttons'])
                for button in defdict['buttons']:
                    text  = button['text']
                    cmdstr= button['command']
                    col   = getdictval(button, 'col', 0)
                    widgetframe = getdictval(button, 'frame', None)
                    targetframe = self.drawframe if widgetframe is None else self.popup_subframes[widgetframe]
                    b  = Tk.Button(master=targetframe, #self.drawframe,
                                   text=text,command=eval(cmdstr))
                    if 'row' in button:
                        b.grid(row=button['row'], column=col,padx=5,sticky='w')
                    else:
                        b.grid(column=col, padx=5, sticky='w')

            # Add the save button
            row = len(defdict['inputwidgets'])+Nbuttons+1  #row+3
            col=0
            if savebutton:
                Tk.Button(self.drawframe,
                          text=savebtxt,command=self.savevals).grid(row=row, column=0)
            col=1
            # Add the close button
            Tk.Button(self.drawframe,
                      text=closebtxt, command=self.okclose).grid(row=row, column=col)
            # col_count, row_count = self.drawframe.grid_size()
            # for n in range(row_count): 
            #     self.drawframe.grid_rowconfigure(n, minsize=25, weight=1) 

            for key, frame in self.popup_subframes.items():
                col_count, row_count = frame.grid_size()
                #print('key = %s col = %i row = %i'%(key, col_count, row_count))
                for n in range(row_count):
                    frame.grid_rowconfigure(n, minsize=15, weight=1)
        return

    def savevals(self):
        for key, widget in self.stored_inputvars.items():
            val = self.temp_inputvars[key].getval()
            self.stored_inputvars[key] = val
        if self.datakeyname is not None:
            return self.stored_inputvars[self.datakeyname]
        else:
            return None

    def okclose(self):
        dataname=self.savevals()
        if self.extraclosefunc is not None:
            # Call this function to validate data or other stuff
            self.extraclosefunc()
        self.destroy()

    def printvals(self):
        for key, widget in self.stored_inputvars.items():
            val = self.stored_inputvars[key]
            print(key+" "+repr(val))
        return

    def savethenexec(self, cmdstr):
        self.savevals()
        eval(cmdstr)
        return

# -- Done popupwindow --


class listboxpopupwindows():
    """
    Creates a widget for editing a list of pop-up windows
    """
    def __init__(self, parent, frame, listboxdict, popupwindict):
        self.parent     = parent
        self.frame      = frame
        self.popupwindict=popupwindict.copy()
        self.height     = getdictval(listboxdict, 'height', 4)
        self.row        = getdictval(listboxdict, 'row',    None)
        self.listboxopt = getdictval(listboxdict, 'listboxopt', {})
        self.label      = getdictval(listboxdict, 'label', 'Label')
        self.editsavebutton = getdictval(listboxdict, 'editsavebutton', True)
        self.closebuttontxt = getdictval(listboxdict, 'closebuttontxt', 'Save & Close')
        self.tklabel    = Tk.Label(frame, text=self.label)
        self.yscroll    = Tk.Scrollbar(frame, orient=Tk.VERTICAL)
        self.tkentry    = Tk.Listbox(self.frame, height=self.height,
                                     exportselection=False,
                                     yscrollcommand=self.yscroll.set,  
                                     **self.listboxopt) 
        self.listboxdict= listboxdict.copy()
        self.alldataentries = OrderedDict()

        self.yscroll['command'] = self.tkentry.yview

        # Add the objects
        if self.row is None:  row, col = frame.grid_size()
        else:                 row = self.row
        self.yscroll.grid(row=row, column=2, sticky=Tk.NW+Tk.S)
        self.tklabel.grid(row=row, column=0, sticky='nw', padx=5)
        self.tkentry.grid(row=row, column=1, sticky='w')
        
        # Add the buttons
        newb  = Tk.Button(master=self.frame, text='New',   command=self.new)
        editb = Tk.Button(master=self.frame, text='Edit',  command=self.edit)
        delb  = Tk.Button(master=self.frame, text='Delete',command=self.remove)
        newb.grid(row=row+1,  column=0)
        editb.grid(row=row+1, column=1)
        delb.grid(row=row+1,  column=2)

    def insertdata(self, storeddata, forcechange=False):
        Ndata = len(self.alldataentries)+1
        datakeyname = getdictval(self.popupwindict, 'datakeyname', None)
        entryname = repr(Ndata) if datakeyname is None else storeddata[datakeyname]
        # Check initial state
        prevstate = self.tkentry.cget('state')
        statedisabled=self.tkentry.cget('state') in ['disable','disabled']
        if statedisabled and forcechange: self.tkentry.config(state='normal') 

        # Add the entry to the data
        # TODO: Should check the name to make sure it's not a duplicate
        self.tkentry.insert(Tk.END, entryname)
        self.alldataentries[entryname] = storeddata.copy()

        # Reset state if necessary
        if statedisabled and forcechange: self.tkentry.config(state=prevstate) 

    def getdefaultdict(self):
        """Returns the default dictionary which can be edited and used to
        populate additional entries.
        """
        defaultdict = OrderedDict()
        for item in self.popupwindict['inputwidgets']:
            if ('labelonly' in item) and  (item['labelonly'] is True):
                continue
            defaultdict[item['name']] = item['defaultval']
        return defaultdict

    def populatefromdict(self, fromdict, deleteprevious=True, 
                         verbose=False, forcechange=False):
        if deleteprevious: 
            self.tkentry.delete(0, Tk.END)
            self.alldataentries.clear()
        for itemkey, itemdict in fromdict.items():
            #print(itemkey)
            # First initialize a default data set
            storeddata = OrderedDict()
            #popupwindow(self.frame, self.frame, self.popupwindict, storeddata,
            popupwindow(self.parent, self.frame, self.popupwindict, storeddata,
                        savebutton=False, quitafterinit=True, popupgui=False)
            # Then customize entry with stuff from item
            for key, item in itemdict.items():
                if verbose: print('%s: %s'%(key, repr(item)))
                storeddata[key] = item
            #if verbose: print(storeddata)
            self.insertdata(storeddata, forcechange=forcechange)
        self.rebuildlist()
        return

    def rebuildlist(self):
        itemlist = [key for key, item in self.alldataentries.items()]
        self.tkentry.delete(0, Tk.END)
        for item in itemlist: self.tkentry.insert(Tk.END, item)

    def checknamechange(self):
        datakeyname = getdictval(self.popupwindict, 'datakeyname', None)
        if datakeyname is None: return
        namechanges=[]
        for key, item in self.alldataentries.items():
            if (key != item[datakeyname]): namechanges.append(key)
        # Do the name changes
        # in future for ordered dicts, maybe try 
        # https://stackoverflow.com/questions/16475384/rename-a-dictionary-key
        if len(namechanges)>0:
            for name in namechanges:
                newname = self.alldataentries[name][datakeyname]
                self.alldataentries[newname] = self.alldataentries.pop(name)
            self.rebuildlist()

    def new(self):
        """Create a new input window entry"""
        storeddata = OrderedDict()
        #popupwindow(self.frame, self.frame, self.popupwindict, storeddata,
        popupwindow(self.parent, self.frame, self.popupwindict, storeddata,
                    savebutton=False, closebtxt=self.closebuttontxt, 
                    entrynum=len(self.alldataentries),
                    extraclosefunc=partial(self.insertdata, storeddata))
        return

    def edit(self):
        """Edit an entry in the list box"""
        # Get the currently highlighted entry
        selected   = tkextractval(moretypes.listbox, None, self.tkentry)
        if len(selected)<1: 
            print("No items to edit")
            return
        storeddata = self.alldataentries[selected[0]]
        #p=popupwindow(self.frame, self.frame, self.popupwindict, storeddata,
        p=popupwindow(self.parent, self.frame, self.popupwindict, storeddata,
                      savebutton=self.editsavebutton,
                      closebtxt=self.closebuttontxt,
                      extraclosefunc=self.checknamechange)
        #for key, data in p.temp_inputvars.items(): print("edit key %s"%key)
        return

    def remove(self):
        selected   = tkextractval(moretypes.listbox, None, self.tkentry)
        if len(selected)<1: 
            print("No items to delete")
            return
        for selitem in selected: 
            self.alldataentries.pop(selitem)
        self.rebuildlist()
        return
    
    def getitemlist(self):
        return [key for key, item in self.alldataentries.items()]

    def dumpdict(self, tag, subset=[], onlyactive=True, keyfunc=None):
        sep = '.'
        output = OrderedDict()
        # Get a list of all entries
        #itemlist = [key for key, item in self.alldataentries.items()]
        itemlist = self.getitemlist()
        if len(itemlist)<1: return output
        if 'outputprefix' in self.listboxdict:
            outputpre  = getdictval(self.listboxdict['outputprefix'], tag, '')
        if 'outputlist' in self.listboxdict:
            outputlist = getdictval(self.listboxdict['outputlist'], tag, '')
            key = outputpre + sep + outputlist
            output[key] = ' '.join([str(elem) for elem in itemlist])
        if len(subset)>0: 
            loopsubset = {key:self.alldataentries[key] for key in subset}
        else: 
            loopsubset = self.alldataentries
        #for key, storeddata in self.alldataentries.items(): 
        for key, storeddata in loopsubset.items(): 
            #p=popupwindow(self.frame, self.frame, self.popupwindict,storeddata,
            p=popupwindow(self.parent, self.frame, self.popupwindict,storeddata,
                          hidden=True)
            for k, data in p.temp_inputvars.items(): 
                if data.isactive() and onlyactive:
                    if tag in data.outputdef:
                        if keyfunc is None:
                            storekey = key+'.'+data.outputdef[tag]
                        else:
                            storekey = keyfunc(key, self.listboxdict, data)
                        output[storekey] = data.getval()
                    #print("dump key %s"%key+" "+repr(data.getval()))
            p.destroy()
        return output
# -- Done listofpopupwindows --

class messagewindow():
    def __init__(self, toproot, mesg, autowidth=True, height=5, 
                 title='', activetext=False):
        width=len(max(mesg.split("\n"), key = len)) if autowidth else 40
        self.mesgwin     = Tk.Toplevel(toproot)
        if len(title)>0: self.mesgwin.wm_title(title)
        self.text_widget = Tk.Text(self.mesgwin, height=height, width=width)
        self.scroll_bar  = Tk.Scrollbar(self.mesgwin,
                                        command=self.text_widget.yview,
                                        orient="vertical")
        self.scroll_bar.grid(row=0, column=1, sticky="ns")
        self.text_widget.grid(row=0, column=0)
        self.text_widget.configure(yscrollcommand=self.scroll_bar.set)
        self.text_widget.insert(Tk.END, mesg)
        if not activetext:
            self.text_widget.configure(state='disabled', bg='light gray')
        self.button = Tk.Button(self.mesgwin, command=self.quit, text="Close")
        self.button.grid(row=1)

    def quit(self):
        self.mesgwin.destroy()
        
def donothing(toproot):
    filewin = Tk.Toplevel(toproot)
    button = Tk.Button(filewin, text="Do nothing button")
    button.pack()

def pullvals(inputs, statuslabel=None):
    for key, inp in inputs.items():
        if inp.labelonly is False:
            val = inp.getval()
            print(inp.name+' '+repr(val))
    if statuslabel is not None: statuslabel.config(text='Pulled values')
    print("--- pulled values ---")
    return


def listindexwithkey(dictlist, keyval, searchkey='name'):
    """
    Finds the index of item with searchkey=keyval in list dictlist
    """
    for i, item in enumerate(dictlist):
        if item[searchkey]==keyval: return i
    return None

def update(d, u, searchkey='name'):
    """
    Updates a dict
    """
    # See https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth

    # Empty dict, just return
    if u is None: 
        return d

    # Loop through items
    for k, v in u.items():
        if isinstance(v, list):
            # Update this a list item
            if k not in d:
                # New list, add it
                d[k] = v
            else:
                # Update the list items
                for vi in v:
                    if searchkey in vi:
                        # list of dicts
                        idx = listindexwithkey(d[k], vi[searchkey], \
                                               searchkey=searchkey)
                        if idx is not None:
                            d[k][idx] = update(d[k][idx], vi)
                        else:
                            d[k].append(vi)
                    else:
                        # Handle it as a simple list
                        if vi not in d[k]: d[k].append(vi)
            pass
        elif isinstance(v, collectionsabc.Mapping):
            # -- Update the dictionary --
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d



class App(Tk.Tk, object):
    """
    Creates a Tk app which loads the configuration from a yaml file
    """
    def __init__(self, menufunc=None, configyaml='default.yaml', 
                 localconfigdir='',
                 title='TK Yaml GUI', leftframew=525, withdraw=False,
                 *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)
        if withdraw: self.withdraw()
        self.leftframew = leftframew
        self.wm_title(title)
        self.geometry("1050x625")
        # Set up the menu bar
        if menufunc is not None:   menufunc(self)
        else:                      self.menubar(self)
        self.bind("<Configure>", self.onconfigure)
        self.masterframe = VerticalScrolledFrame(self, extraconfigfunc=None)
        self.masterframe.pack(fill=Tk.BOTH, expand=True) # fill window
        # Set up the status bar
        self.statusbar = Tk.Label(self, text="%200s"%" ", 
                                  bd=1, relief=Tk.SUNKEN, anchor=Tk.W)
        # self.statusbar.grid(row=1, columnspan=2, sticky='w')

        # Get the drawing window
        self.center = Tk.Frame(self.masterframe, width=leftframew, height=500)
        #self.center.grid(row=0, column=1, sticky='nsew')
        self.center.pack(side=Tk.RIGHT, fill=Tk.BOTH, expand=True)
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
        self.leftframeh = 580 # 530
        self.leftframe=Tk.Frame(self.masterframe, width=leftframew) #530
        self.leftframe.pack(side=Tk.LEFT, fill=Tk.BOTH, expand=True)
        #self.leftframe=Tk.Frame(self.masterframe, width=leftframew, height=530) #530
        #self.leftframe.grid(row=0, column=0, sticky='nsew')
        #self.leftframe.grid_propagate(0)

        # Load the yaml input file
        with open(configyaml) as fp:
            if useruemel: Loader=yaml.load
            else:         Loader=yaml.safe_load
            yamldict = Loader(fp)

        # Load any additional local yaml configuration 
        if os.path.exists(localconfigdir):
            for fname in os.listdir(localconfigdir):
                # Load only "real modules"
                if not fname.startswith('.') and \
                   not fname.startswith('__') and fname.endswith('.yaml'):
                    loadfile = os.path.join(localconfigdir, fname)
                    updatedict = Loader(open(loadfile))
                    #print("Updating with "+loadfile)
                    yamldict = update(yamldict, updatedict)
        # save yamldict
        self.yamldict=yamldict

        # -- Set up the tabs --
        self.alltabslist = yamldict['tabs']
        self.notebook = Notebook(self.leftframe, self.alltabslist, canvasheight=self.leftframeh)
        self.notebook.pack(side=Tk.LEFT, fill=Tk.BOTH, expand=True)
        #self.notebook.grid(row=0, column=0, sticky='nsew')

        # -- Set up the frames --
        self.subframes = OrderedDict()
        self.toggledframes = OrderedDict()
        if 'frames' in yamldict:
            for frame in yamldict['frames']:
                name = frame['name']
                tab  = self.notebook.tab(frame['tab'])
                toggled = True if (('toggled' in frame) and frame['toggled']) else False
                if toggled:
                    title = '' if ('title' not in frame) else frame['title']
                    state = 0 if ('initstate' not in frame) else frame['initstate']
                    self.toggledframes[name] = ToggledFrame(tab, text=title, 
                                                            relief="raised", 
                                                            initstate=state,
                                                            borderwidth=1)
                    self.subframes[name] = self.toggledframes[name].sub_frame
                    subframelayout = self.toggledframes[name].title_frame
                else:
                    self.subframes[name] = Tk.LabelFrame(tab)
                    subframelayout = self.subframes[name]
                if 'row' in frame:
                    subframelayout.grid(column=0, row=frame['row'],
                                        padx=10,pady=10, 
                                        columnspan=4, sticky='w')
                else:
                    subframelayout.grid(column=0, padx=10,pady=10,
                                            columnspan=4, sticky='w') 
                if ('title' in frame) and (not toggled):
                    Tk.Label(subframelayout, 
                             text=frame['title']).grid(row=0, column=0, 
                                                       columnspan=4,
                                                       sticky='w')
                #print('Done with frame '+name)

        # -- Set up the input widgets --
        self.inputvars = OrderedDict()
        for widget in yamldict['inputwidgets']:
            name  = widget['name']
            frame = self.tabframeselector(widget)
            iwidget = inputwidget.fromdict(frame, widget, parent=self,
                                           allframes=self.subframes,
                                           allinputs=self.inputvars)
            self.inputvars[name] = iwidget
        
        # -- Set up the listbox pop-up windows --
        if 'listboxpopupwindows' in yamldict:
            self.listboxpopupwindict = OrderedDict()
            for listboxdict in yamldict['listboxpopupwindows']:
                frame  = self.tabframeselector(listboxdict)
                name   = listboxdict['name']
                popupdict = yamldict['popupwindow'][listboxdict['popupinput']]
                self.listboxpopupwindict[name] = listboxpopupwindows(self, frame, listboxdict, popupdict)

        # -- Initialize the startup pop-up windows --
        self.popup_storteddata = OrderedDict()
        if 'popupwindow' in yamldict:
            for key, win in yamldict['popupwindow'].items():
                if win['loadonstart'] == True:
                    self.popup_storteddata[key] = OrderedDict()
                    if withdraw: self.launchpopupwin(key, hidden=True)

        # -- Set up the buttons --
        if 'buttons' in yamldict:
            for button in yamldict['buttons']:
                frame = self.tabframeselector(button)
                text  = button['text']
                cmdstr= button['command']
                kwargs= getdictval(button, 'buttonoptions', {})
                b  = Tk.Button(master=frame, text=text, command=eval(cmdstr), 
                               **kwargs)
                # Set up the grid layout
                col = getdictval(button, 'col', 0)
                gridopts = getdictval(button, 'gridoptions',{})
                if 'row' in button:          gridopts['row'] = button['row']
                if 'sticky' not in gridopts: gridopts['sticky'] = 'w'
                if 'padx'   not in gridopts: gridopts['padx']   = 5
                b.grid(column=col, **gridopts)
                # Add a tool tip
                if 'help' in button:
                    CreateToolTip(b, button['help'])

        # link any widgets necessary
        for key,  inputvar in self.inputvars.items():
            if self.inputvars[key].ctrlelem is not None:
                self.inputvars[key].linkctrlelem(self.subframes, self.inputvars)
                self.inputvars[key].onoffctrlelem(None)

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

        # Test the list box populate command
        #listboxpopupwindict['listboxpopup1'].populatefromdict(yamldict['setlistboxfromdict']['listboxpopup1'])
        self.formatgridrows()
        return

    def tabframeselector(self, d):
        if 'frame' in d:  
            framename = d['frame'].split()
            dframe = self.subframes[framename[0]]
            if (framename[0] in self.toggledframes):
                # Return some part of toggle frame
                if (len(framename)>1) and (framename[1]=='header_frame'):
                    return self.toggledframes[framename[0]].header_frame
                else:
                    return dframe #.sub_frame
            else:
                # Just a normal frame
                return dframe #self.subframes[d['frame']]
        else:     
            # no frames, just tabs
            return self.notebook.tab(d['tab'])

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

    def onconfigure(self,event=None):
        # Clear and resize figure
        canvaswidget=self.figcanvas.get_tk_widget()
        w,h1 = self.winfo_width(), self.winfo_height()
        #print("w = %i h1 = %i"%(w, h1))
        try:
            canvaswidget.configure(width=w-self.leftframew-10, height=h1-75)
        except:
            pass
    
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

    def getInputVal(self, inp):
        if inp.labelonly is True: return None
        val = inp.getval()
        return val

    def getDictFromInputs(self, tag, onlyactive=True):
        """
        Create a dict based on tag in outputdefs
        """
        output = OrderedDict()
        for key, var in self.inputvars.items():
            if (not var.isactive()) and onlyactive: 
                #print("Skipping "+key)
                continue
            if tag in var.outputdef:
                outputkey = var.outputdef[tag]
                output[outputkey] = self.getInputVal(var)
        return output

    def getHelpFromInputs(self, outputtag, helptag, onlyactive=True):
        """
        Extract the help fields from inputs
        """
        output = OrderedDict()
        for key, var in self.inputvars.items():
            if (not var.isactive()) and onlyactive: 
                continue
            if helptag in var.outputdef:
                outputkey = var.outputdef[outputtag]
                output[outputkey] = var.outputdef[helptag]
        return output
        

    def launchpopupwin(self, key, **kwargs):
        popupwindow(self, self,  self.yamldict['popupwindow'][key], 
                    self.popup_storteddata[key], **kwargs)
        
if __name__ == "__main__":
    App().mainloop()
