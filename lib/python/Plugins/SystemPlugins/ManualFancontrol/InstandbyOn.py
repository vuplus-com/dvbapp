from Components.config import config, ConfigSubList, ConfigSubsection
import NavigationInstance
from enigma import iRecordableService
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSelection, ConfigInteger, ConfigSlider

config.plugins.simplefancontrols = ConfigSubsection()
config.plugins.simplefancontrols.standbymode = ConfigSelection(default = "on", choices = [
	("off", _("off")), ("on", _("on"))])
config.plugins.simplefancontrols.recordingmode = ConfigSelection(default = "on", choices = [
	("off", _("no")), ("on", _("yes"))])
config.plugins.simplefancontrols.pwmvalue = ConfigSlider(default = 100, increment = 5, limits = (5, 255))

class instandbyOn:
	def __init__(self):
		config.misc.standbyCounter.addNotifier(self.standbyBegin, initial_call = False)

	def standbyBegin(self, configElement):
			print "<SimpleFancontrol> config.plugins.fancontrols.standbymode.value : ", config.plugins.simplefancontrols.standbymode.value
			if config.plugins.simplefancontrols.standbymode.value == "on":
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

instandbyon = instandbyOn()

