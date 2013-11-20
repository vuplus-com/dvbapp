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

def getModel():
	filename = "/proc/stb/info/vumodel"
	if fileExists(filename):
		return file(filename).read().strip()
	return ""

def getProcValue(procPath):
	fd = open(procPath,'r')
	curValue = fd.read().strip(' ').strip('\n')
	fd.close()
#	print "[TranscodingSetup] get %s from %s" % (curValue, procPath)
	return curValue

def setProcValue(procPath, value):
	print "[TranscodingSetup] set %s to %s" % (procPath, value)
	fd = open(procPath,'w')
	fd.write(value)
	fd.close()

def checkSupportAdvanced():
	if fileExists( g_procPath["aspectratio"] ):
		return True
	return False

transcodingsetupinit = None

g_procPath = {
	"bitrate"		: 	"/proc/stb/encoder/0/bitrate",
	"framerate"		: 	"/proc/stb/encoder/0/framerate",
	"resolution" 	: 	"/proc/stb/encoder/0/display_format",
	"aspectratio" 	: 	"/proc/stb/encoder/0/aspectratio",
	"audiocodec" 	: 	"/proc/stb/encoder/0/audio_codec",
	"videocodec" 	: 	"/proc/stb/encoder/0/video_codec",
	"gopframeb" 	: 	"/proc/stb/encoder/0/gop_frameb",
	"gopframep" 	: 	"/proc/stb/encoder/0/gop_framep",
	"level" 		: 	"/proc/stb/encoder/0/level",
	"profile" 		: 	"/proc/stb/encoder/0/profile",
	"width" 		: 	"/proc/stb/encoder/0/width",
	"height" 		: 	"/proc/stb/encoder/0/height",
}

config.plugins.transcodingsetup = ConfigSubsection()
config.plugins.transcodingsetup.transcoding = ConfigSelection(default = "enable", choices = [ ("enable", _("enable")), ("disable", _("disable"))] )
config.plugins.transcodingsetup.port = ConfigSelection(default = "8002", choices = [ ("8001", "8001"), ("8002", "8002")] )

if fileExists( g_procPath["bitrate"] ):
	if getModel() == "solo2":
		config.plugins.transcodingsetup.bitrate = ConfigInteger(default = 400000, limits = (50000, 1000000))
	else:
		config.plugins.transcodingsetup.bitrate = ConfigInteger(default = 2000000, limits = (100000, 5000000))

if fileExists( g_procPath["framerate"] ):
	config.plugins.transcodingsetup.framerate = ConfigSelection(default = "30000", choices = [ ("23976", _("23976")), ("24000", _("24000")), ("25000", _("25000")), ("29970", _("29970")), ("30000", _("30000")), ("50000", _("50000")), ("59940", _("59940")), ("60000", _("60000"))] )

if checkSupportAdvanced() and (hasattr(config.plugins.transcodingsetup, "bitrate") or hasattr(config.plugins.transcodingsetup, "framerate")):
	config.plugins.transcodingsetup.automode = ConfigSelection(default = "Off", choices = [ ("On", _("On")), ("Off", _("Off")) ] )

if fileExists( g_procPath["resolution"] ):
	config.plugins.transcodingsetup.resolution = ConfigSelection(default = "480p", choices = [ ("480p", _("480p")), ("576p", _("576p")), ("720p", _("720p")), ("320x240", _("320x240")), ("160x120", _("160x120")) ] )

if fileExists( g_procPath["aspectratio"] ):
	config.plugins.transcodingsetup.aspectratio = ConfigSelection(default = "1", choices = [ ("0", _("auto")), ("1", _("4x3")), ("2", _("16x9")) ] )

if fileExists( g_procPath["audiocodec"] ):
	config.plugins.transcodingsetup.audiocodec = ConfigSelection(default = "aac", choices = [("mpg", _("mpg")), ("mp3", _("mp3")), ("aac", _("aac")), ("aac+", _("aac+")), ("aac+loas", _("aac+loas")), ("aac+adts", _("aac+adts")), ("ac3", _("ac3"))] )

if fileExists( g_procPath["videocodec"] ):
	config.plugins.transcodingsetup.videocodec = ConfigSelection(default = "h264", choices = [ ("h264", _("h264")), ("mpeg2", _("mpeg2")), ("mpeg4p2", _("mpeg4p2"))] )

if fileExists( g_procPath["gopframeb"] ):
	config.plugins.transcodingsetup.gopframeb = ConfigInteger(default = 0, limits = (0, 60))

if fileExists( g_procPath["gopframep"] ):
	config.plugins.transcodingsetup.gopframep = ConfigInteger(default = 29, limits = (0, 60))

if fileExists( g_procPath["level"] ):
	config.plugins.transcodingsetup.level = ConfigSelection(default = "3.1", choices = [("1.0", _("1.0")), ("2.0", _("2.0")),
		("2.1", _("2.1")), ("2.2", _("2.2")), ("3.0", _("3.0")), ("3.1", _("3.1")),
		("3.2", _("3.2")), ("4.0", _("4.0")), ("4.1", _("4.1")), ("4.2", _("4.2")),
		("5.0", _("5.0")), ("low", _("low")), ("main", _("main")), ("high", _("high"))] )

if fileExists( g_procPath["profile"] ):
	config.plugins.transcodingsetup.profile = ConfigSelection(default = "baseline", choices = [("baseline", _("baseline")), ("simple", _("simple")), ("main", _("main")), ("high", _("high")), ("advanced simple", _("advanced simple"))] )

class TranscodingSetupInit:
	def __init__(self):
		self.pluginsetup = None
		config.plugins.transcodingsetup.port.addNotifier(self.setPort)

		if hasattr(config.plugins.transcodingsetup, "automode"):
			if config.plugins.transcodingsetup.automode.value == "On":
				config.plugins.transcodingsetup.automode.addNotifier(self.setAutomode)

				if hasattr(config.plugins.transcodingsetup, "bitrate"):
					config.plugins.transcodingsetup.bitrate.addNotifier(self.setBitrate, False)

				if hasattr(config.plugins.transcodingsetup, "framerate"):
					config.plugins.transcodingsetup.framerate.addNotifier(self.setFramerate, False)

			else: # autoMode Off
				config.plugins.transcodingsetup.automode.addNotifier(self.setAutomode, False)
				if hasattr(config.plugins.transcodingsetup, "bitrate"):
					config.plugins.transcodingsetup.bitrate.addNotifier(self.setBitrate)

				if hasattr(config.plugins.transcodingsetup, "framerate"):
					config.plugins.transcodingsetup.framerate.addNotifier(self.setFramerate)

		if hasattr(config.plugins.transcodingsetup, "resolution"):
			config.plugins.transcodingsetup.resolution.addNotifier(self.setResolution)

		if hasattr(config.plugins.transcodingsetup, "aspectratio"):
			config.plugins.transcodingsetup.aspectratio.addNotifier(self.setAspectRatio)

		if hasattr(config.plugins.transcodingsetup, "audiocodec"):
			config.plugins.transcodingsetup.audiocodec.addNotifier(self.setAudioCodec)

		if hasattr(config.plugins.transcodingsetup, "videocodec"):
			config.plugins.transcodingsetup.videocodec.addNotifier(self.setVideoCodec)

		if hasattr(config.plugins.transcodingsetup, "gopframeb"):
			config.plugins.transcodingsetup.gopframeb.addNotifier(self.setGopFrameB)

		if hasattr(config.plugins.transcodingsetup, "gopframep"):
			config.plugins.transcodingsetup.gopframep.addNotifier(self.setGopFrameP)

		if hasattr(config.plugins.transcodingsetup, "level"):
			config.plugins.transcodingsetup.level.addNotifier(self.setLevel)

		if hasattr(config.plugins.transcodingsetup, "profile"):
			config.plugins.transcodingsetup.profile.addNotifier(self.setProfile)

	def setConfig(self, procPath, value, configName = ""):
		if not fileExists(procPath):
			return -1
		if isinstance(value, str):
			value = value.strip(' ').strip('\n')
		else:
			value = str(value)
		try:
			oldValue = getProcValue(procPath)
			if oldValue != value:
#				print "[TranscodingSetup] set %s "%procPath, value
				setProcValue(procPath, value)
				setValue = getProcValue(procPath)
				if value != setValue:
					print "[TranscodingSetup] set failed. (%s > %s)" % ( value, procPath )
					return -1
				return 0
		except:
			print "setConfig exception error (%s > %s)" % ( value, procPath )
			return -1
		return 0

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
		if port == "8001":
			msg = "Set port OK.\nPC Streaming is replaced with mobile streaming."
			self.showMessage(msg, MessageBox.TYPE_INFO)

	def setupConfig(self, configElement, configName):
#		print "[TranscodingSetup] set %s to %s" % ( configName, configElement.value )
		configValue = configElement.value
		procPath = g_procPath[configName]
		if self.setConfig(procPath, configValue):
			# set config failed, reset to current proc value
			self.getConfigFromProc(procPath, configElement)
			self.showMessage("Set %s failed." % (configName), MessageBox.TYPE_ERROR)

	def getConfigFromProc(self, procPath, configElement):
		curValue = getProcValue(procPath)
		if isinstance(configElement.value, int): # is int ?
			curValue = int(curValue)
		configElement.value = curValue
		configElement.save()

	def setAutomode(self, configElement):
		configName = "AutoMode"
#		print "[TranscodingSetup]  setAutomode, configName %s, value %s" % ( configName, configElement.value )
		if configElement.value == "On":
			autoValue = str(-1)
			if ((hasattr(config.plugins.transcodingsetup, "bitrate") and
					self.setConfig(g_procPath["bitrate"], autoValue) ) or
					(hasattr(config.plugins.transcodingsetup, "framerate") and
					self.setConfig(g_procPath["framerate"], autoValue) ) ):
				configElement.value = "Off" # set config failed, reset to previous value
				configElement.save()
				self.showMessage("Set %s failed." % (configName), MessageBox.TYPE_ERROR)
		else: # Off
			if hasattr(config.plugins.transcodingsetup, "bitrate"):
				self.setBitrate(config.plugins.transcodingsetup.bitrate)
			if hasattr(config.plugins.transcodingsetup, "framerate"):
				self.setFramerate(config.plugins.transcodingsetup.framerate)

	def setBitrate(self, configElement):
		self.setupConfig(configElement, "bitrate")

	def setFramerate(self, configElement):
		self.setupConfig(configElement, "framerate")

	def setResolution(self, configElement):
		resolution = configElement.value
		if resolution in [ "320x240", "160x120" ]:
			(width, height) = tuple(resolution.split('x'))
			self.setConfig(g_procPath["resolution"], "custom")
			self.setConfig(g_procPath["width"], width)
			self.setConfig(g_procPath["height"], height)
		else:
			self.setupConfig(configElement, "resolution")

	def setAspectRatio(self, configElement):
		self.setupConfig(configElement, "aspectratio")

	def setAudioCodec(self, configElement):
		self.setupConfig(configElement, "audiocodec")

	def setVideoCodec(self, configElement):
		self.setupConfig(configElement, "videocodec")

	def setGopFrameB(self, configElement):
		self.setupConfig(configElement, "gopframeb")

	def setGopFrameP(self, configElement):
		self.setupConfig(configElement, "gopframep")

	def setLevel(self, configElement):
		self.setupConfig(configElement, "level")

	def setProfile(self, configElement):
		self.setupConfig(configElement, "profile")

	def inetdRestart(self):
		if fileExists("/etc/init.d/inetd"):
			os_system("/etc/init.d/inetd restart")
		elif fileExists("/etc/init.d/inetd.busybox"):
			os_system("/etc/init.d/inetd.busybox restart")

	def showMessage(self, msg, msgType):
		if self.pluginsetup:
			self.pluginsetup.showMessage(msg, msgType)

class TranscodingSetup(Screen, ConfigListScreen):
	skin_expert =  """
		<screen position="center,center" size="600,450">
			<ePixmap pixmap="skin_default/buttons/red.png" position="5,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="155,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="305,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="455,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="5,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="155,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_yellow" render="Label" position="305,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_blue" render="Label" position="455,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" foregroundColor="#ffffff" transparent="1" />
			<widget name="config" zPosition="2" position="25,70" size="560,300" scrollbarMode="showOnDemand" transparent="1" />
			<widget source="description" render="Label" position="20,370" size="540,60" font="Regular;20" halign="center" valign="center" />
			<widget source="text" render="Label" position="20,430" size="540,20" font="Regular;22" halign="center" valign="center" />
		</screen>
		"""

	skin_normal =  """
		<screen position="center,center" size="540,290">
			<ePixmap pixmap="skin_default/buttons/red.png" position="30,10" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="200,10" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="370,10" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="30,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="200,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_yellow" render="Label" position="370,10" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" foregroundColor="#ffffff" transparent="1" />
			<widget name="config" zPosition="2" position="20,70" size="500,120" scrollbarMode="showOnDemand" transparent="1" />
			<widget source="description" render="Label" position="30,190" size="480,60" font="Regular;20" halign="center" valign="center" />
			<widget source="text" render="Label" position="30,250" size="480,30" font="Regular;22" halign="center" valign="center" />
		</screen>
		"""

	def __init__(self,session):
		Screen.__init__(self,session)
		self.session = session
		self.setTitle(_("Transcoding Setup"))

		if checkSupportAdvanced():
			self.skin = TranscodingSetup.skin_expert
		else:
			self.skin = TranscodingSetup.skin_normal
		if getModel() == "solo2":
			TEXT = _("Transcoding and PIP are mutually exclusive.")
		else:
			TEXT = _("2nd transcoding and PIP are mutually exclusive.")
		self["text"] = StaticText(_("%s")%TEXT)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText(_("Default"))
		self["key_blue"] = StaticText(_("Advanced"))
		self["description"] = StaticText(_("Transcoding Setup"))

		self["shortcuts"] = ActionMap(["ShortcutActions", "SetupActions" ],
		{
			"cancel"	: self.keyCancel,
			"red"		: self.keyCancel,
			"green"		: self.keySave,
			"yellow" 	: self.KeyDefault,
			"blue" 		: self.keyBlue,
		}, -2)

		self.list = []
		ConfigListScreen.__init__(self, self.list,session = self.session)
		self.setupMode = "Normal" # Normal / Advanced
		self.automode = None
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
		self.list.append(getConfigListEntry(_("Port"), config.plugins.transcodingsetup.port))

		if self.automode is None and checkSupportAdvanced() and hasattr(config.plugins.transcodingsetup, "automode"):
			self.automode = getConfigListEntry(_("Auto set Framerate / Bitrate"), config.plugins.transcodingsetup.automode)

		if self.automode is not None:
			self.list.append( self.automode )

		if not ( hasattr(config.plugins.transcodingsetup, "automode") and config.plugins.transcodingsetup.automode.value == "On" ):
			if hasattr(config.plugins.transcodingsetup, "bitrate"):
				self.list.append(getConfigListEntry(_("Bitrate"), config.plugins.transcodingsetup.bitrate))
			if hasattr(config.plugins.transcodingsetup, "framerate"):
				self.list.append(getConfigListEntry(_("Framerate"), config.plugins.transcodingsetup.framerate))

		if hasattr(config.plugins.transcodingsetup, "resolution"):
				self.list.append(getConfigListEntry(_("Resolution"), config.plugins.transcodingsetup.resolution))

		if checkSupportAdvanced() and self.setupMode != "Normal":
			if hasattr(config.plugins.transcodingsetup, "aspectratio"):
				self.list.append(getConfigListEntry(_("Aspect Ratio"), config.plugins.transcodingsetup.aspectratio))

			if hasattr(config.plugins.transcodingsetup, "audiocodec"):
				self.list.append(getConfigListEntry(_("Audio codec"), config.plugins.transcodingsetup.audiocodec))

			if hasattr(config.plugins.transcodingsetup, "videocodec"):
				self.list.append(getConfigListEntry(_("Video codec"), config.plugins.transcodingsetup.videocodec))

			if hasattr(config.plugins.transcodingsetup, "gopframeb"):
				self.list.append(getConfigListEntry(_("GOP Frame B"), config.plugins.transcodingsetup.gopframeb))

			if hasattr(config.plugins.transcodingsetup, "gopframep"):
				self.list.append(getConfigListEntry(_("GOP Frame P"), config.plugins.transcodingsetup.gopframep))

			if hasattr(config.plugins.transcodingsetup, "level"):
				self.list.append(getConfigListEntry(_("Level"), config.plugins.transcodingsetup.level))

			if hasattr(config.plugins.transcodingsetup, "profile"):
				self.list.append(getConfigListEntry(_("Profile"), config.plugins.transcodingsetup.profile))

		self["config"].list = self.list
		self["config"].l.setList(self.list)
		if not self.showDescription in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.showDescription)

	def showDescription(self):
		configName = "<%s>\n"%self["config"].getCurrent()[0]
		current = self["config"].getCurrent()[1]
		className = self["config"].getCurrent()[1].__class__.__name__
		text = ""
		if className == "ConfigSelection":
			text = configName
			for choice in current.choices.choices:
				if text == configName:	
					text += choice[1]
				else:
					text += ', ' + choice[1]
		elif className == "ConfigInteger":
			limits = current.limits[0]
			text = configName
			text += "Max : %d, Min : %d" % (limits[0], limits[1])
		self["description"].setText( _(text) )

	def showMessage(self, msg, msgType = MessageBox.TYPE_ERROR):
		self.session.open(MessageBox, _(msg), msgType)

	def keySave(self):
		self.saveAll()
		self.close()

	def KeyDefault(self):
		configs = config.plugins.transcodingsetup.dict()
		for (configName, configElement) in configs.items():
			if configName == "automode":
				continue
			configElement.value = configElement.default

		if "automode" in configs.keys():
			configElement = configs["automode"]
			configElement.value = configElement.default

		self.createSetup()

	def keyBlue(self):
		if not checkSupportAdvanced():
			return
		if self.setupMode == "Normal":
			self.setupMode = "Advanced"
			self["key_blue"].setText( _("Normal") )
		else:
			self.setupMode = "Normal"
			self["key_blue"].setText( _("Advanced") )
		self.createSetup()

	def resetConfig(self):
		for x in self["config"].list:
			x[1].cancel()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		if self.automode is not None and (self["config"].getCurrent() == self.automode) :
			self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		if self.automode is not None and (self["config"].getCurrent() == self.automode) :
			self.createSetup()

	def cancelConfirm(self, result):
		if not result:
			return

		configs = config.plugins.transcodingsetup.dict()
		for (key, configElement) in configs.items():
			if key == "automode":
				continue
			configElement.cancel()

		if "automode" in configs.keys():
			configElement = configs["automode"]
			configElement.cancel()

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

