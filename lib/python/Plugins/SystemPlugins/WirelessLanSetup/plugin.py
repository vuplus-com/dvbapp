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
from pythonwifi.iwlibs import Wireless
import pythonwifi.flags

class WlanSelection(Screen,HelpableScreen):
	skin = 	"""
		<screen position="center,center" size="510,400" title="Wireless Network Adapter Selection..." >
			<ePixmap pixmap="skin_default/div-h.png" position="0,350" zPosition="1" size="560,2" />
			<ePixmap pixmap="skin_default/border_menu.png" position="10,10" zPosition="1" size="250,300" transparent="1" alphatest="on" />

			<ePixmap pixmap="skin_default/buttons/red.png" position="10,360" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="360,360" size="140,40" alphatest="on" />

			<widget source="key_red" render="Label" position="10,360" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="360,360" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />

			<widget name="menulist" position="20,20" size="230,260" transparent="1" backgroundColor="#371e1c1a" zPosition="10" scrollbarMode="showOnDemand" />
			<widget source="description" render="Label" position="305,10" size="195,300" font="Regular;19" halign="center" valign="center" />
		</screen>
		"""
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
		self.updateInterfaces()
		self.onClose.append(self.cleanup)

	def updateInterfaces(self):
		iNetwork.config_ready = False
		iNetwork.msgPlugins()
		iNetwork.getInterfaces()

	def checkIfaceMode(self, iface = None):
		try:
			obj = Wireless(iface)
			if obj.getMode() == 'Master':
				return -1
			else:
				return 0
		except:
			return -2

	def ok(self):
#		print len(self["menulist"].list)
		if len(self["menulist"].list) == 0:
			self.session.open(MessageBox, (_("Can not find any WirelessLan Module\n")),MessageBox.TYPE_ERROR,5 )
			return
		iface=self["menulist"].getCurrent()[1]
		if iface == None:
			return
		elif iNetwork.getAdapterAttribute(iface, "up") == True:
			ret = self.checkIfaceMode(iface)
			if ret == -2:
				self.session.open(MessageBox, (_("Invalid WirelessLan Module.\n")),MessageBox.TYPE_ERROR,5 )
				return
			elif ret == -1:
				self.session.open(MessageBox, (_("Can not setup WirelessLan Module in 'AP Mode'\n")),MessageBox.TYPE_ERROR,5 )
				return
		self.session.open(WlanSetup, iface)

	def getWlandevice(self):
		list = []
		for x in iNetwork.getInstalledAdapters():
			if x.startswith('eth') or x.startswith('br') or x.startswith('mon'):
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
					return _("Realtek")+ " " + _("WLAN adapter.")
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

	def cleanup(self):
		iNetwork.stopGetInterfacesConsole()

class WlanSetup(Screen,HelpableScreen):
	skin = 	"""
		<screen position="center,center" size="510,400" title="Wireless Network Setup Menu..." >
			<ePixmap pixmap="skin_default/div-h.png" position="0,350" zPosition="1" size="560,2" />
			<ePixmap pixmap="skin_default/border_menu.png" position="10,10" zPosition="1" size="250,300" transparent="1" alphatest="on" />

			<ePixmap pixmap="skin_default/buttons/red.png" position="10,360" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="360,360" size="140,40" alphatest="on" />

			<widget source="key_red" render="Label" position="10,360" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="360,360" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />

			<widget name="menulist" position="20,20" size="230,260" transparent="1" backgroundColor="#371e1c1a" zPosition="10" scrollbarMode="showOnDemand" />
			<widget source="description" render="Label" position="305,10" size="195,300" font="Regular;19" halign="center" valign="center" />
		</screen>
		"""
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
		self.onClose.append(self.cleanup)

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
		self.cleanup()
		if self["menulist"].getCurrent()[1] == 'setting':
			self.session.openWithCallback(self.checklist, WlanConfig, self.iface)
		elif self["menulist"].getCurrent()[1] == 'scanap':
			self.session.openWithCallback(self.WlanScanApCallback, WlanScanAp, self.iface)
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

	def WlanScanApCallback(self, essid = None):
		if essid is not None:
			self.session.openWithCallback(self.checklist, WlanConfig, self.iface, essid)

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

	def cleanup(self):
		iNetwork.stopRestartConsole()
		iNetwork.stopGetInterfacesConsole()

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
wlanconfig.key = ConfigPassword(default = "XXXXXXXX", visible_width = 50, fixed_size = False)
wlanconfig.usegateway = ConfigSelection(default = "off", choices = [
	("off", _("no")), ("on", _("yes"))])
wlanconfig.ip	 = ConfigIP([0,0,0,0])
wlanconfig.netmask = ConfigIP([0,0,0,0])
wlanconfig.gateway = ConfigIP([0,0,0,0])

selectap = None	
class WlanConfig(Screen, ConfigListScreen, HelpableScreen):
	skin = 	"""
		<screen position="center,center" size="510,400" title="Wireless Network Configuration..." >
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,360" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="360,360" size="140,40" alphatest="on" />

			<widget source="key_red" render="Label" position="10,360" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="360,360" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />

			<widget name="config" position="10,10" backgroundColor="#371e1c1a" transparent="1" size="480,210" scrollbarMode="showOnDemand" />
			<ePixmap pixmap="skin_default/div-h.png" position="0,225" zPosition="1" size="550,2" />
			<eLabel text="IP Address : " position="100,250" size="190,21" font="Regular;19" />
			<widget source="ipaddress" render="Label" position="300,250" zPosition="1" size="150,26" font="Regular;20" halign="center" valign="center" />
			<eLabel text="NetMask : " position="100,275" size="190,21" font="Regular;19" />
			<widget source="netmask" render="Label" position="300,275" zPosition="1" size="150,26" font="Regular;20" halign="center" valign="center" />	
			<eLabel text="Gateway : " position="100,300" size="190,21" font="Regular;19" />
			<widget source="gateway" render="Label" position="300,300" zPosition="1" size="150,26" font="Regular;20" halign="center" valign="center" />
			<widget name="VKeyIcon" pixmap="skin_default/buttons/key_text.png" position="460,230" zPosition="10" size="35,25" transparent="1" alphatest="on" />
			<widget name="HelpWindow" pixmap="skin_default/buttons/key_text.png" position="383,420" zPosition="1" size="1,1" transparent="1" alphatest="on" />
		</screen>
		"""
	def __init__(self, session, iface, essidSelected = None):
		Screen.__init__(self,session)
		self.session = session
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Ok"))
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
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()
		self["VKeyIcon"] = Pixmap()
		self["VKeyIcon"].hide()
		self.iface = iface
		self.essidSelected = essidSelected
		self.ssid = None
		self.ap_scan = None
		self.scan_ssid = None
		self.key_mgmt = None
		self.proto = None
		self.key_type = None
		self.encryption_key = None
		self.wlanscanap = None
		self.wpaphraseconsole = None
		self.list = []
		ConfigListScreen.__init__(self, self.list,session = self.session)
		self.oldInterfaceState = iNetwork.getAdapterAttribute(self.iface, "up")
		self.readWpaSupplicantConf()
		self.scanAplistTimer = eTimer()
		self.scanAplistTimer.callback.append(self.scanApList)
		self.emptyListMsgTimer = eTimer()
		self.emptyListMsgTimer.callback.append(self.emptyListMsg)
		self.Console = Console()
		self.updateInterfaces(self.readWlanSettings)
		self.onClose.append(self.cleanup)

	def updateInterfaces(self,callback = None):
		iNetwork.config_ready = False
		iNetwork.msgPlugins()
		iNetwork.getInterfaces(callback)

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
		wlanconfig.key = ConfigPassword(default = default_tmp, visible_width = 50, fixed_size = False)
		self.getApList()

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
						elif data.startswith('#psk="') and len(data) > 6:
							self.key_type = 0 # hex
							self.encryption_key = data[6:-2]
						elif not self.encryption_key and data.startswith('psk=') and len(data) > 4:
							self.key_type = 0 # hex
							self.encryption_key = data[4:-1]
						data = wpafd.readline()
#					print self.ssid,self.scan_ssid,self.key_mgmt,self.proto,self.key_type,self.encryption_key
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
			if wlanconfig.essid.value == 'Input hidden ESSID':
				self.configList.append( self.hiddenessidEntry )
			self.configList.append( self.encryptEntry )
			if wlanconfig.encrypt.value is "on" :
				self.configList.append( self.methodEntry )
				if wlanconfig.method.value =="wep":
					self.configList.append( self.keytypeEntry )
				self.configList.append( self.keyEntry )

		self["config"].list = self.configList
		self["config"].l.setList(self.configList)
		if not self.showTextIcon in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.showTextIcon)

	def showTextIcon(self):
		if isinstance(self["config"].getCurrent()[1], ConfigText) or isinstance(self["config"].getCurrent()[1], ConfigPassword):
			self["VKeyIcon"].show()
		else:
			self["VKeyIcon"].hide()

	def getApList(self):
		if self.essidSelected is None:
			self.apList = []
			self.configurationmsg = self.session.open(MessageBox, _("Please wait for scanning AP..."), type = MessageBox.TYPE_INFO, enable_input = False)
			self.scanAplistTimer.start(100,True)
		else:
			self.apList = [self.essidSelected]
			wlanconfig.essid = ConfigSelection(choices = self.apList)
			if self.ssid is not None:
				wlanconfig.hiddenessid = ConfigText(default = self.ssid, visible_width = 50, fixed_size = False)
			else:
				wlanconfig.hiddenessid = ConfigText(default = "<Input ESSID>", visible_width = 50, fixed_size = False)
			self.createConfig()

	def getScanResult(self, wirelessObj):
		Iwscanresult  = None
		try:
			Iwscanresult  = wirelessObj.scan()
		except IOError:
			print "%s Interface doesn't support scanning.."%self.iface
		return Iwscanresult

	def scanApList(self):
		if self.oldInterfaceState is not True:
			os_system("ifconfig "+self.iface+" up")
			iNetwork.setAdapterAttribute(self.iface, "up", True)
		wirelessObj = Wireless(self.iface)
		Iwscanresult=self.getScanResult(wirelessObj)
		if Iwscanresult is None or len(Iwscanresult.aplist) == 0 :
			import time
			time.sleep(1.5)
			Iwscanresult=self.getScanResult(wirelessObj)
		self.configurationmsg.close(True)
		if Iwscanresult is None or len( Iwscanresult.aplist) == 0:
			self.emptyListMsgTimer.start(100,True)
		else:
			for ap in Iwscanresult:
				if ap.essid is not None and ap.essid not in self.apList and len(ap.essid) > 0:
					self.apList.append(ap.essid)
		self.apList.append('Input hidden ESSID')
		if selectap is not None and selectap in self.apList:
			wlanconfig.essid = ConfigSelection(default=selectap,choices = self.apList)
		elif self.scan_ssid is not None and self.scan_ssid.strip() == '1':
			wlanconfig.essid = ConfigSelection(default='Input hidden ESSID',choices = self.apList)
		elif self.ssid is not None and self.ssid in self.apList:
			wlanconfig.essid = ConfigSelection(default=self.ssid, choices = self.apList)
		else:
			try:
				wlanconfig.essid = ConfigSelection(defalut = self.apList[0], choices = self.apList)
			except:
				wlanconfig.essid = ConfigSelection(choices = self.apList)
		if self.ssid is not None:
			wlanconfig.hiddenessid = ConfigText(default = self.ssid, visible_width = 50, fixed_size = False)
		else:
			wlanconfig.hiddenessid = ConfigText(default = "<Input ESSID>", visible_width = 50, fixed_size = False)
		self.createConfig()

	def emptyListMsg(self):
		self.session.open(MessageBox, _("No AP detected."), type = MessageBox.TYPE_INFO, timeout = 10)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()

	def newConfig(self):
		if self["config"].getCurrent() == self.usedeviceEntry or self["config"].getCurrent() == self.encryptEntry \
			or self["config"].getCurrent() == self.usedhcpEntry or self["config"].getCurrent() == self.usegatewayEntry \
			or self["config"].getCurrent() == self.essidEntry or self["config"].getCurrent() == self.methodEntry:
			self.createConfig()

	def saveWlanConfig(self):
		try:
			if self["config"].getCurrent() == self.keyEntry or self["config"].getCurrent() == self.hiddenessidEntry :
				self["config"].getCurrent()[1].onDeselect(self.session)
			if self["config"].isChanged():
				self.session.openWithCallback(self.checkNetworkConfig, MessageBox, (_("Are you sure you want to restart your network interfaces?\n") ) )
			else:
				self.session.openWithCallback(self.checkNetworkConfig, MessageBox, (_("Network configuration is not changed....\n\nAre you sure you want to restart your network interfaces?\n") ) )
		except:
			pass

	def checkNetworkConfig(self, ret = False):
		if ret == False:
			if self["config"].getCurrent() == self.keyEntry or self["config"].getCurrent() == self.hiddenessidEntry :
				self["config"].getCurrent()[1].onSelect(self.session)
			return
		if wlanconfig.essid.value == 'Input hidden ESSID':
			if len(wlanconfig.hiddenessid.value) == 0:
				self.session.open(MessageBox, ("PLEASE INPUT HIDDEN ESSID"), type = MessageBox.TYPE_ERROR, timeout = 10)
				return
		if len(wlanconfig.key.value) == 0:
			self.session.open(MessageBox, ("PLEASE INPUT NETWORK KEY"), type = MessageBox.TYPE_ERROR, timeout = 10)
			return
		self.checkNetworkShares()

	def checkNetworkShares(self):
		if not self.Console:
			self.Console = Console()
		cmd = "cat /proc/mounts"
		self.Console.ePopen(cmd, self.checkSharesFinished, self.confirmAnotherIfaces)

	def checkSharesFinished(self, result, retval, extra_args):
		callback = extra_args
#		print "checkMountsFinished : result : \n",result
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
					self.getWpaPhrase(False)
				else:
					self.session.openWithCallback(self.getWpaPhrase, MessageBox, _("A second configured interface has been found.\n\nDo you want to disable the second network interface?"), default = True)
			else:
				self.getWpaPhrase(False)

	def getWpaPhrase(self,ret):
		if ret == True:
			configuredInterfaces = iNetwork.getConfiguredAdapters()
			for interface in configuredInterfaces:
				if interface == self.iface:
					continue
				iNetwork.setAdapterAttribute(interface, "up", False)
				iNetwork.deactivateInterface(interface)
		if wlanconfig.method.value =="wep":
			self.writeWpasupplicantConf("wep") # passphrasekey is not None
		else:
			if wlanconfig.essid.value == 'Input hidden ESSID':
				cmd = "wpa_passphrase '%s' %s" % (wlanconfig.hiddenessid.value,wlanconfig.key.value)
			else :
				cmd = "wpa_passphrase '%s' %s" % (wlanconfig.essid.value,wlanconfig.key.value)
			print cmd
			self.wpaphraseconsole = Console()
			self.wpaphraseconsole.ePopen(cmd, self.parseWpaPhrase, self.writeWpasupplicantConf)

	def parseWpaPhrase(self, result, retval, extra_args):
		(writewlanconfig) = extra_args
		if self.wpaphraseconsole is not None:
			if retval == 0:
				self.wpaphraseconsole.killAll()
				self.wpaphraseconsole = None
#				print "parseWpaPhrase result : "
#				print result
				psk = None
				for line in result.splitlines():
					if line.find('ssid') == -1 and line.find('#psk=') != -1:
						plainpwd	= line
	 				elif line.find('psk=') != -1:
						psk = line
				if psk:
					writewlanconfig(psk,plainpwd)
				else:
					writewlanconfig(None)
			else:
				writewlanconfig(None)

	def writeWpasupplicantConf(self, passphrasekey=None,plainpwd=None):
		if passphrasekey:
			wpafd = open("/etc/wpa_supplicant.conf","w")
			if wpafd > 0:
				contents = "#WPA Supplicant Configuration by STB\n"
				contents += "ctrl_interface=/var/run/wpa_supplicant\n"
				contents += "eapol_version=1\n"
				contents += "fast_reauth=1\n"
				contents += "ap_scan=1\n"
				contents += "network={\n"
				if wlanconfig.essid.value == 'Input hidden ESSID':
					contents += "\tssid=\""+wlanconfig.hiddenessid.value+"\"\n"
					contents += "\tscan_ssid=1\n"
				else :
					contents += "\tssid=\""+wlanconfig.essid.value+"\"\n"
					contents += "\tscan_ssid=0\n"
				if wlanconfig.encrypt.value == "on":
					if wlanconfig.method.value =="wep":
						contents += "\tkey_mgmt=NONE\n"
						contents += "\twep_key0="
						if wlanconfig.keytype.value == "ascii":
							contents += "\""+wlanconfig.key.value+"\"\n"
						else:
							contents += wlanconfig.key.value+"\n"
					else:
#						print "plainpwd : ",plainpwd
#						print "passphrasekey : ",passphrasekey
						if wlanconfig.method.value == "wpa":
							contents += "\tkey_mgmt=WPA-PSK\n"
							contents += "\tproto=WPA\n"
							contents += "\tpairwise=CCMP TKIP\n"
							contents += "\tgroup=CCMP TKIP\n"	
						elif wlanconfig.method.value == "wpa2":
							contents += "\tkey_mgmt=WPA-PSK\n"
							contents += "\tproto=RSN\n"
							contents += "\tpairwise=CCMP TKIP\n"
							contents += "\tgroup=CCMP TKIP\n"
						else:
							contents += "\tkey_mgmt=WPA-PSK\n"
							contents += "\tproto=WPA RSN\n"
							contents += "\tpairwise=CCMP TKIP\n"
							contents += "\tgroup=CCMP TKIP\n"
						contents += plainpwd+"\n"
						contents += passphrasekey+"\n"
				else:
					contents += "\tkey_mgmt=NONE\n"
				contents += "}\n"
				print "content = \n"+contents
				wpafd.write(contents)
				wpafd.close()
				self.writeNetConfig(0)
			else :
				self.session.open(MessageBox, _("wpa_supplicant.conf open error."), type = MessageBox.TYPE_ERROR, timeout = 10)
				self.writeNetConfig(-1)
		else:
			self.writeNetConfig(-2)

	def writeNetConfig(self,ret = -1):
		if ret == -1:
			self.session.open(MessageBox, _("wpa_supplicant.conf open error."), type = MessageBox.TYPE_ERROR, timeout = 10)
			return
		elif ret == -2:
			self.session.open(MessageBox, _("Can NOT generate passphrase"), type = MessageBox.TYPE_ERROR, timeout = 10)
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

	def cleanup(self):
		iNetwork.stopRestartConsole()
		iNetwork.stopGetInterfacesConsole()
		iNetwork.stopDeactivateInterfaceConsole()
		self.stopwlanscanapConsole()
		self.stopCheckNetworkSharesConsole()
		self.stopWpaPhraseConsole()

	def stopwlanscanapConsole(self):
		if self.wlanscanap is not None:
			if len(self.wlanscanap.appContainers):
				for name in self.wlanscanap.appContainers.keys():
					self.wlanscanap.kill(name)

	def stopCheckNetworkSharesConsole(self):
		if self.Console is not None:
			if len(self.Console.appContainers):
				for name in self.Console.appContainers.keys():
					self.Console.kill(name)

	def stopWpaPhraseConsole(self):
		if self.wpaphraseconsole is not None:
			if len(self.wpaphraseconsole.appContainers):
					for name in self.wpaphraseconsole.appContainers.keys():
						self.wpaphraseconsole.kill(name)

class WlanScanAp(Screen,HelpableScreen):
	skin = 	"""
		<screen position="center,center" size="510,400" title="Wireless Network AP Scan..." >
			<ePixmap pixmap="skin_default/div-h.png" position="0,350" zPosition="1" size="560,2" />
			<ePixmap pixmap="skin_default/border_menu.png" position="10,10" zPosition="1" size="250,300" transparent="1" alphatest="on" />

			<ePixmap pixmap="skin_default/buttons/red.png" position="10,360" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="185,360" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="360,360" size="140,40" alphatest="on" />

			<widget source="key_red" render="Label" position="10,360" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="185,360" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_blue" render="Label" position="360,360" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" foregroundColor="#ffffff" transparent="1" />

			<widget name="menulist" position="20,20" size="230,260" backgroundColor="#371e1c1a" transparent="1" zPosition="10" scrollbarMode="showOnDemand" />

			<widget source="Address" render="Label" position="265,70" zPosition="1" size="240,30" font="Regular;18" halign="center" valign="center" />
			<widget source="ESSID" render="Label" position="265,100" zPosition="1" size="240,30" font="Regular;18" halign="center" valign="center" />
			<widget source="Protocol" render="Label" position="265,130" zPosition="1" size="240,30" font="Regular;18" halign="center" valign="center" />
			<widget source="Frequency" render="Label" position="265,160" zPosition="1" size="240,40" font="Regular;18" halign="center" valign="center" />
			<widget source="Encryption key" render="Label" position="265,200" zPosition="1" size="240,30" font="Regular;18" halign="center" valign="center" />
			<widget source="BitRate" render="Label" position="265,220" zPosition="1" size="240,60" font="Regular;18" halign="center" valign="center" />
		</screen>
		"""
	def __init__(self, session, iface):
		Screen.__init__(self,session)
		HelpableScreen.__init__(self)
		self.session = session
		self.iface = iface
		self.wlanscanap = None
		self.apList = {}
		self.setApList = []

		self["WizardActions"] = HelpableActionMap(self, "WizardActions",
		{
			"up": (self.up, _("move up to previous entry")),
			"down": (self.down, _("move down to next entry")),
			"left": (self.left, _("move up to first entry")),
			"right": (self.right, _("move down to last entry")),
		}, -2)

		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
		{
			"cancel": (self.close, _("exit")),
			"ok": (self.ok, "select AP"),
		})

		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
		{
			"red": (self.close, _("exit")),
			"green": (self.ok, "select AP"),
			"yellow": (self.restartScanAP, "restart scan AP"),
			"blue": (self.startWlanConfig, "Edit Wireless settings"),
		})

		self["menulist"] = MenuList(self.setApList)
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Select"))
		self["key_blue"] = StaticText(_("EditSetting"))
		self["Address"] = StaticText(_("Scanning AP List.."))
		self["ESSID"] = StaticText(_("Wait a moment"))
		self["Protocol"] = StaticText(" ")
		self["Frequency"] = StaticText(" ")
		self["Encryption key"] = StaticText(" ")
		self["BitRate"] = StaticText(" ")
		self.oldInterfaceState = iNetwork.getAdapterAttribute(self.iface, "up")
		self.getAplistTimer = eTimer()
		self.getAplistTimer.callback.append(self.getApList)
		self.scanAplistTimer = eTimer()
		self.scanAplistTimer.callback.append(self.scanApList)
		self.emptyListMsgTimer = eTimer()
		self.emptyListMsgTimer.callback.append(self.emptyListMsg)
		self.apList = {}
		self.onClose.append(self.__onClose)
		self.getAplistTimer.start(100,True)
		
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
		if self["menulist"].getCurrent() is not None:
			selectAp=self["menulist"].getCurrent()[0]
			selectap = selectAp
		self.close()

	def startWlanConfig(self):
		if self["menulist"].getCurrent() is not None:
			selectAp=self["menulist"].getCurrent()[0]
			self.close(selectAp)

	def getApList(self):
		self.apList = {}
		self.setApList = []
		self.configurationmsg = self.session.open(MessageBox, _("Please wait for scanning AP..."), type = MessageBox.TYPE_INFO, enable_input = False)
		self.scanAplistTimer.start(100,True)

	def getScanResult(self, wirelessObj):
		Iwscanresult  = None
		try:
			Iwscanresult  = wirelessObj.scan()
		except IOError:
			print "%s Interface doesn't support scanning.."%self.iface
		return Iwscanresult

	def scanApList(self):
		if self.oldInterfaceState is not True:
			os_system("ifconfig "+self.iface+" up")
			iNetwork.setAdapterAttribute(self.iface, "up", True)
		wirelessObj = Wireless(self.iface)
		Iwscanresult=self.getScanResult(wirelessObj)
		if Iwscanresult is None or len(Iwscanresult.aplist) == 0 :
			import time
			time.sleep(1.5)
			Iwscanresult=self.getScanResult(wirelessObj)
		self.configurationmsg.close(True)
		if Iwscanresult is not None and len(Iwscanresult.aplist) != 0:
			(num_channels, frequencies) = wirelessObj.getChannelInfo()
			index = 1
			for ap in Iwscanresult:
				self.apList[index] = {}
				self.apList[index]["Address"] = ap.bssid
				if len(ap.essid) == 0:
					self.apList[index]["ESSID"] = "<hidden ESSID>"
				else:
					self.apList[index]["ESSID"] = ap.essid
					self.setApList.append( (self.apList[index]["ESSID"], index) )
				self.apList[index]["Protocol"] = ap.protocol
				self.apList[index]["Frequency"] = wirelessObj._formatFrequency(ap.frequency.getFrequency())
				try:
					self.apList[index]["Channel"] = frequencies.index(self.apList[index]["Frequency"] + 1)
				except:
					self.apList[index]["Channel"] = "Unknown"

				self.apList[index]["Quality"] = "%s/%s" % \
					( ap.quality.quality, wirelessObj.getQualityMax().quality )
				self.apList[index]["Signal Level"] = "%s/%s" % \
					( ap.quality.getSignallevel(), "100" )
				self.apList[index]["Noise Level"] = "%s/%s" % \
					( ap.quality.getNoiselevel(), "100" )

# get encryption key on/off
				key_status = "Unknown"
				if (ap.encode.flags & pythonwifi.flags.IW_ENCODE_DISABLED):
					key_status = "off"
				elif (ap.encode.flags & pythonwifi.flags.IW_ENCODE_NOKEY):
					if (ap.encode.length <= 0):
						key_status = "on"
				self.apList[index]["Encryption key"] = key_status
				self.apList[index]["BitRate"] = wirelessObj._formatBitrate(ap.rate[-1][-1])
				index += 1
#		print self.apList
#		print self.setApList
		self.displayApInfo()
		if len(self.apList) == 0:
			self.emptyListMsgTimer.start(100,True)

	def displayApInfo(self):
		if len(self.apList) >0:
			self["menulist"].setList(self.setApList)
			if self["menulist"].getCurrent() is not None:
				index = self["menulist"].getCurrent()[1]
				for key in ["Address", "ESSID", "Protocol", "Frequency", "Encryption key", "BitRate"]:
					if self.apList[index].has_key(key) and self.apList[index][key] is not None:
						self[key].setText((key+":  "+self.apList[index][key]))
					else:
						self[key].setText((key+": None"))

	def emptyListMsg(self):
		self.session.open(MessageBox, _("No AP detected."), type = MessageBox.TYPE_INFO, timeout = 10)
		self["Address"].setText(_("No AP detected."))
		self["ESSID"].setText(_(""))

	def restartScanAP(self):
		self.getAplistTimer.start(100,True)

	def __onClose(self):
		if self.oldInterfaceState is False:
			iNetwork.setAdapterAttribute(self.iface, "up", False)
			iNetwork.deactivateInterface(self.iface)

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
			self.cleanup()
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
		iNetwork.stopPingConsole()
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
	skin =  """
		<screen position="center,center" size="510,400" title="Wireless Network Status..." >
			<widget source="status" render="Label" position="5,15" size="500,350" font="Regular;18" zPosition="1" />

			<ePixmap pixmap="skin_default/buttons/red.png" position="185,360" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="185,360" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
		</screen>
		"""
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
		self.onClose.append(self.cleanup)

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

	def cleanup(self):
		self.stopWlanStatusConsole()

	def stopWlanStatusConsole(self):
		if self.wlanstatus is not None:
			if len(self.wlanstatus.appContainers):
				for name in self.wlanstatus.appContainers.keys():
					self.wlanstatus.kill(name)

def openconfig(session, **kwargs):
	session.open(WlanSelection)

def selSetup(menuid, **kwargs):
	list=[]
	if menuid != "system":
		return [ ]
	else:
		for x in iNetwork.getInstalledAdapters():
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
