from __future__ import print_function
# for localized messages
from . import _
#
#  Czech Meteo Viewer - Plugin E2
#
#  by ims (c) 2011-2026
VERSION = "v2.2.1 (ims 2011-2026)"
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#

# remove FileList by jbleyel

import os
from re import search
from enigma import ePicLoad, getDesktop
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.HelpMenu import HelpableScreen
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Pixmap import Pixmap, MovingPixmap
from Components.Sources.List import List
from enigma import eTimer
from Components.config import ConfigSubsection, ConfigYesNo, ConfigText, ConfigDirectory, ConfigSelection, getConfigListEntry, config
from Components.Label import Label
from Components.ConfigList import ConfigListScreen, ConfigList
from six.moves import range
from time import gmtime, strftime, localtime, time, mktime, strptime, ctime
import calendar
import enigma
from Tools.Directories import fileExists
from Screens.ChoiceBox import ChoiceBox
from Components.ProgressBar import ProgressBar

TMPDIR = "/tmp/"
SUBDIR = "czmeteo"

# LIST OF USED NAMES IN MENU, OPTIONS AS INFO ("All" must be at last)
INFO = [_("VIS-IR Central Europe"), _("IR Central Europe"), _("VIS-IR Czech Republic"), _("IR Czech Republic"), _("IR BT Czech Republic"), _("24h-MF Czech Republic"), _("WV6.2 Czech Republic"), _("VIS-IR Europe"), _("IR Europe"), _("Lightning detection"), _("Czech Radar"), _("Czech Radar precipitation")]
INFO += [_("All")]

# LIST OF USED INDEX NAMES AS TYPES: ("all" must be at last")
TYPE = ["visce", "irce", "vis", "ircz", "bt", "24m", "wv", "viseu", "ireu", "lightning", "radar", "rain"]
TYPE += ["all"]

DESCR = [
_("VIS-IR - 'Traditional' RGB combination, approaching human eye perception.\n\n\
  - YELLOWISH = low to medium cloudiness (generally warmer)\n\
  - WHITE to BLUE = high cloudiness (cold)\n\
  - GREEN = vegetation-covered terrain\n\
  - DARK BLUE = water"),
_("IR - Traditional display\n\n\
  - DARK - warm areas\n\
  - LIGHT - cold areas"),
_("VIS-IR - 'Traditional' RGB combination, approaching human eye perception.\n\n\
  - YELLOWISH = low to medium cloudiness (generally warmer)\n\
  - WHITE to BLUE = high cloudiness (cold)\n\
  - GREEN = vegetation-covered terrain\n\
  - DARK BLUE = water"),
_("IR - Traditional display\n\n\
  - DARK - warm areas\n\
  - LIGHT - cold areas"),
_("IR-BT - Traditional display (color scale is embedded in individual images)\n\n\
  - DARK = warm areas\n\
  - LIGHT = cold areas\n\
  - PURPLE = -33%sC (240 K)\n\
  - RED = -73%sC (200 K)") % (chr(176),chr(176)),
_("24h-MF - Vertically extensive cloudiness is depicted in dark red, thin cirrus clouds in dark blue, medium and low cloudiness in ocher, the lowest cloudiness transitions to green, terrain according to temperature to pink or blue, water surfaces to blue.\n\n\
  - RED, the more intense = vertically extensive cloudiness\n\
  - GREEN = low cloudiness formed by small droplets\n\
  - BLUE, the more intense = warmer object"),
_("WV - spectral band of water vapor absorption (channel WV 6.2)\n\n\
  - DARK shades correspond to dry and cloud-free upper troposphere\n\
  - LIGHTER shade, the more water vapor is present in that layer\n\
  This spectral channel also captures the highest cloud tops - cirrus and cumulonimbus clouds (shown in white), but not medium or low cloudiness."),
_("VIS-IR - 'Traditional' RGB combination, approaching human eye perception.\n\n\
  - YELLOWISH = low to medium cloudiness (generally warmer)\n\
  - WHITE to BLUE = high cloudiness (cold)\n\
  - GREEN = vegetation-covered terrain\n\
  - DARK BLUE = water"),
_("IR - Traditional display\n\n\
  - DARK - warm areas\n\
  - LIGHT - cold areas"),
_("Lightning detection"),
_("Radar information\n\n\
  - current composite radar image from the Czech radar network CZRAD (from Brdy-Praha and Skalky radars)"),
_("Radar precipitation\n\n\
  - radar precipitation at 2 km altitude from the Czech radar network CZRAD (from Brdy-Praha and Skalky radars) - a more realistic estimate of precipitation reaching the ground."),
""
	]

PPATH = "/usr/lib/enigma2/python/Plugins/Extensions/CzechMeteo/pictures/"
E2PATH = "/etc/enigma2/"

HD = False
if getDesktop(0).size().width() >= 1280:
	HD = True

# position of BACKGROUND and MER must be equal as position of SUBDIR and TYPE. For unused item use e.png
BACKGROUND = ["bgce.png", "bgce.png", "bgcz.png", "bgcz.png", "bgcz.png", "bgcz.png", "bgcz.png", "bgeu.png", "bgeu.png", "radar.png", "radar.png", "radar.png"]
MER = ["merce.png", "merce.png", "mercz.png", "mercz.png", "mercz.png", "mercz.png", "mercz.png", "mereu.png", "mereu.png", "e.png", "e.png"]
HOME = ["homece.png", "homece.png", "homecz.png", "homecz.png", "homecz.png", "homecz.png", "homecz.png", "e.png", "e.png", "e.png", "e.png"]
# fallback items for future TYPE extensions
for i in range(0, len(TYPE) + 1):
	BACKGROUND.append("e.png")
	MER.append("e.png")
	HOME.append("e.png")

EMPTYFRAME = "e.jpg"
RADAR_MM = "radar_mm.png"
HOME_CSR = "homecsr.png"
HOME_RADAR = "homeradar.png"
RADAR_CITY = "radar_cities.png"
REGIONS = "bgczregions.png"

config.plugins.czechmeteo.nr = ConfigSelection(default="8", choices=[("4", "1h"), ("8", "2h"), ("12", "3h"), ("24", "6h"), ("48", "12h"), ("96", "24h"), ("192", "48h")])
config.plugins.czechmeteo.frames = ConfigSelection(default="0", choices=[("0", _("downloaded interval")), ("1", _("all frames"))])
config.plugins.czechmeteo.time = ConfigSelection(default="750", choices=[("400", "400 ms"), ("500", "500 ms"), ("600", "600 ms"), ("750", "750 ms"), ("1000", "1s"), ("2000", "2s"), ("5000", "5s"), ("10000", "10s")])
config.plugins.czechmeteo.refresh = ConfigSelection(default="0", choices=[("0", _("no")), ("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5"), ("10", "10"), ("15", "15")])
config.plugins.czechmeteo.slidetype = ConfigSelection(default="0", choices=[("0", _("begin")), ("1", _("actual position"))])
config.plugins.czechmeteo.download = ConfigYesNo(default=False)
# CHOICES FOR OPTIONS:
choicelist = []
for i in range(0, len(INFO)):
	choicelist.append(("%d" % i, "%s" % INFO[i]))
config.plugins.czechmeteo.type = ConfigSelection(default="8", choices=choicelist)

# CHOICES FOR AFTER "ALL" (WITHOUT "ALL"):
config.plugins.czechmeteo.typeafterall = ConfigSelection(default="9", choices=config.plugins.czechmeteo.type.choices[:-1])
config.plugins.czechmeteo.display = ConfigSelection(default="3", choices=[("0", _("none")), ("1", _("info")), ("2", _("progress bar")), ("3", _("info and progress bar"))])
config.plugins.czechmeteo.localtime = ConfigYesNo(default=False)
config.plugins.czechmeteo.delete = ConfigSelection(default="4", choices=[("0", _("no")), ("1", _("current type")), ("2", _("all types")),
										("3", _("older than max. interval")), ("4", _("older than downloaded interval"))])
config.plugins.czechmeteo.delend = ConfigYesNo(default=True)
config.plugins.czechmeteo.tmpdir = ConfigDirectory(TMPDIR)
config.plugins.czechmeteo.mer = ConfigYesNo(default=False)
config.plugins.czechmeteo.regions = ConfigYesNo(default=False)
config.plugins.czechmeteo.home = ConfigYesNo(default=False)
config.plugins.czechmeteo.city = ConfigYesNo(default=False)

choicelist = []
for i in range(16, 65):
	choicelist.append(("%d" % i, "%s mins" % i))
cfg = config.plugins.czechmeteo

TMPDIR = cfg.tmpdir.value

from twisted.internet.defer import DeferredSemaphore
from twisted.web.client import downloadPage


class LimitedDownloader:
	def __init__(self, howMany):
		self._semaphore = DeferredSemaphore(howMany)

	def downloadPage(self, *a, **kw):
		return self._semaphore.run(downloadPage, *a, **kw)


class czechMeteo(Screen, HelpableScreen):

	if HD:
		cx = "center"			# x-position of window
		cy = "60"			# y-position of window
		sx = 800 			# x-size of window
		sy = 650			# y-size of window
		bgcolor = "#00000000"		# background of window
		# size for picture:
		px = 0				#
		py = 30
		pw = 800			# width of pictures
		ph = 600			# height of pictures
		# arrows:
		tx = 391			# top
		ty = py
		lx = 0				# left
		ly = 321
		rx = 790			# right
		ry = ly
		bx = tx				# bottom
		by = ph + py - 10
		# status bar, clock:
		msg_y = ph + py
		div_y = msg_y - 2		# top line of statusbar
		div_w = sx
		cli_x = sx - 55 - 15 - 10  # x-position of clock's icon
		cli_y = msg_y + 3
		cl_x = sx - 55			# x-position of clock
		cl_y = msg_y
		msg_w = cl_x			# width of status bar
		div2_y = msg_y + 20		# bottom line of statusbar
		down_x = 120
		down_y = msg_y + 5
		slide_x = 450
		slide_y = msg_y + 7
	else:
		cx = "center"
		cy = 50
		sx = 640
		sy = 500
		bgcolor = "#31000000"
		# size for picture:
		px = 20
		py = 30
		pw = 600			# width of pictures
		ph = 450			# height of pictures
		# arrows:
		tx = 311			# top
		ty = py
		lx = 0				# left
		ly = 250
		rx = 630			# right
		ry = ly
		bx = tx				# bottom
		by = ph + py - 10
		# status bar, clock:
		msg_y = ph + py + 2
		div_y = msg_y - 2		# top line of statusbar
		div_w = sx
		cli_x = sx - 55 - 15 - 10  # x-position of clock's icon
		cli_y = msg_y + 3
		cl_x = sx - 55			# x-position of clock
		cl_y = msg_y
		msg_w = cl_x			# width of status bar
		div2_y = msg_y + 20		# bottom line of statusbar
		down_x = 100
		down_y = msg_y + 4
		slide_x = 330
		slide_y = msg_y + 7

	skin = """
		<screen name="czechMeteo" position="%s,%s" size="%s,%s" backgroundColor="%s" title="CzechMeteo">

			<widget name="border" position="%s,%s" zPosition="2" size="%s,%s" alphatest="on"/>
			<widget name="mer" position="%s,%s" zPosition="3" size="%s,%s" alphatest="on"/>
			<widget name="frames" position="%s,%s" zPosition="1" size="%s,%s" alphatest="on"/>
			<widget name="home" position="%s,%s" zPosition="1" size="%s,%s" alphatest="on"/>

			<ePixmap position="  0,0" size="160,30" pixmap="%s%s" zPosition="2" alphatest="blend" />
			<ePixmap position="160,0" size="160,30" pixmap="%s%s" zPosition="2" alphatest="blend" />
			<ePixmap position="320,0" size="160,30" pixmap="%s%s" zPosition="2" alphatest="blend" />
			<ePixmap position="480,0" size="160,30" pixmap="%s%s" zPosition="2" alphatest="blend" />

			<widget name="key_red"    position="  0,0" zPosition="3" size="160,30" valign="center" halign="center" font="Regular;20" transparent="1" foregroundColor="white" />
			<widget name="key_green"  position="160,0" zPosition="3" size="160,30" valign="center" halign="center" font="Regular;20" transparent="1" foregroundColor="white" />
			<widget name="key_yellow" position="320,0" zPosition="3" size="160,30" valign="center" halign="center" font="Regular;20" transparent="1" foregroundColor="white" />
			<widget name="key_blue"   position="480,0" zPosition="3" size="160,30" valign="center" halign="center" font="Regular;20" transparent="1" foregroundColor="white" />

			<ePixmap position="%s,%s" size="18,10" pixmap="%s%s" zPosition="4" alphatest="on" />
			<ePixmap position="%s,%s" size="10,18" pixmap="%s%s" zPosition="4" alphatest="on" />
			<ePixmap position="%s,%s" size="10,18" pixmap="%s%s" zPosition="4" alphatest="on" />
			<ePixmap position="%s,%s" size="18,10" pixmap="%s%s" zPosition="4" alphatest="on" />

			<ePixmap pixmap="skin_default/div-h.png" position="0,%s" zPosition="4" size="%s,3" transparent="0" />
			<ePixmap alphatest="on" pixmap="skin_default/icons/clock.png" position="%s,%s" size="14,14" zPosition="4"/>
			<widget font="Regular;18" halign="left" position="%s,%s" render="Label" size="55,20" source="global.CurrentTime" transparent="0" valign="center" zPosition="4">
				<convert type="ClockToText">Default</convert>
			</widget>
			<widget name="msg" position="0,%s" zPosition="4" size="%s,20" valign="center" halign="left" font="Regular;18" transparent="0" foregroundColor="white" />
			<ePixmap pixmap="skin_default/div-h.png" position="0,%s" zPosition="4" size="%s,2" transparent="0" />

			<widget name="download" position="%s,%s" zPosition="5" borderWidth="1" size="100,12" backgroundColor="#0000ff" />
			<widget name="slide" position="%s,%s" zPosition="5" borderWidth="0" size="210,6" backgroundColor="dark" />

		</screen>""" % (cx, cy, sx, sy, bgcolor,
				px, py, pw, ph,
				px, py, pw, ph,
				px, py, pw, ph,
				px, py, pw, ph,
				PPATH, "red.png", PPATH, "green.png", PPATH, "yellow.png", PPATH, "blue.png",
				tx, ty, PPATH, "top.png",
				lx, ly, PPATH, "left.png",
				rx, ry, PPATH, "right.png",
				bx, by, PPATH, "bottom.png",
				div_y, div_w,
				cli_x, cli_y,
				cl_x, cl_y,
				msg_y, msg_w,
				div2_y, div_w,
				down_x, down_y,
				slide_x, slide_y)

	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.skinName = ["czechMeteo", "meteoViewer"]
		self.setup_title = _("CzechMeteo")

		# Used timers
		self.stopSlideShowDelay = eTimer()
		self.stopSlideShowDelay.timeout.get().append(self.stopSlideShowFinished)
		self.waitLastFrame = eTimer()
		self.waitLastFrame.timeout.get().append(self.lastFrame)
		self.waitDownloadFrames = eTimer()
		self.waitDownloadFrames.timeout.get().append(self.downloadFrames)
		self.waitHTTPS = eTimer()
		self.waitHTTPS.timeout.get().append(self.httpsRun)
		self.waitFiles = eTimer()
		self.waitFiles.timeout.get().append(self.waitingFiles)
		self.slideShowTimer = eTimer()
		self.slideShowTimer.timeout.get().append(self.slideShowEvent)
		self.refreshTimer = eTimer()
		self.refreshTimer.timeout.get().append(self.setRefreshFlag)
		self.waitRefresh = eTimer()
		self.waitRefresh.timeout.get().append(self.waitingRefresh)

		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
			{
			"cancel": (self.end, _("exit plugin")),
			"ok": (self.lastFrame, _("go to last frame")),
			})

		self["CzechMeteoActions"] = HelpableActionMap(self, "CzechMeteoActions",
			{
			"menu": (self.showMenu, _("menu")),
			"left": (self.previousFrame, _("go to previous frame")),
			"right": (self.nextFrame, _("go to next frame")),
			"up": (self.increase_typ, _("switch to next meteo type")),
			"down": (self.decrease_typ, _("switch to previous meteo type")),
			"red": (self.end, _("exit plugin")),
			"green": (self.slideButton, _("play/stop slideshow")),
			"play": (self.runSlideShow, _("play slideshow")),
			"yellow": (self.download_delayed, _("run/abort download")),
			"blue": (self.callCfg, _("options")),
			"stop": (self.stopSlideShow, _("stop slideshow/synaptic map")),
			"tv": (self.displaySynaptic, _("synaptic maps")),
			"8": (self.deleteFrame, _("delete current frame")),
			"previous": (self.firstFrame, _("go to first downloaded frame")),
			"next": (self.lastFrame, _("go to last downloaded frame")),
			#"1": (self.refreshFrames, _("refresh last frame")),
			}, -2)

		self.picload = self.initPixmap("frames", self.showPic)
		self.borderLoad = self.initPixmap("border", self.showBorderPic)
		self.merLoad = self.initPixmap("mer", self.showMerPic)
		self.homeLoad = self.initPixmap("home", self.showHomePic)

		self["msg"] = Label()
		self["description"] = Label()

		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label()
		self["key_yellow"] = Label(_("Download"))
		self["key_blue"] = Label(_("Options"))

		self["download"] = ProgressBar()
		self["download"].hide()
		self["slide"] = ProgressBar()
		self["slide"].hide()

		self.x = 0
		self.dlFrame = 0
		self.errFrame = 0
		self.idx = 0
		self.EXT = ".jpg"
		self.startIdx = 0
		self.maxFrames = 0
		self.filesOK = False
		self.isShow = False
		self.typ = int(cfg.type.value)
		self.last_frame = False
		self.isReading = False
		self.stopRead = False
		self.isSynaptic = False
		self.beginTime = 0
		self.endTime = 0
		self.refreshLast = False
		self.refreshFlag = False
		self.midx = 0
		self.maxMap = 0
		self.firstSynaptic = False
		self.mainMenu = False

		self.queue = []

		self.Limited = LimitedDownloader(5)  # limit for parallel downloading
		if cfg.download.value:
			self.onLayoutFinish.append(self.download_delayed)
		else:
			if self.typ == (len(TYPE) - 1):
				self.typ = int(cfg.typeafterall.value)
			self.onLayoutFinish.append(self.readFiles)
		self.onShown.append(self.setParams)

	def initPixmap(self, widget, callback):
		self[widget] = Pixmap()

		loader = enigma.ePicLoad()
		loader.PictureData.get().append(callback)

		return loader

	def setPicloadPara(self, widget, loader):
		par = [
			self[widget].instance.size().width(),
			self[widget].instance.size().height(),
			1, 1, False, 0, "#00000000"
		]
		loader.setPara(par)

	def setParams(self):
		self.displayMeteoType()

		self.setPicloadPara("frames", self.picload)
		self.setPicloadPara("border", self.borderLoad)
		self.setPicloadPara("mer", self.merLoad)
		self.setPicloadPara("home", self.homeLoad)

	def showPixmap(self, loader, widget):
		ptr = loader.getData()
		if ptr is not None:
			self[widget].instance.setPixmap(ptr.__deref__())
			self[widget].show()

	def showPic(self, picInfo=None):
		self.showPixmap(self.picload, "frames")

	def showBorderPic(self, picInfo=None):
		self.showPixmap(self.borderLoad, "border")

	def showMerPic(self, picInfo=None):
		self.showPixmap(self.merLoad, "mer")

	def showHomePic(self, picInfo=None):
		self.showPixmap(self.homeLoad, "home")

	def getDir(self, num_typ):
		return TMPDIR + SUBDIR + "/" + TYPE[num_typ] + "/"

	def setWindowTitle(self):
		self.setTitle(_("CzechMeteo"))

	def runSlideShow(self):
		if not self.isShow:
			self.slideShow()

	def slideButton(self):
		if self.isShow:
			self.stopSlideShow()
		else:
			self.slideShow()

	def showMenu(self):
		if self.isReading:
			return
		menu = []
		self.mainMenu = True
		for i in range(0, len(TYPE)-1):
#			print(INFO[i], TYPE[i])
			menu.append((INFO[i], TYPE[i]))
		self.session.openWithCallback(self.menuCallback, ChoiceBox, title=_("Select info type:"), list=menu)

	def menuCallback(self, choice):
		if choice is None:
			return
		self.typ = int(TYPE.index(choice[1]))
		self.displayMeteoType()
		if self.typ == len(TYPE) - 1:
			self.download_delayed()
		else:
			self.readFiles(green=False)
			if not self.filesOK:
				self.download_delayed()

	def increase_typ(self):
		self.change_type(1)

	def decrease_typ(self):
		self.change_type(-1)

	def change_type(self, step):
		slide = self.isShow
		if slide:
			self.stopSlideShow(delay=False)
		self.typ += step
		if self.typ < 0:
			self.typ = len(TYPE) - 2
		elif self.typ > len(TYPE) - 2:
			self.typ = 0
		self.displayMeteoType()
		self.readFiles(delay=0.1, border=True)
		if slide:
			self.slideShow()

	def displayMeteoType(self):
#		print("000000000000", self.typ)
		self.setTitle(_("CzechMeteo") + " - " + INFO[self.typ])
		self.displayDescription()

	def displayMsg(self, message):
		self["msg"].setText("  " + message)

	def displayDescription(self):
		self["description"].setText(DESCR[self.typ])		

	def download_delayed(self):
		self["slide"].hide()
		if self.isReading:
			self.stopRead = True
		else:
			self.displayMsg(_("Prepare..."))
			self.waitDownloadFrames.start(250, True)

	def downloadFrames(self):
		self.emptyFrame()
		if self.isShow:
			self.stopSlideShow()
		if not self.isShow:
#			if cfg.tmpdir.value.startswith('/tmp/'):
#				self.typ = int(cfg.typeafterall.value)

			self["key_red"].setText(_("Back"))
			self["key_green"].setText("")
			self["key_yellow"].setText(_("Abort"))
			self["key_blue"].setText("")

			print("[CzechMeteo] download - type: %s" % TYPE[self.typ])
			self.downloadFiles(TYPE[self.typ])

			self.displayMsg(_("Download:"))
			self["download"].setValue(0)
			self["download"].show()

			self.waitFiles.start(500, True)
		else:
			self.displayMsg(_("Stop slideshow, please!"))

	def waitingFiles(self):
		if self.dlFrame:
			print("[CzechMeteo] NR: %d" % self.dlFrame)
			self["download"].setValue(int(100.0 * (self.x - self.dlFrame) / self.x + 0.25))
			self.waitFiles.start(100, True)
		else:
			self["download"].setValue(self.x)
			self["download"].hide()
			self.displayMsg("")
			self.isReading = False
			self.statistic()
			self["key_red"].setText(_("Cancel"))
			self["key_green"].setText(_("Slideshow"))
			self["key_yellow"].setText(_("Download"))
			self["key_blue"].setText(_("Options"))
			self.stopRead = False
			self.readFiles()
			self.readMap()

	def refreshFrames(self):
		self.refreshLast = True
		self.displayMsg(_("refresh..."))

		self.downloadFiles(TYPE[self.typ])
		self.waitRefresh.start(100, True)

	def waitingRefresh(self):
		if self.dlFrame:
			self.waitRefresh.start(100, True)
		else:
			self.isReading = False
			self.refreshLast = False
			self.statistic()
			self.readFiles(last_frame=False, green=False)
			self.slideShowTimer.start(int(cfg.time.value), True)

	def setRefreshFlag(self):
		self.refreshFlag = True
		self.refreshTimer.start(int(cfg.refresh.value) * 60000, True)

	def getFilesFromDir(self, directory, matchingPattern):
		result = []
		try:
			files = os.listdir(directory)
		except Exception:
			files = []
		files.sort()
		files = [x for x in files if not os.path.isdir(os.path.join(directory, x))]
		for x in files:
			path = os.path.join(directory, x)
			if (matchingPattern is None) or search(matchingPattern, path):
				result.append(x)
		return result

	def readFiles(self, last_frame=True, empty_frame=True, border=False, green=True, delay=0.2):
		self.setExtension()
		self.maxFrames = 0
		self.frame = []
		for x in self.getFilesFromDir(self.getDir(self.typ), self.EXT):
			self.frame.append(x[:-4])
			self.maxFrames += 1

		self.filesOK = False
		if self.maxFrames != 0:
			self.filesOK = True
			self.setIndex()
			if border:
				self.redrawBorder()
			if green:
				self["key_green"].setText(_("Slideshow"))
			if last_frame:
				self.waitLastFrame.start(int(delay * 1000), True)
		else:
			self.setIndex()
			if empty_frame:
				self.emptyFrame()
			if border:
				self.redrawBorder()
			self["slide"].hide()
			self.displayMsg(_("No files found!"))

	def statistic(self):
		self.endTime = time()
		print("[CzechMeteo] >>> Files readed=%d, skipped=%d, time: %d:%02d min" % (self.x, self.errFrame, (self.endTime - self.beginTime) // 60, (self.endTime - self.beginTime) % 60))

	def setIndex(self):
		self.idx = self.startIdx = 0
		if TYPE[self.typ] == "lightning": # 10 minuts
			if self.maxFrames > int(cfg.nr.value) // 4 * 6:
				if cfg.frames.value == "0":
					self.startIdx = self.maxFrames - int(cfg.nr.value) // 4 * 6 - 1
		elif TYPE[self.typ] in ("radar", "rain"): # 5 minuts
			if self.maxFrames > int(cfg.nr.value) // 4 * 12:
				if cfg.frames.value == "0":
					self.startIdx = self.maxFrames - int(cfg.nr.value) // 4 * 12 - 1
		else: # 15 minuts
			if self.maxFrames > int(cfg.nr.value):
				if cfg.frames.value == "0":
					self.startIdx = self.maxFrames - int(cfg.nr.value) - 1
		self.idx = self.startIdx
		#print("[CzechMeteo] >>> type: %s, maxFrames=%d, cfg.nr=%d, cfg.frames=%s startIdx=%d" % (TYPE[self.typ], self.maxFrames, int(cfg.nr.value),cfg.frames.value, self.startIdx))

	def afterCfg(self, data=True):
		if self.isSynaptic:
			self.displaySynoptic(True)
			self.displayInfo(self.idx + 1, self.maxFrames, self.frame[self.idx])
			if cfg.display.value > "1":
				self["slide"].show()
			return

		self.displayMeteoType()
		if self.lastdir != cfg.tmpdir.value:
			self.readFiles(delay=0.5)
			if self.filesOK:
				self.redrawBorder()
		else:
			if self.last_frames != cfg.frames.value:
				self.readFiles()
			else:
				if self.filesOK:
					self.redrawFrame()
					self.redrawBorder()
		if not self.filesOK:
			self.displayMsg(_("Download pictures, please!"))

	def callCfg(self):
		if not self.isShow and not self.isReading:
			self.displayMsg("")
			self.emptyFrame()
			self["slide"].hide()
			self.lastdir = cfg.tmpdir.value
			self.last_typ = self.typ
			self.last_frames = cfg.frames.value
			self.session.openWithCallback(self.afterCfg, czechMeteoCfg)

	def redrawFrame(self):
		path = self.getDir(self.typ) + self.frame[self.idx] + self.EXT
		if fileExists(path):
			self.displayFrame(path)
			self.displayInfo(self.idx + 1, self.maxFrames, self.frame[self.idx])
			if cfg.display.value > "1":
				self["slide"].show()

	def setExtension(self):
		if TYPE[self.typ] in ("lightning", "radar", "rain"):
			self.EXT = ".png"
		else:
			self.EXT = ".jpg"

	def displayFrame(self, path):
		if TYPE[self.typ] in ("lightning", "radar", "rain"):
			self.borderLoad.startDecode(path)
		else:
			self.picload.startDecode(path)

	def firstFrame(self):
		if self.isSynaptic:
			self.isSynaptic = False
		self.displayMeteoType()
		self.displayMsg("")
		if self.filesOK:
			self.redrawBorder()
			if not self.isShow:
				path = self.getDir(self.typ) + self.frame[self.startIdx] + self.EXT
				if fileExists(path):
					self.displayFrame(path)
					if cfg.display.value > "1":
						self["slide"].setValue(100)
						self["slide"].show()
						self.displayInfo(self.startIdx + 1, self.maxFrames, self.frame[self.idx])
					self.idx = self.startIdx
		else:
			self.emptyFrame()
			self.displayMsg(_("Download pictures, please!"))

	def lastFrame(self):
		#print(self.typ, TYPE[self.typ])
		if self.isSynaptic:
			self.isSynaptic = False

		self.displayMeteoType()
		self.displayMsg("")
		if self.filesOK:
			self.redrawBorder()
			if not self.isShow:
				path = self.getDir(self.typ) + self.frame[self.maxFrames - 1] + self.EXT
				if fileExists(path):
					self.displayFrame(path)
					if cfg.display.value > "1":
						self["slide"].setValue(100)
						self["slide"].show()
						self.displayInfo(self.maxFrames, self.maxFrames, self.frame[self.maxFrames - 1])
					self.idx = self.maxFrames - 1
		else:
			self.emptyFrame()
			self.displayMsg(_("Download pictures, please!"))

	def nextFrame(self):
		if self.isSynaptic:
			self.isSynaptic = False
			self.redrawBorder()
		self.displayMsg("")
		if self.filesOK:
			if not self.isShow:
				if self.idx < (self.maxFrames - 1):
					self.idx += 1
				else:
					self.idx = self.startIdx
				path = self.getDir(self.typ) + self.frame[self.idx] + self.EXT
				if fileExists(path):
					self.displayFrame(path)
					self.displayInfo(self.idx + 1, self.maxFrames, self.frame[self.idx])
			else:
				self.displayMsg(_("Stop slideshow, please!"))
		else:
			self.displayMsg(_("No files found!"))

	def previousFrame(self):
		if self.isSynaptic:
			self.isSynaptic = False
			self.redrawBorder()
		self.displayMsg("")
		if self.filesOK:
			if not self.isShow:
				if self.idx > self.startIdx:
					self.idx -= 1
				else:
					self.idx = self.maxFrames - 1
				path = self.getDir(self.typ) + self.frame[self.idx] + self.EXT
				if fileExists(path):
					self.displayFrame(path)
					self.displayInfo(self.idx + 1, self.maxFrames, self.frame[self.idx])
			else:
				self.displayMsg(_("Stop slideshow, please!"))
		else:
			self.displayMsg(_("No files found!"))

	def redrawBorder(self):
		if self.isSynaptic:
			if TYPE[self.typ] not in ("lightning", "radar", "rain"):
				self.borderLoad.startDecode(PPATH + MER[len(TYPE) - 1])
			else:
				self.picload.startDecode(PPATH + BACKGROUND[len(BACKGROUND) - 1])
			self.merLoad.startDecode(PPATH + MER[len(TYPE) - 1])
			self.firstSynaptic = False
		else:
			if TYPE[self.typ] in ("lightning", "radar", "rain"):
				RADAR_BACKGROUND = BACKGROUND[self.typ]
				if cfg.city.value:
					RADAR_BACKGROUND = RADAR_CITY
				self.picload.startDecode(PPATH + RADAR_BACKGROUND)

				if TYPE[self.typ] in ("radar", "rain"):
					if cfg.mer.value and fileExists(E2PATH + RADAR_MM): # for own mm picture
						self.merLoad.startDecode(E2PATH + RADAR_MM)
					else:
						self.merLoad.startDecode(PPATH + RADAR_MM)
				else:
					self.merLoad.startDecode(PPATH + MER[len(TYPE) - 1])

				if cfg.home.value and fileExists(E2PATH + HOME_RADAR):
					self.homeLoad.startDecode(E2PATH + HOME_RADAR)
				else:
					self.homeLoad.startDecode(PPATH + MER[len(TYPE) - 1])
			else:
				if cfg.regions.value and TYPE[self.typ] in ("vis", "ircz", "bt", "24m", "wv"):
					self.borderLoad.startDecode(PPATH + REGIONS)
				else:
					self.borderLoad.startDecode(PPATH + BACKGROUND[self.typ])
				if cfg.mer.value: # paralel an meridians
					self.merLoad.startDecode(PPATH + MER[self.typ])
				else:
					self.merLoad.startDecode(PPATH + MER[len(TYPE) - 1])

				if cfg.home.value: # home position
					if TYPE[self.typ] in ("ireu", "viseu", "irce", "visce", "vis", "ircz", "bt", "24m", "wv", "lightning") and fileExists(E2PATH + HOME[self.typ]):
						self.homeLoad.startDecode(E2PATH + HOME[self.typ])
					else:
						self.homeLoad.startDecode(PPATH + MER[len(TYPE) - 1])
				else:
					self.homeLoad.startDecode(PPATH + MER[len(TYPE) - 1])

	def slideShow(self):
		self.isSynaptic = False
		self.redrawBorder()

		if int(cfg.refresh.value) > 0:
			self.refreshFlag = False
			self.refreshTimer.start(int(cfg.refresh.value) * 60000, True)
		if self.filesOK:
			self.isShow = True

			if cfg.slidetype.value == "0": 		# from begin
				self.idx = self.startIdx
			elif cfg.slidetype.value == "1":	# from actual position
				if self.idx > self.startIdx:
					self.idx += 1
					if self.idx >= self.maxFrames:
						self.idx = self.startIdx

			self["key_green"].setText(_("Stop Show"))
			self["key_yellow"].setText("")
			self["key_blue"].setText("")
			self.slideShowTimer.start(500, True)

	def stopSlideShow(self, delay=True):
		if self.isShow:
			self.slideShowTimer.stop()
			if int(cfg.refresh.value) > 0:
				self.refreshTimer.stop()
			self["key_green"].setText(_("Slideshow"))
			self["key_yellow"].setText(_("Download"))
			self["key_blue"].setText(_("Options"))
			if self.filesOK:
				if self.idx == self.startIdx:
					self.idx = self.maxFrames - 1
				else:
					self.idx -= 1
			else:
				self.emptyFrame()
				self.displayMsg(_("No files found!"))
			if delay:
				self.stopSlideShowDelay.start(1000, True)
			else:
				self.stopSlideShowFinished()

	def stopSlideShowFinished(self):
		self.isShow = False

	def displaySynaptic(self):
		if self.isShow:
			self.stopSlideShow()
		if self.isReading:
			self.isReading = False
		else:  # if is not slideshow with STOP button:
			if not self.isSynaptic:
				self.firstSynaptic = True
			self.isSynaptic = True
			if self.firstSynaptic:
				self.redrawBorder()
			self.displaySynoptic()

	def slideShowEvent(self):
		if self.filesOK:
			if self.isShow:
				if self.idx < self.maxFrames:
					path = self.getDir(self.typ) + self.frame[self.idx] + self.EXT
					if fileExists(path):
						self.displayFrame(path)
						self.displayInfo(self.idx + 1, self.maxFrames, self.frame[self.idx])
						self.idx += 1
					self.slideShowTimer.start(int(cfg.time.value), True)
				else:   # pozastaveni na konci. Jestlize nechci, tak sloucit a jen zmenit podminku a index
					if self.refreshFlag:
						self.refreshFrames()
						self.refreshFlag = False
					else:
						self.slideShowTimer.start(int(cfg.time.value), True)
					self.idx = self.startIdx
				#self.slideShowTimer.start(int(cfg.time.value), True)
		else:
			self.emptyFrame()
			self.displayMsg(_("No files found!"))

	def displayInfo(self, i, n, name):
		if cfg.display.value == "1":
			self.displayMsg(_("%s of %s  -  %s") % (i, n, self.timeFormat(name)))
		elif cfg.display.value == "2":
			self["slide"].setValue(int(100.0 * i / n + 0.25))
		elif cfg.display.value == "3":
			self.displayMsg(_("%s of %s  -  %s") % (i, n, self.timeFormat(name)))
			self["slide"].setValue(int(100.0 * i / n + 0.25))

	def readMap(self):
		self.maxMap = 0
		self.map = []
		for x in self.getFilesFromDir(TMPDIR + SUBDIR, ".gif"):
			self.map.append(x[:-4])
			self.maxMap += 1

	def displaySynoptic(self, decrease=False):
		if self.maxMap > 0:
			if decrease:  # for return from config only
				self.midx -= 1
			self.isSynaptic = True
			path = TMPDIR + SUBDIR + "/" + self.map[self.midx] + ".gif"
			if fileExists(path):
				self.displayFrame(path)
				#self.displayInfo(self.midx+1,self.maxMap,self.frame[self.midx])
			if self.midx < (self.maxMap - 1):
				self.midx += 1
			else:
				self.midx = 0

	def timeFormat(self, name):
		epochTimeUTC = mktime(strptime(name, '%Y%m%d%H%M'))
		if cfg.localtime.value:
			utcTime = localtime(epochTimeUTC)
			localTime = calendar.timegm(utcTime)
			return strftime("%d.%m.%Y %H:%M", localtime(localTime)) + " " + _("LT")
		else:
			return strftime("%d.%m.%Y %H:%M", localtime(epochTimeUTC)) + " " + _("UTC")

	def emptyFrame(self):
		if fileExists(PPATH + EMPTYFRAME):
			self.displayFrame(PPATH + EMPTYFRAME)

	def deleteFrame(self):
		if not self.isShow and not self.isReading:
			if self.filesOK:
				self.session.openWithCallback(self.eraseFrame, MessageBox, _("Are You sure delete this frame?"), MessageBox.TYPE_YESNO, default=False)
			else:
				self.displayMsg(_("No files found!"))

	def eraseFrame(self, answer):
		if answer is True:
			removedIdx = self.idx
			os.unlink("%s%s" % (self.getDir(self.typ), self.frame[self.idx] + self.EXT))
			self.readFiles(last_frame=False)
			if removedIdx > self.maxFrames - 1:
				self.idx = self.maxFrames - 1
			elif removedIdx < self.startIdx:
				self.idx = self.startIdx
			else:
				self.idx = removedIdx
			self.redrawFrame()
		else:
			return

	def deleteOldFiles(self, typ, lastUTCTime):
		self.setExtension()
		name = strftime("%Y%m%d%H%M", lastUTCTime) + self.EXT
		for x in self.getFilesFromDir(self.getDir(TYPE.index(typ)), self.EXT):
			if x < name:
				os.unlink("%s%s" % (self.getDir(TYPE.index(typ)), x))

	def downloadFiles(self, typ):
		self.isReading = True
		self.x = self.dlFrame = self.errFrame = 0

		if cfg.delete.value == "1" or cfg.delete.value == "2":
			self.displayMsg(_("Erase files..."))
			if typ == "all" or cfg.delete.value == "2":
				os.system("rm -r %s >/dev/null 2>&1" % (TMPDIR + SUBDIR))
			else:
				os.system("rm %s*.* >/dev/null 2>&1" % (self.getDir(TYPE.index(typ))))

		os.system("mkdir %s >/dev/null 2>&1" % (TMPDIR + SUBDIR))
		if typ == "all":
			for i in range(0, len(TYPE) - 1):
				os.system("mkdir %s >/dev/null 2>&1" % (self.getDir(i)))
		else:
			os.system("mkdir %s >/dev/null 2>&1" % (self.getDir(TYPE.index(typ))))

		self.beginTime = time()
		if not self.stopRead:
			if not self.refreshLast:  # dont read if refresh
				self.downloadOnce(typ)

		if typ in ("ireu", "viseu", "irce", "visce", "vis", "ircz", "bt", "24m", "wv", "radar", "rain", "all"):
			if not self.stopRead:
				self.downloadMain(typ)
		if typ in ("lightning", "all"):
			if not self.stopRead:
				self.downloadLightning(typ)
		if self.typ == len(TYPE) - 1:  # from ALL after start of plugin set typ "After All"
			self.typ = int(cfg.typeafterall.value)

		self.stopRead = False

	def downloadFail(self, failure):
		print("[CzechMeteo]", failure)
		self.dlFrame -= 1
		self.errFrame += 1

	def afterDownload(self, result=None):
		self.dlFrame -= 1

	def increment(self):
		self.x += 1
		self.dlFrame += 1

	def downloadOnce(self, typ):  # only, when is choose "Download"
		#print("[CzechMeteo] >>>Once>>>", typ,  TYPE.index(typ))
		os.system("rm %s/*.* >/dev/null 2>&1" % (TMPDIR + SUBDIR))

		url = "https://intranet.chmi.cz/files/portal/docs/meteo/om/evropa/T2m_stredomori.gif"
		path = "%s03T2m_stredomori.gif" % (TMPDIR + SUBDIR + "/")
		self.downloadFrame(url, path)
		url = "https://intranet.chmi.cz/files/portal/docs/meteo/om/evropa/RH_stredomori.gif"
		path = "%s04RH_stredomori.gif" % (TMPDIR + SUBDIR + "/")
		self.downloadFrame(url, path)
		url = "https://intranet.chmi.cz/files/portal/docs/meteo/om/svet/T2m_svet.gif"
		path = "%s05T2m_svet.gif" % (TMPDIR + SUBDIR + "/")
		self.downloadFrame(url, path)
		url = "https://intranet.chmi.cz/files/portal/docs/meteo/om/svet/T2m_amerika.gif"
		path = "%s06T2m_amerika.gif" % (TMPDIR + SUBDIR + "/")
		self.downloadFrame(url, path)
		url = "https://intranet.chmi.cz/files/portal/docs/meteo/om/svet/T2m_jvazaust.gif"
		path = "%s07T2m_jvazaust.gif" % (TMPDIR + SUBDIR + "/")
		self.downloadFrame(url, path)
		url = "https://intranet.chmi.cz/files/portal/docs/meteo/om/svet/T2m_afrika.gif"
		path = "%s08T2m_afrika.gif" % (TMPDIR + SUBDIR + "/")
		self.downloadFrame(url, path)
		url = "https://intranet.chmi.cz/files/portal/docs/meteo/om/evropa/T2m_evropa.gif"
		path = "%s02T2m_evropa.gif" % (TMPDIR + SUBDIR + "/")
		self.downloadFrame(url, path)
		url = "https://intranet.chmi.cz/files/portal/docs/meteo/om/evropa/analyza.gif"
		path = "%s01synoptic.gif" % (TMPDIR + SUBDIR + "/")
		self.downloadFrame(url, path)

	def downloadFrame(self, url, path):
		#print("[CzechMeteo] >>>downloadFrame>>>", url, path)
		if self.stopRead:
			self.dlFrame = 0
			return False
		if not os.path.isfile(path):
			if url.startswith('https'):
				self.increment()
				self.queue.append((url, path))
				if not self.waitHTTPS.isActive():
					self.waitHTTPS.start(500, True)
			else:
				self.increment()
				self.Limited.downloadPage(url.encode('utf-8'), path).addCallbacks(self.afterDownload).addErrback(self.downloadFail)
		return True

	def download(self):
		if len(self.queue):
			(url, path) = self.queue.pop(0)
			self.downloadHttpsPicture(url, path)

	def httpsRun(self):
		self.download()
		if self.stopRead:
			self.waitHTTPS.stop()
			self.dlFrame = 0
			return

	def downloadHttpsPicture(self, url, path):
		self.Limited.downloadPage(url.encode('utf-8'), path).addCallback(self.afterHTTPSDownload).addErrback(self.downloadHTTPSFail)
	def afterHTTPSDownload(self, result=None):
		self.dlFrame -= 1
		if len(self.queue):
			self.waitHTTPS.start(20, True)
	def downloadHTTPSFail(self, failure):
		print("[CzechMeteo]", failure)
		self.dlFrame -= 1
		self.errFrame += 1
		self.x -= 1
		if len(self.queue):
			self.waitHTTPS.start(20, True)

	def downloadMain(self, typ):
		#print("[CzechMeteo] >>>Main>>>", typ,  TYPE.index(typ))
		interval = int(cfg.nr.value) * 900
		step = 900			# 15 minut
		if typ in ("radar", "rain"):	# 5 minuts radar
			step = 300
		now = int(time())		# LT
		now15 = (now // step) * step 	# last x min

		start = now15 - interval
		stop = now15 + step

		if cfg.delete.value == "3" or cfg.delete.value == "4":
			startDel = start
			if cfg.delete.value == "3":
				startDel = now15 - int(cfg.nr.choices[len(cfg.nr.choices) - 1]) * 900
			if typ == "all":
				for i in ("ireu", "viseu", "irce", "visce", "vis", "ircz", "bt", "24m", "wv", "radar", "rain"):
					self.deleteOldFiles(i, gmtime(startDel))
			else:
				self.deleteOldFiles(typ, gmtime(startDel))

		page = "https://opendata.chmi.cz/meteorology/weather/satellite/geo"

		for i in range(start, stop, step):
			frDate = strftime("%Y%m%d", gmtime(i))  # utc
			frTime = strftime("%H%M", gmtime(i))  # utc

			if typ == "ireu" or typ == "all":
				url = "%s/ir108/%s%s_geo_ir108_eu.jpg" % (page, frDate, frTime)
				path = "%s%s%s.jpg" % (self.getDir(TYPE.index("ireu")), frDate, frTime)
				if not self.downloadFrame(url, path):
					break
			if typ == "viseu" or typ == "all":
				url = "%s/vis-ir/%s%s_geo_vis-ir_eu.jpg" % (page, frDate, frTime)
				path = "%s%s%s.jpg" % (self.getDir(TYPE.index("viseu")), frDate, frTime)
				if not self.downloadFrame(url, path):
					break
			if typ == "irce" or typ == "all":
				url = "%s/ir108/%s%s_geo_ir108_ce.jpg" % (page, frDate, frTime)
				path = "%s%s%s.jpg" % (self.getDir(TYPE.index("irce")), frDate, frTime)
				if not self.downloadFrame(url, path):
					break
			if typ == "visce" or typ == "all":
				url = "%s/vis-ir/%s%s_geo_vis-ir_ce.jpg" % (page, frDate, frTime)
				path = "%s%s%s.jpg" % (self.getDir(TYPE.index("visce")), frDate, frTime)
				if not self.downloadFrame(url, path):
					break
			if typ == "vis" or typ == "all":
				url = "%s/vis-ir/%s%s_geo_vis-ir_cz.jpg" % (page, frDate, frTime)
				path = "%s%s%s.jpg" % (self.getDir(TYPE.index("vis")), frDate, frTime)
				if not self.downloadFrame(url, path):
					break
			if typ == "ircz" or typ == "all":
				url = "%s/ir108/%s%s_geo_ir108_cz.jpg" % (page, frDate, frTime)
				path = "%s%s%s.jpg" % (self.getDir(TYPE.index("ircz")), frDate, frTime)
				if not self.downloadFrame(url, path):
					break
			if typ == "bt" or typ == "all":
				url = "%s/ir108BT/%s%s_geo_ir108BT_cz.jpg" % (page, frDate, frTime)
				path = "%s%s%s.jpg" % (self.getDir(TYPE.index("bt")), frDate, frTime)
				if not self.downloadFrame(url, path):
					break
			if typ == "wv" or typ == "all":
				url = "%s/wv062/%s%s_geo_wv062_cz.jpg" % (page, frDate, frTime)
				path = "%s%s%s.jpg" % (self.getDir(TYPE.index("wv")), frDate, frTime)
				if not self.downloadFrame(url, path):
					break
			if typ == "24m" or typ == "all":
				url = "%s/24M/%s%s_geo_24M_cz.jpg" % (page, frDate, frTime)
				path = "%s%s%s.jpg" % (self.getDir(TYPE.index("24m")), frDate, frTime)
				if not self.downloadFrame(url, path):
					break

			if typ == "radar" or typ == "all":
				url = "https://opendata.chmi.cz/meteorology/weather/radar/composite/maxz/png/pacz2gmaps3.z_max3d.%s.%s.0.png" % (frDate, frTime)
				path = "%s%s%s.png" % (self.getDir(TYPE.index("radar")), frDate, frTime)
				if not self.downloadFrame(url, path):
					break
			if typ == "rain" or typ == "all":
				url = "https://opendata.chmi.cz/meteorology/weather/radar/composite/pseudocappi2km/png/pacz2gmaps3.z_cappi020.%s.%s.0.png" % (frDate, frTime)
				path = "%s%s%s.png" % (self.getDir(TYPE.index("rain")), frDate, frTime)
				if not self.downloadFrame(url, path):
					break

	def downloadLightning(self, typ):
		#print("[CzechMeteo] >>>Lightning>>>", typ, TYPE.index(typ))
		interval = int(cfg.nr.value) * 900
		step = 600			# 10 minut
		now = int(time())		# LT
		now10 = (now // step) * step 	# last x min
		start = now10 - interval
		stop = now10 + step

		if cfg.delete.value == "3" or cfg.delete.value == "4":
			startDel = start
			if cfg.delete.value == "3":
				startDel = now10 - int(cfg.nr.choices[len(cfg.nr.choices) - 1]) * 900
			if typ == "all":
				for i in ("lightning",):
					self.deleteOldFiles(i, gmtime(startDel))
			else:
				self.deleteOldFiles(typ, gmtime(startDel))

		for i in range(start, stop, step):
			frDate = strftime("%Y%m%d", gmtime(i))  # utc
			frTime = strftime("%H%M", gmtime(i))  # utc
			url = "https://produkty.chmi.cz/radar/input_data/blesk/pacz2gmaps3.blesk.%s.%s.png" % (frDate, frTime)
			path = "%s%s%s.png" % (self.getDir(TYPE.index("lightning")), frDate, frTime)
			if not self.downloadFrame(url, path):
				break


	def eraseAllDirectory(self):
		os.system("rm -r %s >/dev/null 2>&1" % (TMPDIR + SUBDIR))

	def end(self):
		if self.mainMenu:
			if self.isReading:
				self.stopRead = True
				return
			if cfg.delend.value:
				self.eraseAllDirectory()
				#cfg.delend.value = False
			self.close()
		else:
			self.close()
#			self.showMenu()


class czechMeteoCfg(Screen, ConfigListScreen):

	bgcolor = "#31000000"
	if HD:
		bgcolor = "#00000000"

	skin = """
	<screen name="czechMeteoCfg" position="center,center" size="560,380" title="CzechMeteo Setup" backgroundColor="%s" >

		<ePixmap name="red"    position="0,0"   zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap name="green"  position="140,0" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />

		<widget name="key_red" position="0,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" /> 
		<widget name="key_green" position="140,0" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;20" transparent="1" shadowColor="background" shadowOffset="-2,-2" />

		<widget name="config" position="10,40" size="540,300" zPosition="1" transparent="0" backgroundColor="%s" scrollbarMode="showOnDemand" />

		<ePixmap pixmap="skin_default/div-h.png" position="0,355" zPosition="1" size="560,2" />
		<ePixmap alphatest="on" pixmap="skin_default/icons/clock.png" position="480,361" size="14,14" zPosition="3"/>
		<widget font="Regular;18" halign="right" position="495,358" render="Label" size="55,20" source="global.CurrentTime" transparent="1" valign="center" zPosition="3">
			<convert type="ClockToText">Default</convert>
		</widget>

	</screen>""" % (bgcolor, bgcolor)

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.skinName = "Setup"
		self.setup_title = "%s - %s" % (_("CzechMeteo Setup"), VERSION)

		self["key_green"] = Label(_("Save"))
		self["key_red"] = Label(_("Cancel"))
		self["description"] = Label()

		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.save,
			"ok": self.ok,
			"red": self.exit,
			"cancel": self.exit
		}, -2)

		self.tmpdir_entry = getConfigListEntry(_("Directory for download"), cfg.tmpdir)

		self["config"] = List()
		cfgList = []
		cfgList.append(getConfigListEntry(_("Run from 'Extended' menu"), cfg.extended_menu))
		cfgList.append(getConfigListEntry(_("Downloaded interval"), cfg.nr))
		cfgList.append(getConfigListEntry(_("Display"), cfg.frames))
		cfgList.append(getConfigListEntry(_("Slideshow's step"), cfg.time))
		cfgList.append(getConfigListEntry(_("Refresh slideshow"), cfg.refresh))
		cfgList.append(getConfigListEntry(_("Slideshow begins from"), cfg.slidetype))
		cfgList.append(getConfigListEntry(_("Download info on plugin's start"), cfg.download))
		cfgList.append(getConfigListEntry(_("Type of meteo info on start"), cfg.type))
		cfgList.append(getConfigListEntry(_("After download \"All\" switch to"), cfg.typeafterall))
		cfgList.append(getConfigListEntry(_("Delete old files before download"), cfg.delete))
		cfgList.append(getConfigListEntry(_("On exit delete files"), cfg.delend))
		cfgList.append(getConfigListEntry(_("Frames info"), cfg.display))
		cfgList.append(getConfigListEntry(_("Local time in info"), cfg.localtime))
		cfgList.append(getConfigListEntry(_("Parallels and meridians"), cfg.mer))
		cfgList.append(getConfigListEntry(_("Display CZ Regions"), cfg.regions))
		cfgList.append(getConfigListEntry(_("Display cities in radars and lightning background"), cfg.city))
		cfgList.append(getConfigListEntry(_("Display home position"), cfg.home, _("For it must be files homece.png, homecz.png (both as 1160*800), homecsr.png (810*610), homeradar.png (680x640) with mark there in /etc/enigma.")))
		cfgList.append(self.tmpdir_entry)
		self["config"].list = cfgList
		ConfigListScreen.__init__(self, cfgList, session, on_change=self.changedEntry)

		self.onChangedEntry = []
		self.old_dir = cfg.tmpdir.value
		self.onShown.append(self.setWindowTitle)

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary
	###

	def setWindowTitle(self):
		self.setTitle(self.setup_title)

	def ok(self):
		from Screens.LocationBox import LocationBox
		currentry = self["config"].getCurrent()
		if currentry == self.tmpdir_entry:
			txt = _("Location for CzechMeteo")
			inhibitDirs = ["/bin", "/boot", "/dev", "/etc", "/lib", "/proc", "/sbin", "/sys", "/usr"]
			self.session.openWithCallback(self.dirSelected, LocationBox, text=txt, currDir=cfg.tmpdir.value,
							bookmarks=config.movielist.videodirs, autoAdd=False, editDir=True,
							inhibitDirs=inhibitDirs, minFree=400)  # in MB
		else:
			ConfigListScreen.keyOK(self)

	def dirSelected(self, res):
		if res is not None:
			cfg.tmpdir.value = res
		else:
			cfg.tmpdir.value = self.old_dir
		self["description"].setText("")

	def save(self):
		global TMPDIR
		if TMPDIR != cfg.tmpdir.value:
			os.system("rm -r %s >/dev/null 2>&1" % (TMPDIR + SUBDIR))
		TMPDIR = cfg.tmpdir.value
		if INFO[int(cfg.type.value)] == 'All' and cfg.tmpdir.value.startswith('/tmp/'):
			text = _("!!! '%s' as 'All' cannot be used with '/tmp/' !!!") % _("Type of meteo info on start")
			self["description"].setText(text)
			return
		self.refreshPlugins()
		self.keySave()

	def exit(self):
		cfg.tmpdir.value = self.old_dir
		self.keyCancel()

	def refreshPlugins(self):
		from Components.PluginComponent import plugins
		from Tools.Directories import SCOPE_PLUGINS, resolveFilename
		plugins.clearPluginList()
		plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))
