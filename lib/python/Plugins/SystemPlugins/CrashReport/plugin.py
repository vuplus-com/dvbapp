# twisted-mail twisted-names python-compression python-mime python-email
import os

from Plugins.Plugin import PluginDescriptor

from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigText, ConfigSelection, ConfigYesNo,ConfigText
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.Pixmap import Pixmap
from Components.Label import Label

from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox

from enigma import ePoint, eConsoleAppContainer, getDesktop

from Tools.Directories import resolveFilename, SCOPE_PLUGINS

g_configfile=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/CrashReport/settings")
g_senderfile=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/CrashReport/sender.py")

g_default_activation   = ""
g_default_aftersummit  = ""
g_default_optionalinfo = False
g_default_username     = ""
g_default_useremail    = ""
g_default_machineinfo  = True

def getValue(str):
	idx = str.find("=")
	#print "---->>[%s][%d][%d]" % (str, len(str), idx)
	if idx == len(str):
		return ""
	elif idx == -1:
		return str
	return str[idx+1:]

def saveConfig(activation, aftersummit, machineinfo, optionalinfo, username="", useremail=""):
	global g_configfile
	configs = []
	configs.append("activation=%s\n"   % (activation))
	configs.append("aftersummit=%s\n"  % (aftersummit))
	configs.append("optionalinfo=%s\n" % (str(optionalinfo)))
	configs.append("username=%s\n"  % (username))
	configs.append("useremail=%s\n" % (useremail))
	configs.append("machineinfo=%s\n" % (str(machineinfo)))

	f = open(g_configfile, 'w')
	f.writelines(configs)
	f.close()
	loadConfig()

def loadConfig():
	global g_configfile
	if os.path.exists(g_configfile) == False:
		return	
	global g_default_activation
	global g_default_aftersummit
	global g_default_optionalinfo
	global g_default_username
	global g_default_useremail
	global g_default_machineinfo
	f = open(g_configfile)
	conf_list = f.readlines()
	f.close()
	print "load config : ", conf_list
	if len(conf_list) < 6:
		return
	g_default_activation  = getValue(conf_list[0].strip())
	g_default_aftersummit = getValue(conf_list[1].strip())
	if getValue(conf_list[2].strip()) == "True":
		g_default_optionalinfo = True
	g_default_username    = getValue(conf_list[3].strip())
	g_default_useremail   = getValue(conf_list[4].strip())
	if getValue(conf_list[5].strip()) == "False":
		g_default_machineinfo = False

class CrashlogReportConfiguration(Screen, ConfigListScreen):
	skin_list = {}
	skin_list["hd"] = """
		<screen name="CrashlogReportSetting" position="209,48" size="865,623" title="CrashlogReport Setting" flags="wfNoBorder" backgroundColor="transparent">	
			<ePixmap pixmap="Vu_HD/Bg_EPG_list.png" zPosition="-1" position="0,0" size="865,623" alphatest="on" />
			<ePixmap pixmap="Vu_HD/menu/ico_title_Setup.png" position="32,41" size="40,40" alphatest="blend"  transparent="1" />
			<eLabel text="CrashlogReport Setting" position="90,50" size="600,32" font="Semiboldit;32" foregroundColor="#5d5d5d" backgroundColor="#27b5b9bd" transparent="1" />
			<ePixmap pixmap="Vu_HD/icons/clock.png" position="750,55" zPosition="1" size="20,20" alphatest="blend" />
			<widget source="global.CurrentTime" render="Label" position="770,57" zPosition="1" size="50,20" font="Regular;20" foregroundColor="#1c1c1c" halign="right" backgroundColor="#27d9dee2" transparent="1">
				<convert type="ClockToText">Format:%H:%M</convert>
			</widget>
			<ePixmap pixmap="Vu_HD/buttons/red.png" position="45,98" size="25,25" alphatest="blend" />
			<ePixmap pixmap="Vu_HD/buttons/green.png" position="240,98" size="25,25" alphatest="blend" />
			<ePixmap pixmap="Vu_HD/buttons/button_off.png" position="435,98" size="25,25" alphatest="blend" />
			<ePixmap pixmap="Vu_HD/buttons/button_off.png" position="630,98" size="25,25" alphatest="blend" />
			<widget source="key_red" render="Label" position="66,97" zPosition="1" size="150,25" font="Regular;20" halign="center" valign="center" backgroundColor="darkgrey" foregroundColor="#1c1c1c" transparent="1" />
			<widget source="key_green" render="Label" position="268,97" zPosition="1" size="150,25" font="Regular;20" halign="center" valign="center" backgroundColor="darkgrey" foregroundColor="#1c1c1c" transparent="1" />
			<widget name="config" zPosition="2" position="50,130" itemHeight="36" size="750,324" scrollbarMode="showOnDemand" transparent="1" />
			<widget source="status" render="Label" position="160,525" size="540,60" zPosition="10" foregroundColor="#3c3c3c" backgroundColor="#27aeaeae" font="Regular;20" halign="center" valign="center" transparent="1"/>
			<widget name="VKeyIcon" pixmap="Vu_HD/buttons/key_text.png" position="500,350" zPosition="10" size="35,25" transparent="1" alphatest="on" />
			<widget name="HelpWindow" pixmap="Vu_HD/vkey_icon.png" position="310,400" zPosition="1" size="1,1" transparent="1" alphatest="on" />
		</screen>
		"""
	skin_list["sd"] = """
		<screen name="CrashlogReportSetting" position="center,120" size="560,420" title="CrashlogReport Settings" >
			<ePixmap pixmap="750S/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="750S/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="20,0" zPosition="1" size="115,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="160,0" zPosition="1" size="115,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" zPosition="2" position="5,50" size="550,300" scrollbarMode="showOnDemand" transparent="1" />
			<ePixmap pixmap="750S/div-h.png" position="0,360" zPosition="10" size="560,2" transparent="1" alphatest="on" />
			<widget source="status" render="Label" position="10,370" size="540,40" zPosition="10" font="Regular;20" halign="center" valign="center" backgroundColor="#25062748" transparent="1"/>
			<widget name="VKeyIcon" pixmap="750S/buttons/key_text.png" position="10,390" zPosition="10" size="35,25" transparent="1" alphatest="on" />
			<widget name="HelpWindow" pixmap="750S/vkey_icon.png" position="160,300" zPosition="1" size="1,1" transparent="1" alphatest="on" />
		</screen>
		"""

	size = getDesktop(0).size()
	skin = skin_list[size.width() > 750 and "hd" or "sd"]

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session

		self["shortcuts"] = ActionMap(["ShortcutActions", "SetupActions" ],
		{
			"ok":     self.keyOK,
			"cancel": self.keyCancel,
			"red":    self.keyCancel,
			"green":  self.keyOK,
		}, -2)
		self["VirtualKB"] = ActionMap(["VirtualKeyboardActions" ],
		{
			"showVirtualKeyboard": self.cbSetTitle,
		}, -1)

		self.list = []
		ConfigListScreen.__init__(self, self.list, session=self.session)
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Save"))
		self["status"] = StaticText(" ")
		self["VKeyIcon"] = Pixmap()
		self["HelpWindow"] = Pixmap()

		self["VKeyIcon"].hide()
		self["VirtualKB"].setEnabled(False)

		self.initGlobal()
		self.setupUI()

	def initGlobal(self):
		global g_default_activation
		global g_default_aftersummit
		global g_default_optionalinfo
		global g_default_username
		global g_default_useremail
		global g_default_machineinfo
		if g_default_activation == "":
			g_default_activation = "send_summit"
		if g_default_aftersummit == "":
			g_default_aftersummit = "rename"
		g_default_optionalinfo
		if g_default_username == "":
			g_default_username = "Vuplus User"
		if g_default_useremail == "":
			g_default_useremail = "yourmail@here.is"
		self.g_activation   = ConfigSelection(default=g_default_activation,  choices=[("send_summit", _("Enable")), ("send_disable", _("Disable"))])
		self.g_aftersummit  = ConfigSelection(default=g_default_aftersummit, choices=[("rename", _("Rename")), ("delete", _("Delete"))])
		self.g_optionalinfo = ConfigYesNo(default = g_default_optionalinfo)
		self.g_username     = ConfigText(default = g_default_username,  fixed_size = False)
		self.g_useremail    = ConfigText(default = g_default_useremail, fixed_size = False)
		self.g_machineinfo  = ConfigYesNo(default = g_default_machineinfo)

		self._activation     = getConfigListEntry(_("Activation mode"), self.g_activation)
		self._after_action   = getConfigListEntry(_("Action after summit"),      self.g_aftersummit)
		self._add_user_info  = getConfigListEntry(_("Include optional infomation"), self.g_optionalinfo)
		self._user_info_name = getConfigListEntry(_("User name"),  self.g_username)
		self._user_info_mail = getConfigListEntry(_("User Email"), self.g_useremail)
		self._machineinfo    = getConfigListEntry(_("Include settop information"), self.g_machineinfo)

		if not self.cbSelectionChanged in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.cbSelectionChanged)

	def setupUI(self):
		self.list = []
		self.list.append(self._activation)
		if self.g_activation.value == "send_summit":
			self.list.append(self._after_action)
			self.list.append(self._add_user_info)
			if self.g_optionalinfo.value:
				self.list.append(self._user_info_name)
				self.list.append(self._user_info_mail)
		self.list.append(self._machineinfo)
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def resetUI(self):
		if self["config"].getCurrent() == self._activation or self["config"].getCurrent() == self._add_user_info:
			self.setupUI()

	def cbSelectionChanged(self):
		current = self["config"].getCurrent()
		if current == self._activation:
			self.enableVKIcon(False)
		elif current == self._after_action:
			self.enableVKIcon(False)
		elif current == self._add_user_info:
			self.enableVKIcon(False)
		elif current == self._user_info_name:
			self.enableVKIcon(True)
		elif current == self._user_info_mail:
			self.enableVKIcon(True)
		elif current == self._machineinfo:
			self.enableVKIcon(False)

	def cbSetTitle(self):
		t = " "
		if self["config"].getCurrent() == self._user_info_mail:
			t = "Please enter user email:"
		if self["config"].getCurrent() == self._user_info_name:
			t = "Please enter user name:"
		self.session.openWithCallback(self.NameCallback, VirtualKeyBoard, title = (t), text = self._user_info_name.value)

	def enableVKIcon(self, mode):
		if mode:
			self["VKeyIcon"].show()
		else:
			self["VKeyIcon"].hide()
		self["VirtualKB"].setEnabled(True)

	def saveConfig(self):
		if self.g_optionalinfo.value:
			saveConfig(self.g_activation.value, self.g_aftersummit.value, self.g_machineinfo.value, self.g_optionalinfo.value, self.g_username.value, self.g_useremail.value)
		else:
			saveConfig(self.g_activation.value, self.g_aftersummit.value, self.g_machineinfo.value, self.g_optionalinfo.value)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.resetUI()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.resetUI()

	def keyOK(self):
		self.saveConfig()
		self.close()

	def keyCancel(self):
		global g_configfile
		if os.path.exists(g_configfile) == False:
			self.saveConfig()
		self.close()

def main(session, **kwargs):
	loadConfig()
	session.open(CrashlogReportConfiguration)

def opensetting(menuid, **kwargs):
	if menuid != "system":
		return []
	return [(_("Crashlog Reporting"), main, "crashlog_configure", 70)]

def generateInformation():
	from os import popen
	from Tools.DreamboxHardware import getFPVersion
	from Components.Harddisk import harddiskmanager
	from Components.NimManager import nimmanager
	from Components.About import about
	def command(cmd):
		try:
			result = popen(cmd, "r").read().strip()
			return str(result)
		except:
			pass
	information = [
		 "kernel         : %s\n"%(command("uname -a"))
		,"version        : %s (%s)\n"%(str(about.getImageVersionString()), str(about.getEnigmaVersionString()))
		,"frontprocessor : %s\n"%(str(getFPVersion()))
		,"frontend       : %s\n"%(str(nimmanager.nimList()))
		,"hdd info       : %s\n"%(str(harddiskmanager.HDDList()))
		,"network information : \n%s\n"%(command("ifconfig -a"))
		]
	f = open("/tmp/machine.info", 'w')
	f.writelines(information)
	f.close()

sender = None
def autosubmit(reason, **kwargs):
	global g_default_activation
	global g_default_aftersummit
	global g_default_username
	global g_default_useremail

	print "[CrashReport] auto submit"
	loadConfig()
	import os
	def isExistCrashlog(d='/media/hdd'):
		try:
			for f in os.listdir(d):
				if f.startswith("enigma2_crash_") and f.endswith(".log"):
					return True
		except:
			pass
	    	return False

	def cbDataAvail(ret_data):
		print ret_data
	def cbAppClosed(retval):
		if os.path.exists("/tmp/machine.info"):
			os.system("rm -f /tmp/machine.info")

	if "session" in kwargs:
		if isExistCrashlog() == False:
			print "[CrashReport] no crash-log"
			return
		session = kwargs["session"]
		if g_default_activation == "send_summit":
			global sender
			global g_senderfile
			sender = eConsoleAppContainer()
			sender.dataAvail.append(cbDataAvail)
			sender.appClosed.append(cbAppClosed)

			if g_default_username == "":
				un = "Vuplus User"
			else:
				un = g_default_username
			if g_default_useremail == "":
				um = "yourmail@here.is"
			else:
				um = g_default_useremail
			if g_default_machineinfo:
				generateInformation()

			sender.execute(_("python %s %s %s %s" % (g_senderfile, um, un.replace(" ", "_"), g_default_aftersummit)))

def Plugins(**kwargs):
	return [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART], needsRestart = False, fnc = autosubmit),
		PluginDescriptor(name=_("CrashlogReportSetting"), description=_("CrashlogReport setting"),where=PluginDescriptor.WHERE_MENU, needsRestart = False, fnc=opensetting)]

