# Tkyamlgui

To see the code in action, run
```bash
python tkyamlgui.py
```

To extend the code for your own use, try the following:
```python
#!/usr/bin/env python
import sys
import numpy as np
from functools import partial
import tkyamlgui as tkyg
if sys.version_info[0] < 3:
    import Tkinter as Tk
else:
    import tkinter as Tk

class MyApp(tkyg.App, object):
    def __init__(self, *args, **kwargs):
        super(MyApp, self).__init__(*args, **kwargs)
        t   = np.arange(0, 3, .01)
        self.fig.clf()
        self.fig.add_subplot(111).plot(t, t**2)

        self.formatgridrows()

if __name__ == "__main__":
    MyApp().mainloop()
```

