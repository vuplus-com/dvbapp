from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSelection, ConfigInteger
from Components.ActionMap import ActionMap,NumberActionMap
from Screens.MessageBox import MessageBox
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Plugins.SystemPlugins.ManualFancontrol.InstandbyOn import instandbyon

class ManualFancontrol(Screen,ConfigListScreen):
	skin = """
			<screen name="ManualFancontrol" position="center,center" size="560,300" title="Fancontrol Settings in Standby mode" >
			<ePixmap pixmap="Vu_HD/buttons/red.png" position="10,10" size="25,25" alphatest="on" />
			<ePixmap pixmap="Vu_HD/buttons/green.png" position="290,10" size="25,25" alphatest="on" />
			<widget source="key_red" render="Label" position="40,10" zPosition="1" size="140,25" font="Regular;20" halign="center" valign="center" transparent="1" />
			<widget source="key_green" render="Label" position="320,10" zPosition="1" size="140,25" font="Regular;20" halign="center" valign="center" transparent="1" />
			<widget name="config" zPosition="2" position="5,50" size="550,200" scrollbarMode="showOnDemand" transparent="1" />
			<widget source="current" render="Label" position="150,270" zPosition="1" size="280,30" font="Regular;20" halign="center" valign="center" transparent="1" />
			</screen>"""

	def __init__(self,session):
		Screen.__init__(self,session)
		print "init"
		self.setup_title="TestSetupTitle"
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
		self["key_green"] = StaticText(_("Save"))
		self["current"] = StaticText(_(" "))
		self.createSetup()

	def displayCurrentValue(self):
		cur = self["config"].getCurrent()[0]
		val = self["config"].getCurrent()[1].value
		currrent_val = cur+" : "+str(val)
		self["current"].setText(_(currrent_val))
		print currrent_val

	def selectionChanged(self):
		self.displayCurrentValue()
		if self["config"].getCurrent() == self.pwmEntry:
			instandbyon.setPWM(self["config"].getCurrent()[1].value)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()
		self.selectionChanged()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()
		self.selectionChanged()

	def createSetup(self):
		self.list = []
		self.standbyEntry = getConfigListEntry(_("FanOFF InStanby"), config.plugins.simplefancontrols.standbymode)
		self.pwmEntry = getConfigListEntry(_("PWM value"), config.plugins.simplefancontrols.pwmvalue)
		self.list.append( self.standbyEntry )
		self.list.append( self.pwmEntry )
		self["config"].list = self.list
		self["config"].l.setList(self.list)
		if not self.displayCurrentValue in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.displayCurrentValue)

	def newConfig(self):
		if self["config"].getCurrent() == self.standbyEntry:
			self.createSetup()

	def keySave(self):
		ConfigListScreen.keySave(self)

	def keyCancel(self):
		ConfigListScreen.keyCancel(self)

def main(session, **kwargs):
	session.open(ManualFancontrol)

def Plugins(**kwargs):
	return [PluginDescriptor(name=_("Manual Fan control"), description="setup Fancontol inStandby mode", where = PluginDescriptor.WHERE_PLUGINMENU, needsRestart = True, fnc=main)]
