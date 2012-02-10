#!/usr/bin/python
# -*- coding: UTF-8 -*-

import wx
from xmi2magik_gui import Mf

if __name__ == "__main__":
    app = wx.App(False)
    frame = Mf()
    frame.Show()
    app.MainLoop()
    
    
