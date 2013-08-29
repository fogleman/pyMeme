import wx
import urllib2
import os
from StringIO import StringIO
class Cache(object):
    def __init__(self):
        self.cache = {}
    def get_bitmap(self, key):
        if key is None or isinstance(key, wx.Bitmap):
            return key
        if key not in self.cache:
            if os.path.exists(key):
                self.cache[key] = wx.Bitmap(key)
            else:
                fp = urllib2.urlopen(key)
                data = fp.read()
                fp.close()
                img = wx.ImageFromStream(StringIO(data))
                self.cache[key] = img.ConvertToBitmap()
        return self.cache[key]
    def get_color(self, key):
        if key is None or isinstance(key, wx.Colour):
            return key
        if key not in self.cache:
            self.cache[key] = wx.Colour(*key)
        return self.cache[key]
    def get_font(self, key):
        if key is None or isinstance(key, wx.Font):
            return key
        if key not in self.cache:
            self.cache[key] = self.make_font(key)
        return self.cache[key]
    def make_font(self, key):
        face, size, bold, italic, underline = key
        family = wx.FONTFAMILY_DEFAULT
        style = wx.FONTSTYLE_ITALIC if italic else wx.FONTSTYLE_NORMAL
        weight = wx.FONTWEIGHT_BOLD if bold else wx.FONTWEIGHT_NORMAL
        font = wx.Font(size, family, style, weight, underline, face)
        return font

DEFAULT_CACHE = Cache()

def get_bitmap(key):
    return DEFAULT_CACHE.get_bitmap(key)

def get_color(key):
    return DEFAULT_CACHE.get_color(key)

def get_font(key):
    return DEFAULT_CACHE.get_font(key)
