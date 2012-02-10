# -*- coding: UTF-8 -*-
#!/usr/bin/python

import wx
from wx.xrc import XRCID, XRCCTRL, EmptyXmlResource
from xml.parsers.expat import ExpatError
import os 
import pickle

from xmi_parser import XmiParser
from xmi_generator import FilesGenerator 


DIR_NAME = os.path.dirname(__file__)
DATA_DIR = os.path.join(DIR_NAME, "data")

# ------------------------ XRC ----------------------
__res = None

def get_resources():
    """ This function provides access to the XML resources in this module."""
    global __res
    if __res == None:
        __init_resources()
    return __res




class xrcFRAME(wx.Frame):
#!XRCED:begin-block:xrcFRAME1.PreCreate
    def PreCreate(self, pre):
        """ This function is called during the class's initialization.
        
        Override it for custom setup before the window is created usually to
        set additional window styles using SetWindowStyle() and SetExtraStyle().

        """
        
        pass
        
#!XRCED:end-block:xrcFRAME1.PreCreate

    def __init__(self, parent):
        # Two stage creation (see http://wiki.wxpython.org/index.cgi/TwoStageCreation)
        pre = wx.PreFrame()
        self.PreCreate(pre)
        get_resources().LoadOnFrame(pre, parent, "FRAME1")
        
        #get_resources().LoadOnFrame(pre, parent, "frame_1")
        self.PostCreate(pre)
        
        # Define variables for the controls, bind event handlers


# ------------------------ Resource data ----------------------

def __init_resources():
    global __res
    __res = EmptyXmlResource()

    __res.Load(os.path.join(DATA_DIR, 'xmi2magik.xrc'))
    #__res.Load('othrt.xml')


# ------------------------ GUI implementation ----------------------

class Mf(xrcFRAME):
    opts = { "size" : {"posix" : (400,600),
                       "nt" : (400, 520)},
             "explore" : {"posix" : (os.system, "nautilus "),
                          "nt" : (os.system, "start explorer ")},
                       }

    file_header = """###########################
#
# Date:    $date
# Author: $user
#
###########################"""    

    def __init__(self):
        """ Frame constructor
        """
        xrcFRAME.__init__(self, None)
        size = self.opts["size"][os.name]
        self.SetMinSize(size)
        self.SetSize(size)
        # control names
        self.items = ("tb_encoding",
                      "tb_pragma",
                      "tb_package",
                      "tb_file_header",
                      "tb_target_folder",
                      "tb_xmi_file_name")
        # control and action name
        items_method = {"bt_close" : self.bt_close_click,
                        "bt_save_options" : self.bt_save_options_click,
                        "bt_xmi_file_name" : self.bt_xmi_file_name_click,
                        "bt_target_folder" : self.bt_target_folder_click,
                        "bt_generate" : self.bt_generate_click}
        # bind controls with slots
        for item in self.items:
            setattr(self, item, XRCCTRL(self, item))
        # bind controls with methods    
        for name, method in items_method.items():
            self.Bind(wx.EVT_BUTTON, method, id=XRCID(name))

        try:
            icon_file = os.path.join(DATA_DIR, "myApp.ico")
            self.SetIcon(wx.Icon(icon_file, wx.BITMAP_TYPE_ICO))
        except Exception as e:
            print(e)
        self.tb_file_header.SetValue(self.file_header)
        self._restore_options()


    def _options(self):
        """ Collect data from controls
        """
        xmi_file = self.tb_xmi_file_name.GetValue()
        topic = self.tb_pragma.GetValue()
        package = self.tb_package.GetValue()
        header = self.tb_file_header.GetValue()
        target_folder = self.tb_target_folder.GetValue()
        encoding = self.tb_encoding.GetValue()
        
        return {"topic" : topic, 
               "package" : package, 
               "header" : header, 
               "target_folder" : target_folder,
               "encoding" : encoding,
               "xmi_file" : xmi_file}


    def _opt_file_name(self):
        """ Return file path to store options
        """
        return os.path.join(DATA_DIR, "otp.pickle")
    
    
    def _restore_options(self):
        """ Try to restore controls values from options file
        """
        fn = self._opt_file_name()
        if os.path.exists(fn):
            try:
                opt = pickle.load(open(fn, "r"))
                self.tb_pragma.SetValue(opt["topic"])
                self.tb_package.SetValue(opt["package"])
                self.tb_file_header.SetValue(opt["header"])
                self.tb_target_folder.SetValue(opt["target_folder"])
                self.tb_encoding.SetValue(opt["encoding"])
            except Exception as ex:
                print("Error durring restore default options")
                print(ex)
    
    
    def _error(self, message):
        """ Show error message to user
        """
        dlg = wx.MessageDialog(self, message,
                               'xmi2magik',
                               wx.OK | wx.ICON_ERROR
                               )
        dlg.ShowModal()
        dlg.Destroy()
        
    
    def _info(self, message):
        """ Show info message to user
        """
        dlg = wx.MessageDialog(self, message,
                               'xmi2magik',
                               wx.OK | wx.ICON_INFORMATION
                               )
        dlg.ShowModal()
        dlg.Destroy()
        

    def _check_options(self, options):
        """ Check if all required fields are filled.
        """
        xmi_file = options.get("xmi_file")
        if not xmi_file or not os.path.exists(xmi_file):
            self._error("Select XMI file")
            return 

        target_folder = options["target_folder"]
        if not target_folder:
            self._error("Select target folder")
            return
        
        if not os.path.exists(target_folder):
            self._error("Target folder not exists")
            return 
    
        return True 
    
    
    def bt_close_click(self, evnt):
        """ close dialog
        """
        self.Close()
        
    
    def bt_save_options_click(self, evnt):
        """ Save default controls values
        """
        opt = self._options()
        pickle.dump(opt, open(self._opt_file_name(), "w"))
        
        
    def bt_xmi_file_name_click(self, evnt):
        """ Call file dialog to select source xmi file
        """
        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir="",#os.getcwd(), 
            defaultFile="",
            wildcard="XML files (*.xml)|*.xml|"\
                    "XMI files(*.xmi)|*.xmi|"\
                    "All files (*.*)|*.*",
                    style=wx.OPEN | wx.CHANGE_DIR)

        if dlg.ShowModal() == wx.ID_OK:
            self.tb_xmi_file_name.SetValue(dlg.GetPath())
        
        dlg.Destroy()
        

    def bt_target_folder_click(self, evnt):
        """ Call directory dialog
        """
        dlg = wx.DirDialog(self, "Choose a directory:",
                          style=wx.DD_DEFAULT_STYLE
                           #| wx.DD_DIR_MUST_EXIST
                           #| wx.DD_CHANGE_DIR
                           )

        if dlg.ShowModal() == wx.ID_OK:
            self.tb_target_folder.SetValue(dlg.GetPath())

        dlg.Destroy()


    def bt_generate_click(self, evnt):
        """ Generate result files
        """
        opt = self._options()
        if not self._check_options(opt):
            return 
        
        xmi_file = opt["xmi_file"]
        target_folder = opt["target_folder"]
        topic = opt["topic"]
        header = opt["header"]
        package = opt["package"]
        encoding = opt["encoding"]
        
        try:
            xmi = XmiParser.parse_file(xmi_file)
        except ExpatError as err:
            self._error("Error while generate:\n{0}".format(err))
            return 
        if not xmi:
            self._info("No files generated.\nPlease check your xmi file.")
            return 
            
        gen = FilesGenerator(xmi, target_folder, topic, header, package, encoding)
        gen.generate()
        dlg = wx.MessageDialog(self, 'Files generated\nOpen target folder?',
                               'xmi2magik',
                               wx.YES_NO | wx.ICON_INFORMATION
                               )
        res = dlg.ShowModal()
        if res == wx.ID_YES:
            cmd, param = self.opts["explore"].get(os.name)
            cmd("""{0}"{1}" """.format(param, target_folder))
            
        dlg.Destroy()
        
    
    
