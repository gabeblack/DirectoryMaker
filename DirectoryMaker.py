#!/usr/bin/python

# Copyright 2009 Gabriel Black
#
# This file is part of Directory Maker.
#
#    Directory Maker is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    any later version.
#
#    Directory MAker is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Directory Maker.  If not, see <http://www.gnu.org/licenses/>.


# TODO: 
#  Look at reportlab's platypus to create a directory (w/o photos) in an easy table-like format
#  Add photo resizing/cropping in the program (maybe drag in the window to move around within the window and wheel mouse and/or slider to resize)?
#  Show the frame in the photo view (including shown fields (i.e. phone, address, etc.))
#  Add drag and drop for photos
#  Have the installer cache the fonts instead of the first time you run the program (since caching takes a while)
#  Provide the ability to regenerate the font cache (in case the user installs additional fonts)
#  Test on other platforms
#  Provide the ability to have the program upload the photos to the ward website
#  Handle unavailable fonts better. (right now sometimes it fails at PDF generation, sometimes when the font is selected) 

import tempfile
import wx
import wx.lib.buttonpanel as bp
import os
import pickle
import Image
import csv

# embed the images in python files to make distribution between platforms easier
from icons.peopleAdd import peopleAdd
from icons.peopleDelete import peopleDelete
from icons.addPicture import addPicture
from icons.deletePicture import deletePicture
from icons.newProject import newProject
from icons.saveProject import saveProject
from icons.pdf import pdf
from icons.excel import excel
from icons.tools import tools
from icons.openProject import openProject
from icons.noImage import noImage
from icons.taskbarIcon import taskbarIcon
from icons.imgFrame import imgFrame

# reportlab does the PDF generation
from reportlab.pdfgen import canvas
from reportlab.lib import fontfinder
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont



ID_ABOUT=101
ID_OPEN=102
ID_NEW=103
ID_SAVE=104
ID_BUTTON1=110
ID_EXIT=200
ID_EXPORT_PDF=201
ID_OPTIONS=202
ID_IMPORT_CSV=203
ID_NAME_FONT=301
ID_ADDRESS_FONT=302
ID_PHONE_FONT=303
ID_MISC1_FONT=304
ID_MISC2_FONT=305

COLOR=0
FONT=1
SIZE=2


TBFLAGS = ( wx.TB_HORIZONTAL
            | wx.NO_BORDER
            | wx.TB_FLAT
            )

# Throughout the file misc1 I have holding the emails when imported from MLS or the ward website, and misc2 contains the children
class tOptionsDialog(wx.Dialog):
    def __init__( self, pdfCreator,  parent, ID, title, size=(-1,-1), pos=(-1,-1), style=wx.DEFAULT_DIALOG_STYLE  | wx.RESIZE_BORDER):
        wx.Dialog.__init__(self,parent,wx.ID_ANY,title,size,pos,style)
        sizer = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, -1, "Export PDF Options")
        sizer.Add(label, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        self.fontSettings = dict(pdfCreator.fontSettings)

        box = wx.StaticBox(self, -1, "PDF Structure Settings")
        boxSizer1 = wx.StaticBoxSizer(box, wx.VERTICAL)
        self.rows = self.addCtrl( boxSizer1, 0, " Number of Rows:", str(pdfCreator.numRows))
        self.cols = self.addCtrl( boxSizer1, 0, " Number of Cols:", str(pdfCreator.numCols))
        self.xSpacing = self.addCtrl( boxSizer1, 0, " Horizontal Spacing:", str(pdfCreator.xSpacing))
        self.ySpacing = self.addCtrl( boxSizer1, 0, " Vertical Spacing:", str(pdfCreator.ySpacing))

        box = wx.StaticBox(self, -1, "Show Optional Fields")
        boxSizer2 = wx.StaticBoxSizer(box, wx.VERTICAL)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.misc1 = wx.CheckBox(self, -1, " Show Misc1 Field")
        self.misc1.SetValue( pdfCreator.showMisc1 )
        self.misc2 = wx.CheckBox(self, -1, " Show Misc2 Field")
        self.misc2.SetValue( pdfCreator.showMisc2 )
        hSizer.Add(self.misc1, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        hSizer.Add((1,0), 1, wx.EXPAND)
        hSizer.Add(self.misc2, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_RIGHT, 5)
        boxSizer2.Add(hSizer,0,wx.EXPAND)

        box = wx.StaticBox(self, -1, "Fonts")
        boxSizer3 = wx.StaticBoxSizer(box, wx.VERTICAL)
        self.nameText = self.addCtrl( boxSizer3, ID_NAME_FONT, "Name Font", "Gabriel and Rebecca Black")
        self.addressText = self.addCtrl( boxSizer3, ID_ADDRESS_FONT, "Address Font", "1234 Fake Street")
        self.phoneText = self.addCtrl( boxSizer3, ID_PHONE_FONT, "Phone Font", "(512) 867-5309")
        self.misc1Text = self.addCtrl( boxSizer3, ID_MISC1_FONT, "Misc 1 Font", "Miscellaneous 1")
        self.misc2Text = self.addCtrl( boxSizer3, ID_MISC2_FONT, "Misc 2 Font", "Miscellaneous 2")

        sizer.Add(boxSizer1, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        sizer.Add(boxSizer2, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        sizer.Add(boxSizer3, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        line = wx.StaticLine(self, -1, size=(50,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()
        
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_RIGHT|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.updateUI()
    
    def addCtrl(self, sizer, id, labelString, textBoxString):
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        ctrl = None
        textBox = None
        if id:
            lbl = wx.Button(self, id, labelString, size=(100,-1))
            self.Bind(wx.EVT_BUTTON, self.OnSelectFont, lbl)
            textBox = wx.StaticText(self, -1, textBoxString, size=(200, -1),style=wx.ALIGN_RIGHT)
            textBox.SetBackgroundColour(wx.WHITE)
        else:
            lbl = wx.StaticText(self, -1, labelString)
            textBox = wx.TextCtrl(self, -1, textBoxString, size=(125, -1))
            
        hSizer.Add(lbl, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        hSizer.Add((1,0), 1, wx.EXPAND)
        hSizer.Add(textBox, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_RIGHT, 5)
        sizer.Add(hSizer,0,wx.EXPAND)
        return textBox
        
    def updateUI(self):
        self.nameText.SetForegroundColour(self.fontSettings[ID_NAME_FONT][COLOR])
        self.nameText.SetFont( self.fontSettings[ID_NAME_FONT][FONT] )

        self.addressText.SetForegroundColour(self.fontSettings[ID_ADDRESS_FONT][COLOR])
        self.addressText.SetFont( self.fontSettings[ID_ADDRESS_FONT][FONT] )

        self.phoneText.SetForegroundColour(self.fontSettings[ID_PHONE_FONT][COLOR])
        self.phoneText.SetFont( self.fontSettings[ID_PHONE_FONT][FONT] )

        self.misc1Text.SetForegroundColour(self.fontSettings[ID_MISC1_FONT][COLOR])
        self.misc1Text.SetFont( self.fontSettings[ID_MISC1_FONT][FONT] )

        self.misc2Text.SetForegroundColour(self.fontSettings[ID_MISC2_FONT][COLOR])
        self.misc2Text.SetFont( self.fontSettings[ID_MISC2_FONT][FONT] )
        
    def OnSelectFont(self,e):
        data = wx.FontData()
        data.EnableEffects(True)
        font = e.GetId()
        data.SetInitialFont( self.fontSettings[font][FONT] )
        data.SetColour(self.fontSettings[font][COLOR])     
        dlg = wx.FontDialog(self, data)
        fontFound = 0
        while True:
            if dlg.ShowModal() == wx.ID_OK:
                data = dlg.GetFontData()
                fonts = getFontCache()
                fontName = data.GetChosenFont().GetFaceName()
                if fontName in fonts.getFamilyNames():
                    self.fontSettings[font][COLOR] = data.GetColour()
                    self.fontSettings[font][FONT] = data.GetChosenFont()
                    self.updateUI()
                    break
                else:
                    msgBox(self, "Sorry, this font is not available for PDF generation!")
            else:
                break
        dlg.Destroy()        


class MainWindow(wx.Frame):
    def __init__(self,parent,id,title):
        self.dirname=''
        windowSize = (890,600)
        wx.Frame.__init__(self,parent,wx.ID_ANY, title, (-1,-1), windowSize, wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.RESIZE_BORDER | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN | wx.TAB_TRAVERSAL)
        self.programVersion = "1.0"
        self.pdfCreator = tPDFCreator()
        self.projectDirty = False
        self.root = None
        self.currentItem = None
        self.projectPath = None
        self.CreateStatusBar() # A Statusbar in the bottom of the window
        self.dontSave = False

        self.Bind( wx.EVT_CLOSE, self.OnClose )
        self.setupMenuBar()
        
        self.SetIcon( self.makeIcon( taskbarIcon.GetImage() ) )
        
        splitter = wx.SplitterWindow(self, -1, style=wx.CLIP_CHILDREN | wx.SP_LIVE_UPDATE | wx.SP_3D)
        leftPanel = wx.ScrolledWindow(splitter, -1, size=(250,-1), style=wx.SUNKEN_BORDER)
        rightPanel = wx.Panel(splitter, -1, style=wx.SUNKEN_BORDER | wx.TAB_TRAVERSAL)
        self.layoutGradientPanel( rightPanel )
        self.layoutTreePanel( leftPanel )

        leftPaneMinWidth = 275
        splitter.SplitVertically( leftPanel, rightPanel, leftPaneMinWidth)
        splitter.SetMinimumPaneSize(leftPaneMinWidth)
        
        sizer = wx.BoxSizer()
        sizer.Add(splitter, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetMinSize(windowSize)
        sizer.Layout()
        self.setControlsState( False )
        self.Show(1)

    def makeIcon( self, img ):
        if "wxMSW" in wx.PlatformInfo:
            img = img.Scale(32, 32)
        elif "wxGTK" in wx.PlatformInfo:
            img = img.Scale(22, 22)
        # wxMac can be any size upto 128x128, so leave the source img alone....
        icon = wx.IconFromBitmap(img.ConvertToBitmap() )
        return icon

    def OnAbout(self,e):
        d= wx.MessageDialog( self, " A Printable Telephone Photo Directory Creator \n"
                             " Version 1.0 \n"
                            " Written by Gabriel Black\n http://DirectoryMaker.blogspot.com","About Directory Maker", wx.OK)
        d.ShowModal()
        d.Destroy() 
    def OnClose( self, e):
        self.checkProjectDirty()
        self.Destroy()

    def OnExit(self,e):
        self.Close()

    def OnSaveDirectory(self,e):
        self.saveProject()

    def OnExportPDF(self,e):
        author = "Gabe Black"
        familyId, cookie = self.tree.GetFirstChild(self.root)
        i = 0
        (f,fname) = tempfile.mkstemp(suffix='.pdf',prefix=self.projectName)
        c = canvas.Canvas(fname)
        os.close(f)
        c.setAuthor( author )
        self.pdfCreator.embedFonts(c)
        while familyId.IsOk():
            familyData = self.tree.GetPyData(familyId)
            img=None
            if familyData.imageIndex > 0:
                img=self.imageFrame.makeImagePath( familyData.imageIndex )
            self.pdfCreator.createFamily(c,familyData,img,i/self.pdfCreator.numCols,i%self.pdfCreator.numCols)
            i+=1
            if i%(self.pdfCreator.numRows*self.pdfCreator.numCols) == 0:
                self.pdfCreator.showPage(c)
                i=0
            familyId, cookie = self.tree.GetNextChild(self.root, cookie)
        if (i%(self.pdfCreator.numRows*self.pdfCreator.numCols)) != 0:
            self.pdfCreator.showPage(c)
        c.save()
        os.startfile(fname)

    def parseName( self, name ):
        if name:
            start = name.find('<')
            end = name.find('>')
            if start != -1 and end != -1:
                return (name[0:start-1],name[start+1:end])
            else:
                return (name,"")
        else:
            return ("","")

    def OnImportCSV(self, e):
        while True:
            dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "CSV Files (*.csv)|*.csv", wx.OPEN)
            if dlg.ShowModal() == wx.ID_OK:
                f = open(dlg.GetPath())
                reader = csv.reader( f )
                row = reader.next()
                if "HofH ID" in row: #for MLS import, hopefully the headers keep the same names
                    ward = {}
                    reader = csv.DictReader(f,row)
                    for entry in reader:
                        id = entry["HofH ID"]
                        
                        if id not in ward:
                            ward[id] = tFamily("","","","","","","","","",0)
                            ward[id].address = entry["Street 1"] + entry["Street 2"]
                            ward[id].homePhone = entry["Phone 1"]
                        (familyName, dummy, firstName) = entry["Preferred Name"].partition(', ')
                        
                        if entry["HH Position"] == "Head of Household":
                            ward[id].familyName = familyName
                            ward[id].fatherName = firstName
                            ward[id].fatherPhone = entry["Phone 2"]
                            if ward[id].misc1:
                                ward[id].misc1 = entry["E-mail Address"] + " " + ward[id].misc1
                            else:
                                ward[id].misc1 = entry["E-mail Address"]
                        elif entry["HH Position"] == "Spouse":
                            ward[id].motherName = firstName
                            ward[id].motherPhone = entry["Phone 2"]
                            if ward[id].misc1:
                                ward[id].misc1 += " " + entry["E-mail Address"]
                            else:
                                ward[id].misc1 = entry["E-mail Address"]
                        else: #child
                            if ward[id].misc2:
                                ward[id].misc2 += " " + firstName
                            else:
                                ward[id].misc2 = firstName
                                
                    for k,family in ward.iteritems():
                        self.tree.AppendItem(self.root, str(family), data=wx.TreeItemData(family) )
                    break
                elif len(row) > 5: #Default to Ward Website format?
                    for row in reader:
                        familyName = phone = address = fatherName = fatherEmail = motherName = motherEmail = misc1 = misc2 = ""
                        try:
                            i = iter(row)
                            (familyName, dummy, parents) = i.next().partition(', ')
                            phone = i.next()
                            address=i.next()
                            address2 = i.next()
                            if i.next():
                                address = address + ' ' + address2
                            i.next()
                            (fatherName, misc1) = self.parseName(i.next())
                            if parents.find('and') != -1:
                                (motherName, motherEmail) = self.parseName(i.next())
                            misc2 = ', '.join(i)
                            if misc1 != "" and motherEmail != "":
                                misc1 = misc1 + " " + motherEmail
                        except StopIteration:
                            pass
                        family = tFamily( familyName,
                                          address,
                                          phone,
                                          fatherName,
                                          "",
                                          motherName,
                                          "",
                                          misc1,
                                          misc2,
                                          0)
                            
                            
                        self.tree.AppendItem(self.root, str(family), data=wx.TreeItemData(family) )
                    break
                else:
                    msgBox( self, "Invalid CSV File!" )
            else:
                break
        dlg.Destroy()

    def OnSetOptions(self,e):
        dlg = tOptionsDialog( self.pdfCreator, self, -1, "Options" )
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        if val == wx.ID_OK:
            self.pdfCreator.fontSettings = dict(dlg.fontSettings)
            self.pdfCreator.setOptions(int(dlg.rows.GetValue()), int(dlg.cols.GetValue()),
                                       int(dlg.xSpacing.GetValue()), int(dlg.ySpacing.GetValue()),
                                       dlg.misc1.GetValue(), dlg.misc2.GetValue())
            self.projectDirty = True
        dlg.Destroy()

    def checkProjectDirty(self):
        open_it = True
        if self.projectDirty:
            # save the current project file first.
            result = warningBox( self, "The project has been changed.  Save?")
            if result == wx.ID_YES:
                self.saveProject()
            if result == wx.ID_CANCEL:
                open_it = False
        return open_it

    def OnNewDirectory(self, e):
        open_it = self.checkProjectDirty()
        if open_it:
            dlg = wx.TextEntryDialog(self, 'Name for new project:', 'New Project',
                                     'New project', wx.OK|wx.CANCEL)
            if dlg.ShowModal() == wx.ID_OK:
                dlg2 = wx.FileDialog(self, 'Place to store new project.', '.', '', '*.dir', wx.SAVE)
                if dlg2.ShowModal() == wx.ID_OK:
                    self.setControlsState( True )
                    self.projectName = dlg.GetValue()
                    self.root = self.tree.AddRoot(self.projectName)

                    self.projectPath = dlg2.GetPath()
                    self.imageFrame.setProjectPath( self.projectPath )
                    (filepath, filename) = os.path.split( self.projectPath )
                    d = os.path.join( filepath, "images" )
                    if not os.path.exists(d):
                        os.mkdir( d )
                    self.saveProject()
                dlg2.Destroy()
            dlg.Destroy()
    def saveProject(self):
        self.OnSaveRecord( wx.ID_ANY )
        proj = open(self.projectPath, 'w')
        pickle.dump(self.programVersion,proj)
        pickle.dump(self.projectName, proj)
        pickle.dump(self.imageFrame.getMaxImageIndex(), proj)
        pickle.dump(self.pdfCreator.getSettings(), proj)
        familyId, cookie = self.tree.GetFirstChild(self.root)
        while familyId.IsOk():
            familyData = self.tree.GetPyData(familyId)
            pickle.dump(familyData, proj)
            familyId, cookie = self.tree.GetNextChild(self.root, cookie)
        proj.close()
        self.projectDirty = False

    def OnOpen(self,e):
        """ Open a file"""
        if self.checkProjectDirty():
            dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "Directory Files (*.dir)|*.dir", wx.OPEN)
            if dlg.ShowModal() == wx.ID_OK:
                filename=dlg.GetFilename()
                self.dirname=dlg.GetDirectory()
                self.projectPath = os.path.join(self.dirname, filename)
                self.tree.DeleteAllItems()
                try:
                    f=open(self.projectPath,'r')
                    self.programVersion = pickle.load(f)
                    self.projectName = pickle.load(f)
                    self.imageFrame.setMaxImageIndex(pickle.load(f))
                    self.imageFrame.setProjectPath(self.projectPath)
                    pdfSettings = pickle.load(f)
                    self.pdfCreator = tPDFCreator(pdfSettings)
                    self.root = self.tree.AddRoot(self.projectName)
                    try:
                        family = pickle.load(f)
                        while family:
                            self.tree.AppendItem(self.root, str(family), data=wx.TreeItemData(family) )
                            family = pickle.load(f)
                    except EOFError:
                        self.currentItem = None
                    f.close()
                    self.setControlsState( True )
                except IOError:
                    msgBox("Not a valid directory file")
            dlg.Destroy()

    def OnDefaultImage(self,e):
        if self.currentItem:
            self.imageFrame.setImage( 0 )
            self.projectDirty = True
        
    def OnNewImage(self,e):
        """ New Image """
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "Image Files (*.jpg)|*.jpg", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetFilename()
            dirname=dlg.GetDirectory()
            imagePath = os.path.join(dirname, filename)
            self.imageFrame.newImage(imagePath)
            if self.currentItem:
                family = self.tree.GetPyData(self.currentItem)
                family.setImageIndex( self.imageFrame.getCurrentImageIndex() )
                self.projectDirty = True
        dlg.Destroy()
        
    def OnDeleteRecord(self,e):
        if self.currentItem:
            # set this to a null tFamily so that OnTreeItemChanged call to OnSaveRecord returns immediately
            self.dontSave = True
            self.tree.Delete( self.currentItem )
            if self.tree.GetCount() == 1:
                self.clearForm()
            self.projectDirty = True

    def OnSaveRecord(self,e):
        if( self.familyName.GetValue() == self.address.GetValue() == self.homePhone.GetValue() == self.fatherName.GetValue() == 
            self.motherName.GetValue() == self.motherPhone.GetValue() == self.misc1.GetValue() == self.misc2.GetValue() == "" ):
            return
        family = tFamily( self.familyName.GetValue(), 
                          self.address.GetValue(), 
                          self.homePhone.GetValue(), 
                          self.fatherName.GetValue(), 
                          self.fatherPhone.GetValue(), 
                          self.motherName.GetValue(), 
                          self.motherPhone.GetValue(), 
                          self.misc1.GetValue(),
                          self.misc2.GetValue(),
                          self.imageFrame.getCurrentImageIndex() )

        if self.currentItem:
            familyOld = self.tree.GetPyData(self.currentItem)
            if familyOld != family:
                self.tree.SetPyData(self.currentItem, family)
                self.tree.SetItemText(self.currentItem, str(family))
                self.projectDirty = True
            
        else:
            self.tree.AppendItem(self.root, str(family), data=wx.TreeItemData(family) )
            self.projectDirty = True

        if self.projectDirty:
            self.tree.SortChildren(self.root)

        self.clearForm()

    def OnTreeItemChanged(self,e):
        if e.GetItem() != self.root:
            if self.dontSave:
                self.dontSave = False
            else:
                self.OnSaveRecord(e)
            self.currentItem = e.GetItem()
            family = self.tree.GetPyData(self.currentItem)
            self.setForm(family)
        else:
            self.clearForm()

    def setForm(self, family):
        self.familyName.SetValue(family.familyName)
        self.address.SetValue(family.address)
        self.homePhone.SetValue(family.homePhone)
        self.fatherName.SetValue(family.fatherName)
        self.fatherPhone.SetValue(family.fatherPhone)
        self.motherName.SetValue(family.motherName)
        self.motherPhone.SetValue(family.motherPhone)
        self.misc1.SetValue(family.misc1)
        self.misc2.SetValue(family.misc2)
        self.imageFrame.setImage(family.getImageIndex())

    def clearForm(self):
        family = tFamily("","","","","","","","","",0)
        self.setForm( family )
        self.currentItem = None
        self.imageFrame.setImage( 0 )

    def setupMenuBar(self):
        # Setting up the menu.
        filemenu= wx.Menu()
        filemenu.Append(ID_NEW, "&New"," New Project")
        filemenu.Append(ID_OPEN, "&Open"," Open a file to edit")
        filemenu.Append(ID_SAVE, "&Save"," Save Project")
        filemenu.AppendSeparator()
        filemenu.Append(ID_IMPORT_CSV, "&Import CSV","Example: Import CSV file")
        filemenu.Append(ID_EXPORT_PDF, "&Export PDF","Export PDF")
        filemenu.AppendSeparator()
        filemenu.Append(ID_OPTIONS, "&Options"," Set Preferences")
        filemenu.Append(ID_ABOUT, "&About"," Information about this program")
        filemenu.AppendSeparator()
        filemenu.Append(ID_EXIT,"E&xit"," Terminate the program")
        # Creating the menubar.
        optionsMenu = wx.Menu()
        optionsMenu.Append(ID_OPTIONS, "&Options"," Set Preferences")
        optionsMenu.Append(ID_IMPORT_CSV, "&Import CSV"," \Example: Import CSV file")
        optionsMenu.Append(ID_EXPORT_PDF, "&Export PDF","Export PDF")
        aboutMenu = wx.Menu()
        aboutMenu.Append(ID_ABOUT, "&About"," Information about this program")

        menuBar = wx.MenuBar()
        menuBar.Append(filemenu,"&File") # Adding the "filemenu" to the MenuBar
        menuBar.Append(optionsMenu,"&Options") 
        menuBar.Append(aboutMenu,"&About") 
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.

        wx.EVT_MENU(self, ID_ABOUT, self.OnAbout)
        wx.EVT_MENU(self, ID_EXIT, self.OnExit)
        wx.EVT_MENU(self, ID_OPEN, self.OnOpen)
        wx.EVT_MENU(self, ID_NEW, self.OnNewDirectory)
        wx.EVT_MENU(self, ID_SAVE, self.OnSaveDirectory)
        wx.EVT_MENU(self, ID_EXPORT_PDF, self.OnExportPDF)
        wx.EVT_MENU(self, ID_OPTIONS, self.OnSetOptions)
        wx.EVT_MENU(self, ID_IMPORT_CSV, self.OnImportCSV)
        self.fileMenu = menuBar
        self.optionsMenu = optionsMenu
        
    def layoutTreePanel(self, panel):
        vSizer = wx.BoxSizer(wx.VERTICAL)

        # add the TOOLBAR for the directory list
        tb = wx.ToolBar(panel, style=TBFLAGS)
        vSizer.Add(tb, 0, wx.EXPAND)
        tb.SetToolBitmapSize((36,36))
        
        tb.AddLabelTool(10, "New", newProject.GetBitmap(), shortHelp="New", longHelp="Create a new project")
        self.Bind(wx.EVT_TOOL, self.OnNewDirectory, id=10)

        tb.AddLabelTool(20, "Open", openProject.GetBitmap(), shortHelp="Open", longHelp="Open an existing project")
        self.Bind(wx.EVT_TOOL, self.OnOpen, id=20)

        tb.AddSimpleTool(30, saveProject.GetBitmap(), "Save", "Save the Project")
        self.Bind(wx.EVT_TOOL, self.OnSaveDirectory, id=30)

        tb.AddSeparator()

        tb.AddSimpleTool(40, tools.GetBitmap(), "Tools", "Set custom options")
        self.Bind(wx.EVT_TOOL, self.OnSetOptions, id=40)

        tb.AddSimpleTool(50, pdf.GetBitmap(), "Export PDF", "Export the Telephone Directory to PDF")
        self.Bind(wx.EVT_TOOL, self.OnExportPDF, id=50)

        tb.AddSimpleTool(60, excel.GetBitmap(), "Import CSV", "Import Directory from CSV file")
        self.Bind(wx.EVT_TOOL, self.OnImportCSV, id=60)
        # Final thing to do for a toolbar is call the Realize() method. This
        # causes it to render (more or less, that is).
        tb.Realize()
        self.toolbarIDs = [30,40,50,60]
        self.toolbar = tb

        # Add Directory Tree Control
        self.tree = wx.TreeCtrl(panel, -1, (-1,-1), (260,500))
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnTreeItemChanged)

        vSizer.Add(self.tree, 1, wx.EXPAND)
        panel.SetSizer(vSizer)
        panel.SetAutoLayout(1)
        vSizer.Fit(panel)
        
        
    def layoutGradientPanel(self, panel):
        mainSizer = wx.BoxSizer(wx.VERTICAL);
        topHalfSizer = wx.BoxSizer(wx.HORIZONTAL);
        bottomHalfSizer = wx.BoxSizer(wx.HORIZONTAL);
        self.addImageFrame( panel, topHalfSizer )
        self.addButtonsFrame( panel, topHalfSizer )
        self.addFormFrame( panel, bottomHalfSizer )
        mainSizer.AddMany( [ (topHalfSizer,1,wx.EXPAND), (bottomHalfSizer,0,wx.EXPAND) ] )
        panel.SetSizer(mainSizer)


    def addTextBox(self, panel, sizer, labelText, size=(85,-1)):
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(panel, -1, labelText)
        textCtrl = wx.TextCtrl(panel, -1, "", (-1,-1),size)
        hSizer.Add(label, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        hSizer.Add((1,0), 1, wx.EXPAND)
        hSizer.Add(textCtrl, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_RIGHT, 5)
        sizer.Add(hSizer,0,wx.EXPAND)
        return textCtrl
        
    def addFormFrame(self, panel, sizer):
        hSizer = wx.BoxSizer(wx.HORIZONTAL)

        box = wx.StaticBox(panel, -1, "Household Information")
        boxSizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        self.familyName = self.addTextBox(panel,boxSizer," Last Name:",size=(130,-1))
        self.address = self.addTextBox(panel,boxSizer," Address:",size=(130,-1))
        self.homePhone = self.addTextBox(panel,boxSizer," Phone:",size=(130,-1))
        hSizer.Add(boxSizer, 0, wx.EXPAND|wx.ALL, 5)

        vSizer = wx.BoxSizer(wx.VERTICAL)
        hSizer2 = wx.BoxSizer(wx.HORIZONTAL)
        box = wx.StaticBox(panel, -1, "Contact 1 Information")
        boxSizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        self.fatherName = self.addTextBox(panel,boxSizer," First Name:")
        self.fatherPhone = self.addTextBox(panel,boxSizer," Phone:")
        hSizer2.Add(boxSizer, 0, wx.EXPAND|wx.ALL, 5)
        
        box = wx.StaticBox(panel, -1, "Contact 2 Information")
        boxSizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        self.motherName = self.addTextBox(panel,boxSizer," First Name:")
        self.motherPhone = self.addTextBox(panel,boxSizer," Phone:")
        hSizer2.Add(boxSizer, 0, wx.EXPAND|wx.ALL, 5)
        
        vSizer.Add(hSizer2,0,wx.EXPAND|wx.ALL,0)

        box = wx.StaticBox(panel, -1, "Optional Fields")
        boxSizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        self.misc1 = self.addTextBox(panel,boxSizer," Miscellaneous 1:",(235,-1))
        self.misc2 = self.addTextBox(panel,boxSizer," Miscellaneous 2:",(235,-1))

        self.controls = [self.familyName, self.address, self.homePhone, self.fatherName, self.fatherPhone, self.motherName, self.motherPhone, self.misc1, self.misc2]
        vSizer.Add(boxSizer, 0, wx.EXPAND|wx.ALL, 5)
        hSizer.Add(vSizer, 0, wx.EXPAND|wx.ALL,0)
        sizer.Add(hSizer, 0, wx.EXPAND|wx.ALL, 5)

    def addImageFrame(self, panel, sizer):
        self.imageFrame = ImageFrame(panel, 0, 0)
        sizer.Add(self.imageFrame, 10, wx.EXPAND|wx.ALL)

    def setControlsState(self, state):
        for btn in self.buttons:
            btn.Enable( state )
        for btnID in self.toolbarIDs:
            self.toolbar.EnableTool(btnID, state)
        for ctrl in self.controls:
            ctrl.Enable( state )

        menuIDs = [ID_EXPORT_PDF, ID_IMPORT_CSV, ID_OPTIONS]
        self.fileMenu.Enable( ID_SAVE, state )
        for id in menuIDs:
            self.fileMenu.Enable( id, state )
            self.optionsMenu.Enable( id, state )
            


        self.Refresh()

    def addButtonsFrame(self, panel, sizer):
        buttonPanel = bp.ButtonPanel( panel, -1, "",style=bp.BP_USE_GRADIENT,alignment=bp.BP_ALIGN_TOP )
        
        btn1 = bp.ButtonInfo(buttonPanel, wx.ID_ANY, peopleAdd.GetBitmap(), kind=wx.ITEM_NORMAL, 
                             shortHelp="Create a new record", longHelp="Create a new record")
        btn2 = bp.ButtonInfo(buttonPanel, wx.ID_ANY, peopleDelete.GetBitmap(), kind=wx.ITEM_NORMAL, 
                             shortHelp="Delete this record", longHelp="Delete this record")
        btn3 = bp.ButtonInfo(buttonPanel, wx.ID_ANY, addPicture.GetBitmap(), kind=wx.ITEM_NORMAL, 
                             shortHelp="Upload a picture", longHelp="Upload a picture to use for this record")
        btn4 = bp.ButtonInfo(buttonPanel, wx.ID_ANY, deletePicture.GetBitmap(), kind=wx.ITEM_NORMAL, 
                             shortHelp="Default Picture", longHelp="Use the default picture")
        self.buttons = [btn1,btn2,btn3,btn4]
        
        self.Bind(wx.EVT_BUTTON, self.OnSaveRecord, btn1)
        self.Bind(wx.EVT_BUTTON, self.OnDeleteRecord, btn2)
        self.Bind(wx.EVT_BUTTON, self.OnNewImage, btn3)
        self.Bind(wx.EVT_BUTTON, self.OnDefaultImage, btn4)

        buttonPanel.AddButton(btn1)
        buttonPanel.AddButton(btn2)
        buttonPanel.AddSeparator()
        buttonPanel.AddButton(btn3)
        buttonPanel.AddButton(btn4)
        buttonPanel.DoLayout()
        sizer.Add(buttonPanel,0,wx.EXPAND)

class tFamily(wx.TreeItemData):
    def __init__(self, familyName, address, homePhone, 
                 fatherName, fatherPhone, 
                 motherName, motherPhone, 
                 misc1, misc2, imageIndex):
        self.familyName = familyName
        self.address = address
        self.homePhone = homePhone
        self.fatherName = fatherName
        self.fatherPhone = fatherPhone
        self.motherName = motherName
        self.motherPhone = motherPhone
        self.misc1 = misc1
        self.misc2 = misc2
        self.imageIndex = imageIndex
    def __cmp__(self, other):
        retVal = cmp(self.familyName, other.familyName)
        if retVal is 0:
            retVal = cmp(self.fatherName, other.fatherName)
            if retVal is 0:
                retVal = cmp(self.motherName, other.motherName)
                if retVal is 0:
                    retVal = cmp(self.address, other.address)
        return retVal

    def __eq__(self, other):
        if isinstance(other, tFamily):
            return self.familyName == other.familyName and self.address == other.address and self.homePhone == other.homePhone and self.fatherName == other.fatherName and self.fatherPhone == other.fatherPhone and self.motherName == other.motherName and self.motherPhone == other.motherPhone and self.misc1 == other.misc1 and self.misc2 == other.misc2 and self.imageIndex == other.imageIndex
        else:
            return NotImplemented
    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __str__(self):
        retVal = self.familyName + ", "
        if self.fatherName and self.motherName:
            return retVal + self.fatherName + " and " + self.motherName
        else:
            return retVal + self.fatherName + self.motherName
    def setImageIndex( self, imageIndex ):
        self.imageIndex = imageIndex
    def getImageIndex( self ):
        return self.imageIndex
    def getFamilyName( self ):
        retVal = " " + self.familyName
        if self.fatherName and self.motherName:
            retVal = self.fatherName + " and " + self.motherName + retVal
        else:
            retVal = self.fatherName + self.motherName + retVal
        return retVal

class ImageFrame(wx.Window):
    def __init__(self, parent, projectPath, currentImageIndex):
        wx.Window.__init__(self, parent, size=(300,200),style=wx.SUNKEN_BORDER)
        self.projectPath = None
        self.currentImageIndex = 0
        self.maxImageIndex = 0
        self.defaultImage = noImage.GetImage()

        self.image = self.defaultImage
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def setMaxImageIndex( self, index ):
        self.maxImageIndex = index

    def getMaxImageIndex( self ):
        return self.maxImageIndex

    def getCurrentImageIndex( self ):
        return self.currentImageIndex

    def setProjectPath( self, projectPath ):
        (path, filename) = os.path.split(projectPath)
        self.projectPath = path

    def newImage( self, imagePath ):
        self.maxImageIndex+=1
        img = Image.open( imagePath )
        img.thumbnail( (600,450), Image.ANTIALIAS )
        img.save( self.makeImagePath( self.maxImageIndex ) )
        self.setImage( self.maxImageIndex )

    def setImage( self, imageIndex ):
        if imageIndex > 0:
            self.image = wx.Image(self.makeImagePath(imageIndex), wx.BITMAP_TYPE_JPEG)
        else:
            self.image = self.defaultImage
        self.currentImageIndex = imageIndex
        self.Refresh()

    def makeImagePath( self, imageIndex ):
        return os.path.join(self.projectPath, "images\\%04d.jpg" % imageIndex )

    def OnPaint(self, event):
        dc= wx.PaintDC(self)
        dc= wx.BufferedDC(dc)
        
        # paint a background to show the alpha manipulation
        dc.SetBackground(wx.Brush("WHITE"))
        dc.Clear()
        image_size = self.image.GetSize()
        client_size = self.GetSizeTuple()
        proportions = (
            float(client_size[i]) / image_size[i]
            for i in xrange(len(image_size))
        )
        proportion = min(proportions) # Use the smallest proportion.
        # Can't use wx.Image.Shrink because it doesn't provide
        # enough pixel granularity -- there are serious discontinuities
        # in the shrunken sizes that can be produced.
        new_size = (pixels * proportion for pixels in image_size)

        image = self.image.Scale(*new_size)
        image_size = image.GetSize()
        offsets = ( (client_size[0] - image_size[0])/2,
                    (client_size[1] - image_size[1])/2 )
                    
        bitmap = wx.BitmapFromImage(image)
        dc.DrawBitmap(bitmap, offsets[0], offsets[1], True)

    def OnSize(self, event):
        self.Refresh()
    
    def OnEraseBackground(self, event):
        pass 




#----------------------------------------------------------------------
class tPDFCreator():
    def __init__(self, settings=None):
        self.author="Gabe Black http://DirectoryMaker.blogspot.com"
        self.pageWidth=595.27
        self.pageHeight=841.89
        self.numRows = 5
        self.numCols = 4
        self.xSpacing = 10
        self.ySpacing = 10
        self.frameImg = os.path.join(tempfile.gettempdir(),"DirectoryDefaultFrame.png")
        self.defaultImg = os.path.join(tempfile.gettempdir(),"DirectoryDefaultImage.jpg")
        imgFrame.GetImage().SaveFile( self.frameImg, wx.BITMAP_TYPE_PNG )
        noImage.GetImage().SaveFile( self.defaultImg, wx.BITMAP_TYPE_JPEG )
        self.yAdjust = -10
        self.ff = getFontCache()

        self.frameWidth = 680.0
        self.frameHeight = 580.0
        self.frameImgWidth = 600.0
        self.frameImgHeight = 450.0
        self.frameImgX = 26.0
        self.frameImgY = 130.0
        self.framePhoneY = 136.0
        self.framePhoneX = 376.0
        self.yAdjust = -10

        self.phoneRatioX = 1.0 * self.framePhoneX / self.frameWidth
        self.phoneRatioY = 1.0 * self.framePhoneY / self.frameHeight
        
        self.width=(self.pageWidth-(self.xSpacing*(self.numCols+1)))/self.numCols
        self.height=(self.pageHeight-(self.ySpacing*(self.numRows+1)))/self.numRows
        self.fontSettings = {ID_NAME_FONT:[wx.BLACK, self.makeFont( "Times New Roman", 15 )],
                             ID_ADDRESS_FONT:[wx.BLACK, self.makeFont(size=13,bold=wx.FONTWEIGHT_BOLD)],
                             ID_PHONE_FONT:[wx.BLACK, self.makeFont(size=11)],
                             ID_MISC1_FONT:[wx.BLACK, self.makeFont()],
                             ID_MISC2_FONT:[wx.BLACK, self.makeFont()],
                             }
        self.showMisc1 = True
        self.showMisc2 = True
        if settings:
            self.setSettings(settings)
        else:
            self.setDefaultOptions()

    def makeFont( self, fontName="Times New Roman", size=11, bold=wx.FONTWEIGHT_NORMAL, style=wx.FONTSTYLE_ITALIC ):
        wxFont = wx.Font(size, wx.FONTFAMILY_SWISS, style, bold, face=fontName)
        return wxFont
        
    def setDefaultOptions( self ):
        self.setOptions(self.numRows,self.numCols,self.xSpacing,self.ySpacing,self.showMisc1,self.showMisc2)
        
    def getSettings( self ):
        return [self.fontSettings[ID_NAME_FONT][FONT].GetNativeFontInfo().ToString(),
                self.fontSettings[ID_ADDRESS_FONT][FONT].GetNativeFontInfo().ToString(),
                self.fontSettings[ID_PHONE_FONT][FONT].GetNativeFontInfo().ToString(),
                self.fontSettings[ID_MISC1_FONT][FONT].GetNativeFontInfo().ToString(),
                self.fontSettings[ID_MISC2_FONT][FONT].GetNativeFontInfo().ToString(),
                self.fontSettings[ID_NAME_FONT][COLOR],
                self.fontSettings[ID_ADDRESS_FONT][COLOR],
                self.fontSettings[ID_PHONE_FONT][COLOR],
                self.fontSettings[ID_MISC1_FONT][COLOR],
                self.fontSettings[ID_MISC2_FONT][COLOR],
                self.showMisc1, self.showMisc2,
                self.numRows, self.numCols, self.xSpacing, self.ySpacing]

    def setSettings( self, settings ):
        self.fontSettings[ID_NAME_FONT][FONT] = wx.FontFromNativeInfoString( settings[0] )
        self.fontSettings[ID_ADDRESS_FONT][FONT] = wx.FontFromNativeInfoString( settings[1] )
        self.fontSettings[ID_PHONE_FONT][FONT] = wx.FontFromNativeInfoString( settings[2] )
        self.fontSettings[ID_MISC1_FONT][FONT] = wx.FontFromNativeInfoString( settings[3] )
        self.fontSettings[ID_MISC2_FONT][FONT] = wx.FontFromNativeInfoString( settings[4] )
        self.fontSettings[ID_NAME_FONT][COLOR] = settings[5]
        self.fontSettings[ID_ADDRESS_FONT][COLOR] = settings[6]
        self.fontSettings[ID_PHONE_FONT][COLOR] = settings[7]
        self.fontSettings[ID_MISC1_FONT][COLOR] = settings[8]
        self.fontSettings[ID_MISC2_FONT][COLOR] = settings[9]
        self.showMisc1 = settings[10]
        self.showMisc2 = settings[11]
        self.numRows = settings[12]
        self.numCols = settings[13]
        self.xSpacing = settings[14]
        self.ySpacing = settings[15]
        self.setDefaultOptions()

    def setOptions( self, nRows, nCols, xSpace, ySpace, showMisc1, showMisc2 ):
        self.numRows = nRows
        self.numCols = nCols
        self.xSpacing = xSpace
        self.ySpacing = ySpace
        self.showMisc1 = showMisc1
        self.showMisc2 = showMisc2
        self.width=(self.pageWidth-(self.xSpacing*(self.numCols+1)))/self.numCols
        self.height=(self.pageHeight-(self.ySpacing*(self.numRows+1)))/self.numRows

    def Y(self,y,h):
        return self.pageHeight-y-h
        
    def getBoundedRatio(self, w, h, windowW, windowH):
        ratio1 = (1.0 * windowW)/(1.0 * w)
        ratio2 = (1.0 * windowH)/(1.0 * h)
        if ratio1 < ratio2:
            return ratio1
        else:
            return ratio2
        
    def createFamily(self,c,familyData,img,row,col):
        nameSize = self.fontSettings[ID_NAME_FONT][FONT].GetPointSize()
        addressSize = self.fontSettings[ID_ADDRESS_FONT][FONT].GetPointSize()
        phoneSize = self.fontSettings[ID_PHONE_FONT][FONT].GetPointSize()
        misc1Size = self.fontSettings[ID_MISC1_FONT][FONT].GetPointSize()
        misc2Size = self.fontSettings[ID_MISC2_FONT][FONT].GetPointSize()
        x = self.xSpacing+((self.xSpacing+self.width)*col)
        y = self.Y(self.ySpacing + ((self.ySpacing+self.height)*row)+self.yAdjust, self.height)
        if img is None:
            img = self.defaultImg
        im = Image.open(img)
        (w,h) = im.size

        imgRatio = self.getBoundedRatio(w,h,self.frameImgWidth, self.frameImgHeight)
        imgWidth = imgRatio * w
        imgHeight = imgRatio * h
        frameWidth = imgWidth/self.frameImgWidth * self.frameWidth
        frameHeight = imgHeight/self.frameImgHeight * self.frameHeight
        frameRatio = self.getBoundedRatio(frameWidth, frameHeight, self.width, self.height)

        frameW = frameRatio * frameWidth
        frameH = frameRatio * frameHeight
        frameX = (-frameW + self.width)/2.0 + x
        frameY = (-frameH + self.height) + y

        imgW = frameRatio * imgWidth
        imgH = frameRatio * imgHeight
        
        # not sure why I have to put in the .025 hack... thought the math would work out...
        imgX = (-imgW + self.width)/2.0 + x - (0.025 * imgW)
        imgY = -imgH + self.height + y
        phoneX = (frameW * self.phoneRatioX) + frameX
        phoneY = (frameH * self.phoneRatioY) + frameY

        ySpace = (addressSize + nameSize) * .05
        nameY = imgY - nameSize - ySpace
        
        c.drawImage(img,imgX,imgY,imgW,imgH,None,False)
        c.drawImage(self.frameImg,frameX,frameY,frameW,frameH,[0,1,0,1,0,1],False)

        # show phone
        if familyData.homePhone and familyData.fatherPhone and familyData.motherPhone:
            # teeny weeny font size... doh!
            phoneSize = phoneSize/2.0
            self.setFont( c, ID_PHONE_FONT, phoneSize )
            c.drawString(phoneX,phoneY+phoneSize,familyData.homePhone)
            c.drawString(phoneX,phoneY,familyData.fatherPhone)
            c.drawString(phoneX,phoneY-phoneSize,familyData.motherPhone)
        elif familyData.homePhone:
            if familyData.fatherPhone or familyData.motherPhone:
                phoneSize = phoneSize/1.5
                phoneGap = phoneSize / 2.0
                self.setFont( c, ID_PHONE_FONT, phoneSize )
                phone2 = familyData.fatherPhone + familyData.motherPhone
                c.drawString(phoneX,phoneY+phoneGap,familyData.homePhone)
                c.drawString(phoneX,phoneY-phoneGap,phone2)
            else:
                self.setFont( c, ID_PHONE_FONT )
                c.drawString(phoneX,phoneY,familyData.homePhone)
        elif familyData.fatherPhone:
            if familyData.motherPhone:
                phoneSize = phoneSize/2.0
                self.setFont( c, ID_PHONE_FONT, phoneSize )
                c.drawString(phoneX,phoneY+phoneSize,familyData.fatherPhone)
                c.drawString(phoneX,phoneY,familyData.motherPhone)
            else:
                self.setFont( c, ID_PHONE_FONT )
                c.drawString(phoneX,phoneY,familyData.fatherPhone)
        elif familyData.motherPhone:
            self.setFont( c, ID_PHONE_FONT )
            c.drawString(phoneX,phoneY,familyData.motherPhone)

        # show name
        self.setFont( c, ID_NAME_FONT )
        self.drawCenteredString(c, x, nameY, familyData.getFamilyName())

        # show address
        addressY = nameY
        if familyData.address:
            addressY = nameY - addressSize - ySpace
            self.setFont( c, ID_ADDRESS_FONT )
            self.drawCenteredString(c, x, addressY, familyData.address)
        
        # optionally show misc1 and misc2
        misc1Y = addressY
        if self.showMisc1 and familyData.misc1:
            misc1Y = misc1Y - misc1Size - ySpace
            self.setFont( c, ID_MISC2_FONT )
            self.drawCenteredString(c, x, misc1Y, familyData.misc1)

        if self.showMisc2 and familyData.misc2:
            misc2Y = misc1Y - misc2Size - ySpace
            self.setFont( c, ID_MISC2_FONT )
            self.drawCenteredString(c, x, misc2Y, familyData.misc2)

    def drawCenteredString( self, c, x, y, text ):
        w = c.stringWidth( text )
        c.drawString(x+((self.width - w)/2),y,text)

    def setFont(self, c, fontID, size=0):
        wxFont = self.fontSettings[fontID][FONT]
        font = self.ff.getFont( wxFont.GetFaceName(), wxFont.GetWeight() == wx.FONTWEIGHT_BOLD, wxFont.GetStyle() == wx.ITALIC )
        if size:
            c.setFont( font.fullName, size )
        else:
            c.setFont( font.fullName, self.fontSettings[fontID][FONT].GetPointSize() )
        (r,g,b) = self.fontSettings[fontID][COLOR].Get( False )
        c.setFillColorRGB(r,g,b)
        
    def showPage( self, c ):
        c.setFont( "Helvetica", 8 )
        c.setFillColor('grey')
        msg = 'Created by Directory Maker (http://DirectoryMaker.blogspot.com)'
        w = c.stringWidth( msg )
        c.drawString((self.pageWidth-w)/2,2,msg)
        c.showPage()

    def registerFont( self, wxFont ):
        font = self.ff.getFont( wxFont.GetFaceName(), wxFont.GetWeight() == wx.FONTWEIGHT_BOLD, wxFont.GetStyle() == wx.ITALIC )
        pdfmetrics.registerFont( TTFont(font.fullName, font.fileName) )

    def embedFonts(self, c):
        self.registerFont( self.fontSettings[ID_NAME_FONT][FONT] )
        self.registerFont( self.fontSettings[ID_ADDRESS_FONT][FONT] )
        self.registerFont( self.fontSettings[ID_PHONE_FONT][FONT] )
        self.registerFont( self.fontSettings[ID_MISC1_FONT][FONT] )
        self.registerFont( self.fontSettings[ID_MISC2_FONT][FONT] )
                
# -------------------------------------

fontCachePath = os.path.join(os.getcwd(), "fontCache.info")

def listdir(root):
    # recursive listdir
    files = []
    files.append(root)
    for f in os.listdir(root):
        fullpath = os.path.join(root, f)
        if os.path.isdir(fullpath) and not os.path.islink(fullpath):
            files.extend(listdir(fullpath))
    return files

def makeFontCache():
    fontPath = []
    if "wxGTK" in wx.PlatformInfo:
        fontPath.extend(listdir("/usr/share/fonts"))
        print fontPath
    elif "wxMAC" in wx.PlatformInfo:
        fontPath.extend(listdir("~/Library/Fonts"))
        fontPath.extend(listdir("/Library/Fonts"))
        fontPath.extend(listdir("/System/Library/Fonts"))
        fontPath.extend(listdir("/Network/Library/Fonts"))
        fontPath.extend(listdir("/System Folder/Library/Fonts"))
    else:
        fontPath.extend(listdir("C:\\WINDOWS\Fonts"))
        
    ff = fontfinder.FontFinder(fontPath,useCache=False,validate=True)
    ff.search()
    try:
        ff.save(fontCachePath)
    except IOError:
        pass
    return ff

def getFontCache():
    try:
        ff = fontfinder.FontFinder()
        ff.load(fontCachePath)
        return ff
    except IOError:
        return makeFontCache()
    except EOFError:
        return makeFontCache()

def warningBox( parent, message, title="Are you sure?", style=wx.YES_NO | wx.NO_DEFAULT | wx.ICON_INFORMATION ):
    return msgBox( parent, message, title, style )

def msgBox( parent, message, title="Message", style=wx.OK | wx.ICON_INFORMATION ):
    dlg = wx.MessageDialog( parent, message, title, style )
    retVal = dlg.ShowModal()
    dlg.Destroy()
    return retVal

def runTest(frame, nb, log):
    win = TestAdjustChannels(nb, log)
    return win

#reportlab.rl_config.warnOnMissingFontGlyphs = 0
app = wx.PySimpleApp()
frame = MainWindow(None, -1, "Directory Maker")

app.MainLoop()
