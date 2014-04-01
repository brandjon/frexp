"""Code to add interactive highlighting of series in matplotlib plots."""


class SelectorCursor(object):
    
    """An abstract cursor that may traverse a sequence of fixed length
    in any order, repeatedly, and which includes a None position.
    Executes a notifier when a position becomes selected or deselected.
    """
    
    def __init__(self, num_elems, cb_activate, cb_deactivate):
        self.num_elems = num_elems
        """Length of sequence."""
        self.cb_activate = cb_activate
        """A callback function to be called as f(i, active=True)
        when an index i is activated.
        """
        self.cb_deactivate = cb_deactivate
        """Analogous to above, but with active=False."""
        self.cursor = None
        """Valid cursor indices go from 0 to num_elems - 1.
        None is also a valid index.
        """
    
    def goto(self, i):
        """Go to the new index. No effect if cursor is currently i."""
        if i == self.cursor:
            return
        
        if self.cursor is not None:
            self.cb_deactivate(self.cursor, active=False)
        self.cursor = i
        if self.cursor is not None:
            self.cb_activate(self.cursor, active=True)
    
    def changeby(self, offset):
        """Skip to an offset of the current position."""
        states = [None] + list(range(0, self.num_elems))
        i = states.index(self.cursor)
        i = (i + offset) % len(states)
        self.goto(states[i])
    
    def next(self):
        self.changeby(1)
    
    def bulknext(self):
        self.changeby(10)
    
    def prev(self):
        self.changeby(-1)
    
    def bulkprev(self):
        self.changeby(-10)


class LineSelector:
    """Utility class for modifying matplotlib artists to highlight
    selected series.
    """
    
    def __init__(self, axes_list):
        """Construct to select from among lines of the given axes."""
        # Matplotlib artists that need to be updated.
        self.lines = []
        self.leglines = []
        self.legtexts = []
        
        for axes in axes_list:
            new_lines = [line for line in axes.get_lines()
                              if line.get_label() != '_nolegend_']
            
            leg = axes.get_legend()
            if leg is not None:
                new_leglines = leg.get_lines()
                new_legtexts = leg.get_texts()
            else:
                new_leglines = []
                new_legtexts = []
            
            assert len(new_lines) == len(new_leglines) == len(new_legtexts)
            
            self.lines.extend(new_lines)
            self.leglines.extend(new_leglines)
            self.legtexts.extend(new_legtexts)
        
        self.cursor = SelectorCursor(
                len(self.lines), self.markLine, self.unmarkLine)
    
    def markLine(self, i, active):
        if i == None:
            return
        line = self.lines[i]
        legline = self.leglines[i]
        legtext = self.legtexts[i]
        
        line.set_zorder(3)
        line.set_linewidth(3.0)
        legline.set_linewidth(3.0)
        legtext.set_color('blue')
    
    def unmarkLine(self, i, active):
        if i == None:
            return
        line = self.lines[i]
        legline = self.leglines[i]
        legtext = self.legtexts[i]
        
        line.set_zorder(2)
        line.set_linewidth(1.0)
        legline.set_linewidth(1.0)
        legtext.set_color('black')
    
    def handler(self, event):
        k = event.key
        actionmap = {
            'down':         self.cursor.next,
            'up':           self.cursor.prev,
            'pagedown':     self.cursor.bulknext,
            'pageup':       self.cursor.bulkprev,
        }
        if k not in actionmap:
            return
        actionmap[k]()
        event.canvas.draw()


def add_lineselector(figure):
    """Add a line selector for all axes of the given figure.
    Return the mpl connection id for disconnection later.
    """
    lineselector = LineSelector(figure.get_axes())
    # Workaround for weird Heisenbug. The handler isn't reliably called
    # when it's a bound method, but is called if I use a wrapper for
    # some reason.
    def wrapper(event):
        lineselector.handler(event)
    return figure.canvas.mpl_connect('key_press_event', wrapper)
