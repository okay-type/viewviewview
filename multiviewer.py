'''

Multiview 
Okay Type, LLC 
(c) 2020

Things to do:

- fix case transofmrations, slash characters in input field
- use suffix menu
- in context suffix bugs

- maxlines redraw on:
    - window size change

- all caps view option
    - convert master text field to all caps
    - but keep spacecenter strings so the switcher still works

- font list
    - drop to open with no ui
        - grey out
        - close button
    - ooohh, maybe it could open/close UI

- click multiline view to select in space matrix
- show metrics (lsb width rsb) of related glyphs in main window

'''


from AppKit import NSApp
from AppKit import NSScreen
from AppKit import NSColor
from AppKit import NSDragOperationCopy
from AppKit import NSFilenamesPboardType
from AppKit import NSDragOperationMove
from AppKit import NSTextAlignmentRight
from vanilla import Window
from vanilla import Button
from vanilla import Slider
from vanilla import EditText
from vanilla import TextBox
from vanilla import CheckBox
from vanilla import Group
from vanilla import List
from vanilla import CheckBoxListCell
from vanilla import SegmentedButton
from vanilla import PopUpButton
from vanilla import ComboBox
from fontParts.world import RFont
from fontParts.world import RGlyph
from mojo.canvas import CanvasGroup
from mojo.drawingTools import rect
from mojo.drawingTools import fill
from mojo.UI import MultiLineView
from mojo.UI import SpaceMatrix
from mojo.UI import getDefault
from mojo.UI import OpenGlyphWindow
from mojo.UI import CurrentFontWindow
from mojo.roboFont import CurrentGlyph
from mojo.roboFont import FontsList
from mojo.roboFont import AllFonts
from lib.UI.spaceCenter.glyphSequenceEditText import splitText
from mojo.roboFont import CurrentFont
from mojo.events import addObserver
from mojo.events import removeObserver
from mojo.extensions import setExtensionDefault
from mojo.extensions import getExtensionDefault
from mojo.extensions import registerExtensionDefaults
from random import random
from random import choice
from itertools import repeat
from difflib import get_close_matches
from re import findall
import os

# from mojo.UI import OutputWindow
# OutputWindow().clear()

debug = False

# size prep
(screenX, screenY), (screenW, screenH) = NSScreen.mainScreen().visibleFrame()
width = screenW * 2 / 3
height = screenH
uiwidth = screenW / 6

# word-o stuff
languages = ['English', 'Streets', 'Hoefler', 'Red Wings', 'OSX Dictionary', 'Catalan', 'Czech', 'Danish', 'Dutch', 'Finnish', 'French', 'German', 'Hungarian', 'Icelandic', 'Italian', 'Latin', 'Norwegian', 'Polish', 'Slovak', 'Spanish', 'Vietnamese', 'Any language']
cases = ['Default Case', 'UPPER', 'lower', 'Title', 'Sмᴀʟʟᴄᴀᴘ', 'Random']
usecharacters = ['Only glyphs in font', 'Only selected glyphs', 'Only marked glyphs']

# size/line sliders
smallest = 18
sizes = [smallest]
ratio = 1.125
steps = 30
x = smallest
for i in range(steps):
    s = x = int(x * ratio)
    sizes.append(s)
lines = [-300, -250, -200, -150, -100, -50, 0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550]


class MultiviewToolbar():
    def __init__(self):
        self.windowname = 'Multiview'
        debugname = 'Debug'
        if debug is True:
            self.debug = Window((500, 50), debugname)
            self.debug.bind('close', self.debugClose)
            for window in [w for w in NSApp().orderedWindows() if w.isVisible()]:
                if window.title() == debugname:
                    window.close()
            self.debug.open()
        addObserver(self, 'addMultiviewToolbarButton', 'fontWindowWillShowToolbarItems')

    def debugClose(self, sender):
        removeObserver(self, 'fontWindowWillShowToolbarItems')

    def addMultiviewToolbarButton(self, notification=None):

        imagePath = '/Users/k/Ok/robofont/multiview/toolbarMultiview.pdf'
        newItem = dict(
            itemIdentifier='multiviewButton',
            label='Multiview',
            toolTip='Multiview',
            imagePath=imagePath,
            callback=self.multiviewButton
        )

        newIndex = 4
        window = CurrentFontWindow()
        vanillaWindow = window.window()
        toolbarItems = vanillaWindow.getToolbarItems()
        if 'spaceCenter' in toolbarItems:
            newIndex = list(window.toolbar).index('spaceCenter') + 1

        toolbar = notification['toolbarItems']
        toolbar.insert(newIndex, newItem)

    def multiviewButton(self, sender):
        self.multiviewButtonEvent()

    def multiviewButtonEvent(self, notification=None):
        windowNames = []
        for window in NSApp().orderedWindows():
            windowNames.append(window.title())
        if self.windowname not in windowNames:
            self.doMultiview()
        else:
            self.showselected()

    def doMultiview(self):
        self.prefKey = 'com.okaytype.multiviewer'
        self.setupWindow()
        self.setupViewer()
        self.setupUI()
        self.setupMLView()
        self.fontListAddOpen()
        self.loadPreferences()
        self.w.open()

    def setupWindow(self):
        self.w = Window(
            (width, height),
            self.windowname,
            minSize=(screenW / 2, screenH / 2),
            textured=True,
            closable=True,
            miniaturizable=True,
            titleVisible=True,
        )
        self.w.bind('close', self.windowClose)
        addObserver(self, 'openedFont', 'fontDidOpen')
        addObserver(self, 'openedFont', 'newFontDidOpen')
        addObserver(self, 'closedFont', 'fontWillClose')
        addObserver(self, 'glyphChanged', 'currentGlyphChanged')
        addObserver(self, 'viewDidChangeGlyph', 'viewDidChangeGlyph')
        addObserver(self, 'trigger', 'multiviewKey')
        addObserver(self, 'windowClose', 'applicationWillTerminate')

    def testResize(self, notification):
        print('testResize', notification)

    def windowClose(self, sender):
        print('multiview window closed')
        for i, font in enumerate(self.w.ui.fonts.list):
            if font['fontname'] == '⇅':
                font['ufo'].close()
        print('close', self.w.preview.control.sequence.get())
        setExtensionDefault(self.prefKey + '.preview.control.sequence', self.w.preview.control.sequence.get())
        setExtensionDefault(self.prefKey + '.ui.view.seperate', self.w.ui.view.seperate.get())
        setExtensionDefault(self.prefKey + '.ui.view.lines', self.w.ui.view.lines.get())
        xywh = list(self.w.getPosSize())
        setExtensionDefault(self.prefKey + '.win.screenX', xywh[0])
        setExtensionDefault(self.prefKey + '.win.screenY', xywh[1])
        setExtensionDefault(self.prefKey + '.win.screenW', xywh[2])
        setExtensionDefault(self.prefKey + '.win.screenH', screenH)
        removeObserver(self, 'fontDidOpen')
        removeObserver(self, 'newFontDidOpen')
        removeObserver(self, 'fontWillClose')
        removeObserver(self, 'currentGlyphChanged')
        removeObserver(self, 'viewDidChangeGlyph')
        removeObserver(self, 'multiviewKey')

    def setupViewer(self):
        # preview
        self.w.preview = preview = Group((0, 0, -0, -0))
        preview.lineview = MultiLineView(
            (0, 0, -uiwidth, -0),
            pointSize=69,
            lineHeight=1,
            doubleClickCallback=self.lineviewClick)
        # preview.lineview.contentView()._buffer = 25  # padding
        # text field and matrix editor
        preview.control = CanvasGroup((0, -70, -uiwidth, 70), delegate=ControlCanvas(self.w, 'matrix'))
        preview.control.matrix = SpaceMatrix((0, 0, -0, -3), callback=self.spaceMatrixCallback)
        preview.control.matrix.show(False)
        preview.control.character = EditText((0, -17.5, 67, 18), '', placeholder='HH', sizeStyle='small', callback=self.setupMLView)
        preview.control.sequence = ComboBox(
            (66, -17, -0, 17),
            items=[],
            continuous=True,
            completes=True,
            sizeStyle='small',
            callback=self.setupMLView
        )
        scTexts = getDefault('spaceCenterInputSamples')
        preview.control.sequence.setItems(scTexts)
        preview.control.sequence.set('Onions are delicious')
        preview.control.sequence.getNSComboBox().setNumberOfVisibleItems_(20)
        # preview.control.sequence.getNSTextField().setBordered_(0)

    def lineviewClick(self, sender):
        g = sender.getSelectedGlyph()
        if g is not None:
            OpenGlyphWindow(g, newWindow=False)

    def setupUI(self):
        # ui panel
        self.w.uitoggle = CanvasGroup((-uiwidth, 0, uiwidth, -70), delegate=ControlCanvas(self.w, 'ui'))
        self.w.ui = ui = CanvasGroup((-uiwidth, 0, uiwidth, -0), delegate=UICanvas(self.w))
        ui.showhide = CheckBox((10, -23, -10, 20), 'Autohide', value=False, sizeStyle='mini', callback=self.showHideUI)
        if ui.showhide is True:
            self.w.ui.show(False)
        self.setupUIFonts()
        # self.setupUIControlChar()
        self.setupUIViewOptions()
        self.setupUIManipulate()
        self.setupUIWordo()
        self.setupUIContext()

    def setupUIFonts(self):
        # ui fonts control
        ui = self.w.ui
        self.y = y = 5
        self.b = 20
        h = self.b * 8
        ui.fonts = Group((10, y, -10, h))
        # ui font control guts
        ui.fonts.label = TextBox((0, 0, -0, self.b), 'Fonts')
        ui.fonts.list = List(
            (0, self.b, -0, -0), [],
            columnDescriptions=[
                {'title': 'On', 'key': 'onoff', 'width': 10,
                    'cell': CheckBoxListCell()},
                {'title': 'Font', 'key': 'fontname', 'editable': False},
                {'title': 'UFO', 'key': 'ufo', 'width': 0},
                {'title': 'ghostUI', 'key': 'ghostui', 'width': 0},
                {'title': 'ghostUIgroup', 'key': 'ghostui', 'width': 0},
            ],
            rowHeight=self.b,
            showColumnTitles=False,
            enableDelete=True,
            editCallback=self.setupMLView,
            allowsMultipleSelection=True,
            drawFocusRing=False,
            dragSettings=dict(
                type='genericListPboardType',
                callback=self.dragCallback
            ),
            selfDropSettings=dict(
                type='genericListPboardType',
                operation=NSDragOperationMove,
                callback=self.selfDropCallback
            ),
            # drop unopened ufos
            otherApplicationDropSettings=dict(
                type=NSFilenamesPboardType,
                operation=NSDragOperationCopy,
                callback=self.addCloakedUFO
            ),
        )
        ui.fonts.list.getNSTableView().setUsesAlternatingRowBackgroundColors_(False)
        ui.fonts.list.getNSScrollView().setBorderType_(0)
        ui.fonts.list.getNSTableView().setBackgroundColor_(NSColor.clearColor())
        ui.fonts.list.getNSScrollView().setDrawsBackground_(0)
        ui.fonts.list.getNSTableView().setFocusRingType_(1)
        ui.fonts.sort = Button((-20, 0, 26, 16), '⤭', callback=self.fontListResort)
        flatButt(ui.fonts.sort, 'Resort Font List')
        ui.fonts.int = Button((-45, 0, 26, 16), '👻', callback=self.fontListAddInterpolated)
        flatButt(ui.fonts.int, 'Summon Ghost Instance')
        self.y = y + h + self.b

    # def setupUIControlChar(self):
    #     ui = self.w.ui
    #     y = self.y
    #     height = h = self.b*2
    #     ui.control = Group((10, y, -10, h))
    #     ui.control.label = TextBox('auto', 'Control')
    #     ui.control.pre = EditText('auto', '', placeholder='Pre', sizeStyle='mini')
    #     ui.control.after = EditText('auto', '', placeholder='After', sizeStyle='mini')

    #     rules = [
    #         'H:|[label]|',
    #         'H:|[pre][after(==pre)]|',
    #         'V:|[label][pre(==label)]|',
    #         'V:|[label][after(==label)]|',
    #     ]
    #     ui.control.addAutoPosSizeRules(rules)

        self.y = y + h + self.b

    def setupUIViewOptions(self):
        ui = self.w.ui
        y = self.y
        h = self.b * 10
        ui.view = Group((10, y, -10, h))
        ui.view.label = TextBox('auto', 'View Options')
        x = ui.view
        x.sizevalue = TextBox((0, self.b * 3, -0, self.b), '1', sizeStyle='mini')
        x.linevalue = TextBox((0, self.b * 4, -0, self.b), '2', sizeStyle='mini')
        x.padvalue = TextBox((0, self.b * 5, -0, self.b), '3', sizeStyle='mini')
        x.offsetYvalue = TextBox((0, self.b * 6, -0, self.b), '4', sizeStyle='mini')
        x.maxvalue = TextBox((0, self.b * 7, -0, self.b), '5', sizeStyle='mini')
        x.sizevalue.getNSTextField().setAlignment_(NSTextAlignmentRight)
        x.linevalue.getNSTextField().setAlignment_(NSTextAlignmentRight)
        x.padvalue.getNSTextField().setAlignment_(NSTextAlignmentRight)
        x.offsetYvalue.getNSTextField().setAlignment_(NSTextAlignmentRight)
        x.maxvalue.getNSTextField().setAlignment_(NSTextAlignmentRight)

        # seperate with
        ui.view.sl = TextBox('auto', 'Seperate', sizeStyle='mini')
        ui.view.seperate = SegmentedButton(
            'auto', [
                {'title': 'Nothing'},
                {'title': 'Space'},
                {'title': 'Break', 'selected': True},
                {'title': '2x'},
                {'title': 'All'}
            ],
            callback=self.setupMLView,
            selectionStyle='one',
            sizeStyle='mini')
        ui.view.seperate.set(2)
        # show as
        ui.view.sa = TextBox('auto', 'Show as', sizeStyle='mini')
        ui.view.showas = SegmentedButton(
            'auto', [
                {'title': 'Fonts', 'selected': True},
                {'title': 'Lines'},
                {'title': 'Glyphs'},
            ],
            callback=self.setupMLView,
            selectionStyle='one',
            sizeStyle='mini')
        ui.view.showas.set(0)
        # view options
        ui.view.sizelabel = TextBox('auto', 'Size', sizeStyle='mini')
        ui.view.size = Slider(
            'auto',
            callback=self.viewSize,
            sizeStyle='mini',
            tickMarkCount=False,
            # tickMarkCount=len(sizes),
            maxValue=len(sizes) - 1,
            stopOnTickMarks=True,
            continuous=True)
        ui.view.linelabel = TextBox('auto', 'Line', sizeStyle='mini')
        ui.view.line = Slider(
            'auto',
            callback=self.viewLine,
            sizeStyle='mini',
            tickMarkCount=False,
            # tickMarkCount=len(lines),
            maxValue=len(lines) - 1,
            stopOnTickMarks=True,
            continuous=True)
        ui.view.padlabel = TextBox('auto', 'Pad', sizeStyle='mini')
        ui.view.pad = Slider(
            'auto',
            callback=self.viewPad,
            sizeStyle='mini',
            tickMarkCount=False,
            # tickMarkCount=10,
            maxValue=60,
            stopOnTickMarks=True,
            continuous=True)
        ui.view.offsetylabel = TextBox('auto', 'Y off', sizeStyle='mini')
        ui.view.offsety = Slider(
            'auto',
            callback=self.viewPad,
            sizeStyle='mini',
            tickMarkCount=False,
            # tickMarkCount=10,
            maxValue=60,
            stopOnTickMarks=True,
            continuous=True)
        self.linesslidermaximum = 12
        ui.view.lineslabel = TextBox('auto', 'Max', sizeStyle='mini')
        ui.view.lines = Slider(
            'auto',
            callback=self.viewMax,
            value=1,
            sizeStyle='mini',
            tickMarkCount=False,
            # tickMarkCount=self.linesslidermaximum-1,
            maxValue=self.linesslidermaximum,
            stopOnTickMarks=True,
            continuous=True)
        ui.view.metrics = CheckBox('auto', 'Metrics', sizeStyle='mini', callback=self.viewMetrics)
        ui.view.invert = CheckBox('auto', 'Invert', sizeStyle='mini', callback=self.viewInvert)
        ui.view.wrap = CheckBox('auto', 'Wrap', value=True, sizeStyle='mini', callback=self.viewWrap)
        ui.view.rotate = CheckBox('auto', 'Rotate', sizeStyle='mini', callback=self.viewRotate)

        ui.view.center = CheckBox('auto', 'Center', sizeStyle='mini', callback=self.viewCenter)
        ui.view.kerning = CheckBox('auto', 'Kerning', sizeStyle='mini', callback=self.viewKerns)
        ui.view.aspath = CheckBox('auto', 'As Path', sizeStyle='mini', callback=self.viewPath)
        ui.view.flip = CheckBox('auto', 'Flip', sizeStyle='mini', callback=self.viewFlip)
        rules = [
            'H:|[label]|',
            'H:|[showas]-[sa(==center)]|',
            'H:|[seperate]-[sl(==center)]|',
            'H:|[size]-[sizelabel(==center)]|',
            'H:|[line]-[linelabel(==center)]|',
            'H:|[pad]-[padlabel(==center)]|',
            'H:|[offsety]-[offsetylabel(==center)]|',
            'H:|[lines]-[lineslabel(==center)]|',
            'H:|[metrics(==center)]-[invert(==center)]-[wrap(==center)]-[flip(==center)]|',
            'H:|[center]-[kerning(==center)]-[aspath(==center)]-[rotate(==center)]|',

            'V:|[label(==sl)][sa][sl][sizelabel(==sl)][linelabel(==sl)][padlabel(==sl)][offsetylabel(==sl)][lineslabel(==sl)][metrics(==sl)][center(==sl)]|',
            'V:|[label][showas(==sl)][seperate(==sl)][size(==sl)][line(==sl)][pad(==sl)][offsety(==sl)][lines(==sl)][invert(==sl)][kerning(==sl)]|',
            'V:|[label][showas(==sl)][seperate(==sl)][size(==sl)][line(==sl)][pad(==sl)][offsety(==sl)][lines(==sl)][wrap(==sl)][aspath(==sl)]|',
            'V:|[label][showas(==sl)][seperate(==sl)][size(==sl)][line(==sl)][pad(==sl)][offsety(==sl)][lines(==sl)][flip(==sl)][rotate(==sl)]|',
        ]
        ui.view.addAutoPosSizeRules(rules)

        self.y = y + h + self.b

    def setupUIManipulate(self):
        # ui maniuplate
        ui = self.w.ui
        y = self.y
        h = self.b * 5
        ui.maniuplate = Group((10, y, -10, h))
        # ui maniuplate guts
        ui.maniuplate.label = TextBox('auto', 'Manipulate Text')
        ui.maniuplate.b1 = Button('auto', 'HH', sizeStyle='mini', callback=self.setCase)
        ui.maniuplate.b2 = Button('auto', 'Hh', sizeStyle='mini', callback=self.setCase)
        ui.maniuplate.b3 = Button('auto', 'hh', sizeStyle='mini', callback=self.setCase)
        ui.maniuplate.b4 = Button('auto', 'Hн', sizeStyle='mini', callback=self.setCase)
        ui.maniuplate.b5 = Button('auto', '– H', sizeStyle='mini', callback=self.subH)
        ui.maniuplate.b6 = Button('auto', '+ H', sizeStyle='mini', callback=self.addH)
        ui.maniuplate.b7 = Button('auto', 'H H ✽ H H', sizeStyle='mini', callback=self.hhxhh)
        ui.maniuplate.b8 = Button('auto', '˙ → Ȧ Ḃ Ċ Ḋ', sizeStyle='mini', callback=self.accentall)
        ui.maniuplate.bA = Button('auto', '˙ → Ȧ', sizeStyle='mini', callback=self.accentone)
        ui.maniuplate.b9 = Button('auto', 'Select ✽', sizeStyle='mini', callback=self.selectsc)
        ui.maniuplate.bB = Button('auto', '✽?', sizeStyle='mini', callback=self.randomselected)
        ui.maniuplate.bC = Button('auto', '✽', sizeStyle='mini', callback=self.showselected)
        rules = [
            # Horizontal
            'H:|[label]|',
            'H:|[b1]-[b2(==b1)]-[b3(==b1)]-[b4(==b1)]|',
            'H:|[b5]-[b6(==b5)]-[bB(==b5)]-[bC(==b5)]|',
            'H:|[b7]-[b8(==b7)]|',
            'H:|[b9]-[bA(==b9)]|',
            # Vertical
            'V:|[label][b1(==label)][b5(==label)][b7(==label)][b9(==label)]|',
            'V:|[label][b2(==label)][b6(==label)][b7(==label)][b9(==label)]|',
            'V:|[label][b3(==label)][bB(==label)][b8(==label)][bA(==label)]|',
            'V:|[label][b4(==label)][bC(==label)][b8(==label)][bA(==label)]|',
        ]
        ui.maniuplate.addAutoPosSizeRules(rules)
        self.y = y + h + self.b

    def setupUIWordo(self):
        # ui word-o
        ui = self.w.ui
        y = self.y
        h = self.b * 6
        ui.wordo = Group((10, y, -10, h))

        # ui word-o guts
        ui.wordo.label = TextBox('auto', 'Word-o-matic')

        ui.wordo.languages = PopUpButton('auto', languages, sizeStyle='mini', callback=self.wordolanguages)
        ui.wordo.cases = PopUpButton('auto', cases, sizeStyle='mini', callback=self.wordocases)
        ui.wordo.characters = PopUpButton('auto', usecharacters, sizeStyle='mini', callback=self.wordocharacters)

        ui.wordo.requirecurrent = CheckBox('auto', 'Require CurrentGlyph', sizeStyle='mini', callback=self.wordorequirecurrent)
        ui.wordo.requireselected = CheckBox('auto', 'Require Selected', sizeStyle='mini', callback=self.wordorequireselected)
        ui.wordo.requiremarked = CheckBox('auto', 'Require Marked', sizeStyle='mini', callback=self.wordorequiremarked)

        ui.wordo.words = EditText('auto', '7', sizeStyle='mini', callback=self.wordowordsd)
        ui.wordo.min = EditText('auto', '2', sizeStyle='mini', callback=self.wordomin)
        ui.wordo.max = EditText('auto', '69', sizeStyle='mini', callback=self.wordomax)
        ui.wordo.t1 = TextBox('auto', 'Words', sizeStyle='mini')
        ui.wordo.t2 = TextBox('auto', 'Min', sizeStyle='mini')
        ui.wordo.t3 = TextBox('auto', 'Max', sizeStyle='mini')
        ui.wordo.b1 = Button('auto', 'Get Word-o', sizeStyle='mini', callback=self.wordo)
        rules = [
            'H:|[label]|',
            'H:|[languages]-[characters(==languages)]|',
            'H:|[cases]-[requireselected(==cases)]|',
            'H:|[words]-[min(==words)]-[max(==words)]-[requiremarked(==languages)]|',
            'H:|[t1]-[t2(==t1)]-[t3(==t1)]-[requirecurrent(==languages)]|',
            'H:|[b1]|',
            'V:|[label][languages(==label)][cases(==label)]-6-[words(==16)][t1(==15)][b1(==label)]|',
            'V:|[label][languages(==label)][cases(==label)]-6-[min(==16)][t2(==15)][b1(==label)]|',
            'V:|[label][languages(==label)][cases(==label)]-6-[max(==16)][t3(==15)][b1(==label)]|',
            'V:|[label][characters(==label)][requirecurrent(==label)][requireselected(==label)][requiremarked(==label)][b1(==label)]|',
            'V:|[label][characters(==label)][requirecurrent(==label)][requireselected(==label)][requiremarked(==label)][b1(==label)]|',
            'V:|[label][characters(==label)][requirecurrent(==label)][requireselected(==label)][requiremarked(==label)][b1(==label)]|',
        ]
        ui.wordo.addAutoPosSizeRules(rules)
        self.initialWordO()
        self.y = y + h + self.b

    def setupUIContext(self):
        # ui con-text
        ui = self.w.ui
        y = self.y
        h = self.b * 4
        ui.context = Group((10, y, -10, h))
        # ui con-text guts
        ui.context.label = TextBox('auto', 'Glyphs In Context')
        ui.context.auto = CheckBox('auto', 'Automatic', sizeStyle='mini', callback=self.contextauto)
        ui.context.glyph = CheckBox('auto', 'Glyph', value=True, sizeStyle='mini', callback=self.contextglyph)
        ui.context.HH = CheckBox('auto', 'HH Spacing', value=True, sizeStyle='mini', callback=self.contextHH)
        ui.context.space = CheckBox('auto', 'Space Between', value=True, sizeStyle='mini', callback=self.contextspace)
        ui.context.string = CheckBox('auto', 'Context String', value=True, sizeStyle='mini', callback=self.contextstring)
        ui.context.line = CheckBox('auto', 'Line Breaks', value=True, sizeStyle='mini', callback=self.contextline)
        ui.context.b1 = Button('auto', '✽ in Context', sizeStyle='mini', callback=self.incontext)
        rules = [
            'H:|[label]|',
            'H:|[auto][HH(==auto)][space(==auto)]|',
            'H:|[glyph][string(==glyph)][line(==glyph)]|',
            'H:|[b1]|',
            'V:|[label][auto(==label)][glyph(==label)][b1(==label)]|',
            'V:|[label][HH(==label)][string(==label)][b1(==label)]|',
            'V:|[label][space(==label)][line(==label)][b1(==label)]|',
        ]
        ui.context.addAutoPosSizeRules(rules)
        self.y = y + h + self.b
        self.initializeIncontext()

    def spaceMatrixCallback(self, sender):
        lineview = self.w.preview.lineview
        lineview.update()

    #############################################
    # ui helpers
    #############################################

    def showHideUI(self, sender):
        check = sender.get()
        wrap = self.w.ui.view.wrap.get()
        if check == 1 and wrap == 1:
                self.w.preview.lineview.setPosSize((0, 0, -0, -0))
        elif check == 0 and wrap == 1:
                self.w.preview.lineview.setPosSize((0, 0, -uiwidth, -0))
        else:
            self.w.preview.lineview.setPosSize((0, 0, 100000, -0))
        self.setupMLView()
        setExtensionDefault(self.prefKey + '.ui.showhide', sender.get())

    #############################################
    # make preview happen
    #############################################

    def setupMLView(self, sender=None):
        # choose your own adventure
        sortas = self.w.ui.view.showas.get()
        if sortas == 0:
            # short as fonts
            self.MLViewAsFonts()
        if sortas == 1:
            # short as lines
            self.MLViewAsLines()
        if sortas == 2:
            # short as glyphs
            self.MLViewAsGlyphs()

    def MLViewAsLines(self):
        # requires line breaks to work
        fontsep = self.w.ui.view.seperate.get()
        if fontsep == 0 or fontsep == 1:
            self.w.ui.view.seperate.set(2)

        fontlist = self.w.ui.fonts.list.get()
        glyphs = []

        if len(fontlist) > 0:
            self.updateGhosts()
            lineview = self.w.preview.lineview
            fontsep = self.w.ui.view.seperate.get()
            text = self.w.preview.control.sequence.get()
            control = self.w.preview.control.character.get()
            if len(control) > 0:
                text = self.intersperse(text, control)
            viewwidth = self.w.preview.lineview.getNSScrollView().frameSize()[0] - self.w.ui.view.pad.get() * 2
            ptsize = self.w.preview.lineview.getPointSize()

            # get first font (and pop it from the fontlist)
            font = fontlist.pop(0)

            # if font visibility is checked, prep things
            if font['onoff'] is True and font['ufo'] is not None:
                linecount = linewidth = 0
                f = font['ufo']
                glyphOrder = f.glyphOrder[:]
                cmap = f.getCharacterMapping()
                fontspecifictext = splitText(text, cmap)
                lineview.setFont(f)
                lines = int(self.w.ui.view.lines.get() + 1)
                if lines == self.linesslidermaximum + 1:
                    lines = 1000000000

                # temp glyphs in current line
                lineglyphs = []

                for character in fontspecifictext:
                    # needs to know what a break character is inserted
                    # stop if we hit max lines
                    if linecount >= lines:
                        break
                    # if line break
                    if fontsep == 4 and character == 'space':
                        character = '\n'
                    if character == '\n' or character == '\\n':
                        # # # REPEAT LINE AS OTHER FONTS
                        glyphs, lineview, lineglyphs = self.doNextFont(glyphs, lineview, fontlist, lineglyphs, fontsep)
                            # # # do before new line, eh
                        linecount += 1
                        linewidth = 0
                    # if special current glyph character
                    elif character == '/?':
                        if CurrentGlyph():
                            glyph = f[character]
                            linewidth += self.upmPixel(glyph.width, ptsize)
                            if linewidth < viewwidth:
                                glyphs.append(glyph)
                                lineglyphs.append(glyph)  # # #
                            elif linewidth >= viewwidth:
                                # # # REPEAT LINE AS OTHER FONTS
                                glyphs, lineview, lineglyphs = self.doNextFont(glyphs, lineview, fontlist, lineglyphs, fontsep)
                                    # # # do before new line, eh
                                linewidth = 0
                                linecount += 1
                                if linecount < lines:
                                    glyphs.append(glyph)
                                    lineglyphs.append(glyph)  # # #
                                    linewidth += self.upmPixel(glyph.width, ptsize)
                    # if character
                    else:
                        if character in glyphOrder:
                            glyph = f[character]
                            linewidth += self.upmPixel(glyph.width, ptsize)
                            if linewidth < viewwidth:
                                glyphs.append(glyph)
                                lineglyphs.append(glyph)  # # #
                            elif linewidth >= viewwidth:
                                # # # REPEAT LINE AS OTHER FONTS
                                glyphs, lineview, lineglyphs = self.doNextFont(glyphs, lineview, fontlist, lineglyphs, fontsep)
                                    # # # do before new line, eh
                                linewidth = 0
                                linecount += 1
                                if linecount < lines and character != 'space':
                                    glyphs.append(glyph)
                                    lineglyphs.append(glyph)  # # #
                                    linewidth += self.upmPixel(glyph.width, ptsize)
                # # # Do last line
                if len(lineglyphs) > 0:
                    # # # REPEAT LINE AS OTHER FONTS
                    glyphs, lineview, lineglyphs = self.doNextFont(glyphs, lineview, fontlist, lineglyphs, fontsep)
                # end with seperator
                if fontsep == 2 or fontsep == 4:
                    linebreak = lineview.createNewLineGlyph()
                    glyphs.append(linebreak)
                if fontsep == 3:
                    linebreak = lineview.createNewLineGlyph()
                    glyphs.append(linebreak)
                    glyphs.append(linebreak)
            # apply thing
            lineview.set(glyphs)
            self.w.preview.control.matrix.set(glyphs)

    def doNextFont(self, glyphs, lineview, fontlist, lineglyphs, fontsep):
        # break after font
        linebreak = lineview.createNewLineGlyph()
        glyphs.append(linebreak)
        # do other fonts
        for font in fontlist:
            if font['onoff'] is True and font['ufo'] is not None:
                f = font['ufo']
                glyphOrder = f.glyphOrder[:]
                lineview.setFont(f)
                for character in lineglyphs:
                    character = character.name
                    # if line break
                    if fontsep == 4 and character == 'space':
                        character = '\n'
                    if character == '\n' or character == '\\n':
                        linebreak = lineview.createNewLineGlyph()
                        glyphs.append(linebreak)
                    # if special current glyph character
                    elif character == '/?':
                        if CurrentGlyph():
                            glyph = f[character]
                            glyphs.append(glyph)
                    # if character
                    else:
                        if character in glyphOrder:
                            glyph = f[character]
                            glyphs.append(glyph)
                # break after font
                linebreak = lineview.createNewLineGlyph()
                glyphs.append(linebreak)
        # return glyphs, lineview, and an empty lineglyphs
        return glyphs, lineview, []

    def MLViewAsGlyphs(self):
        fontlist = self.w.ui.fonts.list.get()
        glyphs = []

        if len(fontlist) > 0:
            self.updateGhosts()
            lineview = self.w.preview.lineview
            fontsep = self.w.ui.view.seperate.get()
            text = self.w.preview.control.sequence.get()
            control = self.w.preview.control.character.get()
            if len(control) > 0:
                text = self.intersperse(text, control)
            viewwidth = self.w.preview.lineview.getNSScrollView().frameSize()[0] - self.w.ui.view.pad.get() * 2
            ptsize = self.w.preview.lineview.getPointSize()
            # get only active fonts
            for font in fontlist:
                if font['onoff'] is False:
                    fontlist.remove(font)
            # setup using the first font
            font = fontlist[0]
            linecount = linewidth = 0
            f = font['ufo']
            glyphOrder = f.glyphOrder[:]
            # need to test to see if different character sets matter here
            cmap = f.getCharacterMapping()
            fontspecifictext = splitText(text, cmap)
            lineview.setFont(f)
            lines = int(self.w.ui.view.lines.get() + 1)
            if lines == self.linesslidermaximum + 1:
                lines = 1000000000
            for character in fontspecifictext:
                for font in fontlist:
                    f = font['ufo']
                    lineview.setFont(f)
                    # stop if we hit max lines
                    if linecount >= lines:
                        break
                    # if line break
                    if fontsep == 4 and character == 'space':
                        character = '\n'
                    if character == '\n' or character == '\\n':
                        linecount += 1
                        linewidth = 0
                    # if special current glyph character
                    elif character == '/?':
                        if CurrentGlyph():
                            glyph = f[character]
                            linewidth += self.upmPixel(glyph.width, ptsize)
                            if linewidth < viewwidth:
                                glyphs.append(glyph)
                            elif linewidth >= viewwidth:
                                linewidth = 0
                                linecount += 1
                                if linecount < lines:
                                    glyphs.append(glyph)
                                    linewidth += self.upmPixel(glyph.width, ptsize)
                    # if character
                    else:
                        if character in glyphOrder:
                            try:
                                glyph = f[character]
                                linewidth += self.upmPixel(glyph.width, ptsize)
                                if linewidth < viewwidth:
                                    glyphs.append(glyph)
                                elif linewidth >= viewwidth:
                                    linewidth = 0
                                    linecount += 1
                                    if linecount < lines and character != 'space':
                                        glyphs.append(glyph)
                                        linewidth += self.upmPixel(glyph.width, ptsize)
                            except:
                                pass
            if fontsep == 2 or fontsep == 4:
                linebreak = lineview.createNewLineGlyph()
                glyphs.append(linebreak)
            if fontsep == 3:
                linebreak = lineview.createNewLineGlyph()
                glyphs.append(linebreak)
                glyphs.append(linebreak)
            # apply thing
            lineview.set(glyphs)
            self.w.preview.control.matrix.set(glyphs)

    def MLViewAsFonts(self):
        fontlist = self.w.ui.fonts.list.get()
        glyphs = []
        if len(fontlist) > 0:
            self.updateGhosts()
            lineview = self.w.preview.lineview
            fontsep = self.w.ui.view.seperate.get()
            text = self.w.preview.control.sequence.get()
            control = self.w.preview.control.character.get()
            if len(control) > 0:
                text = self.intersperse(text, control)
            viewwidth = self.w.preview.lineview.getNSScrollView().frameSize()[0] - self.w.ui.view.pad.get() * 2
            ptsize = self.w.preview.lineview.getPointSize()
            for font in fontlist:
                linecount = linewidth = 0
                if font['onoff'] is True and font['ufo'] is not None:
                    f = font['ufo']
                    glyphOrder = f.glyphOrder[:]
                    cmap = f.getCharacterMapping()
                    fontspecifictext = splitText(text, cmap)
                    lineview.setFont(f)
                    lines = int(self.w.ui.view.lines.get() + 1)
                    if lines == self.linesslidermaximum + 1:
                        lines = 1000000000
                    for character in fontspecifictext:
                        if linecount >= lines:
                            break
                        if fontsep == 0 or fontsep == 1:
                            character = character.replace(' \n', 'space').replace('\\n', 'space').replace('\n', 'space')
                        if fontsep == 4 and character == 'space':
                            character = '\n'
                        if character == '\n' or character == '\\n':
                            if fontsep != 0 or fontsep != 1:
                                linebreak = lineview.createNewLineGlyph()
                                glyphs.append(linebreak)
                                linecount += 1
                                linewidth = 0
                        # if space
                        elif character == 'space' and fontsep == 0:
                            continue
                        elif character == '/?':
                            if CurrentGlyph():
                                glyph = f[character]
                                linewidth += self.upmPixel(glyph.width, ptsize)
                                if linewidth < viewwidth:
                                    glyphs.append(glyph)
                                elif linewidth >= viewwidth:
                                    linewidth = 0
                                    linecount += 1
                                    if linecount < lines:
                                        glyphs.append(glyph)
                                        linewidth += self.upmPixel(glyph.width, ptsize)
                        else:
                            if character in glyphOrder:
                                glyph = f[character]
                                linewidth += self.upmPixel(glyph.width, ptsize)
                                if linewidth < viewwidth:
                                    glyphs.append(glyph)
                                elif linewidth >= viewwidth and character != 'space':
                                    linewidth = 0
                                    linecount += 1
                                    if linecount < lines:
                                        glyphs.append(glyph)
                                        linewidth += self.upmPixel(glyph.width, ptsize)
                    if fontsep == 1:
                        if 'space' in glyphOrder:
                             glyphs.append(f['space'])
                        else:
                            spacebreak = lineview.createEmptyGlyph()
                            glyphs.append(spacebreak)
                    if fontsep == 2 or fontsep == 4:
                        linebreak = lineview.createNewLineGlyph()
                        glyphs.append(linebreak)
                    if fontsep == 3:
                        linebreak = lineview.createNewLineGlyph()
                        glyphs.append(linebreak)
                        glyphs.append(linebreak)
            lineview.set(glyphs)
            self.w.preview.control.matrix.set(glyphs)

    def upmPixel(self, glyphwidth, ptsize):
        return glyphwidth / 1000 * ptsize

    def intersperse(self, text, control):
        newtext = ''
        for character in text:
            newtext += control
            newtext += character
        newtext += control
        return newtext

    oldglyphs = []

    def history(self, glyphs):
        # save old text strings so we can go back but limit it to 20 or so because performance
        self.oldglyphs.append(glyphs)
        self.oldglyphs[20:]

    def historyback(self):
        current = self.w.preview.control.sequence.get()
        if current in self.oldglyphs:
            count = len(self.oldglyphs)
            index = self.oldglyphs.index(current)
            nextitem = index - 1
            if nextitem < 0:
                nextitem = count - 1
            glyphs = self.oldglyphs[nextitem]
            del self.oldglyphs[index]
            self.w.preview.control.sequence.set(glyphs)
            self.setupMLView()

    #############################################
    # font list stuff
    #############################################

    def dragCallback(self, sender, indexes):
        self.fontlistGhostPos()
        return indexes

    def selfDropCallback(self, sender, dropInfo):
        isProposal = dropInfo['isProposal']
        if not isProposal:
            indexes = [int(i) for i in sorted(dropInfo['data'])]
            indexes.sort()
            rowIndex = dropInfo['rowIndex']
            items = sender.get()
            toMove = [items[index] for index in indexes]
            for index in reversed(indexes):
                del items[index]
            rowIndex -= len([index for index in indexes if index < rowIndex])
            for font in toMove:
                items.insert(rowIndex, font)
                rowIndex += 1
            sender.set(items)
        self.fontlistGhostPos()
        self.setupMLView()
        # udpate ghostlist
        if len(self.ghostfonts) != 0:
            fonts = self.w.ui.fonts.list
            for gfd in self.ghostfonts:
                ghostfont = gfd['ufo']
                for i, x in enumerate(fonts):
                    if x['ufo'] == ghostfont:
                        gfd['masterA'] = fonts[i - 1]['ufo']
                        gfd['masterB'] = fonts[i + 1]['ufo']
        return True

    def fontListAddOpen(self):
        for f in self.sortedAllFonts():
            font = {}
            font['onoff'] = True
            font['fontname'] = f.info.familyName + ' ' + f.info.styleName
            font['ufo'] = f
            self.w.ui.fonts.list.append(font)
        self.fontlistFitter()

    def sortedAllFonts(self):
        allFonts = FontsList(AllFonts())
        allFonts.sortBy('styleName', reverse=False)
        allFonts.sortBy('weightValue', reverse=False)
        allFonts.sortBy('widthValue', reverse=False)
        allFonts.sortBy('isProportional', reverse=False)
        return allFonts

    def closedFont(self, notification):
        for i, x in enumerate(self.w.ui.fonts.list):
            if notification['font'] == x['ufo']:
                del self.w.ui.fonts.list[i]
        self.fontlistFitter()
        print('len(AllFonts())', len(AllFonts()))
        if len(AllFonts()) == 1:
            self.w.close()

    def openedFont(self, notification):
        f = notification['font']
        if f.info.familyName is None:
            return
        font = {}
        font['onoff'] = True
        font['fontname'] = f.info.familyName + ' ' + f.info.styleName
        font['ufo'] = f
        if font['fontname'] == 'RFont RFont':
            self.w.ui.fonts.list.insert(-1, font)
        else:
            self.w.ui.fonts.list.append(font)
        self.fontlistFitter()

    def fontlistFitter(self):
        # shift UI to fit
        count = len(self.w.ui.fonts.list) + 1
        fontgroupheight = count * (self.b + 2)
        # font list
        xywh = list(self.w.ui.fonts.getPosSize())
        xywh[3] = fontgroupheight
        self.w.ui.fonts.setPosSize(xywh)
        # view options
        xywh = list(self.w.ui.view.getPosSize())
        newy = 5 + fontgroupheight + self.b
        xywh[1] = newy
        saveheight = xywh[3]
        self.w.ui.view.setPosSize(xywh)
        # manipulate text
        xywh = list(self.w.ui.maniuplate.getPosSize())
        newy = newy + saveheight + self.b
        xywh[1] = newy
        saveheight = xywh[3]
        self.w.ui.maniuplate.setPosSize(xywh)
        # wordo
        xywh = list(self.w.ui.wordo.getPosSize())
        newy = newy + saveheight + self.b
        xywh[1] = newy
        saveheight = xywh[3]
        self.w.ui.wordo.setPosSize(xywh)
        # context
        xywh = list(self.w.ui.context.getPosSize())
        newy = newy + saveheight + self.b
        xywh[1] = newy
        saveheight = xywh[3]
        self.w.ui.context.setPosSize(xywh)
        self.fontlistGhostPos()

    def fontlistGhostPos(self):
        # move ghost group to match rfont position in list
        fonts = self.w.ui.fonts.list
        for i, font in enumerate(fonts):
            if font['fontname'] == '⇅':
                xywh = (35, ((self.b + 2) * (i + 1)), -0, self.b)
                font['ghostuigroup'].setPosSize(xywh)
                font['ghostuigroup'].slider.enable(True)
                if i == 0 or i == len(fonts) - 1:
                    font['ghostuigroup'].slider.enable(False)
                    font['onoff'] = False

    def fontListResort(self, sender):
        fonts = self.w.ui.fonts.list.get()
        fonts = list(reversed(fonts))
        self.w.ui.fonts.list.set(fonts)
        self.fontlistGhostPos()

    #############################################
    # ghostfont
    #############################################

    ghostno = 0
    ghostfonts = []

    def fontListAddInterpolated(self, sender):
        self.ghostno += 1
        ghostfont = RFont(showInterface=False)
        # ghostfont = RFont(showInterface=True)
        ghostfont.info.familyName = 'RFont'
        ghostfont.info.styleName = '50'
        ghost = Group((35, 65, -0, self.b))
        ghost.slider = ghostSlider(
            (0, 3, -self.b, -0),
            minValue=0,
            value=int(ghostfont.info.styleName),
            maxValue=100,
            tickMarkCount=False,
            # tickMarkCount=2
            stopOnTickMarks=True,
            sizeStyle='mini',
            ghostfont=ghostfont,
            callback=self.ghostSlider,
            continuous=False)
        ghost.label = ghostButton((-self.b, 0, -0, 10), '✕', ghostfont=ghostfont, callback=self.destroyGhost)
        flatButt(ghost.label, 'Exorcise Ghost Instance')
        setattr(self.w.ui.fonts, 'ghost' + str(self.ghostno), ghost)
        font = {}
        font['onoff'] = True
        font['fontname'] = '⇅'
        font['ufo'] = ghostfont
        font['ghostui'] = self.ghostno
        font['ghostuigroup'] = ghost
        # insert between masters
        everyother = (int(len(self.ghostfonts) + 1) * 2) - 1
        self.w.ui.fonts.list.insert(everyother, font)
        self.fontlistFitter()
        self.summonGhost(ghostfont)

    def destroyGhost(self, sender):
        ghostfont = sender.ghostfont
        for i, x in enumerate(self.w.ui.fonts.list):
            if ghostfont == x['ufo']:
                ghostui = x['ghostui']
                del self.w.ui.fonts.list[i]
                delattr(self.w.ui.fonts, 'ghost' + str(ghostui))
        ghostfont.close()
        for i, gfd in enumerate(self.ghostfonts):
            if gfd['ufo'] == ghostfont:
                self.ghostfonts.remove(self.ghostfonts[i])
        self.fontlistFitter()

    def ghostSlider(self, sender):
        ghostfont = sender.ghostfont
        interpolateby = sender.get()
        ghostfont.info.styleName = str(int(interpolateby))
        self.summonGhost(ghostfont)

    def summonGhost(self, ghostfont, refreshview=True):
        fonts = self.w.ui.fonts.list
        for i, x in enumerate(fonts):
            if ghostfont == x['ufo']:
                # ghostui = x['ghostui']
                if i == 0 or i == len(fonts) - 1:
                    print(i, 'this needs to be between two masters')
                    break
                fontA = fonts[i - 1]['ufo']
                fontB = fonts[i + 1]['ufo']
                ghostfont.lib['com.okaytype.ghostFont.A'] = fontA
                ghostfont.lib['com.okaytype.ghostFont.B'] = fontB
                self.updateGhost(ghostfont, refreshview)
                if not any(gfd['ufo'] == ghostfont for gfd in self.ghostfonts):
                    ghostfontdict = {}
                    ghostfontdict['ufo'] = ghostfont
                    ghostfontdict['masterA'] = fontA
                    ghostfontdict['masterB'] = fontB
                    self.ghostfonts.append(ghostfontdict)

    def updateGhost(self, ghostfont, refreshview=True):
        fontA = ghostfont.lib['com.okaytype.ghostFont.A']
        fontB = ghostfont.lib['com.okaytype.ghostFont.B']
        interpolateby = int(ghostfont.info.styleName) / 100
        # get text string
        text = self.w.preview.control.sequence.get()
        cmap = fontA.getCharacterMapping()
        fontspecifictext = splitText(text, cmap)
        # make list unique so we're not repeating shit
        fontspecifictext = list(set(fontspecifictext))
        # interpolate glyphs
        for glyphName in fontspecifictext[:]:
            if glyphName in fontA.glyphOrder and glyphName in fontB.glyphOrder:
                if fontA[glyphName].isCompatible(fontB[glyphName]):
                    g = self.interpolateGlyph(interpolateby, fontA[glyphName], fontB[glyphName], ghostfont)
                    ghostfont.insertGlyph(g, name=glyphName)
                else:
                    print('not compatible', glyphName)
        # ghostfont.changed()
        if refreshview is True:
            self.setupMLView()

    def updateGhosts(self):
        for ghostfont in self.ghostfonts:
            self.summonGhost(ghostfont['ufo'], False)

    def ghostGlyphChanged(self, glyph):
        if glyph is not None:
            editedfont = glyph.font
            glyphName = glyph.name
            for i, gfd in enumerate(self.ghostfonts):
                if gfd['masterA'] == editedfont or gfd['masterB'] == editedfont:
                    ghostfont = self.ghostfonts[i]['ufo']
                    fonts = self.w.ui.fonts.list
                    for n, x in enumerate(fonts):
                        if ghostfont == x['ufo']:
                            fontA = self.ghostfonts[i]['masterA']
                            fontB = self.ghostfonts[i]['masterB']
                            interpolateby = int(ghostfont.info.styleName) / 100
                            if glyphName in fontA.glyphOrder and glyphName in fontB.glyphOrder:
                                if fontA[glyphName].isCompatible(fontB[glyphName]):
                                    g = self.interpolateGlyph(interpolateby, fontA[glyphName], fontB[glyphName], ghostfont)
                                    ghostfont.insertGlyph(g, name=glyphName)
            self.w.preview.lineview.update()

    def interpolateGlyph(self, factor, glyphA, glyphB, ghostfont):
        ig = RGlyph()
        gA = glyphA
        gB = glyphB
        ig.interpolate(factor, gA, gB)
        ig.name = gA.name
        ig.unicode = gA.unicode
        # do the components
        components = []
        if len(gA.components) > 0:
            for component in gA.components:
                components.append(component.baseGlyph)
        if len(gB.components) > 0:
            for component in gB.components:
                components.append(component.baseGlyph)
        components = set(components)
        for component in components:
                self.interpolateComponentToo(ghostfont, component, glyphA, glyphB, factor)
        return ig

    def interpolateComponentToo(self, ghostfont, component, glyphA, glyphB, factor):
        fontA = glyphA.font
        fontB = glyphB.font
        if component in fontA.glyphOrder and component in fontB.glyphOrder:
            componentA = fontA[component]
            componentB = fontB[component]
            if componentA.isCompatible(componentB):
                ig = RGlyph()
                ig.interpolate(factor, componentA, componentB)
                ghostfont.insertGlyph(ig, name=component)

    #############################################
    # no UI font
    #############################################
    def addCloakedUFO(self, sender, dropInfo):
        isProposal = dropInfo["isProposal"]
        print('addCloakedUFO', dropInfo["isProposal"])
        paths = dropInfo["data"]
        if isProposal is False:
            print('drooooppppeeed')
        if not paths:
            return False
        if not isProposal:
            existingPaths = sender.get()
            paths = [path for path in paths if path not in existingPaths]
            paths = [path for path in paths if os.path.splitext(path)[-1].lower() in ['.ufo'] or os.path.isdir(path)]
            for path in paths:
                print('path', path)
                # open fonts without UI
                # add vanilla button to close

    # def fontlistGhostPos(self):
    #     # move ghost group to match rfont position in list
    #     fonts = self.w.ui.fonts.list
    #     for i, font in enumerate(fonts):
    #         if font['fontname'] == '⇅':
    #             xywh = (35, ((self.b+2)*(i+1)), -0, self.b)
    #             font['ghostuigroup'].setPosSize(xywh)
    #             font['ghostuigroup'].slider.enable(True)
    #             if i == 0 or i == len(fonts)-1:
    #                 font['ghostuigroup'].slider.enable(False)
    #                 font['onoff'] = False

    # ghostno = 0
    # ghostfonts = []

    # def fontListAddNoUIfont(self, sender):
    #     self.ghostno += 1

    #     ghost = Group((35, 65, -0, self.b))

    #     ghost.label = ghostButton(
    #         (-self.b, 0, -0, 10),
    #         '✕',
    #         ghostfont=ghostfont,
    #         callback=self.destroyGhost
    #     )
    #     flatButt(ghost.label, 'Close UFO')
    #     setattr(self.w.ui.fonts, 'ghost'+str(self.ghostno), ghost)

    #     font = {}
    #     font['onoff'] = True
    #     font['fontname'] = '⇅'
    #     font['ufo'] = ghostfont
    #     font['ghostui'] = self.ghostno
    #     font['ghostuigroup'] = ghost
    #     # insert between masters
    #     everyother = (int(len(self.ghostfonts) + 1) * 2) - 1
    #     self.w.ui.fonts.list.insert(everyother, font)
    #     self.fontlistFitter()
    #     self.summonGhost(ghostfont)

    #############################################
    # view option functions
    #############################################

    def viewSize(self, sender):
        size = sizes[int(sender.get())]
        self.w.preview.lineview.setPointSize(size)
        self.setupMLView()
        self.w.ui.view.sizevalue.set(size)
        setExtensionDefault(self.prefKey + '.ui.view.size', sender.get())

    def viewLine(self, sender):
        line = lines[int(sender.get())]
        self.w.preview.lineview.setLineHeight(line)
        self.w.ui.view.linevalue.set(line)
        setExtensionDefault(self.prefKey + '.ui.view.line', sender.get())
        self.viewPad(None)

    def viewPad(self, sender=None):
        pad = int(self.w.ui.view.pad.get())
        yff = int(self.w.ui.view.offsety.get())
        line = lines[int(self.w.ui.view.line.get())]
        size = sizes[int(self.w.ui.view.size.get())]

        lineOffset = line / 1000 * size
        self.w.preview.lineview.setOffset((pad, pad + yff - lineOffset))

        self.w.ui.view.padvalue.set(pad)
        self.w.ui.view.offsetYvalue.set(yff)
        self.w.preview.lineview.contentView().refresh()

        setExtensionDefault(self.prefKey + '.ui.view.pad', pad)
        setExtensionDefault(self.prefKey + '.ui.view.offsety', yff)
        self.setupMLView()

    def viewMax(self, sender):
        maxlines = int(sender.get()) + 1
        if maxlines == self.linesslidermaximum + 1:
            maxlines = '∞'
        self.w.ui.view.maxvalue.set(maxlines)
        self.setupMLView()

    def viewMetrics(self, sender):
        setExtensionDefault(self.prefKey + '.ui.view.metrics', sender.get())

    def viewInvert(self, sender):
        lv = self.w.preview.lineview
        states = lv.getDisplayStates()
        if sender.get() == 1:
            states['Inverse'] = True
        else:
            states['Inverse'] = False
        lv.setDisplayStates(states)
        setExtensionDefault(self.prefKey + '.ui.view.invert', sender.get())

    def viewWrap(self, sender):
        lv = self.w.preview.lineview
        if sender.get() == 0:
            xywh = list(lv.getPosSize())
            xywh[2] = 100000
            lv.setPosSize(xywh)
            self.w.ui.view.center.set(0)
            self.viewCenter(self.w.ui.view.center)
        else:
            xywh = list(lv.getPosSize())
            xywh[2] = -0
            if self.w.ui.showhide.get() == 0:
                xywh[2] = -uiwidth
            lv.setPosSize(xywh)
        self.setupMLView()
        setExtensionDefault(self.prefKey + '.ui.view.wrap', sender.get())

    def viewCenter(self, sender):
        lv = self.w.preview.lineview
        states = lv.getDisplayStates()
        if sender.get() == 1:
            states['Center'] = True
            states['Left to Right'] = False
            states['Right to Left'] = False
            self.w.ui.view.wrap.set(1)
            self.viewWrap(self.w.ui.view.wrap)
        else:
            states['Center'] = False
            states['Left to Right'] = True
            states['Right to Left'] = False
        lv.setDisplayStates(states)
        setExtensionDefault(self.prefKey + '.ui.view.center', sender.get())

    def viewKerns(self, sender):
        lv = self.w.preview.lineview
        states = lv.getDisplayStates()
        if sender.get() == 1:
            states['setApplyKerning'] = True
        else:
            states['setApplyKerning'] = False
        lv.setDisplayStates(states)
        setExtensionDefault(self.prefKey + '.ui.view.kerning', sender.get())

    def viewPath(self, sender):
        lv = self.w.preview.lineview
        states = lv.getDisplayStates()
        if sender.get() == 1:
            states['Stroke'] = True
            states['Fill'] = False
        else:
            states['Stroke'] = False
            states['Fill'] = True
        lv.setDisplayStates(states)
        setExtensionDefault(self.prefKey + '.ui.view.aspath', sender.get())

    def viewFlip(self, sender):
        lineview = self.w.preview.lineview
        states = lineview.getDisplayStates()
        if sender.get() == 1:
            states['Upside Down'] = True
        else:
            states['Upside Down'] = False
        lineview.setDisplayStates(states)
        setExtensionDefault(self.prefKey + '.ui.view.flip', sender.get())

    rotateInitialOrigin = None

    def viewRotate(self, sender):
        lv = self.w.preview.lineview
        lvNS = lv.getNSScrollView()

        if sender.get() == 0:
            lvNS.setFrameCenterRotation_(0)
        else:
            lvNS.setFrameCenterRotation_(-180)

    #############################################
    # manipulate text functions
    #############################################

    def setCase(self, sender='upper'):
        case = sender.getTitle()
        if case == 'HH':
            case = 'upper'
        if case == 'Hh':
            case = 'title'
        if case == 'hh':
            case = 'lower'
        if case == 'Hн':
            case = 'sc'
        text = self.w.preview.control.sequence.get()
        if case != 'sc':
            results = findall(r'/[A-Za-z]\\.sc ', text)
            for result in results:
                unsmallcaped = result.replace('/', '')
                unsmallcaped = unsmallcaped.replace('.sc ', '')
                unsmallcaped = unsmallcaped.lower()
                text = text.replace(result, unsmallcaped)
            text = getattr(text, case)()
        elif case == 'sc':
            newtext = ''
            for g in text:
                if g.islower():
                    g = '/' + g.upper() + '.sc '
                newtext += g
            text = newtext
        self.w.preview.control.sequence.set(text)
        self.setupMLView()

    def subH(self, sender):
        print('multilineview doesnt support pre/after yet')

    def addH(self, sender):
        text = self.w.preview.control.sequence.get()
        newtext = ''
        for x in text:
            newtext = newtext + x + 'H'
        self.w.preview.control.sequence.set(newtext)
        self.setupMLView()

    def hhxhh(self, sender):
        gs = CurrentFont().selectedGlyphNames
        newtext = ''
        for x in gs:
            newtext = newtext + 'H' + x + 'H'
        self.w.preview.control.sequence.set(newtext)
        self.setupMLView()

    def accentall(self, sender):
        f = CurrentFont()
        newtext = ''
        if f is not None:
            glyphorder = f.glyphOrder
            selectedGlyphNames = f.selectedGlyphNames
            for g in selectedGlyphNames:
                if f[g].unicode is not None and f[g].unicode < 10000:
                    newtext += chr(f[g].unicode)
                else:
                    newtext += '/' + f[g].name + ' '
                for x in glyphorder:
                    if f[x].name != f[g].name:
                        for c in f[x].components:
                            if c.baseGlyph == f[g].name:
                                if f[x].unicode is not None and f[x].unicode < 10000:
                                    newtext += chr(f[x].unicode)
                                else:
                                    newtext += '/' + f[x].name + ' '
            if newtext != '':
                self.w.preview.control.sequence.set(newtext)
                self.setupMLView()

    def accentone(self, sender):
        f = CurrentFont()
        newtext = ''
        if f is not None:
            glyphorder = f.glyphOrder
            selectedGlyphNames = f.selectedGlyphNames
            for g in selectedGlyphNames:
                if f[g].unicode is not None and f[g].unicode < 10000:
                    newtext += chr(f[g].unicode)
                else:
                    newtext += '/' + f[g].name + ' '
                n = 0
                for x in glyphorder:
                    if f[x].name != f[g].name and n == 0:
                        for c in f[x].components:
                            if c.baseGlyph == f[g].name:
                                if f[x].unicode is not None and f[x].unicode < 10000:
                                    newtext += chr(f[x].unicode)
                                else:
                                    newtext += '/' + f[x].name + ' '
                                n = 1
            if newtext != '':
                self.w.preview.control.sequence.set(newtext)
                self.setupMLView()

    def selectsc(self, sender):
        a = AllFonts()
        text = self.w.preview.control.sequence.get()
        if a is not None and text is not None:
            for f in a:
                for g in f:
                    g.selected = False
                for g in text:
                    if g in f:
                        f[g].selected = True

    def showselected(self, sender=None):
        f = CurrentFont()
        newtext = ''
        if f is not None:
            selectedGlyphNames = f.selectedGlyphNames
            for g in selectedGlyphNames:
                if f[g].unicode is not None and f[g].unicode < 10000:
                    newtext += chr(f[g].unicode)
                else:
                    newtext += '/' + f[g].name + ' '
            if newtext != '':
                self.w.preview.control.sequence.set(newtext)
                self.setupMLView()

    def randomselected(self, sender=None):
        f = CurrentFont()
        newtext = ''
        if f is not None:
            N = 123
            foo = list(f.selectedGlyphNames)
            for x in repeat(None, N):
                g = choice(foo)
                if f[g].unicode is not None and f[g].unicode < 10000:
                    newtext += chr(f[g].unicode)
                else:
                    newtext += '/' + f[g].name + ' '
            self.w.preview.control.sequence.set(newtext)
            self.setupMLView()

    #############################################
    # incontext stuff
    ############################################

    contextData = ''

    def initializeIncontext(self):
        if self.contextData == '':
            glyphContextFile = os.path.dirname(os.path.realpath(__file__)) + u'/contexts/contexts.txt'
            with open(glyphContextFile, 'r', encoding='utf-8', errors='surrogateescape') as datafile:
                data = datafile.read().split('\n')
            cleandata = []
            for line in data:
                if line.startswith('##') is False and line.startswith(' ') is False:
                    cleandata.append(line.split('\t'))
            self.contextData = cleandata

    def incontext(self, sender=None):
        context = self.w.ui.context
        usehhstring = context.HH.get()
        useglyph = context.glyph.get()
        usespaces = context.space.get()
        usecontext = context.string.get()
        usebreaks = context.line.get()
        self.getcontext(usehhstring, usecontext, usespaces, usebreaks, useglyph)

    def getcontext(self, usehhstring, usecontext, usespaces, usebreaks, useglyph):
        f = CurrentFont()
        s = ''
        glyphs = []
        try:
            glyphs = [CurrentGlyph().name]
        except Exception:
            glyphs = list(f.selectedGlyphNames)
        space = ' '
        if usespaces == 0:
            space = ''
        if CurrentGlyph() and CurrentGlyph().name not in glyphs:
            glyphs.insert(0, CurrentGlyph().name)

        for i, g in enumerate(glyphs):
            # try to use the unicode character
            if f[g].unicode:
                g = chr(f[g].unicode)
            # if no unicode character, use /glyphname
            else:
                g = '/' + g + ' '

            string = ''

            # go through context lines to find the glyph entry
            for line in self.contextData:
                if string == '':
                    if g.strip() == line[0].strip():
                        string = self.returnstring(line, g, False, usespaces, usehhstring, usecontext, useglyph)
                        # print('s1', '|' + g + '|', string)

            # if nothing was found, see if there is a baseglyph we can use
            if string == '' and '.' in g and len(g) > 1:
                gBase = g.split('.')[0].replace('/', '')
                try:
                    gBase = chr(f[gBase].unicode)
                except Exception:
                    gBase = '/' + gBase
                # if baseglyph isn't what we tried before
                if gBase != g:
                    for line in self.contextData:
                        # just double checking
                        if g.strip() == line[0].strip():
                            string = self.returnstring(line, g, False, usespaces, usehhstring, usecontext, useglyph)
                            # print('s1b', '|' + g + '|', string)
                        elif gBase.strip() == line[0].strip():
                            if '.' in g and len(g) > 1:  # if dot.glyphname, try replacing baseglyph with glyph
                                line[1] = line[1].replace(gBase, g)
                            string = self.returnstring(line, g, True, usespaces, usehhstring, usecontext, useglyph)
                            # print('s2', '|' + g + '|', string)

            # if still nothing was found, give up and use a control string
            if string == '':
                string = self.returnstring(['', ''], g, False, usespaces, usehhstring, usecontext, useglyph)
                # print('s3', '|' + g + '|', string)

            if usebreaks == 1:
                if i + 1 == len(glyphs):
                    s = s + string
                else:
                    s = s + string + '\\n'
            else:
                s = s + string + space

        self.w.preview.control.sequence.set(s)
        self.history(s)
        self.setupMLView()

    def returnstring(self, line, g, pseudo, usespaces, usehhstring, usecontext, useglyph):
        # helper for above
        space = ' '
        if usespaces == 0:
            space = ''
        # if the glyph is a slash, add an escape slash
        if g == '/':
            g = '//'
        # case test for spacing control glyphs
        if g.islower() and len(g) <= 1:
            control = u'n'
        elif g.isdigit():
            control = u'H'
        else:
            control = u'H'
        if '.lt' in g:
            control = u'H'
        elif '.lp' in g:
            control = u'H'
        elif '.uc' in g:
            control = u'H'
        elif '.case' in g:
            control = u'H'
        # if glyph is a glyphname, not a character
        # not sure what this is actually doing though
        if pseudo is True:
            # base = g.split('.')[0]
            # suffix = g.split('.')[1]
            g = g + ' '
        # build string
        string = ''
        if usehhstring == 1:
            string += 'H' + control + g + control + control + space
        if useglyph == 1:
            string += g + space
        if usecontext == 1:
            string += line[1].replace(' ', space)
            if usehhstring == 0:
                if line[1] == '':
                    string += 'H' + control + g + control + control + space
        return string

    def contextauto(self, sender):
        setExtensionDefault(self.prefKey + '.ui.context.auto', sender.get())
        if sender.get() == 1:
            addObserver(self, 'incontext', 'currentGlyphChanged')
        else:
            removeObserver(self, 'currentGlyphChanged')

    def contextglyph(self, sender):
        setExtensionDefault(self.prefKey + '.ui.context.glyph', sender.get())

    def contextHH(self, sender):
        setExtensionDefault(self.prefKey + '.ui.context.HH', sender.get())

    def contextspace(self, sender):
        setExtensionDefault(self.prefKey + '.ui.context.space', sender.get())

    def contextstring(self, sender):
        setExtensionDefault(self.prefKey + '.ui.context.string', sender.get())

    def contextline(self, sender):
        setExtensionDefault(self.prefKey + '.ui.context.line', sender.get())

    #############################################
    # wordomatic stuff
    #############################################

    wordDictionaries = {}

    def initialWordO(self):
        if self.wordDictionaries == {}:
            dirpath = os.path.dirname(os.path.realpath(__file__))
            for language in languages:
                if language == 'OSX Dictionary':
                    with open('/usr/share/dict/words', 'r') as userFile:
                        lines = userFile.read()
                    self.wordDictionaries['osx'] = lines.splitlines()
                elif language == 'Any language':
                    # jackson = 'needs to code better'
                    pass
                else:
                    path = dirpath + '/dictionaries/' + language.replace(' ', '').lower() + '.txt'
                    with open(path, mode='r', encoding='utf-8') as fo:
                        lines = fo.read()
                    self.wordDictionaries[language] = lines.splitlines()

    def wordo(self, sender=None):
        # get settings from ui
        wordo = self.w.ui.wordo
        wLanguage = languages[wordo.languages.get()]
        wCase = cases[wordo.cases.get()]
        wUse = usecharacters[wordo.characters.get()]
        wCount = int(wordo.words.get())
        wMin = int(wordo.min.get())
        wMax = int(wordo.max.get())
        wReqSeld = wordo.requireselected.get()
        wReqMark = wordo.requiremarked.get()
        wReqCur = wordo.requirecurrent.get()
        f = CurrentFont()
        if f is None:
            print('word-o needs a current font')
        else:
            words = wordomatic(f, wLanguage, wCase, wUse, wReqSeld, wReqMark, wReqCur, wCount, wMin, wMax, self.wordDictionaries).words
            self.w.preview.control.sequence.set(words)
            self.history(words)
            self.setupMLView()

    def wordolanguages(self, sender):
        setExtensionDefault(self.prefKey + '.ui.wordo.languages', sender.get())

    def wordocases(self, sender):
        setExtensionDefault(self.prefKey + '.ui.wordo.cases', sender.get())

    def wordocharacters(self, sender):
        setExtensionDefault(self.prefKey + '.ui.wordo.characters', sender.get())

    def wordorequirecurrent(self, sender):
        setExtensionDefault(self.prefKey + '.ui.wordo.requirecurrent', sender.get())

    def wordorequireselected(self, sender):
        setExtensionDefault(self.prefKey + '.ui.wordo.requireselected', sender.get())

    def wordorequiremarked(self, sender):
        setExtensionDefault(self.prefKey + '.ui.wordo.requiremarked', sender.get())

    def wordowordsd(self, sender):
        setExtensionDefault(self.prefKey + '.ui.wordo.words', sender.get())

    def wordomin(self, sender):
        setExtensionDefault(self.prefKey + '.ui.wordo.min', sender.get())

    def wordomax(self, sender):
        setExtensionDefault(self.prefKey + '.ui.wordo.max', sender.get())

    #############################################
    # watch for glyph changes
    #############################################

    def glyphChanged(self, notification):
        self.w.preview.lineview.contentView().refresh()
        g = notification['glyph']
        if len(self.ghostfonts) != 0 and g is not None:
            self.ghostGlyphChanged(g)

    def glyphChangedDefCon(self, notification):
        tempf = {}
        tempf['glyph'] = self.glyph
        if tempf['glyph'] is not None:
            self.glyphChanged(tempf)

    def viewDidChangeGlyph(self, notification):
        self.glyph = CurrentGlyph()
        self.unsubscribeGlyph()
        self.subscribeGlyph()
        self.w.preview.lineview.contentView().refresh()

    def subscribeGlyph(self):
        self.glyph.addObserver(self, 'glyphChangedDefCon', 'Glyph.Changed')

    def unsubscribeGlyph(self):
        if self.glyph is None:
            return
        self.glyph.removeObserver(self, 'Glyph.Changed')

    #############################################
    # do things after notification scripts
    #############################################

    def trigger(self, notification):
        # print('notification trigger', notification['trigger'])
        if notification['trigger'] == 'wordo':
            self.wordo()
        elif notification['trigger'] == 'context':
            self.incontext()
        elif notification['trigger'] == 'history':
            self.historyback()
        elif notification['trigger'] == 'next':
            current = nextline = self.w.preview.control.sequence.get()
            items = self.w.preview.control.sequence.getItems()
            if current in items:
                index = items.index(current)
                nextitem = index + 1
                if nextitem >= len(items):
                    nextitem = 0
                nextline = items[nextitem]
            else:
                x = get_close_matches(current, items)
                try:
                    index = items.index(x[0])
                    nextline = items[index]
                except Exception:
                    tempcurrent = [item[:5] for item in items]
                    x = get_close_matches(current, tempcurrent)
                    try:
                        index = tempcurrent.index(x[0])
                        nextline = items[index]
                    except Exception:
                        restart = 0
                        nextline = items[restart]
            self.w.preview.control.sequence.set(nextline)
            self.setupMLView()
        elif notification['trigger'] == 'previous':
            current = nextline = self.w.preview.control.sequence.get()
            items = self.w.preview.control.sequence.getItems()
            if current in items:
                count = len(items)
                index = items.index(current)
                nextitem = index - 1
                if nextitem < 0:
                    nextitem = count - 1
                nextline = items[nextitem]
            else:
                x = get_close_matches(current, items)
                try:
                    index = items.index(x[0])
                    nextline = items[index]
                except Exception:
                    tempcurrent = [item[:5] for item in items]
                    x = get_close_matches(current, tempcurrent)
                    try:
                        index = tempcurrent.index(x[0])
                        nextline = items[index]
                    except Exception:
                        restart = 0
                        nextline = items[restart]
            self.w.preview.control.sequence.set(nextline)
            self.setupMLView()

    #############################################
    # preferences
    #############################################
    def loadPreferences(self):
        initialDefaults = {
            self.prefKey + '.win.screenX': 0,
            self.prefKey + '.win.screenY': 0,
            self.prefKey + '.win.screenW': 1120,
            self.prefKey + '.win.screenH': 1050,
            self.prefKey + '.ui.showhide': 0,
            # main text
            self.prefKey + '.preview.control.sequence': 'Onions are delicious',
            # seperate fonts with
            self.prefKey + '.ui.view.seperate': 2,
            self.prefKey + '.ui.view.lines': 1,
            self.prefKey + '.ui.view.size': 5,
            self.prefKey + '.ui.view.line': 5,
            self.prefKey + '.ui.view.pad': 25,
            self.prefKey + '.ui.view.offsety': 5,
            self.prefKey + '.ui.view.metrics': 0,
            self.prefKey + '.ui.view.invert': 0,
            self.prefKey + '.ui.view.wrap': 1,
            self.prefKey + '.ui.view.center': 0,
            self.prefKey + '.ui.view.kerning': 0,
            self.prefKey + '.ui.view.aspath': 0,
            self.prefKey + '.ui.view.flip': 0,
            # word o matic
            self.prefKey + '.ui.wordo.languages': 0,
            self.prefKey + '.ui.wordo.cases': 0,
            self.prefKey + '.ui.wordo.characters': 1,
            self.prefKey + '.ui.wordo.requirecurrent': 1,
            self.prefKey + '.ui.wordo.requireselected': 1,
            self.prefKey + '.ui.wordo.requiremarked': 0,
            self.prefKey + '.ui.wordo.words': 5,
            self.prefKey + '.ui.wordo.min': 2,
            self.prefKey + '.ui.wordo.max': 69,
            # glyphs in context
            self.prefKey + '.ui.context.auto': 0,
            self.prefKey + '.ui.context.string': 1,
            self.prefKey + '.ui.context.glyph': 1,
            self.prefKey + '.ui.context.HH': 1,
            self.prefKey + '.ui.context.space': 1,
            self.prefKey + '.ui.context.line': 1,
        }
        # for v, p in initialDefaults.items():
        #     removeExtensionDefault(v)
        registerExtensionDefaults(initialDefaults)

        # set values from preferences
        vanillagroup = 'self.w'
        for key, value in initialDefaults.items():
            if '.win.' not in key:
                value = getExtensionDefault(key)
                vanillaobject = vanillagroup + key.replace(self.prefKey, '')
                eval(vanillaobject).set(value)

        # trigger updates
        preftext = getExtensionDefault(self.prefKey + '.preview.control.sequence')
        print('preftext', preftext)
        self.w.preview.control.sequence.set(preftext)
        xywh = ((getExtensionDefault(self.prefKey + '.win.screenX'), getExtensionDefault(self.prefKey + '.win.screenY')), (getExtensionDefault(self.prefKey + '.win.screenW'), getExtensionDefault(self.prefKey + '.win.screenH')))
        self.w.getNSWindow().setFrame_display_animate_(xywh, True, False)
        self.showHideUI(self.w.ui.showhide)
        self.viewSize(self.w.ui.view.size)
        self.viewLine(self.w.ui.view.line)
        self.viewPad(None)
        self.viewMetrics(self.w.ui.view.metrics)
        self.viewInvert(self.w.ui.view.invert)
        self.viewWrap(self.w.ui.view.wrap)
        self.viewCenter(self.w.ui.view.center)
        self.viewKerns(self.w.ui.view.kerning)
        self.viewPath(self.w.ui.view.aspath)
        self.viewFlip(self.w.ui.view.flip)
        self.viewMax(self.w.ui.view.lines)
        self.setupMLView()


class wordomatic(object):
    def __init__(self, f, wLanguage, wCase, wUse, wReqSeld, wReqMark, wReqCur, wCount, wMin, wMax, dictionaries):
        requiredGlyphs = self.getRequiredCharacters(f, wReqSeld, wReqMark, wReqCur, wCase)
        useGlyphs = self.getUseCharacters(f, wUse, wCase)
        wordList = self.getWordlist(dictionaries, wLanguage)
        # if requiredGlyphs are all uppercase, pretend the case setting is UPPER
        if all(g[0].isupper() for g in useGlyphs) is True and all(g[0].isupper() for g in requiredGlyphs) is True:
            wCase = 'UPPER'
            useGlyphs = [x.lower() for x in useGlyphs]
            requiredGlyphs = [x.lower() for x in requiredGlyphs]
        words = self.getWords(wordList, wCount, wMin, wMax, requiredGlyphs, useGlyphs)
        self.words = self.setCase(words, wCase)

    def getRequiredCharacters(self, f, wReqSeld, wReqMark, wReqCur, wCase):
        # required glyphs
        require = []
        if wReqCur == 1 and CurrentGlyph():
            g = CurrentGlyph().name
            if f[g].unicode:
                g = chr(f[g].unicode)
            require.append(g)
        if wReqSeld == 1:
            selectedGlyphNames = f.selectedGlyphNames
            for g in selectedGlyphNames:
                if f[g].unicode:
                    g = chr(f[g].unicode)
                require.append(g)
        if wReqMark == 1:
            for g in f:
                if g.markColor:
                    if g.unicode:
                        g = chr(g.unicode)
                        require.append(g)
                else:
                    require.append(g.name)
        if wCase == 'UPPER':
            require = [x.lower() for x in require]
        return require

    def getUseCharacters(self, f, wUse, wCase):
        # use glyphs
        useGlyphs = []
        if wUse == 'Only glyphs in font':
            glyphOrder = f.glyphOrder
            for g in glyphOrder:
                if g in f:
                    if f[g].unicode:
                        g = chr(f[g].unicode)
                    useGlyphs.append(g)
        elif wUse == 'Only selected glyphs':
            selectedGlyphNames = f.selectedGlyphNames
            for g in selectedGlyphNames:
                if f[g].unicode:
                    g = chr(f[g].unicode)
                useGlyphs.append(g)
            if CurrentGlyph():
                x = CurrentGlyph()
                if x.unicode:
                    x = chr(x.unicode)
                    useGlyphs.append(x)
                else:
                    useGlyphs.append(g.name)
        elif wUse == 'Only marked glyphs':
            for g in f:
                if g.markColor:
                    if g.unicode:
                        g = chr(g.unicode)
                        useGlyphs.append(g)
                    else:
                        useGlyphs.append(g.name)
        if wCase == 'UPPER':
            useGlyphs = [glyph.lower() for glyph in useGlyphs]
        return useGlyphs

    def getWordlist(self, dictionaries, wLanguage):
        wordList = []
        if wLanguage == 'OSX Dictionary':
            wordList = dictionaries['osx']
        elif wLanguage == 'Any language':
            for dic in dictionaries:
                wordList += dictionaries[dic]
        else:
            wordList += dictionaries[wLanguage]
        return wordList

    def getWords(self, wordList, wCount, wMin, wMax, requiredGlyphs, useGlyphs):
        # print('requiredGlyphs', requiredGlyphs)
        # print('useGlyphs', useGlyphs)
        # make words
        useGlyphs.extend(requiredGlyphs)
        words = []
        parachute = 0
        # this hack let's us repeat as many times as needed
        for n in wordList:
            parachute += 1
            if len(words) >= wCount:
                break
            elif parachute >= 15000:
                break
            else:
                # pick a random word
                word = choice(wordList)
                # if it's long enough
                if wMax >= len(word) >= wMin:
                    # if there are no use glyphs
                    if useGlyphs == []:
                        # if there are required glyphs
                        if requiredGlyphs != []:
                            glyphTest = False
                            for reqg in requiredGlyphs:
                                if reqg in word:
                                    glyphTest = True
                            if glyphTest is True:
                                words.append(word)
                        # if any
                        else:
                            words.append(word)
                    # if there are use glyphs
                    else:
                        glyphTest = True
                        for x in word:
                            if x not in useGlyphs:
                                glyphTest = False
                        if glyphTest is True:
                            if requiredGlyphs != []:
                                glyphTest = False
                                for x in word:
                                    if x in requiredGlyphs:
                                        glyphTest = True
                            if glyphTest is True:
                                words.append(word)
        # if none:
        if len(words) < 1:
            words = ['/' + CurrentGlyph().name]
        return words

    def setCase(self, words, wCase):
        # case transformations
        toSC = False
        toCase = wCase
        for i, word in enumerate(words):
            if wCase == 'Random':
                randomcases = ['Default Case', 'UPPER', 'lower', 'Title', 'Title']
                toCase = choice(randomcases)
            if toCase == 'UPPER':
                words[i] = word.upper()
            elif toCase == 'lower':
                words[i] = word.lower()
            elif toCase == 'Title':
                words[i] = word.title()
            elif toCase == 'Sмᴀʟʟᴄᴀᴘ':
                words[i] = word.title()
                toSC = True
        words = ' '.join(words)
        if toSC is True:
            newwords = ''
            for g in words:
                if g.islower():
                    g = '/' + g.upper() + '.sc '
                    newwords += g
            words = newwords
        return words


class ControlCanvas(object):
    def __init__(self, window, target='matrix'):
        self.w = window
        self.target = target

    def opaque(self):
        return False

    def acceptsFirstResponder(self):
        return False

    def acceptsMouseMoved(self):
        return False

    def becomeFirstResponder(self):
        return False

    def resignFirstResponder(self):
        return False

    def shouldDrawBackground(self):
        return False

    def mouseEntered(self, event):
        if self.target == 'matrix':
            if self.w.ui.view.metrics.get() == True:
                self.w.preview.control.matrix.show(True)
        if self.target == 'ui':
            self.w.ui.show(True)
            self.w.uitoggle.setPosSize((-uiwidth, 0, uiwidth, -0))
            self.w.preview.control.setPosSize((0, -70, -uiwidth, 70))

    def mouseExited(self, event):
        if self.target == 'matrix':
            self.w.preview.control.matrix.show(False)
        if self.target == 'ui' and self.w.ui.showhide.get() == True:
            self.w.ui.show(False)
            self.w.uitoggle.setPosSize((-uiwidth / 2, 0, uiwidth / 2, -70))
            self.w.preview.control.setPosSize((0, -70, -0, 70))


class UICanvas(object):
    def __init__(self, window):
        self.w = window
        self.colorR, self.colorG, self.colorB = random(), random(), random()

    def opaque(self):
        return False

    def acceptsFirstResponder(self):
        return False

    def acceptsMouseMoved(self):
        return False

    def becomeFirstResponder(self):
        return False

    def resignFirstResponder(self):
        return False

    def shouldDrawBackground(self):
        return False

    def mouseExited(self, event):
        self.colorR, self.colorG, self.colorB = random(), random(), random()

    def draw(self):
        fill(1, 1, 1, 0.9)
        rect(0, 0, 2000, 2000)
        fill(self.colorR, self.colorG, self.colorB, 0.5)
        rect(0, 0, 2000, 2000)


#############################################
# subclassed ui guts
#############################################

def flatButt(this, tip=None, match=False):
    this = this.getNSButton()
    this.setBordered_(False)
    this.setBackgroundColor_(NSColor.clearColor())
    if tip is not None:
        this.setToolTip_(tip)
    if match is True:
        this.setBackgroundColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(.9, 1, .85, 1))


class ghostButton(Button):
    def __init__(self, *args, **kwargs):
        self.ghostfont = kwargs['ghostfont']
        del kwargs['ghostfont']
        super(ghostButton, self).__init__(*args, **kwargs)


class ghostSlider(Slider):
    def __init__(self, *args, **kwargs):
        self.ghostfont = kwargs['ghostfont']
        del kwargs['ghostfont']
        super(ghostSlider, self).__init__(*args, **kwargs)


MultiviewToolbar()
