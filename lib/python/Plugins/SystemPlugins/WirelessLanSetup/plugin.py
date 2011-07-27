from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InputBox import InputBox
from Screens.Standby import *
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.HelpMenu import HelpableScreen
from Components.Network import iNetwork
from Screens.NetworkSetup import NameserverSetup
from Components.Sources.StaticText import StaticText
from Components.Sources.Boolean import Boolean
from Components.Sources.List import List
from Components.Label import Label,MultiColorLabel
from Components.Pixmap import Pixmap,MultiPixmap
from Components.MenuList import MenuList
from Components.config import config, ConfigYesNo, ConfigIP, NoSave, ConfigText, ConfigPassword, ConfigSelection, getConfigListEntry, ConfigNothing
from Components.config import ConfigInteger, ConfigSubsection
from Components.ConfigList import ConfigListScreen
from Components.PluginComponent import plugins
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.ActionMap import ActionMap, NumberActionMap, HelpableActionMap
from Components.Console import Console
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_CURRENT_SKIN
from Tools.LoadPixmap import LoadPixmap
from Plugins.Plugin import PluginDescriptor
from enigma import eTimer, ePoint, eSize, RT_HALIGN_LEFT, eListboxPythonMultiContent, gFont
from os import path as os_path, system as os_system, unlink,listdir
from re import compile as re_compile, search as re_search
from Tools.Directories import fileExists
import time

class WlanSelection(Screen,HelpableScreen):
	skin = """
	<screen name="WlanSelection" position="209,48" size="865,623" title="Wireless Network Configuration..." flags="wfNoBorder" backgroundColor="transparent">
		<ePixmap pixmap="Vu_HD/Bg_EPG_view.png" zPosition="-1" position="0,0" size="865,623" alphatest="on" />
		<ePixmap pixmap="Vu_HD/menu/ico_title_Setup.png" position="32,41" size="40,40" alphatest="blend"  transparent="1" />
		<eLabel text="Wireless Network Adapter Selection..." position="90,50" size="600,32" font="Semiboldit;32" foregroundColor="#5d5d5d" backgroundColor="#27b5b9bd" transparent="1" />
		<ePixmap pixmap="Vu_HD/icons/clock.png" position="750,55" zPosition="1" size="20,20" alphatest="blend" />
		<widget source="global.CurrentTime" render="Label" position="770,57" zPosition="1" size="50,20" font="Regular;20" foregroundColor="#1c1c1c" backgroundColor="#27d9dee2" halign="right" transparent="1">
			<convert type="ClockToText">Format:%H:%M</convert>
		</widget>
		<ePixmap pixmap="Vu_HD/buttons/red.png" position="45,98" size="25,25" alphatest="blend" />
		<ePixmap pixmap="Vu_HD/buttons/green.png" position="240,98" size="25,25" alphatest="blend" />
		<widget source="key_red" render="Label" position="66,97" zPosition="1" size="150,25" font="Regular;20" halign="center" valign="center" backgroundColor="darkgrey" foregroundColor="#1c1c1c" transparent="1" />
		<widget source="key_green" render="Label" position="268,97" zPosition="1" size="150,25" font="Regular;20" halign="center" valign="center" backgroundColor="darkgrey" foregroundColor="#1c1c1c" transparent="1" />
		<ePixmap pixmap="Vu_HD/border_menu.png" position="120,140" zPosition="-1" size="342,358" transparent="1" alphatest="blend" />
		<widget name="menulist" position="130,150" size="322,338" transparent="1" backgroundColor="#27d9dee2" zPosition="10" scrollbarMode="showOnDemand" />
		<widget source="description" render="Label" position="500,140" size="280,360" font="Regular;19" halign="center" valign="center" backgroundColor="#c5c9cc" transparent="1"/>
	</screen>"""
	
	def __init__(self, session):
		Screen.__init__(self,session)
		HelpableScreen.__init__(self)
		self.mainmenu = self.getWlandevice()
		self["menulist"] = MenuList(self.mainmenu)
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Select"))
		self["description"] = StaticText()
		self["description"].setText(_("Select Wireless Lan module. \n" ))
		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
		{
			"ok": (self.ok, _("select interface")),
			"cancel": (self.close, _("exit network interface list")),
		})

		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
		{
			"green": (self.ok, _("select interface")),
			"red": (self.close, _("exit network interface list")),
		})

	def ok(self):
#		print len(self["menulist"].list)
		if len(self["menulist"].list) == 0:
			self.session.open(MessageBox, (_("Can not find any WirelessLan Module\n")),MessageBox.TYPE_ERROR,5 )
			return
		ifaces=self["menulist"].getCurrent()[1]
		if ifaces == None:
			pass
		else:
			self.session.open(WlanSetup,ifaces)

	def getWlandevice(self):
		list = []
		for x in iNetwork.getAdapterList():
			if x.startswith('eth'):
				continue
			description=self.getAdapterDescription(x)
			if description == "Unknown network adapter":
				list.append((description,x))
			else:
				list.append((description + " (%s)"%x,x))
		return list

	def getAdapterDescription(self, iface):
		classdir = "/sys/class/net/" + iface + "/device/"
		driverdir = "/sys/class/net/" + iface + "/device/driver/"
		if os_path.exists(classdir):
			files = listdir(classdir)
			if 'driver' in files:
				if os_path.realpath(driverdir).endswith('rtw_usb_drv'):
					return _("Realtak")+ " " + _("WLAN adapter.")
				elif os_path.realpath(driverdir).endswith('ath_pci'):
					return _("Atheros")+ " " + _("WLAN adapter.")
				elif os_path.realpath(driverdir).endswith('zd1211b'):
					return _("Zydas")+ " " + _("WLAN adapter.")
				elif os_path.realpath(driverdir).endswith('rt73'):
					return _("Ralink")+ " " + _("WLAN adapter.")
				elif os_path.realpath(driverdir).endswith('rt73usb'):
					return _("Ralink")+ " " + _("WLAN adapter.")
				else:
					return str(os_path.basename(os_path.realpath(driverdir))) + " " + _("WLAN adapter")
			else:
				return _("Unknown network adapter")
		else:
			return _("Unknown network adapter")

class WlanSetup(Screen,HelpableScreen):
	skin = """
	<screen name="WlanSetup" position="209,48" size="865,623" title="Wireless Network Configuration..." flags="wfNoBorder" backgroundColor="transparent">	
		<ePixmap pixmap="Vu_HD/Bg_EPG_view.png" zPosition="-1" position="0,0" size="865,623" alphatest="on" />
		<ePixmap pixmap="Vu_HD/menu/ico_title_Setup.png" position="32,41" size="40,40" alphatest="blend"  transparent="1" />
		<eLabel text="Wireless Network Setup Menu..." position="90,50" size="600,32" font="Semiboldit;32" foregroundColor="#5d5d5d" backgroundColor="#27b5b9bd" transparent="1" />
		<ePixmap pixmap="Vu_HD/icons/clock.png" position="750,55" zPosition="1" size="20,20" alphatest="blend" />
		<widget source="global.CurrentTime" render="Label" position="770,57" zPosition="1" size="50,20" font="Regular;20" foregroundColor="#1c1c1c" backgroundColor="#27d9dee2" halign="right" transparent="1">
			<convert type="ClockToText">Format:%H:%M</convert>
		</widget>
		<ePixmap pixmap="Vu_HD/buttons/red.png" position="45,98" size="25,25" alphatest="blend" />
		<ePixmap pixmap="Vu_HD/buttons/green.png" position="240,98" size="25,25" alphatest="blend" />
		<widget source="key_red" render="Label" position="66,97" zPosition="1" size="150,25" font="Regular;20" halign="center" valign="center" backgroundColor="darkgrey" foregroundColor="#1c1c1c" transparent="1" />
		<widget source="key_green" render="Label" position="268,97" zPosition="1" size="150,25" font="Regular;20" halign="center" valign="center" backgroundColor="darkgrey" foregroundColor="#1c1c1c" transparent="1" />
		<ePixmap pixmap="Vu_HD/border_menu.png" position="120,140" zPosition="-1" size="342,358" transparent="1" alphatest="blend" />
		<widget name="menulist" position="130,150" size="322,338" transparent="1" backgroundColor="#27d9dee2" zPosition="10" scrollbarMode="showOnDemand" />
		<widget source="description" render="Label" position="500,140" size="280,360" font="Regular;19" halign="center" valign="center" backgroundColor="#c5c9cc" transparent="1"/>
	</screen>"""
	def __init__(self, session, ifaces):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.session = session
		self.iface = ifaces
		self.restartLanRef = None
		self.LinkState = None
		self.mainmenu = self.MakeMenu()
		self["menulist"] = MenuList(self.mainmenu)
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Select"))
		self["description"] = StaticText()
		self["IFtext"] = StaticText()
		self["IF"] = StaticText()
		self["Statustext"] = StaticText()
		self["statuspic"] = MultiPixmap()
		self["statuspic"].hide()
		self.onLayoutFinish.append(self.loadDescription)
		
		self.oktext = _("Press OK on your remote control to continue.")
		
		self["WizardActions"] = HelpableActionMap(self, "WizardActions",
			{
			"up": (self.up, _("move up to previous entry")),
			"down": (self.down, _("move down to next entry")),
			"left": (self.left, _("move up to first entry")),
			"right": (self.right, _("move down to last entry")),
			})
		
		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
			{
			"cancel": (self.close, _("exit networkadapter setup menu")),
			"ok": (self.ok, _("select menu entry")),
			})

		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
			{
			"red": (self.close, _("exit networkadapter setup menu")),
			"green": (self.ok, _("select menu entry")),
			})

		self["actions"] = NumberActionMap(["WizardActions","ShortcutActions"],
		{
			"ok": self.ok,
			"back": self.close,
			"up": self.up,
			"down": self.down,
			"red": self.close,
			"left": self.left,
			"right": self.right,
		}, -2)

	def loadDescription(self):
		if self["menulist"].getCurrent()[1] == 'setting':
			self["description"].setText(_("Edit the network configuration of your STB.\n" ) + self.oktext )
		if self["menulist"].getCurrent()[1] == 'scanap':
			self["description"].setText(_("Scan your network for wireless access points and connect to them using your selected wireless device.\n" ) + self.oktext )
		if self["menulist"].getCurrent()[1] == 'dns':
			self["description"].setText(_("Edit the Nameserver configuration of your STB.\n" ) + self.oktext )
		if self["menulist"].getCurrent()[1] == 'status':
			self["description"].setText(_("Shows the state of your wireless LAN connection.\n" ) + self.oktext )
		if self["menulist"].getCurrent()[1] == 'test':
			self["description"].setText(_("Test the network configuration of your STB.\n" ) + self.oktext )
		if self["menulist"].getCurrent()[1] == 'restart':
			self["description"].setText(_("Restart your network connection and interfaces.\n" ) + self.oktext )

	def up(self):
		self["menulist"].up()
		self.loadDescription()

	def down(self):
		self["menulist"].down()
		self.loadDescription()

	def left(self):
		self["menulist"].pageUp()
		self.loadDescription()

	def right(self):
		self["menulist"].pageDown()
		self.loadDescription()

	def ok(self):
		if self["menulist"].getCurrent()[1] == 'setting':
			self.session.openWithCallback(self.checklist, WlanConfig, self.iface)
		elif self["menulist"].getCurrent()[1] == 'scanap':
			self.session.open(WlanScanAp, self.iface)
		elif self["menulist"].getCurrent()[1] == 'dns':
			self.session.open(NameserverSetup)
		elif self["menulist"].getCurrent()[1] == 'status':
			self.session.open(Wlanstatus, self.iface)
		elif self["menulist"].getCurrent()[1] == 'test':
			self.session.openWithCallback(self.checklist,NetworkAdapterTest,self.iface)
		elif self["menulist"].getCurrent()[1] == 'restart':
			self.session.openWithCallback(self.restartLan, MessageBox, (_("Are you sure you want to restart your network interfaces?\n\n") + self.oktext ) )

	def checklist(self):
		self["menulist"].setList(self.MakeMenu())

	def MakeMenu(self):
		menu = []
		menu.append((_("Adapter settings"), "setting"))
		menu.append((_("Scan Wireless AP"), "scanap"))
		menu.append((_("Nameserver settings"), "dns"))
		if iNetwork.getAdapterAttribute(self.iface, "up"):
			menu.append((_("Show WLAN Status"), "status"))
		menu.append((_("Network test"), "test"))
		menu.append((_("Restart network"), "restart"))

		return menu

	def restartLan(self, ret = False):
		if (ret == True):
			iNetwork.restartNetwork(self.restartLanDataAvail)
			self.restartLanRef = self.session.openWithCallback(self.restartfinishedCB, MessageBox, _("Please wait while your network is restarting..."), type = MessageBox.TYPE_INFO, enable_input = False)

	def restartLanDataAvail(self, data):
		if data is True:
			iNetwork.getInterfaces(self.getInterfacesDataAvail)

	def getInterfacesDataAvail(self, data):
		if data is True:
			self.restartLanRef.close(True)

	def restartfinishedCB(self,data):
		if data is True:
			self.session.open(MessageBox, _("Finished restarting your network"), type = MessageBox.TYPE_INFO, timeout = 5, default = False)

wlanconfig = ConfigSubsection()
wlanconfig.usedevice = ConfigSelection(default = "off", choices = [
	("off", _("off")), ("on", _("on"))])
wlanconfig.usedhcp = ConfigSelection(default = "off", choices = [
	("off", _("no")), ("on", _("yes"))])
wlanconfig.essid = ConfigSelection(default = "none", choices = ["none"])
wlanconfig.encrypt = ConfigSelection(default = "off", choices = [
	("off", _("no")), ("on", _("yes"))])
wlanconfig.method = ConfigSelection(default = "wep", choices = [
	("wep", _("WEP")), ("wpa", _("WPA")), ("wpa2", _("WPA2")),("wpa/wpa2", _("WPA/WPA2"))])
wlanconfig.keytype = ConfigSelection(default = "ascii", choices = [
	("ascii", _("ASCII")), ("hex", _("HEX"))])
wlanconfig.key = ConfigText(default = "XXXXXXXX", visible_width = 50, fixed_size = False)
wlanconfig.usegateway = ConfigSelection(default = "off", choices = [
	("off", _("no")), ("on", _("yes"))])
wlanconfig.ip	 = ConfigIP([0,0,0,0])
wlanconfig.netmask = ConfigIP([0,0,0,0])
wlanconfig.gateway = ConfigIP([0,0,0,0])

selectap = None	
class WlanConfig(Screen, ConfigListScreen, HelpableScreen):
	skin = """
	<screen name="WlanConfig" position="209,48" size="865,623" title="Wireless Network Configuration..." flags="wfNoBorder" backgroundColor="transparent">	
		<ePixmap pixmap="Vu_HD/Bg_EPG_view.png" zPosition="-1" position="0,0" size="865,623" alphatest="on" />
		<ePixmap pixmap="Vu_HD/menu/ico_title_Setup.png" position="32,41" size="40,40" alphatest="blend"  transparent="1" />
		<eLabel text="Wireless Network Configuration..." position="90,50" size="600,32" font="Semiboldit;32" foregroundColor="#5d5d5d" backgroundColor="#27b5b9bd" transparent="1" />
		<ePixmap pixmap="Vu_HD/icons/clock.png" position="750,55" zPosition="1" size="20,20" alphatest="blend" />
		<widget source="global.CurrentTime" render="Label" position="770,57" zPosition="1" size="50,20" font="Regular;20" foregroundColor="#1c1c1c" backgroundColor="#27d9dee2" halign="right" transparent="1">
			<convert type="ClockToText">Format:%H:%M</convert>
		</widget>
		<ePixmap pixmap="Vu_HD/buttons/red.png" position="45,98" size="25,25" alphatest="blend" />
		<ePixmap pixmap="Vu_HD/buttons/green.png" position="240,98" size="25,25" alphatest="blend" />
		<widget source="key_red" render="Label" position="66,97" zPosition="1" size="150,25" font="Regular;20" halign="center" valign="center" backgroundColor="darkgrey" foregroundColor="#1c1c1c" transparent="1" />
		<widget source="key_grean" render="Label" position="268,97" zPosition="1" size="150,25" font="Regular;20" halign="center" valign="center" backgroundColor="darkgrey" foregroundColor="#1c1c1c" transparent="1" />
		<ePixmap pixmap="Vu_HD/border_menu.png" position="120,140" zPosition="-1" size="342,358" transparent="1" alphatest="blend" />
		<widget name="config" position="130,150" size="322,338" transparent="1" backgroundColor="#27d9dee2" zPosition="10" scrollbarMode="showOnDemand" />
		<eLabel text="IP Address : " position="500,160" size="200,26" font="Semiboldit;22" foregroundColor="#5d5d5d" backgroundColor="#27b5b9bd" transparent="1" />		
		<widget source="ipaddress" render="Label" position="530,190" zPosition="1" size="150,26" font="Regular;20" halign="center" valign="center" backgroundColor="#27b5b9bd" foregroundColor="#1c1c1c" transparent="1" />		
		<eLabel text="NetMask : " position="500,220" size="200,26" font="Semiboldit;22" foregroundColor="#5d5d5d" backgroundColor="#27b5b9bd" transparent="1" />		
		<widget source="netmask" render="Label" position="530,250" zPosition="1" size="150,26" font="Regular;20" halign="center" valign="center" backgroundColor="#27b5b9bd" foregroundColor="#1c1c1c" transparent="1" />		
		<eLabel text="Gateway : " position="500,280" size="200,26" font="Semiboldit;22" foregroundColor="#5d5d5d" backgroundColor="#27b5b9bd" transparent="1" />		
		<widget source="gateway" render="Label" position="530,310" zPosition="1" size="150,26" font="Regular;20" halign="center" valign="center" backgroundColor="#27b5b9bd" foregroundColor="#1c1c1c" transparent="1" />		
	</screen>"""

	def __init__(self, session, iface):
		Screen.__init__(self,session)
		self.session = session
		self["key_red"] = StaticText(_("Close"))
		self["key_grean"] = StaticText(_("Ok"))
		self["ipaddress"] = StaticText(_("[ N/A ]"))
		self["netmask"] = StaticText(_("[ N/A ]"))		
		self["gateway"] = StaticText(_("[ N/A ]"))
		self["OkCancelActions"] = ActionMap(["ShortcutActions", "SetupActions" ],
		{
			"ok": self.saveWlanConfig,
			"green": self.saveWlanConfig,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
		}, -2)
		self.iface = iface
		self.ssid = None
		self.ap_scan = None
		self.scan_ssid = None
		self.key_mgmt = None
		self.proto = None
		self.key_type = None
		self.encryption_key = None
		self.wlanscanap = None
#		self.scanAPcount =5
		self.scanAPcount =1
		self.list = []
		ConfigListScreen.__init__(self, self.list,session = self.session)
		self.oldInterfaceState = iNetwork.getAdapterAttribute(self.iface, "up")
		self.readWpaSupplicantConf()
		self.scanAPFailedTimer = eTimer()
		self.scanAPFailedTimer.callback.append(self.scanAPFailed)
		self.scanAplistTimer = eTimer()
		self.scanAplistTimer.callback.append(self.scanApList)
		self.Console = Console()
#		self.scanAplistTimer.start(100,True)
		iNetwork.getInterfaces(self.readWlanSettings)

	def readWlanSettings(self,ret=None):
		if ret is not True:
			print "getInterfaces Fail... "
		if iNetwork.getAdapterAttribute(self.iface, "up") == True:
			default_tmp = "on"
		else:
			default_tmp = "off"
		wlanconfig.usedevice = ConfigSelection(default=default_tmp, choices = [("off", _("off")), ("on", _("on"))])

		if iNetwork.getAdapterAttribute(self.iface, "dhcp"):
			default_tmp = "on"
		else:
			default_tmp = "off"
		wlanconfig.usedhcp = ConfigSelection(default=default_tmp, choices = [("off", _("no")), ("on", _("yes"))])

		wlanconfig.ip = ConfigIP(default=iNetwork.getAdapterAttribute(self.iface, "ip")) or [0,0,0,0]

		wlanconfig.netmask = ConfigIP(default=iNetwork.getAdapterAttribute(self.iface, "netmask") or [255,0,0,0])
		if iNetwork.getAdapterAttribute(self.iface, "gateway"):
			default_tmp = "on"
		else:
			default_tmp = "off"
		wlanconfig.usegateway = ConfigSelection(default = default_tmp, choices = [("off", _("no")), ("on", _("yes"))])

		wlanconfig.gateway = ConfigIP(default=iNetwork.getAdapterAttribute(self.iface, "gateway") or [0,0,0,0])

		self["ipaddress"].setText(_(self.formatip(iNetwork.getAdapterAttribute(self.iface, "ip"))))
		self["netmask"].setText(_(self.formatip(iNetwork.getAdapterAttribute(self.iface, "netmask"))))
		self["gateway"].setText(_(self.formatip(iNetwork.getAdapterAttribute(self.iface, "gateway"))))

		if self.encryption_key is not None:
			default_tmp = "on"
		else:
			default_tmp = "off"
		wlanconfig.encrypt = ConfigSelection(default = default_tmp, choices = [("off", _("no")), ("on", _("yes"))])

		if self.key_mgmt=="NONE":
			default_tmp = "wep"
		elif self.key_mgmt == "WPA-PSK":
			if self.proto == "WPA":
				default_tmp = "wpa"
			elif self.proto == "RSN":
				default_tmp = "wpa2"
			elif self.proto in ( "WPA RSN", "WPA WPA2"):
				default_tmp = "wpa/wpa2"
			else:
				default_tmp = "wpa"
		else:
			default_tmp = "wep"

		wlanconfig.method = ConfigSelection(default = default_tmp, choices = [
			("wep", _("WEP")), ("wpa", _("WPA")), ("wpa2", _("WPA2")),("wpa/wpa2", _("WPA/WPA2"))])

		if self.key_type == 0:
			default_tmp = "hex"
		else:
			default_tmp = "ascii"
		wlanconfig.keytype = ConfigSelection(default = default_tmp, choices = [
			("ascii", _("ASCII")), ("hex", _("HEX"))])
		default_tmp = self.encryption_key or "XXXXXXXX"
		wlanconfig.key = ConfigText(default = default_tmp, visible_width = 50, fixed_size = False)
		self.scanAplistTimer.start(100,True)

	def readWpaSupplicantConf(self):
		try:
			if fileExists("/etc/wpa_supplicant.conf"):
				wpafd = open("/etc/wpa_supplicant.conf","r")
				if wpafd >0:
					data = wpafd.readline()
					while len(data) > 0:
#						print "####readWpaSupplicantConf, data : ",data
						data = data.lstrip()
						if len(data) == 0:
							data = wpafd.readline()
							continue
						if data.startswith('ssid=') and len(data) > 6:
							self.ssid = data[6:-2]
						elif data.startswith('ap_scan=') :
							self.ap_scan = data[8:]
#							print "####readWpaSupplicantConf, ap_scan : ",self.ap_scan
						elif data.startswith('scan_ssid=') and len(data) > 10:
							self.scan_ssid = data[10:-1]
						elif data.startswith('key_mgmt=') and len(data) > 9:
							self.key_mgmt = data[9:-1]
						elif data.startswith('proto=') and len(data) > 6:
							self.proto = data[6:-1]
						elif data.startswith('wep_key0="') and len(data) > 11:
							self.key_type = 1 # ascii
							self.encryption_key = data[10:-2]
						elif data.startswith('wep_key0=') and len(data) > 9:
							self.key_type = 0 # hex
							self.encryption_key = data[9:-1]
						elif data.startswith('psk="') and len(data) > 6:
							self.key_type = 1 # ascii
							self.encryption_key = data[5:-2]
						elif data.startswith('psk=') and len(data) > 4:
							self.key_type = 0 # hex
							self.encryption_key = data[4:-1]
						data = wpafd.readline()
					print self.ssid,self.scan_ssid,self.key_mgmt,self.proto,self.key_type,self.encryption_key
					wpafd.close()
				else:
					print 'read error'
			else:
				pass
		except:
			print 'failed loading wpasupplicant.conf'

	def createConfig(self):
		self.configList=[]
		self.usedeviceEntry = getConfigListEntry(_("Use Device"), wlanconfig.usedevice)
		self.usedhcpEntry = getConfigListEntry(_("Use DHCP"), wlanconfig.usedhcp)
		self.essidEntry = getConfigListEntry(_("ESSID"), wlanconfig.essid)
		self.hiddenessidEntry = getConfigListEntry(_("Input Hidden ESSID"), wlanconfig.hiddenessid)
		self.encryptEntry = getConfigListEntry(_("Encrypt"), wlanconfig.encrypt)
		self.methodEntry = getConfigListEntry(_("Method"), wlanconfig.method)
		self.keytypeEntry = getConfigListEntry(_("Key Type"), wlanconfig.keytype)
		self.keyEntry = getConfigListEntry(_("KEY"), wlanconfig.key)

		self.ipEntry = getConfigListEntry(_("IP"), wlanconfig.ip)
		self.netmaskEntry = getConfigListEntry(_("NetMask"), wlanconfig.netmask)

		self.usegatewayEntry = getConfigListEntry(_("Use Gateway"), wlanconfig.usegateway)
		self.gatewayEntry = getConfigListEntry(_("Gateway"), wlanconfig.gateway)

		self.configList.append( self.usedeviceEntry )
		if wlanconfig.usedevice.value is "on":
			self.configList.append( self.usedhcpEntry )
			if wlanconfig.usedhcp.value is "off":
				self.configList.append(self.ipEntry)
				self.configList.append(self.netmaskEntry)
				self.configList.append(self.usegatewayEntry)
				if wlanconfig.usegateway.value is "on":
					self.configList.append(self.gatewayEntry)
			self.configList.append( self.essidEntry )
#			print "#### wlanconfig.essid.value : ",wlanconfig.essid.value
			if wlanconfig.essid.value == 'Input hidden ESSID':
				self.configList.append( self.hiddenessidEntry )
			self.configList.append( self.encryptEntry )
			if wlanconfig.encrypt.value is "on" :
				self.configList.append( self.methodEntry )
				self.configList.append( self.keytypeEntry )
				self.configList.append( self.keyEntry )

		self["config"].list = self.configList
		self["config"].l.setList(self.configList)
#		if not self.selectionChanged in self["config"].onSelectionChanged:
#			self["config"].onSelectionChanged.append(self.selectionChanged)

	def scanApList(self):
		self.apList = []
		self.configurationmsg = self.session.open(MessageBox, _("Please wait for scanning AP..."), type = MessageBox.TYPE_INFO, enable_input = False)
		cmd = "ifconfig "+self.iface+" up"
		print 'cmd ',cmd
		os_system(cmd)
		self.wlanscanap = Console()
		cmd = "iwlist "+self.iface+" scan"
		print 'cmd ',cmd
		self.wlanscanap.ePopen(cmd, self.apListFinnished,self.apListParse)

	def apListFinnished(self, result, retval,extra_args):
		(callback) = extra_args
		if self.wlanscanap is not None:
			if retval == 0:
				self.wlanscanap = None
				content = result.splitlines()
				first = content[0].split()
				completed = False
				for x in first:
					if x == 'completed':
						completed = True
				if completed == True:
					callback(result)
				else:
					callback(0)
			else:
				callback(0)

	def apListParse(self,data):
		global selectap
		if data == 0:
			if self.scanAPcount >0:
				self.scanAPcount -=1
				self.configurationmsg.close(True)
				time.sleep(3)
				self.scanAplistTimer.start(500,True)
				return
			else:
				self.configurationmsg.close(True)
				self.scanAPFailedTimer.start(500,True)
				return
		else:
			self.apList = []
#			self.scanAPcount =5
			self.scanAPcount =0
			list = data.splitlines()
			for x in list:
				xx = x.lstrip()
				if xx.startswith('ESSID:') and len(xx)>8 and xx[7:-1]not in self.apList:
					self.apList.append(xx[7:-1])
			self.apList.append('Input hidden ESSID')
#			print "###### selectap : ",selectap
			if selectap is not None and selectap in self.apList:
				wlanconfig.essid = ConfigSelection(default=selectap,choices = self.apList)
			elif self.ap_scan is not None and self.ap_scan.strip() == '2':
				wlanconfig.essid = ConfigSelection(default='Input hidden ESSID',choices = self.apList)
			elif self.ssid is not None and self.ssid in self.apList:
				wlanconfig.essid = ConfigSelection(default=self.ssid,choices = self.apList)
			else:
				wlanconfig.essid = ConfigSelection(choices = self.apList)
			if self.ssid is not None:
				wlanconfig.hiddenessid = ConfigText(default = self.ssid, visible_width = 50, fixed_size = False)
			else:
				wlanconfig.hiddenessid = ConfigText(default = "<Input ESSID>", visible_width = 50, fixed_size = False)
		self.configurationmsg.close(True)
		self.createConfig()

	def scanAPFailed(self):
		self.session.openWithCallback(self.keyCancel ,MessageBox, _("Scan AP Failed"), MessageBox.TYPE_ERROR,10)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()

	def newConfig(self):
		if self["config"].getCurrent() == self.usedeviceEntry or self["config"].getCurrent() == self.encryptEntry \
			or self["config"].getCurrent() == self.usedhcpEntry or self["config"].getCurrent() == self.usegatewayEntry \
			or self["config"].getCurrent() == self.essidEntry:
			self.createConfig()

	def saveWlanConfig(self):
		if self["config"].getCurrent() == self.keyEntry or self["config"].getCurrent() == self.hiddenessidEntry :
			self["config"].getCurrent()[1].onDeselect(self.session)
		if self["config"].isChanged():
			self.session.openWithCallback(self.checkNetworkShares, MessageBox, (_("Are you sure you want to restart your network interfaces?\n") ) )
		else:
			self.session.openWithCallback(self.checkNetworkShares, MessageBox, (_("Network configuration is not changed....\n\nAre you sure you want to restart your network interfaces?\n") ) )

	def checkNetworkShares(self,ret = False):
		if ret == False:
			if self["config"].getCurrent() == self.keyEntry or self["config"].getCurrent() == self.hiddenessidEntry :
				self["config"].getCurrent()[1].onSelect(self.session)
			return
		if not self.Console:
			self.Console = Console()
		cmd = "cat /proc/mounts"
		self.Console.ePopen(cmd, self.checkSharesFinished, self.confirmAnotherIfaces)

	def checkSharesFinished(self, result, retval, extra_args):
		callback = extra_args
		print "checkMountsFinished : result : \n",result
		networks = ['nfs','smbfs','ncp','coda']
		for line in result.splitlines():
			split = line.strip().split(' ',3)
			if split[2] in networks:
				self.session.open(MessageBox, ("NOT deconfiguring network interfaces :\n network shares still mounted\n"), type = MessageBox.TYPE_ERROR, timeout = 10)
				callback(False)
				if self["config"].getCurrent() == self.keyEntry or self["config"].getCurrent() == self.hiddenessidEntry :
					self["config"].getCurrent()[1].onSelect(self.session)
				return
		callback(True)

	def confirmAnotherIfaces(self, ret = False):
		if ret == False:
			return
		else:
			num_configured_if = len(iNetwork.getConfiguredAdapters())
			if num_configured_if >= 1:
				if num_configured_if == 1 and self.iface in iNetwork.getConfiguredAdapters():
					self.writeWlanConfig(False)
				else:
					self.session.openWithCallback(self.writeWlanConfig, MessageBox, _("A second configured interface has been found.\n\nDo you want to disable the second network interface?"), default = True)
			else:
				self.writeWlanConfig(False)

	def writeWlanConfig(self,ret = False):
		if ret == True:
			configuredInterfaces = iNetwork.getConfiguredAdapters()
			for interface in configuredInterfaces:
				if interface == self.iface:
					continue
				iNetwork.setAdapterAttribute(interface, "up", False)
				iNetwork.deactivateInterface(interface)
		ret=self.writeWpasupplicantConf()
		if ret == -1:
			self.session.open(MessageBox, _("wpa_supplicant.conf open error."), type = MessageBox.TYPE_ERROR, timeout = 10)
			return
		elif ret == -2:
			self.session.open(MessageBox, _("hidden ESSID empty"), type = MessageBox.TYPE_ERROR, timeout = 10)
			return

		if wlanconfig.usedevice.value=="on":
			iNetwork.setAdapterAttribute(self.iface, "up", True)
			if wlanconfig.usedhcp.value =="on":
				iNetwork.setAdapterAttribute(self.iface, "dhcp", True)
			else:
				iNetwork.setAdapterAttribute(self.iface, "dhcp", False)
				iNetwork.setAdapterAttribute(self.iface, "ip", wlanconfig.ip.value)
				iNetwork.setAdapterAttribute(self.iface, "netmask", wlanconfig.netmask.value)
				if wlanconfig.usegateway.value == "on":
					iNetwork.setAdapterAttribute(self.iface, "gateway", wlanconfig.gateway.value)
		else:
			iNetwork.setAdapterAttribute(self.iface, "up", False)
			iNetwork.deactivateInterface(self.iface)
		contents = "\tpre-up wpa_supplicant -i"+self.iface+" -c/etc/wpa_supplicant.conf -B -D"+iNetwork.detectWlanModule(self.iface)+"\n"
		contents += "\tpost-down wpa_cli terminate\n\n"
		iNetwork.setAdapterAttribute(self.iface, "configStrings", contents)
		iNetwork.writeNetworkConfig()
		iNetwork.restartNetwork(self.updateCurrentInterfaces)
		self.configurationmsg = None
		self.configurationmsg = self.session.openWithCallback(self.configFinished, MessageBox, _("Please wait for activation of your network configuration..."), type = MessageBox.TYPE_INFO, enable_input = False)

	def writeWpasupplicantConf(self):
		wpafd = open("/etc/wpa_supplicant.conf","w")
		if wpafd > 0:
			contents = "#WPA Supplicant Configuration by STB\n"
			contents += "ctrl_interface=/var/run/wpa_supplicant\n"
			contents += "eapol_version=1\n"
			contents += "fast_reauth=1\n"

			if wlanconfig.essid.value == 'Input hidden ESSID':
				contents += "ap_scan=2\n"
			else :
				contents += "ap_scan=1\n"
			contents += "network={\n"
			if wlanconfig.essid.value == 'Input hidden ESSID':
				if len(wlanconfig.hiddenessid.value) == 0:
					wpafd.close()
					return -2
				contents += "\tssid=\""+wlanconfig.hiddenessid.value+"\"\n"
			else :
				contents += "\tssid=\""+wlanconfig.essid.value+"\"\n"
			contents += "\tscan_ssid=0\n"
			if wlanconfig.encrypt.value == "on":
				if wlanconfig.method.value =="wep":
					contents += "\tkey_mgmt=NONE\n"
					contents += "\twep_key0="
				elif wlanconfig.method.value == "wpa":
					contents += "\tkey_mgmt=WPA-PSK\n"
					contents += "\tproto=WPA\n"
					contents += "\tpairwise=CCMP TKIP\n"
					contents += "\tgroup=CCMP TKIP\n"
					contents += "\tpsk="
				elif wlanconfig.method.value == "wpa2":
					contents += "\tkey_mgmt=WPA-PSK\n"
					contents += "\tproto=RSN\n"
					contents += "\tpairwise=CCMP TKIP\n"
					contents += "\tgroup=CCMP TKIP\n"
					contents += "\tpsk="
				else:
					contents += "\tkey_mgmt=WPA-PSK\n"
					contents += "\tproto=WPA RSN\n"
					contents += "\tpairwise=CCMP TKIP\n"
					contents += "\tgroup=CCMP TKIP\n"
					contents += "\tpsk="
				if wlanconfig.keytype.value == "ascii":
					contents += "\""+wlanconfig.key.value+"\"\n"
				else:
					contents += wlanconfig.key.value+"\n"
			else:
				contents += "\tkey_mgmt=NONE\n"
			contents += "}\n"
			print "content = \n"+contents
			wpafd.write(contents)
			wpafd.close()
			return 0
		else :
			self.session.open(MessageBox, _("wpa_supplicant.conf open error."), type = MessageBox.TYPE_ERROR, timeout = 10)
			return -1
	def updateCurrentInterfaces(self,ret):
		if ret is True:
			iNetwork.getInterfaces(self.configurationMsgClose)

	def configurationMsgClose(self,ret):
		if ret is True and self.configurationmsg is not None:
			self.configurationmsg.close(True)

	def configFinished(self,data):
		global selectap
		if data is True:
			self.session.openWithCallback(self.configFinishedCB, MessageBox, _("Your network configuration has been activated."), type = MessageBox.TYPE_INFO, timeout = 10)
			selectap = wlanconfig.essid.value

	def configFinishedCB(self,data):
		if data is not None:
			if data is True:
				self.close()
	
	def formatip(self, iplist):
		list = []
		list = iplist
#		print "iplist : ",iplist
		try:
			if len(iplist) == 4:
				result = str(iplist[0])+"."+str(iplist[1])+"."+str(iplist[2])+"."+str(iplist[3])
			else:
				result ="0.0.0.0"
#			print "result : ",result
			return result
		except:
			return "[N/A]"
			
	def keyCancelConfirm(self, result):
		if not result:
			return
		if self.oldInterfaceState is False:
			iNetwork.setAdapterAttribute(self.iface, "up", False)
			iNetwork.deactivateInterface(self.iface,self.keyCancelCB)
		else:
			self.close()

	def keyCancel(self,yesno = True):
		if self["config"].isChanged():
			self.session.openWithCallback(self.keyCancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.keyCancelConfirm(True)

	def keyCancelCB(self,data):
		if data is not None:
			if data is True:
				self.close()

#	def selectionChanged(self):
#		current = self["config"].getCurrent()
#		print current

class WlanScanAp(Screen,HelpableScreen):
	skin = """
	<screen name="WlanScanAp" position="209,48" size="865,623" title="Wireless Network Configuration..." flags="wfNoBorder" backgroundColor="transparent">
		<ePixmap pixmap="Vu_HD/Bg_EPG_view.png" zPosition="-1" position="0,0" size="865,623" alphatest="on" />
		<ePixmap pixmap="Vu_HD/menu/ico_title_Setup.png" position="32,41" size="40,40" alphatest="blend"  transparent="1" />
		<eLabel text="Wireless Network AP Scan..." position="90,50" size="600,32" font="Semiboldit;32" foregroundColor="#5d5d5d" backgroundColor="#27b5b9bd" transparent="1" />
		<ePixmap pixmap="Vu_HD/icons/clock.png" position="750,55" zPosition="1" size="20,20" alphatest="blend" />
		<widget source="global.CurrentTime" render="Label" position="770,57" zPosition="1" size="50,20" font="Regular;20" foregroundColor="#1c1c1c" backgroundColor="#27d9dee2" halign="right" transparent="1">
			<convert type="ClockToText">Format:%H:%M</convert>
		</widget>
		<ePixmap pixmap="Vu_HD/buttons/red.png" position="45,98" size="25,25" alphatest="blend" />
		<ePixmap pixmap="Vu_HD/buttons/green.png" position="240,98" size="25,25" alphatest="blend" />
		<ePixmap pixmap="Vu_HD/buttons/blue.png" position="630,98" size="25,25" alphatest="blend" />
		<widget source="key_red" render="Label" position="66,97" zPosition="1" size="150,25" font="Regular;20" halign="center" valign="center" backgroundColor="darkgrey" foregroundColor="#1c1c1c" transparent="1" />
		<widget source="key_green" render="Label" position="268,97" zPosition="1" size="150,25" font="Regular;20" halign="center" valign="center" backgroundColor="darkgrey" foregroundColor="#1c1c1c" transparent="1" />
		<widget source="key_blue" render="Label" position="665,97" zPosition="1" size="150,25" font="Regular;20" halign="center" valign="center" backgroundColor="darkgrey" foregroundColor="#1c1c1c" transparent="1" />
		<ePixmap pixmap="Vu_HD/border_menu.png" position="120,140" zPosition="-1" size="342,358" transparent="1" alphatest="blend" />
		<widget name="menulist" position="130,150" size="322,338" transparent="1" backgroundColor="#27d9dee2" zPosition="10" scrollbarMode="showOnDemand" />
		<widget source="Address" render="Label" position="490,220" zPosition="1" size="300,30" font="Regular;20" halign="center" valign="center" backgroundColor="#27b5b9bd" foregroundColor="#1c1c1c" transparent="1" />		
		<widget source="ESSID" render="Label" position="490,250" zPosition="1" size="300,30" font="Regular;20" halign="center" valign="center" backgroundColor="#27b5b9bd" foregroundColor="#1c1c1c" transparent="1" />
		<widget source="Protocol" render="Label" position="490,280" zPosition="1" size="300,30" font="Regular;20" halign="center" valign="center" backgroundColor="#27b5b9bd" foregroundColor="#1c1c1c" transparent="1" />	
		<widget source="Frequency" render="Label" position="490,310" zPosition="1" size="300,30" font="Regular;20" halign="center" valign="center" backgroundColor="#27b5b9bd" foregroundColor="#1c1c1c" transparent="1" />	
		<widget source="Encryption key" render="Label" position="490,340" zPosition="1" size="300,30" font="Regular;20" halign="center" valign="center" backgroundColor="#27b5b9bd" foregroundColor="#1c1c1c" transparent="1" />	
		<widget source="BitRate" render="Label" position="490,370" zPosition="1" size="300,60" font="Regular;20" halign="center" valign="center" backgroundColor="#27b5b9bd" foregroundColor="#1c1c1c" transparent="1" />
	</screen>"""

	def __init__(self, session, iface):
		Screen.__init__(self,session)
		HelpableScreen.__init__(self)
		self.session = session
		self.iface = iface
		self.wlanscanap = None
#		self.scanAPcount = 5
		self.scanAPcount = 1
		self.apList = {}
		self.SetApList = []

		self["WizardActions"] = HelpableActionMap(self, "WizardActions",
		{
			"up": (self.up, _("move up to previous entry")),
			"down": (self.down, _("move down to next entry")),
			"left": (self.left, _("move up to first entry")),
			"right": (self.right, _("move down to last entry")),
		})

		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
		{
			"cancel": (self.close, _("exit")),
			"ok": (self.ok, "select AP"),
		})

		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
		{
			"red": (self.close, _("exit")),
			"green": (self.ok, "select AP"),
			"blue": (self.startWlanConfig, "Edit Wireless settings"),
		})

		self["actions"] = NumberActionMap(["WizardActions","ShortcutActions"],
		{
			"ok": self.ok,
			"back": self.close,
			"up": self.up,
			"down": self.down,
			"red": self.close,
			"left": self.left,
			"right": self.right,
		}, -2)

		self["menulist"] = MenuList(self.SetApList)
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Select"))
		self["key_blue"] = StaticText(_("EditSetting"))
		self["Address"] = StaticText(_("Scanning AP List.."))
		self["ESSID"] = StaticText(_("Wait a moment"))
		self["Protocol"] = StaticText(" ")
		self["Frequency"] = StaticText(" ")
		self["Encryption key"] = StaticText(" ")
		self["BitRate"] = StaticText(" ")
		self.scanAPFailedTimer = eTimer()
		self.scanAPFailedTimer.callback.append(self.scanAPFailed)
		self.scanAplistTimer = eTimer()
		self.scanAplistTimer.callback.append(self.scanApList)
		self.scanAplistTimer.start(100,True)
		
	def left(self):
		self["menulist"].pageUp()
		self.displayApInfo()
	
	def right(self):
		self["menulist"].pageDown()
		self.displayApInfo()

	def up(self):
		self["menulist"].up()
		self.displayApInfo()
		
	def down(self):
		self["menulist"].down()
		self.displayApInfo()

	def ok(self):
		global selectap
		selectAp=self["menulist"].getCurrent()[0]
		selectap = selectAp
		self.close()

	def startWlanConfig(self):
		global selectap
		selectAp=self["menulist"].getCurrent()[0]
		selectap = selectAp
		self.session.open(WlanConfig,self.iface)
#		self.close()

	def scanApList(self):
	#	print "self.scanAPcount : ",self.scanAPcount
		self.apList = {}
		self.SetApList = []
		self.configurationmsg = self.session.open(MessageBox, _("Please wait for scanning AP..."), type = MessageBox.TYPE_INFO, enable_input = False)
		os_system('ifconfig '+self.iface+" up")
		self.wlanscanap = Console()
		cmd = "iwlist "+self.iface+" scan"
		print cmd
		self.wlanscanap.ePopen(cmd, self.iwlistfinnished,self.APListParse)

	def iwlistfinnished(self, result, retval,extra_args):
#		print "iwlistfinnished"
		(statecallback) = extra_args
		if self.wlanscanap is not None:
#			print "retval = ",retval
			if retval == 0:
				self.wlanscanap = None
				content = result.splitlines()
				first = content[0].split()
				completed = False
				for x in first:
					if x == 'completed':
						completed = True
				if completed == True:
					statecallback(result)
				else:
					statecallback(0)
			else:
				statecallback(0)

	def APListParse(self,data):
		if data == 0:
			if self.scanAPcount >0:
				self.scanAPcount -=1
				self.configurationmsg.close(True)
				time.sleep(3)
				self.scanAplistTimer.start(500,True)
				return
			else:
				self.configurationmsg.close(True)
				self.scanAPFailedTimer.start(500,True)
				return
		else:
#			print data
			self.apList = {}
#			self.scanAPcount =5
			self.scanAPcount =0
			list = data.splitlines()
			for line in list:
#				print "line : ",line
				if line.strip().startswith("Cell"): #  Cell 01 - Address: 00:26:66:5C:EF:24
					parts = line.strip().split(" ")
					current_ap_id = int(parts[1])
					self.apList[current_ap_id]={}
					self.apList[current_ap_id]["Address"]=parts[4]
				elif line.strip().startswith("ESSID"):
					self.apList[current_ap_id]["ESSID"]=line.strip()[6:].strip('"')
					self.SetApList.append( (self.apList[current_ap_id]["ESSID"],current_ap_id) )
				elif line.strip().startswith("Protocol"):
					self.apList[current_ap_id]["Protocol"]=line.strip()[9:]
				elif line.strip().startswith("Frequency"):
					self.apList[current_ap_id]["Frequency"]=line.strip()[10:]
				elif line.strip().startswith("Encryption key"):
					self.apList[current_ap_id]["Encryption key"]=line.strip()[15:]
				elif line.strip().startswith("Bit Rates"):
					self.apList[current_ap_id]["BitRate"]=line.strip()[10:]
			print self.apList
			print len(self.apList)
		self.configurationmsg.close(True)
		self.displayApInfo()

	def scanAPFailed(self):
		self.session.openWithCallback(self.ScanAPclose,MessageBox, _("Scan AP Failed"), MessageBox.TYPE_ERROR,10)

	def displayApInfo(self):
		if len(self.apList) >0:
			self["menulist"].setList(self.SetApList)
			index = self["menulist"].getCurrent()[1]
			for key in ["Address", "ESSID", "Protocol", "Frequency", "Encryption key", "BitRate"]:
				if self.apList[index].has_key(key):
					self[key].setText((key+":  "+self.apList[index][key]))
				else:
					self[key].setText(("None"))
		else:
			self.session.openWithCallback(self.ScanAPclose, MessageBox, _("No AP detected."), type = MessageBox.TYPE_INFO, timeout = 10)

	def ScanAPclose(self,data):
		self.close()

class NetworkAdapterTest(Screen):
	def __init__(self, session,iface):
		Screen.__init__(self, session)
		self.iface = iface
		self.oldInterfaceState = iNetwork.getAdapterAttribute(self.iface, "up")
		self.setLabels()
		self.onClose.append(self.cleanup)
		self.onHide.append(self.cleanup)
		
		self["updown_actions"] = NumberActionMap(["WizardActions","ShortcutActions"],
		{
			"ok": self.KeyOK,
			"blue": self.KeyOK,
			"up": lambda: self.updownhandler('up'),
			"down": lambda: self.updownhandler('down'),
		
		}, -2)
		
		self["shortcuts"] = ActionMap(["ShortcutActions","WizardActions"],
		{
			"red": self.cancel,
			"back": self.cancel,
		}, -2)
		self["infoshortcuts"] = ActionMap(["ShortcutActions","WizardActions"],
		{
			"red": self.closeInfo,
			"back": self.closeInfo,
		}, -2)
		self["shortcutsgreen"] = ActionMap(["ShortcutActions"],
		{
			"green": self.KeyGreen,
		}, -2)
		self["shortcutsgreen_restart"] = ActionMap(["ShortcutActions"],
		{
			"green": self.KeyGreenRestart,
		}, -2)
		self["shortcutsyellow"] = ActionMap(["ShortcutActions"],
		{
			"yellow": self.KeyYellow,
		}, -2)
		
		self["shortcutsgreen_restart"].setEnabled(False)
		self["updown_actions"].setEnabled(False)
		self["infoshortcuts"].setEnabled(False)
		self.onClose.append(self.delTimer)	
		self.onLayoutFinish.append(self.layoutFinished)
		self.steptimer = False
		self.nextstep = 0
		self.activebutton = 0
		self.nextStepTimer = eTimer()
		self.nextStepTimer.callback.append(self.nextStepTimerFire)

	def cancel(self):
		if self.oldInterfaceState is False:
			iNetwork.setAdapterAttribute(self.iface, "up", self.oldInterfaceState)
			iNetwork.deactivateInterface(self.iface)
		self.close()

	def closeInfo(self):
		self["shortcuts"].setEnabled(True)		
		self["infoshortcuts"].setEnabled(False)
		self["InfoText"].hide()
		self["InfoTextBorder"].hide()
		self["key_red"].setText(_("Close"))

	def delTimer(self):
		del self.steptimer
		del self.nextStepTimer

	def nextStepTimerFire(self):
		self.nextStepTimer.stop()
		self.steptimer = False
		self.runTest()

	def updownhandler(self,direction):
		if direction == 'up':
			if self.activebutton >=2:
				self.activebutton -= 1
			else:
				self.activebutton = 6
			self.setActiveButton(self.activebutton)
		if direction == 'down':
			if self.activebutton <=5:
				self.activebutton += 1
			else:
				self.activebutton = 1
			self.setActiveButton(self.activebutton)

	def setActiveButton(self,button):
		if button == 1:
			self["EditSettingsButton"].setPixmapNum(0)
			self["EditSettings_Text"].setForegroundColorNum(0)
			self["NetworkInfo"].setPixmapNum(0)
			self["NetworkInfo_Text"].setForegroundColorNum(1)
			self["AdapterInfo"].setPixmapNum(1) 		  # active
			self["AdapterInfo_Text"].setForegroundColorNum(2) # active
		if button == 2:
			self["AdapterInfo_Text"].setForegroundColorNum(1)
			self["AdapterInfo"].setPixmapNum(0)
			self["DhcpInfo"].setPixmapNum(0)
			self["DhcpInfo_Text"].setForegroundColorNum(1)
			self["NetworkInfo"].setPixmapNum(1) 		  # active
			self["NetworkInfo_Text"].setForegroundColorNum(2) # active
		if button == 3:
			self["NetworkInfo"].setPixmapNum(0)
			self["NetworkInfo_Text"].setForegroundColorNum(1)
			self["IPInfo"].setPixmapNum(0)
			self["IPInfo_Text"].setForegroundColorNum(1)
			self["DhcpInfo"].setPixmapNum(1) 		  # active
			self["DhcpInfo_Text"].setForegroundColorNum(2) 	  # active
		if button == 4:
			self["DhcpInfo"].setPixmapNum(0)
			self["DhcpInfo_Text"].setForegroundColorNum(1)
			self["DNSInfo"].setPixmapNum(0)
			self["DNSInfo_Text"].setForegroundColorNum(1)
			self["IPInfo"].setPixmapNum(1)			# active
			self["IPInfo_Text"].setForegroundColorNum(2)	# active		
		if button == 5:
			self["IPInfo"].setPixmapNum(0)
			self["IPInfo_Text"].setForegroundColorNum(1)
			self["EditSettingsButton"].setPixmapNum(0)
			self["EditSettings_Text"].setForegroundColorNum(0)
			self["DNSInfo"].setPixmapNum(1)			# active
			self["DNSInfo_Text"].setForegroundColorNum(2)	# active
		if button == 6:
			self["DNSInfo"].setPixmapNum(0)
			self["DNSInfo_Text"].setForegroundColorNum(1)
			self["EditSettingsButton"].setPixmapNum(1) 	   # active
			self["EditSettings_Text"].setForegroundColorNum(2) # active
			self["AdapterInfo"].setPixmapNum(0)
			self["AdapterInfo_Text"].setForegroundColorNum(1)
			
	def runTest(self):
		next = self.nextstep
		if next == 0:
			self.doStep1()
		elif next == 1:
			self.doStep2()
		elif next == 2:
			self.doStep3()
		elif next == 3:
			self.doStep4()
		elif next == 4:
			self.doStep5()
		elif next == 5:
			self.doStep6()
		self.nextstep += 1

	def doStep1(self):
		self.steptimer = True
		self.nextStepTimer.start(3000)
		self["key_yellow"].setText(_("Stop test"))

	def doStep2(self):
		self["Adapter"].setText(iNetwork.getFriendlyAdapterName(self.iface))
		self["Adapter"].setForegroundColorNum(2)
		self["Adaptertext"].setForegroundColorNum(1)
		self["AdapterInfo_Text"].setForegroundColorNum(1)
		self["AdapterInfo_OK"].show()
		self.steptimer = True
		self.nextStepTimer.start(3000)

	def doStep3(self):
		self["Networktext"].setForegroundColorNum(1)
		self["Network"].setText(_("Please wait..."))
		self.AccessPointInfo(self.iface)
		self["NetworkInfo_Text"].setForegroundColorNum(1)
		self.steptimer = True
		self.nextStepTimer.start(3000)

	def doStep4(self):
		self["Dhcptext"].setForegroundColorNum(1)
		if iNetwork.getAdapterAttribute(self.iface, 'dhcp') is True:
			self["Dhcp"].setForegroundColorNum(2)
			self["Dhcp"].setText(_("enabled"))
			self["DhcpInfo_Check"].setPixmapNum(0)
		else:
			self["Dhcp"].setForegroundColorNum(1)
			self["Dhcp"].setText(_("disabled"))
			self["DhcpInfo_Check"].setPixmapNum(1)
		self["DhcpInfo_Check"].show()
		self["DhcpInfo_Text"].setForegroundColorNum(1)
		self.steptimer = True
		self.nextStepTimer.start(3000)

	def doStep5(self):
		self["IPtext"].setForegroundColorNum(1)
		self["IP"].setText(_("Please wait..."))
		iNetwork.checkNetworkState(self.NetworkStatedataAvail)

	def doStep6(self):
		self.steptimer = False
		self.nextStepTimer.stop()
		self["DNStext"].setForegroundColorNum(1)
		self["DNS"].setText(_("Please wait..."))
		iNetwork.checkDNSLookup(self.DNSLookupdataAvail)

	def KeyGreen(self):
		self["shortcutsgreen"].setEnabled(False)
		self["shortcutsyellow"].setEnabled(True)
		self["updown_actions"].setEnabled(False)
		self["key_yellow"].setText("")
		self["key_green"].setText("")
		self.steptimer = True
		self.nextStepTimer.start(1000)

	def KeyGreenRestart(self):
		self.nextstep = 0
		self.layoutFinished()
		self["Adapter"].setText((""))
		self["Network"].setText((""))
		self["Dhcp"].setText((""))
		self["IP"].setText((""))
		self["DNS"].setText((""))
		self["AdapterInfo_Text"].setForegroundColorNum(0)
		self["NetworkInfo_Text"].setForegroundColorNum(0)
		self["DhcpInfo_Text"].setForegroundColorNum(0)
		self["IPInfo_Text"].setForegroundColorNum(0)
		self["DNSInfo_Text"].setForegroundColorNum(0)
		self["shortcutsgreen_restart"].setEnabled(False)
		self["shortcutsgreen"].setEnabled(False)
		self["shortcutsyellow"].setEnabled(True)
		self["updown_actions"].setEnabled(False)
		self["key_yellow"].setText("")
		self["key_green"].setText("")
		self.steptimer = True
		self.nextStepTimer.start(1000)

	def KeyOK(self):
		self["infoshortcuts"].setEnabled(True)
		self["shortcuts"].setEnabled(False)
		if self.activebutton == 1: # Adapter Check
			self["InfoText"].setText(_("This test detects your configured Wireless LAN-Adapter."))
			self["InfoTextBorder"].show()
			self["InfoText"].show()
			self["key_red"].setText(_("Back"))
		if self.activebutton == 2: #LAN Check
			self["InfoText"].setText(_("This test checks whether a network cable is connected to your Wireless LAN-Adapter."))
			self["InfoTextBorder"].show()
			self["InfoText"].show()
			self["key_red"].setText(_("Back"))
		if self.activebutton == 3: #DHCP Check
			self["InfoText"].setText(_("This test checks whether your Wireless LAN Adapter is set up for automatic IP Address configuration with DHCP.\nIf you get a \"disabled\" message:\n - then your Wireless LAN Adapter is configured for manual IP Setup\n- verify thay you have entered correct IP informations in the AdapterSetup dialog.\nIf you get an \"enabeld\" message:\n-verify that you have a configured and working DHCP Server in your network."))
			self["InfoTextBorder"].show()
			self["InfoText"].show()
			self["key_red"].setText(_("Back"))
		if self.activebutton == 4: # IP Check
			self["InfoText"].setText(_("This test checks whether a valid IP Address is found for your LAN Adapter.\nIf you get a \"unconfirmed\" message:\n- no valid IP Address was found\n- please check your DHCP, cabling and adapter setup"))
			self["InfoTextBorder"].show()
			self["InfoText"].show()
			self["key_red"].setText(_("Back"))
		if self.activebutton == 5: # DNS Check
			self["InfoText"].setText(_("This test checks for configured Nameservers.\nIf you get a \"unconfirmed\" message:\n- please check your DHCP, cabling and Adapter setup\n- if you configured your Nameservers manually please verify your entries in the \"Nameserver\" Configuration"))
			self["InfoTextBorder"].show()
			self["InfoText"].show()
			self["key_red"].setText(_("Back"))
		if self.activebutton == 6: # Edit Settings
			self.session.open(WlanConfig,self.iface)
			self["shortcuts"].setEnabled(True)		
			self["infoshortcuts"].setEnabled(False)

	def KeyYellow(self):
		self.nextstep = 0
		self["shortcutsgreen_restart"].setEnabled(True)
		self["shortcutsgreen"].setEnabled(False)
		self["shortcutsyellow"].setEnabled(False)
		self["key_green"].setText(_("Restart test"))
		self["key_yellow"].setText("")
		self.steptimer = False
		self.nextStepTimer.stop()

	def layoutFinished(self):
		self.setTitle(_("Network test: ") + iNetwork.getFriendlyAdapterName(self.iface) )
		self["shortcutsyellow"].setEnabled(False)
		self["AdapterInfo_OK"].hide()
		self["NetworkInfo_Check"].hide()
		self["DhcpInfo_Check"].hide()
		self["IPInfo_Check"].hide()
		self["DNSInfo_Check"].hide()
		self["EditSettings_Text"].hide()
		self["EditSettingsButton"].hide()
		self["InfoText"].hide()
		self["InfoTextBorder"].hide()
		self["key_yellow"].setText("")

	def setLabels(self):
		self["Adaptertext"] = MultiColorLabel(_("LAN Adapter"))
		self["Adapter"] = MultiColorLabel()
		self["AdapterInfo"] = MultiPixmap()
		self["AdapterInfo_Text"] = MultiColorLabel(_("Show Info"))
		self["AdapterInfo_OK"] = Pixmap()
		
		if self.iface in iNetwork.wlan_interfaces:
			self["Networktext"] = MultiColorLabel(_("Wireless Network"))
		else:
			self["Networktext"] = MultiColorLabel(_("Local Network"))
		
		self["Network"] = MultiColorLabel()
		self["NetworkInfo"] = MultiPixmap()
		self["NetworkInfo_Text"] = MultiColorLabel(_("Show Info"))
		self["NetworkInfo_Check"] = MultiPixmap()
		
		self["Dhcptext"] = MultiColorLabel(_("DHCP"))
		self["Dhcp"] = MultiColorLabel()
		self["DhcpInfo"] = MultiPixmap()
		self["DhcpInfo_Text"] = MultiColorLabel(_("Show Info"))
		self["DhcpInfo_Check"] = MultiPixmap()
		
		self["IPtext"] = MultiColorLabel(_("IP Address"))
		self["IP"] = MultiColorLabel()
		self["IPInfo"] = MultiPixmap()
		self["IPInfo_Text"] = MultiColorLabel(_("Show Info"))
		self["IPInfo_Check"] = MultiPixmap()
		
		self["DNStext"] = MultiColorLabel(_("Nameserver"))
		self["DNS"] = MultiColorLabel()
		self["DNSInfo"] = MultiPixmap()
		self["DNSInfo_Text"] = MultiColorLabel(_("Show Info"))
		self["DNSInfo_Check"] = MultiPixmap()
		
		self["EditSettings_Text"] = MultiColorLabel(_("Edit settings"))
		self["EditSettingsButton"] = MultiPixmap()
		
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Start test"))
		self["key_yellow"] = StaticText(_("Stop test"))
		
		self["InfoTextBorder"] = Pixmap()
		self["InfoText"] = Label()

	def NetworkStatedataAvail(self,data):
		if data <= 2:
			self["IP"].setForegroundColorNum(2)
			self["IP"].setText(_("confirmed"))
			self["IPInfo_Check"].setPixmapNum(0)
		else:
			self["IP"].setForegroundColorNum(1)
			self["IP"].setText(_("unconfirmed"))
			self["IPInfo_Check"].setPixmapNum(1)
		self["IPInfo_Check"].show()
		self["IPInfo_Text"].setForegroundColorNum(1)		
		self.steptimer = True
		self.nextStepTimer.start(3000)		
		
	def DNSLookupdataAvail(self,data):
		if data <= 2:
			self["DNS"].setForegroundColorNum(2)
			self["DNS"].setText(_("confirmed"))
			self["DNSInfo_Check"].setPixmapNum(0)
		else:
			self["DNS"].setForegroundColorNum(1)
			self["DNS"].setText(_("unconfirmed"))
			self["DNSInfo_Check"].setPixmapNum(1)
		self["DNSInfo_Check"].show()
		self["DNSInfo_Text"].setForegroundColorNum(1)
		self["EditSettings_Text"].show()
		self["EditSettingsButton"].setPixmapNum(1)
		self["EditSettings_Text"].setForegroundColorNum(2) # active
		self["EditSettingsButton"].show()
		self["key_yellow"].setText("")
		self["key_green"].setText(_("Restart test"))
		self["shortcutsgreen"].setEnabled(False)
		self["shortcutsgreen_restart"].setEnabled(True)
		self["shortcutsyellow"].setEnabled(False)
		self["updown_actions"].setEnabled(True)
		self.activebutton = 6

	def getInfoCB(self,status):
		if status is not None:
			if status.startswith("No Connection") or status.startswith("Not-Associated") or status == False:
				self["Network"].setForegroundColorNum(1)
				self["Network"].setText(_("disconnected"))
				self["NetworkInfo_Check"].setPixmapNum(1)
				self["NetworkInfo_Check"].show()
			else:
				self["Network"].setForegroundColorNum(2)
				self["Network"].setText(_("connected"))
				self["NetworkInfo_Check"].setPixmapNum(0)
				self["NetworkInfo_Check"].show()
						
	def cleanup(self):
		iNetwork.stopLinkStateConsole()
		iNetwork.stopDNSConsole()

	def AccessPointInfo(self,iface):
		cmd = "iwconfig %s"%iface
		self.iwconfigConsole = Console()
		self.iwconfigConsole.ePopen(cmd,self.readAP,self.getInfoCB)

	def readAP(self,result,retval,extra_args):
		(callback) = extra_args
		self.apState = None
		if self.iwconfigConsole is not None:
			if retval == 0:
				self.iwconfigConsole = None
				for content in result.splitlines():
					if 'Access Point' in content:
						self.apState = content.strip().split('Access Point: ')[1]
						callback(self.apState)
						return
		callback(self.apState)
		
class Wlanstatus(Screen):
	skin = """
	<screen name="Wlanstatus" position="209,48" size="865,623" title="Wireless Network Configuration..." flags="wfNoBorder" backgroundColor="transparent">
		<ePixmap pixmap="Vu_HD/Bg_EPG_view.png" zPosition="-1" position="0,0" size="865,623" alphatest="on" />
		<ePixmap pixmap="Vu_HD/menu/ico_title_Setup.png" position="32,41" size="40,40" alphatest="blend"  transparent="1" />
		<eLabel text="Wireless Network Status..." position="90,50" size="600,32" font="Semiboldit;32" foregroundColor="#5d5d5d" backgroundColor="#27b5b9bd" transparent="1" />
		<ePixmap pixmap="Vu_HD/icons/clock.png" position="750,55" zPosition="1" size="20,20" alphatest="blend" />
		<widget source="global.CurrentTime" render="Label" position="770,57" zPosition="1" size="50,20" font="Regular;20" foregroundColor="#1c1c1c" backgroundColor="#27d9dee2" halign="right" transparent="1">
			<convert type="ClockToText">Format:%H:%M</convert>
		</widget>
		<ePixmap pixmap="Vu_HD/buttons/red.png" position="45,98" size="25,25" alphatest="blend" />
		<widget source="key_red" render="Label" position="66,97" zPosition="1" size="150,25" font="Regular;20" halign="center" valign="center" backgroundColor="darkgrey" foregroundColor="#1c1c1c" transparent="1" />
		<widget source="status" render="Label" position="110,200" size="650,400" transparent="1" font="Regular;20" foregroundColor="#1c1c1c" backgroundColor="#27d9dee2" zPosition="1" />
	</screen>"""
	def __init__(self, session,iface):
		Screen.__init__(self,session)
		self.session = session
		self.iface = iface
		self["status"] = StaticText(_("Wait a moment..."))
		self["key_red"] = StaticText(_("Close"))
		self["OkCancelActions"] = ActionMap(["ShortcutActions", "SetupActions" ],
		{
			"ok": self.ok,
			"cancel": self.close,
			"red": self.close,
		}, -2)
		self.readstatus()

	def readstatus(self):
		self.wlanstatus = Console()
		cmd1 = "iwconfig "+self.iface
		self.wlanstatus.ePopen(cmd1, self.iwconfigfinnished,self.statusdisplay)

	def iwconfigfinnished(self, result, retval,extra_args):
		try:
			(statecallback) = extra_args
			if self.wlanstatus is not None:
				if retval == 0:
					statecallback(result)
				else:
					statecallback(0)
		except:
			self.close()


	def statusdisplay(self,data):
		if data == 0:
			self["status"].setText(_("No information..."))
		else:
			self["status"].setText(data)

	def ok(self):
		pass

def openconfig(session, **kwargs):
	session.open(WlanSelection)

def selSetup(menuid, **kwargs):
	list=[]
	if menuid != "system":
		return [ ]
	else:
		for x in iNetwork.getAdapterList():
			if x.startswith('eth'):
				continue
			list.append(x)
		if len(list):
			return [(_("Wireless LAN Setup"), openconfig, "wlansetup_config", 80)]
		else:
			return [ ]
	return [ ]

def Plugins(**kwargs):
	return 	PluginDescriptor(name=_("Wireless LAN Setup"), description="Wireless LAN Setup", where = PluginDescriptor.WHERE_MENU, fnc=selSetup)
