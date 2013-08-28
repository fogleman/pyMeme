import cache
import core
import os
import wx

def menu_item(window, menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.AppendItem(item)
    if func:
        window.Bind(wx.EVT_MENU, func, id=item.GetId())
    return item

def tool_item(window, toolbar, label, func, icon):
    item = toolbar.AddSimpleTool(-1, wx.Bitmap(icon), label)
    if func:
        window.Bind(wx.EVT_TOOL, func, id=item.GetId())
    return item

def load_images():
    result = []
    path = 'images'
    names = os.listdir(path)
    for name in names:
        base, ext = os.path.splitext(name)
        if ext in ('.png', '.jpg', '.jpeg'):
            title = base.replace('-', ' ')
            full_path = os.path.join(path, name)
            result.append((title, full_path))
    return result

class FileDropTarget(wx.FileDropTarget):
    def __init__(self, callback):
        super(FileDropTarget, self).__init__()
        self.callback = callback
    def OnDropFiles(self, x, y, filenames):
        self.callback(filenames)

class Model(object):
    def __init__(self):
        self.path = ''
        self.reset()
    def reset(self):
        self.header = ''
        self.footer = ''
        self.header_size = 20
        self.footer_size = 20
        self.header_alignment = core.CENTER
        self.footer_alignment = core.CENTER
        self.padding = 10
        self.border_size = 3
    def generate(self):
        background = cache.get_bitmap(self.path)
        width, height = background.GetSize()
        page = core.Page()
        page.add(core.Bitmap(background))
        text_width = width - self.padding * 2
        adjusted_header_size = int(height*(self.header_size/200.0))
        adjusted_footer_size = int(height*(self.footer_size/200.0))
        header = core.Text(
            self.header.upper(),
            text_width,
            alignment=self.header_alignment,
            border_color=(0, 0, 0),
            border_size=self.border_size,
            color=(255, 255, 255),
            font=core.font('Impact', adjusted_header_size),
        )
        page.add(header, (width / 2, self.padding), (0.5, 0))
        footer = core.Text(
            self.footer.upper(),
            text_width,
            alignment=self.footer_alignment,
            border_color=(0, 0, 0),
            border_size=self.border_size,
            color=(255, 255, 255),
            font=core.font('Impact', adjusted_footer_size),
        )
        page.add(footer, (width / 2, -self.padding), (0.5, 1))
        bitmap = wx.EmptyBitmap(width, height)
        dc = wx.MemoryDC(bitmap)
        page.render(dc, (width, height), (0, 0))
        return bitmap

class BitmapView(wx.Panel):
    def __init__(self, parent):
        super(BitmapView, self).__init__(parent, style=wx.BORDER_STATIC)
        self.bitmap = None
        self.scaled_bitmap = None
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
    def set_bitmap(self, bitmap):
        self.bitmap = bitmap
        self.Refresh()
    def on_size(self, event):
        event.Skip()
        self.Refresh()
    def on_paint(self, event):
        color = wx.SystemSettings_GetColour(wx.SYS_COLOUR_BTNFACE)
        dc = wx.BufferedPaintDC(self)
        dc.SetBackground(wx.Brush(color))
        dc.Clear()
        dc = wx.GCDC(dc)
        if self.bitmap is None:
            return
        pad = 0
        cw, ch = self.GetClientSize()
        dw, dh = cw - pad * 2, ch - pad * 2
        bw, bh = self.bitmap.GetSize()
        xr, yr = float(dw) / float(bw), float(dh) / float(bh)
        ratio = min(xr, yr)
        ratio = min(ratio, 1)
        sw, sh = int(cw / ratio), int(ch / ratio)
        x, y = (sw - bw) / 2, (sh - bh) / 2
        dc.SetUserScale(ratio, ratio)
        dc.DrawBitmap(self.bitmap, x, y)

class Frame(wx.Frame):
    def __init__(self):
        super(Frame, self).__init__(None, -1, 'iMeme')
        self.SetIcon(wx.Icon('icons/icon.ico', wx.BITMAP_TYPE_ICO))
        self.model = Model()
        self.create_menu()
        self.create_toolbar()
        panel = self.create_contents(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizerAndFit(sizer)
        self.on_change()
    def on_change(self):
        self.bitmap_view.set_bitmap(self.model.generate())
    def on_files_dropped(self, filenames):
        if filenames:
            self.model.path = filenames[-1]
            self.on_change()
    def create_contents(self, parent):
        panel = wx.Panel(parent)
        controls = self.create_controls(panel)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(controls, 1, wx.EXPAND | wx.ALL, 12)
        panel.SetSizerAndFit(sizer)
        return panel
    def create_controls(self, parent):
        list_box = self.create_list_box(parent)
        right = self.create_right(parent)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(list_box, 0, wx.EXPAND)
        sizer.AddSpacer(8)
        sizer.Add(right, 1, wx.EXPAND)
        return sizer
    def create_list_box(self, parent):
        self.list_box = wx.ListBox(parent, size=(200, -1))
        self.list_box.Bind(wx.EVT_LISTBOX, self.on_list_box)
        data = load_images()
        for title, path in data:
            self.list_box.Append(title, path)
        self.model.path = data[0][1]
        self.list_box.Select(0)
        return self.list_box
    def create_right(self, parent):
        view = self.create_view(parent)
        widgets = self.create_widgets(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(view, 1, wx.EXPAND)
        sizer.AddSpacer(8)
        sizer.Add(widgets, 0, wx.EXPAND)
        return sizer
    def create_view(self, parent):
        self.bitmap_view = BitmapView(parent)
        self.bitmap_view.SetMinSize((400, 400))
        self.bitmap_view.SetDropTarget(FileDropTarget(self.on_files_dropped))
        return self.bitmap_view
    def create_widgets(self, parent):
        self.header = header = wx.TextCtrl(parent)
        self.footer = footer = wx.TextCtrl(parent)
        header_smaller = wx.BitmapButton(parent, -1, wx.Bitmap('icons/minus.png'))
        header_bigger = wx.BitmapButton(parent, -1, wx.Bitmap('icons/plus.png'))
        header_left = wx.BitmapButton(parent, -1, wx.Bitmap('icons/align-left.png'))
        header_center = wx.BitmapButton(parent, -1, wx.Bitmap('icons/align-center.png'))
        header_right = wx.BitmapButton(parent, -1, wx.Bitmap('icons/align-right.png'))
        footer_smaller = wx.BitmapButton(parent, -1, wx.Bitmap('icons/minus.png'))
        footer_bigger = wx.BitmapButton(parent, -1, wx.Bitmap('icons/plus.png'))
        footer_left = wx.BitmapButton(parent, -1, wx.Bitmap('icons/align-left.png'))
        footer_center = wx.BitmapButton(parent, -1, wx.Bitmap('icons/align-center.png'))
        footer_right = wx.BitmapButton(parent, -1, wx.Bitmap('icons/align-right.png'))
        header.Bind(wx.EVT_TEXT, self.on_header)
        header_smaller.Bind(wx.EVT_BUTTON, self.on_header_smaller)
        header_bigger.Bind(wx.EVT_BUTTON, self.on_header_bigger)
        header_left.Bind(wx.EVT_BUTTON, self.on_header_left)
        header_center.Bind(wx.EVT_BUTTON, self.on_header_center)
        header_right.Bind(wx.EVT_BUTTON, self.on_header_right)
        footer.Bind(wx.EVT_TEXT, self.on_footer)
        footer_smaller.Bind(wx.EVT_BUTTON, self.on_footer_smaller)
        footer_bigger.Bind(wx.EVT_BUTTON, self.on_footer_bigger)
        footer_left.Bind(wx.EVT_BUTTON, self.on_footer_left)
        footer_center.Bind(wx.EVT_BUTTON, self.on_footer_center)
        footer_right.Bind(wx.EVT_BUTTON, self.on_footer_right)
        grid = wx.FlexGridSizer(2, 8, 8, 0)
        grid.AddGrowableCol(0)
        grid.Add(header, flag=wx.EXPAND)
        grid.AddSpacer(8)
        grid.Add(header_smaller)
        grid.Add(header_bigger)
        grid.AddSpacer(8)
        grid.Add(header_left)
        grid.Add(header_center)
        grid.Add(header_right)
        grid.Add(footer, flag=wx.EXPAND)
        grid.AddSpacer(8)
        grid.Add(footer_smaller)
        grid.Add(footer_bigger)
        grid.AddSpacer(8)
        grid.Add(footer_left)
        grid.Add(footer_center)
        grid.Add(footer_right)
        return grid
    def create_menu(self):
        menubar = wx.MenuBar()
        # File
        menu = wx.Menu()
        menu_item(self, menu, 'New\tCtrl+N', self.on_new)
        menu_item(self, menu, 'Open...\tCtrl+O', self.on_open)
        menu_item(self, menu, 'Save As...\tCtrl+S', self.on_save)
        menu.AppendSeparator()
        menu_item(self, menu, 'Exit\tAlt+F4', self.on_exit)
        menubar.Append(menu, '&File')
        self.SetMenuBar(menubar)
    def create_toolbar(self):
        toolbar = self.CreateToolBar()
        toolbar.SetToolBitmapSize((18, 18))
        tool_item(self, toolbar, 'New', self.on_new, 'icons/new.png')
        tool_item(self, toolbar, 'Open', self.on_open, 'icons/open.png')
        tool_item(self, toolbar, 'Save', self.on_save, 'icons/save.png')
        toolbar.Realize()
        toolbar.Fit()
        self.SetToolBar(toolbar)
    def on_list_box(self, event):
        index = self.list_box.GetSelection()
        if index >= 0:
            self.model.path = self.list_box.GetClientData(index)
            self.on_change()
    def on_header(self, event):
        self.model.header = self.header.GetValue()
        self.on_change()
    def on_header_smaller(self, event):
        self.model.header_size -= 4
        self.model.header_size = max(self.model.header_size, 1)
        self.on_change()
    def on_header_bigger(self, event):
        self.model.header_size += 4
        self.model.header_size = min(self.model.header_size, 100)
        self.on_change()
    def on_header_left(self, event):
        self.model.header_alignment = core.LEFT
        self.on_change()
    def on_header_center(self, event):
        self.model.header_alignment = core.CENTER
        self.on_change()
    def on_header_right(self, event):
        self.model.header_alignment = core.RIGHT
        self.on_change()
    def on_footer(self, event):
        self.model.footer = self.footer.GetValue()
        self.on_change()
    def on_footer_smaller(self, event):
        self.model.footer_size -= 4
        self.model.footer_size = max(self.model.footer_size, 8)
        self.on_change()
    def on_footer_bigger(self, event):
        self.model.footer_size += 4
        self.model.footer_size = min(self.model.footer_size, 144)
        self.on_change()
    def on_footer_left(self, event):
        self.model.footer_alignment = core.LEFT
        self.on_change()
    def on_footer_center(self, event):
        self.model.footer_alignment = core.CENTER
        self.on_change()
    def on_footer_right(self, event):
        self.model.footer_alignment = core.RIGHT
        self.on_change()
    def on_new(self, event):
        self.model.reset()
        self.header.SetValue('')
        self.footer.SetValue('')
        self.on_change()
    def on_open(self, event):
        exts = sorted(['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp'])
        wildcard = ';'.join(exts)
        dialog = wx.FileDialog(self, 'Open', wildcard=wildcard,
            style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            self.model.path = path
            self.on_change()
    def on_save(self, event):
        dialog = wx.FileDialog(self, 'Save As', wildcard='*.jpg',
            style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            bitmap = self.model.generate()
            image = wx.ImageFromBitmap(bitmap)
            image.SetOptionInt(wx.IMAGE_OPTION_QUALITY, 95)
            image.SaveFile(path, wx.BITMAP_TYPE_JPEG)
    def on_exit(self, event):
        self.Close()

def main():
    app = wx.PySimpleApp()
    frame = Frame()
    frame.Center()
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()
