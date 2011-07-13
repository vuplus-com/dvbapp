from Components.config import config, ConfigSubList, ConfigSubsection
import NavigationInstance
from enigma import iRecordableService
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigSlider
from enigma import eTimer

config.plugins.simplefancontrols = ConfigSubsection()
config.plugins.simplefancontrols.standbymode = ConfigSelection(default = "yes", choices = [
	("no", _("no")), ("yes", _("yes"))])
config.plugins.simplefancontrols.pwmvalue = ConfigSlider(default = 10, increment = 5, limits = (0, 255))

class instandbyOn:
	def __init__(self):
		self.fanoffmode = 'OFF'
		self.default_pwm_value_onRecordings = 5
		config.misc.standbyCounter.addNotifier(self.standbyBegin, initial_call = False)
		if config.plugins.simplefancontrols.pwmvalue.value == 0:
			self.fanoffmode = 'ON'
		self.InitTimer = eTimer()
		if self.initConfig not in self.InitTimer.callback:
			self.InitTimer.callback.append(self.initConfig)
		print "<SimpleFancontrol> init : Timer loop start!!"
		self.InitTimer.startLongTimer(3)
		print "<SimpleFancontrol> init :  self.fanoffmode : ", self.fanoffmode
		print "<SimpleFancontrol> init :  config.plugins.simplefancontrols.pwmvalue.value : ", config.plugins.simplefancontrols.pwmvalue.value

	def initConfig(self):
		print "<SimpleFancontrol>Try initConfig..."
		if NavigationInstance.instance is None:
			self.InitTimer.startLongTimer(1)
		else:
			if config.plugins.simplefancontrols.pwmvalue.value == 0:
				NavigationInstance.instance.record_event.append(self.getRecordEvent_onFanOFF)
				recordings = NavigationInstance.instance.getRecordings()
				print "<SimpleFancontrol> initConfig :  recordings : ", recordings
				if recordings:
					self.setPWM(self.default_pwm_value_onRecordings)
				else:
					self.setPWM(0)
			else:
				self.setPWM(config.plugins.simplefancontrols.pwmvalue.value)

	def standbyBegin(self, configElement):
			print "<SimpleFancontrol> standbyBegin : config.plugins.fancontrols.standbymode.value : ", config.plugins.simplefancontrols.standbymode.value
			print "<SimpleFancontrol> standbyBegin : self.fanoffmode : ", self.fanoffmode
			if config.plugins.simplefancontrols.standbymode.value == "yes" and config.plugins.simplefancontrols.pwmvalue > 0:
				from Screens.Standby import inStandby
				inStandby.onClose.append(self.StandbyEnd)
				NavigationInstance.instance.record_event.append(self.getRecordEvent)
				recordings = NavigationInstance.instance.getRecordings()
				if not recordings:
					self.setPWM(0)

	def StandbyEnd(self):
			print "<SimpleFancontrol> Standby End"
			NavigationInstance.instance.record_event.remove(self.getRecordEvent)
			if self.getPWM() == 0:
				self.setPWM(config.plugins.simplefancontrols.pwmvalue.value)

	def getRecordEvent(self, recservice, event):
			recordings = len(NavigationInstance.instance.getRecordings())
			print "<SimpleFancontrol> recordings : %d , event : %d" % (recordings,event)
			if event == iRecordableService.evEnd:
				print "<SimpleFancontrol> getRecordEvent : evEnd"
				if recordings == 0:
					self.setPWM(0)
			elif event == iRecordableService.evStart:
				print "<SimpleFancontrol> getRecordEvent : evStart"
				if self.getPWM() == 0:
					self.setPWM(config.plugins.simplefancontrols.pwmvalue.value)

	def getPWM(self):
		f = open("/proc/stb/fp/fan_pwm", "r")
		value = int(f.readline().strip(), 16)
		f.close()
		print "<SimpleFancontrol> getPWM : %d "%value
		return value

	def setPWM(self, value):
		print "<SimpleFancontrol> setPWM to : %d"%value
		f = open("/proc/stb/fp/fan_pwm", "w")
		f.write("%x" % value)
		f.close()

	def appendRecordEventCallback(self):
		print "<SimpleFancontrol> appendRecordEventCallback "
		NavigationInstance.instance.record_event.append(self.getRecordEvent_onFanOFF)
		recordings = NavigationInstance.instance.getRecordings()
		if recordings:
			instandbyon.setPWM(self.default_pwm_value_onRecordings)

	def removeRecordEventCallback(self):
		print "<SimpleFancontrol> removeRecordEventCallback "
		NavigationInstance.instance.record_event.remove(self.getRecordEvent_onFanOFF)

	def getRecordEvent_onFanOFF(self, recservice, event):
		recordings = len(NavigationInstance.instance.getRecordings())
		print "<SimpleFancontrol_> recordings : %d , event : %d" % (recordings,event)
		if event == iRecordableService.evEnd:
			print "<SimpleFancontrol_> getRecordEvent : evEnd"
			if recordings == 0:
				self.setPWM(0)
		elif event == iRecordableService.evStart:
			print "<SimpleFancontrol_> getRecordEvent : evStart"
			if self.getPWM() == 0:
				self.setPWM(self.default_pwm_value_onRecordings)

instandbyon = instandbyOn()

