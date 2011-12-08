from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigInteger
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Tools.Directories import fileExists
from enigma import eTimer
from ledsetup import LEDUpdate

config.plugins.brightnesssetup = ConfigSubsection()
config.plugins.brightnesssetup.brightness = ConfigInteger(default = 1, limits = (1,15))
config.plugins.brightnesssetup.brightnessstandby = ConfigInteger(default = 5, limits = (1,15))
config.plugins.brightnesssetup.brightnessdeepstandby = ConfigInteger(default = 5, limits = (1,15))
config.plugins.brightnesssetup.blinkingtime = ConfigInteger(default = 5, limits = (1,15))

class LEDOption:
	BRIGHTNESS = 0
	DEEPSTANDBY = 1
	BLINKINGTIME = 2

class LEDBrightnessSetupStandby:
	def __init__(self):
		self.initLEDSetup()
		config.misc.standbyCounter.addNotifier(self.standbyBegin, initial_call = False)

	def standbyBegin(self, configElement):
		from Screens.Standby import inStandby
		inStandby.onClose.append(self.StandbyEnd)
		brightness = int(config.plugins.brightnesssetup.brightnessstandby.value)
		LEDUpdate(brightness ,LEDOption.BRIGHTNESS)

	def StandbyEnd(self):
		brightness = int(config.plugins.brightnesssetup.brightness.value)
		LEDUpdate(brightness ,LEDOption.BRIGHTNESS)

	def initLEDSetup(self):
		brightness = int(config.plugins.brightnesssetup.brightness.value)
		brightnessstandby = int(config.plugins.brightnesssetup.brightnessdeepstandby.value)
		blinkingtime = int(config.plugins.brightnesssetup.blinkingtime.value)
		cmdList = []
		cmdList.append( (brightness,LEDOption.BRIGHTNESS) )
		cmdList.append( (brightnessstandby,LEDOption.DEEPSTANDBY) )
		cmdList.append( (blinkingtime,LEDOption.BLINKINGTIME) )
		for ( value, option ) in cmdList:
			ret = LEDUpdate(value ,option)
			if ret != 0:
				print "DEVICE OPEN ERROR"
				break;

class LEDBrightnessSetup(Screen,ConfigListScreen):
	skin = """
			<screen name="LEDBrightnessSetup" position="center,center" size="560,250" title="LED Brightness Setup" >
			<ePixmap pixmap="Vu_HD/buttons/red.png" position="10,10" size="25,25" alphatest="on" />
			<ePixmap pixmap="Vu_HD/buttons/green.png" position="290,10" size="25,25" alphatest="on" />
			<widget source="key_red" render="Label" position="40,10" zPosition="1" size="140,25" font="Regular;20" halign="center" valign="center" transparent="1" />
			<widget source="key_green" render="Label" position="320,10" zPosition="1" size="140,25" font="Regular;20" halign="center" valign="center" transparent="1" />
			<widget name="config" zPosition="2" position="5,50" size="550,200" scrollbarMode="showOnDemand" transparent="1" />
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
		}, -2)
		self.list = []
		ConfigListScreen.__init__(self, self.list,session = self.session)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Ok"))
		self.createSetup()
		self.onLayoutFinish.append(self.checkModel)
		self.checkModelTimer = eTimer()
		self.checkModelTimer.callback.append(self.invalidmodel)

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
		self.brightness = getConfigListEntry(_("Touch LED brightness at normal state"), config.plugins.brightnesssetup.brightness)
		self.brightness_standby = getConfigListEntry(_("Touch LED brightness at Standby"), config.plugins.brightnesssetup.brightnessstandby)
		self.brightness_deepstandby = getConfigListEntry(_("Touch LED brightness at Deep Standby"), config.plugins.brightnesssetup.brightnessdeepstandby)
		self.blinkingtime = getConfigListEntry(_("Touch LED blinking time"), config.plugins.brightnesssetup.blinkingtime)
		self.list.append( self.brightness )
		self.list.append( self.brightness_standby )
		self.list.append( self.brightness_deepstandby )
		self.list.append( self.blinkingtime )
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def saveLEDSetup(self):
		brightness = int(config.plugins.brightnesssetup.brightness.value)
		brightnessstandby = int(config.plugins.brightnesssetup.brightnessdeepstandby.value)
		blinkingtime = int(config.plugins.brightnesssetup.blinkingtime.value)
		cmdList = []
		cmdList.append( (brightness,LEDOption.BRIGHTNESS) )
		cmdList.append( (brightnessstandby,LEDOption.DEEPSTANDBY) )
		cmdList.append( (blinkingtime,LEDOption.BLINKINGTIME) )
		for ( value, option ) in cmdList:
			ret = LEDUpdate(value ,option)
			if ret != 0:
				self.session.open(MessageBox, "DEVICE OPEN ERROR", type = MessageBox.TYPE_ERROR, timeout = 30)
				break;

	def keySave(self):
		self.saveLEDSetup()
		ConfigListScreen.keySave(self)

def main(session, **kwargs):
	session.open(LEDBrightnessSetup)

def Plugins(**kwargs):
	return [PluginDescriptor(name=_("LED Brightness Setup"), description="Setup LED brightness and blink interval", where = PluginDescriptor.WHERE_PLUGINMENU, needsRestart = False, fnc=main)]

ledbrightnesssetupstandby = LEDBrightnessSetupStandby()
