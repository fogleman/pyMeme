import cache
import re
import wx

# Constants
LEFT = 1
RIGHT = 2
CENTER = 3

# Functions
def font(face='', size=12, bold=False, italic=False, underline=False):
    return (face, size, bold, italic, underline)

def word_wrap(dc, width, text):
    lines = []
    pattern = re.compile(r'(\s+)')
    lookup = dict((c, dc.GetTextExtent(c)[0]) for c in set(text))
    for line in text.splitlines():
        tokens = pattern.split(line)
        tokens.append('')
        widths = [sum(lookup[c] for c in token) for token in tokens]
        start, total = 0, 0
        for index in xrange(0, len(tokens), 2):
            if total + widths[index] > width:
                end = index + 2 if index == start else index
                lines.append(''.join(tokens[start:end]))
                start, total = end, 0
                if end == index + 2:
                    continue
            total += widths[index] + widths[index + 1]
        if start < len(tokens):
            lines.append(''.join(tokens[start:]))
    lines = [line.strip() for line in lines]
    return lines or ['']

def get_dc():
    return wx.MemoryDC(wx.EmptyBitmap(1, 1))

# Classes
class Control(object):
    def __init__(self, **kwargs):
        kwargs.setdefault('position', (0, 0))
        kwargs.setdefault('anchor', (0, 0))
        for name, value in kwargs.items():
            setattr(self, name, value)
    def get_computed_position(self, size):
        ww, wh = size
        ax, ay = self.anchor
        x, y = self.position
        w, h = self.get_size()
        x = ww + x if x < 0 else x
        y = wh + y if y < 0 else y
        x -= w * ax
        y -= h * ay
        return (x, y)
    def render(self, dc, size, offset):
        dx, dy = offset
        x, y = self.get_computed_position(size)
        x, y = x + dx, y + dy
        w, h = self.get_size()
        dc.SetDeviceOrigin(x, y)
        dc.SetClippingRegion(0, 0, w, h)
        self.draw(dc)
        dc.DestroyClippingRegion()
        dc.SetDeviceOrigin(0, 0)
    def get_size(self):
        raise NotImplementedError
    def draw(self, dc):
        raise NotImplementedError

class Page(object):
    def __init__(self):
        self.controls = []
    def add(self, control, position=None, anchor=None):
        if position:
            control.position = position
        if anchor:
            control.anchor = anchor
        self.controls.append(control)
    def render(self, dc, size, offset):
        for control in self.controls:
            control.render(dc, size, offset)

class Bitmap(Control):
    def __init__(self, bitmap, **kwargs):
        super(Bitmap, self).__init__(**kwargs)
        self.bitmap = bitmap
    def get_size(self):
        bitmap = cache.get_bitmap(self.bitmap)
        return bitmap.GetSize()
    def draw(self, dc):
        bitmap = cache.get_bitmap(self.bitmap)
        dc.DrawBitmap(bitmap, 0, 0, True)

class Text(Control):
    def __init__(self, label, width, **kwargs):
        kwargs.setdefault('alignment', LEFT)
        kwargs.setdefault('color', (0, 0, 0))
        kwargs.setdefault('font', font())
        kwargs.setdefault('shadow', None)
        kwargs.setdefault('max_height', None)
        kwargs.setdefault('line_offset', 0)
        kwargs.setdefault('border_color', None)
        kwargs.setdefault('border_size', 0)
        super(Text, self).__init__(**kwargs)
        self.label = label
        self.width = width
        height = self.compute_height()
        if self.max_height is not None:
            height = min(height, self.max_height)
        self.height = height
    def get_size(self):
        return (self.width, self.height)
    def get_lines(self, dc=None):
        dc = dc or get_dc()
        dc.SetFont(cache.get_font(self.font))
        lines = word_wrap(dc, self.width, self.label)
        lines = [line or ' ' for line in lines]
        return lines
    def compute_height(self):
        dc = get_dc()
        lines = self.get_lines(dc)
        height = sum(dc.GetTextExtent(line)[1] for line in lines)
        return height
    def draw_text(self, dc, text, x, y):
        color = cache.get_color(self.color)
        shadow_color = cache.get_color(self.shadow)
        border_color = cache.get_color(self.border_color)
        p = self.border_size
        if shadow_color is not None:
            dc.SetTextForeground(shadow_color)
            dc.DrawText(text, x + p + 1, y + p + 1)
        if border_color is not None:
            dc.SetTextForeground(border_color)
            for dy in xrange(-p, p + 1):
                for dx in xrange(-p, p + 1):
                    if dx * dx + dy * dy > p * p:
                        continue
                    dc.DrawText(text, x + dx, y + dy)
        dc.SetTextForeground(color)
        dc.DrawText(text, x, y)
    def draw(self, dc):
        dc.SetFont(cache.get_font(self.font))
        lines = self.get_lines(dc)
        lines = lines[self.line_offset:]
        padding, _ = dc.GetTextExtent(' ')
        y = 0
        for line in lines:
            tw, th = dc.GetTextExtent(line)
            if y + th > self.height:
                break
            if self.alignment == LEFT:
                x = padding
            elif self.alignment == RIGHT:
                x = self.width - tw - padding
            else:
                x = self.width / 2 - tw / 2
            self.draw_text(dc, line, x, y)
            y += th
