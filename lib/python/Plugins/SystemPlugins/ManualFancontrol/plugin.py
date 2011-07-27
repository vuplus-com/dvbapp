from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSelection, ConfigInteger
from Components.ActionMap import ActionMap,NumberActionMap
from Screens.MessageBox import MessageBox
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Plugins.SystemPlugins.ManualFancontrol.InstandbyOn import instandbyon
import NavigationInstance

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
		self.configSetup()

	def isRecording(self):
		recordings = NavigationInstance.instance.getRecordings()
		if recordings :
			return True
		else:
			return False

	def displayCurrentValue(self):
		currrent_val = self["config"].getCurrent()[0]+" : "+str(self["config"].getCurrent()[1].value)
		self["current"].setText(_(currrent_val))
		print currrent_val

	def selectionChanged(self):
		if self["config"].getCurrent() == self.pwmEntry:
			instandbyon.setPWM(self["config"].getCurrent()[1].value)

	def keyLeft(self):
		oldpwmvalue=config.plugins.simplefancontrols.pwmvalue.value
		ConfigListScreen.keyLeft(self)
		if self["config"].getCurrent() == self.pwmEntry and oldpwmvalue == 5:
			self.createSetup()
		else:
			self.displayCurrentValue()
		self.selectionChanged()

	def keyRight(self):
		oldpwmvalue=config.plugins.simplefancontrols.pwmvalue.value
		ConfigListScreen.keyRight(self)
		if self["config"].getCurrent() == self.pwmEntry and oldpwmvalue == 0:
			self.createSetup()
			while self["config"].getCurrent() != self.pwmEntry:
				self["config"].setCurrentIndex(self["config"].getCurrentIndex()+1)
		else:
			self.displayCurrentValue()
		self.selectionChanged()

	def createSetup(self):
		self.list = []
		if config.plugins.simplefancontrols.pwmvalue.value > 0:
			self.list.append( self.standbyEntry )
		self.list.append( self.pwmEntry )
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def configSetup(self):
		self.standbyEntry = getConfigListEntry(_("FanOFF InStanby"), config.plugins.simplefancontrols.standbymode)
		self.pwmEntry = getConfigListEntry(_("PWM value"), config.plugins.simplefancontrols.pwmvalue)
		if not self.displayCurrentValue in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.displayCurrentValue)
		self.createSetup()

	def newConfig(self):
		if self["config"].getCurrent() == self.pwmEntry and config.plugins.simplefancontrols.pwmvalue.value == 0:
			self.createSetup()

	def keySave(self):
		if instandbyon.fanoffmode is 'OFF' and config.plugins.simplefancontrols.pwmvalue.value == 0:
			instandbyon.appendRecordEventCallback()
			instandbyon.fanoffmode = 'ON'
			print "<SimpleFancontrol> instandbyon.fanoffmode 'OFF' -> 'ON'"

		elif instandbyon.fanoffmode is 'ON' and config.plugins.simplefancontrols.pwmvalue.value != 0:
			instandbyon.removeRecordEventCallback()
			instandbyon.fanoffmode = 'OFF'
			print "<SimpleFancontrol> instandbyon.fanoffmode 'ON' -> 'OFF'"
		if instandbyon.fanoffmode == 'ON' and self.isRecording() and instandbyon.getPWM() != instandbyon.default_pwm_value_onRecordings:
			instandbyon.setPWM(instandbyon.default_pwm_value_onRecordings)
		ConfigListScreen.keySave(self)

	def cancelConfirm(self, result):
		if not result:
			return
		for x in self["config"].list:
			x[1].cancel()
		if instandbyon.fanoffmode == 'ON' and self.isRecording():
			if instandbyon.getPWM() != instandbyon.default_pwm_value_onRecordings:
				instandbyon.setPWM(instandbyon.default_pwm_value_onRecordings)
			else:
				pass
		else:
			instandbyon.setPWM(config.plugins.simplefancontrols.pwmvalue.value)
		self.close()

	def keyCancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			if instandbyon.fanoffmode == 'ON' and self.isRecording() and instandbyon.getPWM() != instandbyon.default_pwm_value_onRecordings:
				instandbyon.setPWM(instandbyon.default_pwm_value_onRecordings)
			self.close()

def main(session, **kwargs):
	session.open(ManualFancontrol)

def Plugins(**kwargs):
	return [PluginDescriptor(name=_("Manual Fan control"), description="setup Fancontol inStandby mode", where = PluginDescriptor.WHERE_PLUGINMENU, needsRestart = True, fnc=main)]
