from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSlider
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.Label import Label
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Tools.Directories import fileExists
from enigma import eTimer
from enigma import eDBoxLCD

config.plugins.brightnesssetup = ConfigSubsection()
config.plugins.brightnesssetup.brightness = ConfigSlider(default = 1, increment = 1, limits = (0,15))
config.plugins.brightnesssetup.brightnessdeepstandby = ConfigSlider(default = 5, increment = 1, limits = (0,15))
config.plugins.brightnesssetup.blinkingtime = ConfigSlider(default = 5, increment = 1, limits = (0,15))

class LEDOption:
	BRIGHTNESS = 0
	DEEPSTANDBY = 1
	BLINKINGTIME = 2

class LEDBrightnessSetupStandby:
	def __init__(self):
		self.initLEDSetup()

	def initLEDSetup(self):
		brightness = int(config.plugins.brightnesssetup.brightness.value)
		brightnessstandby = int(config.plugins.brightnesssetup.brightnessdeepstandby.value)
		blinkingtime = int(config.plugins.brightnesssetup.blinkingtime.value)
		eDBoxLCD.getInstance().setLEDDefault(brightness, brightnessstandby, blinkingtime)

class LEDBrightnessSetup(Screen,ConfigListScreen):
	skin = """
			<screen name="LEDBrightnessSetup" position="center,center" size="560,300" title="LED Brightness Setup">
			<ePixmap pixmap="Vu_HD/buttons/red.png" position="10,10" size="25,25" alphatest="on" />
			<ePixmap pixmap="Vu_HD/buttons/green.png" position="195,10" size="25,25" alphatest="on" />
			<ePixmap pixmap="Vu_HD/buttons/yellow.png" position="380,10" size="25,25" alphatest="on" />
			<widget source="key_red" render="Label" position="30,10" zPosition="1" size="140,25" font="Regular;20" halign="center" valign="center" transparent="1" />
			<widget source="key_green" render="Label" position="215,10" zPosition="1" size="140,25" font="Regular;20" halign="center" valign="center" transparent="1" />
			<widget source="key_yellow" render="Label" position="400,10" zPosition="1" size="140,25" font="Regular;20" halign="center" valign="center" transparent="1" />
			<widget name="config" zPosition="2" position="5,50" size="550,200" scrollbarMode="showOnDemand" transparent="1"/>
			<widget name="current_entry" position="130,240" size="300,30" font="Regular;18" halign="center" valign="center"/>
			</screen>"""

	def __init__(self,session):
		Screen.__init__(self,session)
		self.session = session
		self["shortcuts"] = ActionMap(["ShortcutActions", "SetupActions" ],
		{
			"ok": self.keySave,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keySave,
			"yellow": self.keyDefault,
		}, -2)
		self.list = []
		ConfigListScreen.__init__(self, self.list,session = self.session)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Ok"))
		self["key_yellow"] = StaticText(_("Defalut"))
		self["current_entry"]=Label("")
		self.createSetup()
		self.onLayoutFinish.append(self.checkModel)
		self.checkModelTimer = eTimer()
		self.checkModelTimer.callback.append(self.invalidmodel)
		if not self.displayText in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.displayText)

	def displayText(self):
		if self["config"].getCurrent() == self.brightness:
			self["current_entry"].setText("Touch LED Brightness at Normal state")
		elif self["config"].getCurrent() == self.brightness_deepstandby:
			self["current_entry"].setText("Touch LED Brightness at Deep Standby")
		elif self["config"].getCurrent() == self.blinkingtime:
			self["current_entry"].setText("Touch LED Blinking time")
		self.setCurrentValue()

	def getModel(self):
		if fileExists("/proc/stb/info/vumodel"):
			vumodel = open("/proc/stb/info/vumodel")
			info=vumodel.read().strip()
			vumodel.close()
			if info == "ultimo":
				return True
			else:
				return False
		else:
			return False

	def checkModel(self):
		if not self.getModel():
			self.checkModelTimer.start(100,True)

	def invalidmodel(self):
			self.session.openWithCallback(self.close, MessageBox, _("This Plugin only support for ULTIMO"), MessageBox.TYPE_ERROR, timeout = 30)

	def createSetup(self):
		self.list = []
		self.brightness = getConfigListEntry(_("Normal state"), config.plugins.brightnesssetup.brightness)
		self.brightness_deepstandby = getConfigListEntry(_("Deep Standby"), config.plugins.brightnesssetup.brightnessdeepstandby)
		self.blinkingtime = getConfigListEntry(_("Blinking time"), config.plugins.brightnesssetup.blinkingtime)
		self.list.append( self.brightness )
		self.list.append( self.brightness_deepstandby )
		self.list.append( self.blinkingtime )
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def setCurrentValue(self):
		if self["config"].getCurrent() == self.blinkingtime:
			eDBoxLCD.getInstance().setLED(1 ,LEDOption.BRIGHTNESS)
			eDBoxLCD.getInstance().setLED(self["config"].getCurrent()[1].value ,LEDOption.BLINKINGTIME)
		else:
			eDBoxLCD.getInstance().setLED(self["config"].getCurrent()[1].value ,LEDOption.BRIGHTNESS)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.setCurrentValue()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.setCurrentValue()

	def saveLEDSetup(self):
		brightness = config.plugins.brightnesssetup.brightness.value
		brightnessstandby = config.plugins.brightnesssetup.brightnessdeepstandby.value
		blinkingtime = config.plugins.brightnesssetup.blinkingtime.value
		eDBoxLCD.getInstance().setLED(brightness ,LEDOption.BRIGHTNESS)
		eDBoxLCD.getInstance().setLED(brightnessstandby ,LEDOption.DEEPSTANDBY)
		eDBoxLCD.getInstance().setLED(blinkingtime ,LEDOption.BLINKINGTIME)

	def keySave(self):
		if self["config"].isChanged():
			self.saveLEDSetup()
		ConfigListScreen.keySave(self)

	def keyDefault(self):
		config.plugins.brightnesssetup.brightness.setValue(1)
		config.plugins.brightnesssetup.brightnessdeepstandby.setValue(5)
		config.plugins.brightnesssetup.blinkingtime.setValue(5)
		for entry in self["config"].getList():
			self["config"].l.invalidateEntry(self["config"].getList().index(entry))

	def cancelConfirm(self, result):
		if not result:
			return
		for x in self["config"].list:
			x[1].cancel()
		self.saveLEDSetup()
		self.close()

def main(session, **kwargs):
	session.open(LEDBrightnessSetup)

def Plugins(**kwargs):
	return [PluginDescriptor(name=_("LED Brightness Setup"), description="Setup LED brightness and blink interval", where = PluginDescriptor.WHERE_PLUGINMENU, needsRestart = False, fnc=main)]

ledbrightnesssetupstandby = LEDBrightnessSetupStandby()
