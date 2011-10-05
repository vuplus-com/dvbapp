from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSelection, ConfigInteger, ConfigSlider
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import fileExists
from enigma import eTimer
from Plugins.Plugin import PluginDescriptor

config.plugins.UIPositionSetup = ConfigSubsection()
config.plugins.UIPositionSetup.dst_left = ConfigInteger(default = 0)
config.plugins.UIPositionSetup.dst_width = ConfigInteger(default = 720)
config.plugins.UIPositionSetup.dst_top = ConfigInteger(default = 0)
config.plugins.UIPositionSetup.dst_height = ConfigInteger(default = 576)

class UIPositionSetupInit:
	def __init__(self):
		self.setPosition(int(config.plugins.UIPositionSetup.dst_left.value), int(config.plugins.UIPositionSetup.dst_width.value), int(config.plugins.UIPositionSetup.dst_top.value), int(config.plugins.UIPositionSetup.dst_height.value))

	def setPosition(self,dst_left, dst_width, dst_top, dst_height):
		if dst_left + dst_width > 720:
			dst_width = 720 - dst_left
		if dst_top + dst_height > 576:
			dst_height = 576 - dst_top
		print "[UIPositionSetup] write dst_left : ",dst_left
		print "[UIPositionSetup] write dst_width : ",dst_width
		print "[UIPositionSetup] write dst_top : ",dst_top
		print "[UIPositionSetup] write dst_height : ",dst_height
		try:
			file = open("/proc/stb/fb/dst_left", "w")
			file.write('%X' % dst_left)
			file.close()
			file = open("/proc/stb/fb/dst_width", "w")
			file.write('%X' % dst_width)
			file.close()
			file = open("/proc/stb/fb/dst_top", "w")
			file.write('%X' % dst_top)
			file.close()
			file = open("/proc/stb/fb/dst_height", "w")
			file.write('%X' % dst_height)
			file.close()
		except:
			return

uipositionsetupinit = UIPositionSetupInit()

class UIPositionSetup(Screen, ConfigListScreen, UIPositionSetupInit):
	def __init__(self,session):
		size_w = session.desktop.size().width()
		size_h = session.desktop.size().height()
		xpos = (size_w-500)/2
		ypos = (size_h-300)/2
		self.skin=""
		self.skin += "<screen position=\"0,0\" size=\"" + str(size_w) + "," + str(size_h) + "\" title=\"Screen Position Setup\" backgroundColor=\"#27d8dee2\">"
		self.skin += "<ePixmap pixmap=\"Vu_HD/buttons/red.png\" position=\""+str(xpos+10) + "," + str(ypos+10) + "\" size=\"25,25\" alphatest=\"on\" />"
		self.skin += "<ePixmap pixmap=\"Vu_HD/buttons/green.png\" position=\""+str(xpos+290) + "," + str(ypos+10) + "\" size=\"25,25\" alphatest=\"on\" />"
		self.skin += "<widget source=\"key_red\" render=\"Label\" position=\""+str(xpos+40) + "," + str(ypos+10) + "\" zPosition=\"1\" size=\"140,25\" font=\"Regular;20\" halign=\"center\" valign=\"center\" foregroundColor=\"#1c1c1c\" transparent=\"1\" />"
		self.skin += "<widget source=\"key_green\" render=\"Label\" position=\""+str(xpos+320) + "," + str(ypos+10) + "\" zPosition=\"1\" size=\"140,25\" font=\"Regular;20\" halign=\"center\" valign=\"center\" foregroundColor=\"#1c1c1c\" transparent=\"1\" />"
		self.skin += "<widget name=\"config\" zPosition=\"2\" position=\""+str(xpos+5) + "," + str(ypos+50) + "\" size=\"550,200\" scrollbarMode=\"showOnDemand\" foregroundColor=\"#1c1c1c\" transparent=\"1\" />"
		self.skin += "</screen>"

		Screen.__init__(self,session)
		self.session = session
		self["shortcuts"] = ActionMap(["ShortcutActions", "SetupActions" ],
		{
			"ok": self.keyOk,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keyOk,
		}, -2)
		self.list = []
		ConfigListScreen.__init__(self, self.list,session = self.session)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["current"] = StaticText(_(" "))
		self.createSetup()

	def createSetup(self):
		self.list = []

		left = config.plugins.UIPositionSetup.dst_left.value
		width = config.plugins.UIPositionSetup.dst_width.value
		top = config.plugins.UIPositionSetup.dst_top.value
		height = config.plugins.UIPositionSetup.dst_height.value

		self.dst_left = ConfigSlider(default = left, increment = 5, limits = (0, 720))
		self.dst_width = ConfigSlider(default = width, increment = 5, limits = (0, 720))
		self.dst_top = ConfigSlider(default = top, increment = 5, limits = (0, 576))
		self.dst_height = ConfigSlider(default = height, increment = 5, limits = (0, 576))

		self.list.append(getConfigListEntry(_("left"), self.dst_left))
		self.list.append(getConfigListEntry(_("width"), self.dst_width))
		self.list.append(getConfigListEntry(_("top"), self.dst_top))
		self.list.append(getConfigListEntry(_("height"), self.dst_height))

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.setPosition(int(self.dst_left.value), int(self.dst_width.value), int(self.dst_top.value), int(self.dst_height.value))

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.setPosition(int(self.dst_left.value), int(self.dst_width.value), int(self.dst_top.value), int(self.dst_height.value))

	def keyOk(self):
		config.plugins.UIPositionSetup.dst_left.value = self.dst_left.value
		config.plugins.UIPositionSetup.dst_width.value = self.dst_width.value
		config.plugins.UIPositionSetup.dst_top.value = self.dst_top.value
		config.plugins.UIPositionSetup.dst_height.value = self.dst_height.value
		config.plugins.UIPositionSetup.save()
		self.close()

	def keyCancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.close()

	def cancelConfirm(self,ret):
		if ret:
			self.setPosition(int(config.plugins.UIPositionSetup.dst_left.value), int(config.plugins.UIPositionSetup.dst_width.value), int(config.plugins.UIPositionSetup.dst_top.value), int(config.plugins.UIPositionSetup.dst_height.value))
			self.close()

def main(session, **kwargs):
	session.open(UIPositionSetup)

def Plugins(**kwargs):
	if fileExists("/proc/stb/fb/dst_left"):
		return [PluginDescriptor(name = "UI position setup", description = "Adjust screen position", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main)]
	return []

