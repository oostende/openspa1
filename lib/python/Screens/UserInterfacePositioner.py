from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.config import config, configfile, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.SystemInfo import SystemInfo
from Components.Sources.StaticText import StaticText
from Components.Pixmap import Pixmap
from Components.Console import Console
from enigma import getDesktop, iPlayableService, iServiceInformation, eServiceCenter, eServiceReference, eDVBDB
from os import access, R_OK
from boxbranding import getBoxType, getBrandOEM

from Components.ServiceEventTracker import ServiceEventTracker
from Screens.ChannelSelection import FLAG_IS_DEDICATED_3D


def InitOsd():
	try:
		SystemInfo["CanChange3DOsd"] = (access('/proc/stb/fb/3dmode', R_OK) or access('/proc/stb/fb/primary/3d', R_OK)) and True or False
	except:
		SystemInfo["CanChange3DOsd"] = False
	try:
		SystemInfo["CanChangeOsdAlpha"] = access('/proc/stb/video/alpha', R_OK) and True or False
	except:
		SystemInfo["CanChangeOsdAlpha"] = False
	try:
		SystemInfo["CanChangeOsdPosition"] = access('/proc/stb/fb/dst_left', R_OK) and True or False
	except:
		SystemInfo["CanChangeOsdPosition"] = False
	SystemInfo["OsdSetup"] = SystemInfo["CanChangeOsdPosition"]
	if SystemInfo["CanChangeOsdAlpha"] == True or SystemInfo["CanChangeOsdPosition"] == True:
		SystemInfo["OsdMenu"] = True
	else:
		SystemInfo["OsdMenu"] = False

	if getBrandOEM() in ('fulan'):
		SystemInfo["CanChangeOsdPosition"] = False
		SystemInfo["CanChange3DOsd"] = False

	def setOSDLeft(configElement):
		if SystemInfo["CanChangeOsdPosition"]:
			f = open("/proc/stb/fb/dst_left", "w")
			f.write('%X' % configElement.getValue())
			f.close()
	config.osd.dst_left.addNotifier(setOSDLeft)

	def setOSDWidth(configElement):
		if SystemInfo["CanChangeOsdPosition"]:
			f = open("/proc/stb/fb/dst_width", "w")
			f.write('%X' % configElement.getValue())
			f.close()
	config.osd.dst_width.addNotifier(setOSDWidth)

	def setOSDTop(configElement):
		if SystemInfo["CanChangeOsdPosition"]:
			f = open("/proc/stb/fb/dst_top", "w")
			f.write('%X' % configElement.getValue())
			f.close()
	config.osd.dst_top.addNotifier(setOSDTop)

	def setOSDHeight(configElement):
		if SystemInfo["CanChangeOsdPosition"]:
			f = open("/proc/stb/fb/dst_height", "w")
			f.write('%X' % configElement.getValue())
			f.close()
	config.osd.dst_height.addNotifier(setOSDHeight)
	print 'Setting OSD position: %s %s %s %s' %  (config.osd.dst_left.getValue(), config.osd.dst_width.getValue(), config.osd.dst_top.getValue(), config.osd.dst_height.getValue())

	def setOSDAlpha(configElement):
		if SystemInfo["CanChangeOsdAlpha"]:
			print 'Setting OSD alpha:', str(configElement.getValue())
			config.av.osd_alpha.setValue(configElement.getValue())
			f = open("/proc/stb/video/alpha", "w")
			f.write(str(configElement.getValue()))
			f.close()
	config.osd.alpha.addNotifier(setOSDAlpha)

	def set3DMode(configElement):
		global isDedicated3D, sessiong
		if SystemInfo["CanChange3DOsd"]:
			mode =  configElement.getValue()
			if sessiong:
				isDedicated3D = checkIfDedicated3D(sessiong)
			mode = isDedicated3D and mode == "auto" and "sidebyside" or mode
			print 'Setting 3D mode:',mode
			f = open("/proc/stb/fb/3dmode", "w")
			f.write(mode)
			f.close()
	config.osd.threeDmode.addNotifier(set3DMode)

	def set3DZnorm(configElement):
		if SystemInfo["CanChange3DOsd"]:
			print 'Setting 3D depth:',configElement.getValue()
			f = open("/proc/stb/fb/znorm", "w")
			f.write('%d' % int(configElement.getValue()-50))
			f.close()
	config.osd.threeDznorm.addNotifier(set3DZnorm)

class UserInterfacePositioner(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setup_title = _("Position Setup")
		self.Console = Console()
		self["status"] = StaticText()
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText(_("Defaults"))

		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
				"left": self.keyLeft,
				"right": self.keyRight,
				"yellow": self.keyDefault,
			}, -2)

		self.onChangedEntry = [ ]
		self.list = []
		ConfigListScreen.__init__(self, self.list, session = self.session, on_change = self.changedEntry)
		if SystemInfo["CanChangeOsdAlpha"] == True:
			self.list.append(getConfigListEntry(_("User interface visibility"), config.osd.alpha, _("This option lets you adjust the transparency of the user interface")))
			self.list.append(getConfigListEntry(_("Teletext base visibility"), config.osd.alpha_teletext, _("Base transparency for teletext, more options available within teletext screen.")))
			self.list.append(getConfigListEntry(_("Web browser base visibility"), config.osd.alpha_webbrowser, _("Base transparency for OpenOpera web browser")))
		if SystemInfo["CanChangeOsdPosition"] == True:
			self.list.append(getConfigListEntry(_("Move Left/Right"), config.osd.dst_left, _("Use the Left/Right buttons on your remote to move the user inyterface left/right")))
			self.list.append(getConfigListEntry(_("Width"), config.osd.dst_width, _("Use the Left/Right buttons on your remote to adjust the size of the user interface. Left button decreases the size, Right increases the size.")))
			self.list.append(getConfigListEntry(_("Move Up/Down"), config.osd.dst_top, _("Use the Left/Right buttons on your remote to move the user interface up/down")))
			self.list.append(getConfigListEntry(_("Height"), config.osd.dst_height, _("Use the Left/Right buttons on your remote to adjust the size of the user interface. Left button decreases the size, Right increases the size.")))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

		self.onLayoutFinish.append(self.layoutFinished)
		if not self.selectionChanged in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.selectionChanged)
		self.selectionChanged()

	def selectionChanged(self):
		if getBoxType().startswith('azbox'):
			pass
		else:
			self["status"].setText(self["config"].getCurrent()[2])

	def layoutFinished(self):
		self.setTitle(_(self.setup_title))
		self.Console.ePopen('/usr/bin/showiframe /usr/share/enigma2/hd-testcard.mvi')

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.setPreviewPosition()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.setPreviewPosition()

	def keyDefault(self):
		config.osd.alpha.setValue(255)
		config.osd.alpha_teletext.setValue(255)
		config.osd.alpha_webbrowser.setValue(255)

		config.osd.dst_left.setValue(0)
		config.osd.dst_width.setValue(720)
		config.osd.dst_top.setValue(0)
		config.osd.dst_height.setValue(576)
		self["config"].l.setList(self.list)

	def setPreviewPosition(self):
		size_w = getDesktop(0).size().width()
		size_h = getDesktop(0).size().height()
		dsk_w = int(float(size_w)) / float(720)
		dsk_h = int(float(size_h)) / float(576)
		dst_left = int(config.osd.dst_left.getValue())
		dst_width = int(config.osd.dst_width.getValue())
		dst_top = int(config.osd.dst_top.getValue())
		dst_height = int(config.osd.dst_height.getValue())
		while dst_width + (dst_left / float(dsk_w)) >= 720.5 or dst_width + dst_left > 720:
			dst_width = int(dst_width) - 1
		while dst_height + (dst_top / float(dsk_h)) >= 576.5 or dst_height + dst_top > 576:
			dst_height = int(dst_height) - 1

		config.osd.dst_left.setValue(dst_left)
		config.osd.dst_width.setValue(dst_width)
		config.osd.dst_top.setValue(dst_top)
		config.osd.dst_height.setValue(dst_height)
		print 'Setting OSD position: %s %s %s %s' %  (config.osd.dst_left.getValue(), config.osd.dst_width.getValue(), config.osd.dst_top.getValue(), config.osd.dst_height.getValue())

	def saveAll(self):
		for x in self["config"].list:
			x[1].save()
		configfile.save()

	# keySave and keyCancel are just provided in case you need them.
	# you have to call them by yourself.
	def keySave(self):
		self.saveAll()
		self.close()

	def cancelConfirm(self, result):
		if not result:
			return

		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def keyCancel(self):
		if self["config"].isChanged():
			from Screens.MessageBox import MessageBox
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"), default = False)
		else:
			self.close()

	def run(self):
		config.osd.dst_left.save()
		config.osd.dst_width.save()
		config.osd.dst_top.save()
		config.osd.dst_height.save()
		configfile.save()
		self.close()

class OSD3DSetupScreen(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setup_title = _("OSD 3D Setup")
		self.skinName = "Setup"
		self["status"] = StaticText()
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))

		self["actions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
			}, -2)

		self.onChangedEntry = [ ]
		self.list = []
		ConfigListScreen.__init__(self, self.list, session = self.session, on_change = self.changedEntry)
		self.list.append(getConfigListEntry(_("3D Mode"), config.osd.threeDmode, _("This option lets you choose the 3D mode")))
		self.list.append(getConfigListEntry(_("Depth"), config.osd.threeDznorm, _("This option lets you adjust the 3D depth")))
		self.list.append(getConfigListEntry(_("Show in extensions list ?"), config.osd.show3dextensions, _("This option lets you show the option in the extension screen")))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

		self.onLayoutFinish.append(self.layoutFinished)
		if not self.selectionChanged in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.selectionChanged)
		self.selectionChanged()

	def selectionChanged(self):
		self["status"].setText(self["config"].getCurrent()[2])

	def layoutFinished(self):
		self.setTitle(_(self.setup_title))

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def saveAll(self):
		for x in self["config"].list:
			x[1].save()
		configfile.save()

	# keySave and keyCancel are just provided in case you need them.
	# you have to call them by yourself.
	def keySave(self):
		self.saveAll()
		self.close()

	def cancelConfirm(self, result):
		if not result:
			return

		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def keyCancel(self):
		if self["config"].isChanged():
			from Screens.MessageBox import MessageBox
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.close()

previous = None
isDedicated3D = False
sessiong = None

def applySettings(mode=config.osd.threeDmode.value, znorm=int(config.osd.threeDznorm.value)-50):
	global previous, isDedicated3D
	mode = isDedicated3D and mode == "auto" and "sidebyside" or mode
	mode == "3dmode" in SystemInfo["3DMode"] and mode or mode == 'sidebyside' and 'sbs' or mode == 'topandbottom' and 'tab' or 'off'
	if previous != (mode, znorm):
		try:
			open(SystemInfo["3DMode"], "w").write(mode)
			open(SystemInfo["3DZNorm"], "w").write('%d' % znorm)
			previous = (mode, znorm)
		except:
			return

def checkIfDedicated3D(session):
	service = session.nav.getCurrentlyPlayingServiceReference()
	servicepath = service and service.getPath()
	if servicepath and servicepath.startswith("/"):
		if service.toString().startswith("1:"):
			info = eServiceCenter.getInstance().info(service)
			service = info and info.getInfoString(service, iServiceInformation.sServiceref)
			return service and eDVBDB.getInstance().getFlag(eServiceReference(service)) & FLAG_IS_DEDICATED_3D == FLAG_IS_DEDICATED_3D and "sidebyside"
		else:
			return ".3d." in servicepath.lower() and "sidebyside" or ".tab." in servicepath.lower() and "topandbottom"
	service = session.nav.getCurrentService()
	info = service and service.info()
	return info and info.getInfo(iServiceInformation.sIsDedicated3D) == 1 and "sidebyside"

class auto3D(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		global sessiong
		sessiong = session
		self.session = session
		self.__event_tracker = ServiceEventTracker(screen = self, eventmap =
			{
				iPlayableService.evStart: self.__evStart,
				iPlayableService.evEnd: self.__evStop,
			})

	def __evStop(self):
		if config.osd.threeDmode.value == "auto":
			applySettings("off")

	def __evStart(self):
		if config.osd.threeDmode.value == "auto":
			global isDedicated3D
			isDedicated3D = checkIfDedicated3D(self.session)
			if isDedicated3D:
				applySettings(isDedicated3D)
			else:
				applySettings("off")

