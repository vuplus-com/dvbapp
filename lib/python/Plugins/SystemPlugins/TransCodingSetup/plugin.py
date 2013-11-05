from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSelection, ConfigInteger
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import fileExists
from enigma import eTimer
from os import system as os_system
from __init__ import _

transcodingsetupinit = None

def getModel():
	filename = "/proc/stb/info/vumodel"
	if fileExists(filename):
		return file(filename).read().strip()
	return ""

config.plugins.transcodingsetup = ConfigSubsection()
config.plugins.transcodingsetup.transcoding = ConfigSelection(default = "enable", choices = [ ("enable", _("enable")), ("disable", _("disable"))] )
config.plugins.transcodingsetup.port = ConfigSelection(default = "8002", choices = [ ("8001", "8001"), ("8002", "8002")] )
if fileExists("/proc/stb/encoder/0/bitrate"):
	if getModel() == "solo2":
		config.plugins.transcodingsetup.bitrate = ConfigInteger(default = 400000, limits = (50000, 1000000))
	else:
		config.plugins.transcodingsetup.bitrate = ConfigInteger(default = 2000000, limits = (100000, 5000000))
if fileExists("/proc/stb/encoder/0/framerate"):
	config.plugins.transcodingsetup.framerate = ConfigSelection(default = "30000", choices = [ ("23976", _("23976")), ("24000", _("24000")), ("25000", _("25000")), ("29970", _("29970")), ("30000", _("30000")), ("50000", _("50000")), ("59940", _("59940")), ("60000", _("60000"))])

class TranscodingSetupInit:
	def __init__(self):
		self.pluginsetup = None
		#config.plugins.transcodingsetup.transcoding.addNotifier(self.setTranscoding)
		config.plugins.transcodingsetup.port.addNotifier(self.setPort)
		if hasattr(config.plugins.transcodingsetup, "bitrate"):
			config.plugins.transcodingsetup.bitrate.addNotifier(self.setBitrate)
		if hasattr(config.plugins.transcodingsetup, "framerate"):
			config.plugins.transcodingsetup.framerate.addNotifier(self.serFramerate)

	def setConfig(self, procPath, value):
		if not fileExists(procPath):
			return -1
		if isinstance(value, str):
			value = value.strip(' ').strip('\n')
		else:
			value = str(value)
		try:
			fd = open(procPath,'r')
			oldValue = fd.read().strip(' ').strip('\n')
			fd.close()
			if oldValue != value:
				print "[TranscodingSetup] set %s "%procPath, value
				fd = open(procPath,'w')
				fd.write(value)
				fd.close()
				fd = open(procPath,'r')
				setvalue = fd.read().strip(' ').strip('\n')
				fd.close()
				if value != setvalue:
					print "[TranscodingSetup] set failed. (%s > %s)" % ( value, procPath )
					return -1
				return 0
		except:
			print "setConfig exception error (%s > %s)" % ( value, procPath )
			return -1

	def setTranscoding(self, configElement):
		encoder = configElement.value
		procPath = "/proc/stb/encoder/enable"
		if self.setConfig(procPath, encoder):
			self.showMessage("Set encoder %s failed."%encoder, MessageBox.TYPE_ERROR)
		elif encoder == "enable" and config.plugins.transcodingsetup.port.value == "8001":
			msg = "OK. Encoder enable.\nPC Streaming is replaced with mobile streaming."
			self.showMessage(msg, MessageBox.TYPE_INFO)
		else:
			self.showMessage("OK. Encoder %s."%encoder, MessageBox.TYPE_INFO)
			if encoder == "disable":
				config.plugins.transcodingsetup.port.value = "8002"

	def setBitrate(self, configElement):
		bitrate = configElement.value
		procPath = "/proc/stb/encoder/0/bitrate"
		if self.setConfig(procPath, bitrate):
			fd = open(procPath,'r')
			curValue = fd.read().strip(' ').strip('\n')
			fd.close()
			if curValue.isdigit():
				config.plugins.transcodingsetup.bitrate.value = int(curValue)
				config.plugins.transcodingsetup.bitrate.save()
			self.showMessage("Set bitrate failed.", MessageBox.TYPE_ERROR)

	def serFramerate(self, configElement):
		framerate = configElement.value
		procPath = "/proc/stb/encoder/0/framerate"
		if self.setConfig(procPath, framerate):
			self.showMessage("Set framerate failed.", MessageBox.TYPE_ERROR)

	def setPort(self, configElement):
		port = configElement.value
		port2 = (port == "8001") and "8002" or "8001"

		print "[TranscodingSetup] set port ",port
		try:
			newConfigData = ""
			oldConfigData = file('/etc/inetd.conf').read()
			for L in oldConfigData.splitlines():
				try:
					if L[0] == '#':
						newConfigData += L + '\n'
						continue
				except: continue
				LL = L.split()
				if LL[5] == '/usr/bin/streamproxy':
					LL[0] = port2
				elif LL[5] == '/usr/bin/transtreamproxy':
					LL[0] = port
				newConfigData += ''.join(str(X) + " " for X in LL) + '\n'

			if newConfigData.find("transtreamproxy") == -1:
				newConfigData += port + " stream tcp nowait root /usr/bin/transtreamproxy transtreamproxy\n"
			file('/etc/inetd.conf', 'w').write(newConfigData)
		except:
			self.showMessage("Set port failed.", MessageBox.TYPE_ERROR)
			return

		self.inetdRestart()
		if config.plugins.transcodingsetup.transcoding.value == "enable" and port == "8001":
			msg = "Set port OK.\nPC Streaming is replaced with mobile streaming."
			self.showMessage(msg, MessageBox.TYPE_INFO)

	def inetdRestart(self):
		if fileExists("/etc/init.d/inetd"):
			os_system("/etc/init.d/inetd restart")
		elif fileExists("/etc/init.d/inetd.busybox"):
			os_system("/etc/init.d/inetd.busybox restart")

	def showMessage(self, msg, msgType):
		if self.pluginsetup:
			self.pluginsetup.showMessage(msg, msgType)

class TranscodingSetup(Screen,ConfigListScreen):
	skin =  """
		<screen position="center,center" size="540,320">
			<ePixmap pixmap="skin_default/buttons/red.png" position="30,10" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="200,10" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="370,10" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="30,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="200,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_yellow" render="Label" position="370,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
			<widget name="config" zPosition="2" position="20,70" size="500,120" scrollbarMode="showOnDemand" transparent="1" />
			<widget source="text" render="Label" position="30,190" size="480,130" font="Regular;18" halign="center" valign="center" />
		</screen>
		"""

	def __init__(self,session):
		Screen.__init__(self,session)
		self.setTitle(_("Transcoding Setup"))
		TEXT = _("Transcoding can be started when there is no corresponding channel recordings.")
		if getModel() == "solo2":
			TEXT += _("\nWhen transcoding, both PIP and analog video outputs are disabled.")
		else:
			TEXT += _("\nWhen transcoding, PIP is disabled.")
		self.session = session
		self["shortcuts"] = ActionMap(["ShortcutActions", "SetupActions" ],
		{
			"ok": self.keySave,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keySave,
			"yellow" : self.KeyDefault,
		}, -2)
		self.list = []
		ConfigListScreen.__init__(self, self.list,session = self.session)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText(_("Default"))
		self["text"] = StaticText(_("%s")%TEXT)
		self.createSetup()
		self.onLayoutFinish.append(self.checkEncoder)
		self.invaliedModelTimer = eTimer()
		self.invaliedModelTimer.callback.append(self.invalidmodel)
		global transcodingsetupinit
		transcodingsetupinit.pluginsetup = self
		self.onClose.append(self.onClosed)

	def onClosed(self):
		transcodingsetupinit.pluginsetup = None

	def checkEncoder(self):
		if not fileExists("/proc/stb/encoder/enable"):
			self.invaliedModelTimer.start(100,True)

	def invalidmodel(self):
		self.session.openWithCallback(self.close, MessageBox, _("This model is not support transcoding."), MessageBox.TYPE_ERROR)

	def createSetup(self):
		self.list = []
		#self.transcoding = getConfigListEntry(_("Transcoding"), config.plugins.transcodingsetup.transcoding)
		#self.list.append( self.transcoding )
		if config.plugins.transcodingsetup.transcoding.value == "enable":
			self.list.append(getConfigListEntry(_("Port"), config.plugins.transcodingsetup.port))
			if hasattr(config.plugins.transcodingsetup, "bitrate"):
				self.list.append(getConfigListEntry(_("Bitrate"), config.plugins.transcodingsetup.bitrate))
			if hasattr(config.plugins.transcodingsetup, "framerate"):
				self.list.append(getConfigListEntry(_("Framerate"), config.plugins.transcodingsetup.framerate))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def showMessage(self, msg, msgType = MessageBox.TYPE_ERROR):
		self.session.open(MessageBox, _(msg), msgType)

	def keySave(self):
		self.saveAll()
		self.close()

	def KeyDefault(self):
		config.plugins.transcodingsetup.port.value = config.plugins.transcodingsetup.port.default
		if hasattr(config.plugins.transcodingsetup, "bitrate"):
			config.plugins.transcodingsetup.bitrate.value = config.plugins.transcodingsetup.bitrate.default
		if hasattr(config.plugins.transcodingsetup, "framerate"):
			config.plugins.transcodingsetup.framerate.value = config.plugins.transcodingsetup.framerate.default
		self.createSetup()

	def resetConfig(self):
		for x in self["config"].list:
			x[1].cancel()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		#if self["config"].getCurrent() == self.transcoding:
		#	self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		#if self["config"].getCurrent() == self.transcoding:
		#	self.createSetup()

	def cancelConfirm(self, result):
		if not result:
			return
		configlist = []
		configlist.append(config.plugins.transcodingsetup.transcoding)
		configlist.append(config.plugins.transcodingsetup.port)
		configlist.append(config.plugins.transcodingsetup.bitrate)
		configlist.append(config.plugins.transcodingsetup.framerate)
		for x in configlist:
			x.cancel()
		self.close()

	def keyCancel(self):
		transcodingsetupinit.pluginsetup = None
		if self["config"].isChanged():
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.close()

def main(session, **kwargs):
	session.open(TranscodingSetup)

def Plugins(**kwargs):
	return [PluginDescriptor(name=_("TranscodingSetup"), description=_("Transcoding Setup"), where = PluginDescriptor.WHERE_PLUGINMENU, needsRestart = False, fnc=main)]

transcodingsetupinit = TranscodingSetupInit()

