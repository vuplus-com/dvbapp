from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InputBox import InputBox
from Screens.Standby import *
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.HelpMenu import HelpableScreen
from Components.Network import iNetwork
#from Screens.NetworkSetup import NameserverSetup, NetworkAdapterTest
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
from os import path as os_path, system as os_system, unlink
from re import compile as re_compile, search as re_search
from Tools.Directories import fileExists
import time

class WlanSelection(Screen):
	skin = """
	<screen name="WlanSelection" position="209,48" size="865,623" title="Wireless Network Selection..." flags="wfNoBorder" backgroundColor="transparent">	
		<ePixmap pixmap="Vu_HD/Bg_EPG_view.png" zPosition="-1" position="0,0" size="865,623" alphatest="on" />
		<ePixmap pixmap="Vu_HD/menu/ico_title_Setup.png" position="32,41" size="40,40" alphatest="blend"  transparent="1" />
		<eLabel text="Wireless Network Selection..." position="90,50" size="600,32" font="Semiboldit;32" foregroundColor="#5d5d5d" backgroundColor="#27b5b9bd" transparent="1" />
		<ePixmap pixmap="Vu_HD/icons/clock.png" position="750,55" zPosition="1" size="20,20" alphatest="blend" />
		<widget source="global.CurrentTime" render="Label" position="770,57" zPosition="1" size="50,20" font="Regular;20" foregroundColor="#1c1c1c" backgroundColor="#27d9dee2" halign="right" transparent="1">
			<convert type="ClockToText">Format:%H:%M</convert>
		</widget>
		<ePixmap pixmap="Vu_HD/buttons/red.png" position="45,98" size="25,25" alphatest="blend" />
		<widget source="key_red" render="Label" position="66,97" zPosition="1" size="150,25" font="Regular;20" halign="center" valign="center" backgroundColor="darkgrey" foregroundColor="#1c1c1c" transparent="1" />
		<ePixmap pixmap="Vu_HD/border_menu.png" position="120,140" zPosition="-1" size="342,358" transparent="1" alphatest="blend" />
		<widget name="menulist" position="130,150" size="322,338" transparent="1" backgroundColor="#27d9dee2" zPosition="10" scrollbarMode="showOnDemand" />
	</screen>"""
	
	def __init__(self, session):
		Screen.__init__(self,session)
		self.mainmenu = self.getWlandevice()
		self["menulist"] = MenuList(self.mainmenu)
		self["key_red"] = StaticText(_("Close"))		
		self["OkCancelActions"] = ActionMap(["ShortcutActions", "SetupActions" ],
		{
			"ok": self.ok,
			"cancel": self.close,
			"red": self.close,
		}, -2)

	def ok(self):
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
			list.append((iNetwork.getFriendlyAdapterName(x),x))
		return list
#		self.adapters = [(iNetwork.getFriendlyAdapterName(x),x) for x in iNetwork.getAdapterList()]
#		print self.adapters
#		return self.adapters
		


class WlanSetup(Screen,HelpableScreen):
	skin = """
	<screen name="WlanSetup" position="209,48" size="865,623" title="Wireless Network Configuration..." flags="wfNoBorder" backgroundColor="transparent">	
		<ePixmap pixmap="Vu_HD/Bg_EPG_view.png" zPosition="-1" position="0,0" size="865,623" alphatest="on" />
		<ePixmap pixmap="Vu_HD/menu/ico_title_Setup.png" position="32,41" size="40,40" alphatest="blend"  transparent="1" />
		<eLabel text="Wireless Network Configuration..." position="90,50" size="600,32" font="Semiboldit;32" foregroundColor="#5d5d5d" backgroundColor="#27b5b9bd" transparent="1" />
		<ePixmap pixmap="Vu_HD/icons/clock.png" position="750,55" zPosition="1" size="20,20" alphatest="blend" />
		<widget source="global.CurrentTime" render="Label" position="770,57" zPosition="1" size="50,20" font="Regular;20" foregroundColor="#1c1c1c" backgroundColor="#27d9dee2" halign="right" transparent="1">
			<convert type="ClockToText">Format:%H:%M</convert>
		</widget>
		<ePixmap pixmap="Vu_HD/buttons/red.png" position="45,98" size="25,25" alphatest="blend" />
		<widget source="key_red" render="Label" position="66,97" zPosition="1" size="150,25" font="Regular;20" halign="center" valign="center" backgroundColor="darkgrey" foregroundColor="#1c1c1c" transparent="1" />
		<ePixmap pixmap="Vu_HD/border_menu.png" position="120,140" zPosition="-1" size="342,358" transparent="1" alphatest="blend" />
		<widget name="menulist" position="130,150" size="322,338" transparent="1" backgroundColor="#27d9dee2" zPosition="10" scrollbarMode="showOnDemand" />
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
		self["description"] = StaticText()
		self["IFtext"] = StaticText()
		self["IF"] = StaticText()
		self["Statustext"] = StaticText()
		self["statuspic"] = MultiPixmap()
		self["statuspic"].hide()
		
		self.oktext = _("Press OK on your remote control to continue.")
		self.reboottext = _("Your STB will restart after pressing OK on your remote control.")
		self.errortext = _("No working wireless network interface found.\n Please verify that you have attached a compatible WLAN device or enable your local network interface.")	
		
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
	def up(self):
		self["menulist"].up()
	def down(self):
		self["menulist"].down()
	def left(self):
		self["menulist"].pageUp()
	def right(self):
		self["menulist"].pageDown()
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
			self.session.openWithCallback(self.restartNet, MessageBox, (_("Are you sure you want to restart your network interfaces?\n\n") + self.oktext ) )

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
		
	def restartNet(self,ret = False):
		if ret == True:
			os_system('/etc/init.d/networking restart')
#		self.updateStatusbar()
#		self.onLayoutFinish.append(self.layoutFinished)
#		self.onClose.append(self.cleanup)

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
		<widget source="key_red" render="Label" position="66,97" zPosition="1" size="150,25" font="Regular;20" halign="center" valign="center" backgroundColor="darkgrey" foregroundColor="#1c1c1c" transparent="1" />
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
		self.mainmenu = []
		self["key_red"] = StaticText(_("Close"))		
		self["ipaddress"] = StaticText(_("[ N/A ]"))
		self["netmask"] = StaticText(_("[ N/A ]"))		
		self["gateway"] = StaticText(_("[ N/A ]"))
		self["OkCancelActions"] = ActionMap(["ShortcutActions", "SetupActions" ],
		{
			"ok": self.ok,
			"cancel": self.close,
			"red": self.close,
		}, -2)
		self.iface = iface
		self.ssid = None
		self.scan_ssid = None
		self.key_mgmt = None
		self.proto = None
		self.key_type = None
		self.wep_key = None
		
		self.list = []
		self.wlanscanap = None
		ConfigListScreen.__init__(self, self.list,session = self.session)
		self.readifSetting()


	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()


	def ok(self):
		if self["config"].isChanged():
			self.session.openWithCallback(self.confirmactive, MessageBox, (_("Are you sure you want to restart your network interfaces?\n") ) )

	def confirmactive(self, ret = False):
		if ret == False:
			return
		else:
			num_configured_if = len(iNetwork.getConfiguredAdapters())
			if num_configured_if >= 1:
				if num_configured_if == 1 and self.iface in iNetwork.getConfiguredAdapters():
					self.saveif(False)
				else:
					self.session.openWithCallback(self.saveif, MessageBox, (_("Are you sure you want to deactive another network interfaces?\n") ) )
			else:
				self.saveif(False)
				
	def saveif(self,ret = False):
		self["OkCancelActions"].setEnabled(False)
		self["config_actions"].setEnabled(False)
		if ret == True:
			configuredInterfaces = iNetwork.getConfiguredAdapters()
			for interface in configuredInterfaces:
				if interface == self.iface:
					continue
				iNetwork.setAdapterAttribute(interface, "up", False)
				iNetwork.deactivateInterface(interface)
		wpafd = open("/etc/wpa_supplicant.conf","w")
		if wpafd > 0:
			contents = "#WPA Supplicant Configuration by enigma2\n"
			contents += "ctrl_interface=/var/run/wpa_supplicant\n"
			contents += "eapol_version=1\n"
			contents += "fast_reauth=1\n"
			contents += "ap_scan=1\n"
			contents += "network={\n"
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
					contents += "\tproto=WPA RSN\n"
					contents += "\tpairwise=CCMP TKIP\n"
					contents += "\tgroup=CCMP TKIP\n"
					contents += "\tpsk="
				elif wlanconfig.method.value == "wpa/wpa2":
					contents += "\tkey_mgmt=WPA-PSK\n"
					contents += "\tproto=WPA WPA2\n"
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
		iffd = open("/etc/network/interfaces","r")
		if iffd > 0:
			prev_content = ""
			next_content = ""
			data = iffd.readline()
			status = 0
			while len(data) >0 :
				if data.startswith('iface '+self.iface) or data.startswith('auto '+self.iface):
					status = 1
					data = iffd.readline()
					continue
				elif not data.startswith('auto lo') and data.startswith('auto '):
					if ret == True or data[5:] not in iNetwork.getConfiguredAdapters():
						data = iffd.readline()
						continue
				if status == 1 and data.startswith('iface ') or data.startswith('auto '):
					status = 2
				if status == 0:
					prev_content += data
				elif status == 2:
					next_content += data
				data = iffd.readline()
			iffd.close()
			iffd = open("/etc/network/interfaces","w")
			if iffd > 0 :
				if prev_content == "":
					prev_content = "# automatically generated by enigma2\n"
					prev_content += "# do Not change manually!\n\n"
					prev_content += "auto lo\n"
					prev_content += "iface lo inet loopback\n\n"
				iffd.write(prev_content)
				if wlanconfig.usedevice.value=="on":
					iNetwork.setAdapterAttribute(self.iface, "up", True)
					contents = "auto "+self.iface+"\n"
					contents += "iface "+self.iface+" inet "
					if wlanconfig.usedhcp.value =="on":
						iNetwork.setAdapterAttribute(self.iface, "dhcp", True)					
						contents +="dhcp\n"
					else:
						iNetwork.setAdapterAttribute(self.iface, "dhcp", False)
						contents +="static\n"
						print wlanconfig.ip.value
						iNetwork.setAdapterAttribute(self.iface, "ip", wlanconfig.ip.value)
						iNetwork.setAdapterAttribute(self.iface, "netmask", wlanconfig.netmask.value)						
						contents +="\taddress "+ self.formatip(wlanconfig.ip.value)+"\n"
						contents +="\tnetmask "+ self.formatip(wlanconfig.netmask.value)+"\n"
						if wlanconfig.usegateway.value == "on":
							iNetwork.setAdapterAttribute(self.iface, "gateway", wlanconfig.gateway.value)			
							contents +="\tgateway "+ self.formatip(wlanconfig.gateway.value)+"\n"
					contents += "\n\tpre-up /usr/sbin/wpa_supplicant -i"+self.iface+" -c/etc/wpa_supplicant.conf -B -D"+iNetwork.detectWlanModule(self.iface)+"\n"
					contents += "\tpost-down wpa_cli terminate\n\n"
					iffd.write(contents)
				else:
					iNetwork.setAdapterAttribute(self.iface, "up", False)
					iNetwork.deactivateInterface(self.iface)
				iffd.write(next_content)
				iffd.close()
		self.restartNetwork(self.ConfigDataApply)
		self.configurationmsg = self.session.openWithCallback(self.WlanConfigClose, MessageBox, _("Please wait for activation of your network configuration..."), type = MessageBox.TYPE_INFO, enable_input = False)

	def restartNetwork(self,callback=None):
		self.restartConsole = Console()
		cmd="/etc/init.d/networking restart"
		self.restartConsole.ePopen(cmd, self.restartNetworkFinished, callback)

	def restartNetworkFinished(self, result, retval,extra_args):
		( callback ) = extra_args
		if callback is not None:
			callback(True)

	def ConfigDataApply(self,ret):
		if ret is True:
			iNetwork.getInterfaces(self.configurationmsgClose)

	def configurationmsgClose(self,ret):
		if ret is True:
			self.configurationmsg.close(True)
			
	def WlanConfigClose(self,ret):
		if ret is True:
			self.close()
	
	def formatip(self, iplist):
		list = []
		list = iplist
		try:
			if len(iplist) == 4:
				result = str(iplist[0])+"."+str(iplist[1])+"."+str(iplist[2])+"."+str(iplist[3])
			else:
				result ="0.0.0.0"
			return result
		except:
			return "[N/A]"
			
	def createConfig(self):
#		wlanconfig.essid = ConfigSelection(default = "none", choices = ["maruap3","maruap2","none"])
			
		self.tlist=[]
		self.usedeviceEntry = getConfigListEntry(_("Use Device"), wlanconfig.usedevice)
		self.usedhcpEntry = getConfigListEntry(_("Use DHCP"), wlanconfig.usedhcp)
		self.essidEntry = getConfigListEntry(_("ESSID"), wlanconfig.essid)
		self.encryptEntry = getConfigListEntry(_("Encrypt"), wlanconfig.encrypt)
		self.methodEntry = getConfigListEntry(_("Method"), wlanconfig.method)
		self.keytypeEntry = getConfigListEntry(_("Key Type"), wlanconfig.keytype)		
		self.keyEntry = getConfigListEntry(_("KEY"), wlanconfig.key)

		self.ipEntry = getConfigListEntry(_("IP"), wlanconfig.ip)
		self.netmaskEntry = getConfigListEntry(_("NetMask"), wlanconfig.netmask)

		self.usegatewayEntry = getConfigListEntry(_("Use Gateway"), wlanconfig.usegateway)
		self.gatewayEntry = getConfigListEntry(_("Gateway"), wlanconfig.gateway)
		
		self.tlist.append( self.usedeviceEntry )
		if wlanconfig.usedevice.value is "on":
			self.tlist.append( self.usedhcpEntry )
			if wlanconfig.usedhcp.value is "off":
				self.tlist.append(self.ipEntry)
				self.tlist.append(self.netmaskEntry)
				self.tlist.append(self.usegatewayEntry)
				if wlanconfig.usegateway.value is "on":
					self.tlist.append(self.gatewayEntry)
			self.tlist.append( self.essidEntry )
			self.tlist.append( self.encryptEntry )
			if wlanconfig.encrypt.value is "on" :
				self.tlist.append( self.methodEntry )
				self.tlist.append( self.keytypeEntry )
				self.tlist.append( self.keyEntry )
		
		self["config"].list = self.tlist
		self["config"].l.setList(self.tlist)
		if not self.selectionChanged in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.selectionChanged)

	def readifSetting(self):
		try:
			if fileExists("/etc/wpa_supplicant.conf"):
				wpafd = open("/etc/wpa_supplicant.conf","r")
				if wpafd >0:
					data = wpafd.readline()
					while len(data) > 0:
						data = data.lstrip()
						if len(data) == 0:
							data = wpafd.readline()
							continue
						if data.startswith('ssid=') and len(data) > 6:
							self.ssid = data[6:-2]
						elif data.startswith('scan_ssid=') and len(data) > 10:
							self.scan_ssid = data[10:-1]
						elif data.startswith('key_mgmt=') and len(data) > 9:
							self.key_mgmt = data[9:-1]
						elif data.startswith('proto=') and len(data) > 6:
							self.proto = data[6:-1]
						elif data.startswith('wep_key0="') and len(data) > 11:
							self.key_type = 1
							self.wep_key = data[10:-2]
						elif data.startswith('wep_key0=') and len(data) > 9:
							self.key_type = 0
							self.wep_key = data[9:-1]
						elif data.startswith('psk="') and len(data) > 6:
							self.key_type = 1
							self.wep_key = data[5:-2]
						elif data.startswith('psk=') and len(data) > 4:
							self.key_type = 0
							self.wep_key = data[4:-1]
							
						data = wpafd.readline()
					print self.ssid,self.scan_ssid,self.key_mgmt,self.proto,self.key_type,self.wep_key
					wpafd.close()
					self.setfromread()
				else:
					print 'read error'
			else:
				self.setfromread()
		except:
			print 'open error'

	def setfromread(self):
		iNetwork.getInterfaces()
		
		if iNetwork.getAdapterAttribute(self.iface, "up") == True:
			default_tmp = "on"
		else:
			default_tmp = "off"
		wlanconfig.usedevice = ConfigSelection(default=default_tmp, choices = [
			("off", _("off")), ("on", _("on"))])
		if iNetwork.getAdapterAttribute(self.iface, "dhcp"):
			default_tmp = "on"
		else:
			default_tmp = "off"
		wlanconfig.usedhcp = ConfigSelection(default=default_tmp, choices = [
			("off", _("no")), ("on", _("yes"))])
		wlanconfig	.ip = ConfigIP(default=iNetwork.getAdapterAttribute(self.iface, "ip")) or [0,0,0,0]
		wlanconfig.netmask = ConfigIP(default=iNetwork.getAdapterAttribute(self.iface, "netmask") or [255,0,0,0])
		if iNetwork.getAdapterAttribute(self.iface, "gateway"):
			default_tmp = "on"
		else:
			default_tmp = "off"
		wlanconfig.usegateway = ConfigSelection(default = default_tmp, choices = [
			("off", _("no")), ("on", _("yes"))])
		wlanconfig.gateway = ConfigIP(default=iNetwork.getAdapterAttribute(self.iface, "gateway") or [0,0,0,0])

		self["ipaddress"] = StaticText(_(self.formatip(iNetwork.getAdapterAttribute(self.iface, "ip"))))
		self["netmask"] = StaticText(_(self.formatip(iNetwork.getAdapterAttribute(self.iface, "netmask"))))
		self["gateway"] = StaticText(_(self.formatip(iNetwork.getAdapterAttribute(self.iface, "gateway"))))

		if self.wep_key is not None:
			default_tmp = "on"
		else:
			default_tmp = "off"
		wlanconfig.encrypt = ConfigSelection(default = default_tmp, choices = [
			("off", _("no")), ("on", _("yes"))])

		if self.key_mgmt=="NONE":
			default_tmp = "wep"
		elif self.key_mgmt == "WPA-PSK":
			if self.proto == "WPA":
				default_tmp = "wpa"
			elif self.proto == "WPA RSN":
				default_tmp = "wpa2"
			elif self.proto == "WPA WPA2":
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
		default_tmp = self.wep_key or "XXXXXXXX"
		wlanconfig.key = ConfigText(default = default_tmp, visible_width = 50, fixed_size = False)
		
		if wlanconfig.usedevice.value is "on":
			self.getAplist()
		else:
			self.createConfig()
		

	def newConfig(self):
		if self["config"].getCurrent() == self.usedeviceEntry :
			if wlanconfig.usedevice.value is "on":
				self.getAplist()
			else:
				if iNetwork.getAdapterAttribute(self.iface, "up"):
					iNetwork.setAdapterAttribute(self.iface, "up",False)
					iNetwork.deactivateInterface(self.iface)
				self.createConfig()
		elif self["config"].getCurrent() == self.encryptEntry or self["config"].getCurrent() == self.usedhcpEntry \
		or self["config"].getCurrent() == self.usegatewayEntry :
			self.createConfig()

	def selectionChanged(self):
		current = self["config"].getCurrent()
		print current

	def getAplist(self):
		self["OkCancelActions"].setEnabled(False) #chang
		self["config_actions"].setEnabled(False) #chang
		if iNetwork.getAdapterAttribute(self.iface, "up") is not True:
			os_system('ifconfig '+self.iface+" up")
			iNetwork.setAdapterAttribute(self.iface, "up",True)
			time.sleep(1.5)
		self.wlanscanap = Console()
		cmd1 = "iwlist "+self.iface+" scan"
		print 'cmd',cmd1
		self.wlanscanap.ePopen(cmd1, self.iwlistfinnished,self.aplistparse)

	def iwlistfinnished(self, result, retval,extra_args):
		(statecallback) = extra_args
		try:
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
						statecallback(result)
					else:
						statecallback(0)					
				else:
					statecallback(0)
		except:
			self.close()


	def aplistparse(self,data):
		global selectap
		if data == 0:
#			self.session.openWithCallback(self.createConfig ,MessageBox, _("Scan AP Failed"), MessageBox.TYPE_INFO,2)		
			self.session.open(MessageBox, _("Scan AP Failed"), MessageBox.TYPE_INFO,2)	
		else:
			self.aplist = []
			list = data.splitlines()
#			print 'aplistparse',list
			for x in list:
				xx = x.lstrip()
				if xx.startswith('ESSID:') and len(xx)>8:
					self.aplist.append(xx[7:-1])
#			print 'rlist\n',rlist
			if len(self.aplist) ==0:
				self.aplist.append('none')
#			print 'aplist', self.aplist
			defaultap = None
			for x in self.aplist:
				if x == selectap:
					defaultap = x
			print 'defaultap',defaultap,self.aplist,selectap
			if selectap is None and self.ssid is not None and self.ssid in self.aplist:
				wlanconfig.essid = ConfigSelection(default=self.ssid,choices = self.aplist)
			elif defaultap == selectap and selectap is not None:
				wlanconfig.essid = ConfigSelection(default=selectap,choices = self.aplist)
			else:
				wlanconfig.essid = ConfigSelection(choices = self.aplist)
			
		self.createConfig()
		self["OkCancelActions"].setEnabled(True)
		self["config_actions"].setEnabled(True)
		if iNetwork.getAdapterAttribute(self.iface, "up"):
			pass
		else:
			os_system('ifconfig '+self.iface+" down")

class WlanScanAp(Screen):
	skin = """
	<screen name="WlanScanAp" position="209,48" size="865,623" title="Wireless Network Scan..." flags="wfNoBorder" backgroundColor="transparent">	
		<ePixmap pixmap="Vu_HD/Bg_EPG_view.png" zPosition="-1" position="0,0" size="865,623" alphatest="on" />
		<ePixmap pixmap="Vu_HD/menu/ico_title_Setup.png" position="32,41" size="40,40" alphatest="blend"  transparent="1" />
		<eLabel text="Wireless Network Scan..." position="90,50" size="600,32" font="Semiboldit;32" foregroundColor="#5d5d5d" backgroundColor="#27b5b9bd" transparent="1" />
		<ePixmap pixmap="Vu_HD/icons/clock.png" position="750,55" zPosition="1" size="20,20" alphatest="blend" />
		<widget source="global.CurrentTime" render="Label" position="770,57" zPosition="1" size="50,20" font="Regular;20" foregroundColor="#1c1c1c" backgroundColor="#27d9dee2" halign="right" transparent="1">
			<convert type="ClockToText">Format:%H:%M</convert>
		</widget>
		<ePixmap pixmap="Vu_HD/buttons/red.png" position="45,98" size="25,25" alphatest="blend" />
		<widget source="key_red" render="Label" position="66,97" zPosition="1" size="150,25" font="Regular;20" halign="center" valign="center" backgroundColor="darkgrey" foregroundColor="#1c1c1c" transparent="1" />
		<ePixmap pixmap="Vu_HD/border_menu.png" position="120,140" zPosition="-1" size="342,358" transparent="1" alphatest="blend" />
		<widget name="menulist" position="130,150" size="322,338" transparent="1" backgroundColor="#27d9dee2" zPosition="10" scrollbarMode="showOnDemand" />
		<widget source="ap_strength" render="Label" position="490,250" zPosition="1" size="300,30" font="Regular;20" halign="center" valign="center" backgroundColor="#27b5b9bd" foregroundColor="#1c1c1c" transparent="1" />		
		<widget source="ap_quality" render="Label" position="490,280" zPosition="1" size="300,30" font="Regular;20" halign="center" valign="center" backgroundColor="#27b5b9bd" foregroundColor="#1c1c1c" transparent="1" />		
	</screen>"""
	def __init__(self, session, iface):
		Screen.__init__(self,session)
		self.session = session
#		self.aplist = []
		self.iface = iface
		self.mainmenu = []
		self.ap_extra = []
		self.ap_quality = []
		self.wlanscanap = None
		self["OkCancelActions"] = ActionMap(["ShortcutActions", "SetupActions","WizardActions" ],
		{
			"ok": self.ok,
			"cancel": self.close,
			"red": self.close,
			"up": self.up,
			"down": self.down,
			"left": self.left,
			"right": self.right,
		}, -2)
		self.getAplist()
		print 'getAplist',self.mainmenu
		self["menulist"] = MenuList(self.mainmenu)
		self["key_red"] = StaticText(_("Close"))
		self["ap_strength"] = StaticText(_("Scanning AP List..")) 
		self["ap_quality"] = StaticText(_("Wait a moment")) 
		

	def left(self):
		self["menulist"].pageUp()
		if len(self.ap_extra) > self["menulist"].getSelectionIndex():
			self["ap_strength"].setText((self.ap_extra[self["menulist"].getSelectionIndex()])+"%") 
			self["ap_quality"].setText(self.ap_quality[self["menulist"].getSelectionIndex()]) 
	
	def right(self):
		self["menulist"].pageDown()
		if len(self.ap_extra) > self["menulist"].getSelectionIndex():
			self["ap_strength"].setText((self.ap_extra[self["menulist"].getSelectionIndex()])+"%") 
			self["ap_quality"].setText(self.ap_quality[self["menulist"].getSelectionIndex()]) 

	def up(self):
		self["menulist"].up()
		if len(self.ap_extra) > self["menulist"].getSelectionIndex():
			self["ap_strength"].setText((self.ap_extra[self["menulist"].getSelectionIndex()])+"%") 
			self["ap_quality"].setText(self.ap_quality[self["menulist"].getSelectionIndex()]) 
		
	def down(self):
		self["menulist"].down()
		if len(self.ap_extra) > self["menulist"].getSelectionIndex():
			self["ap_strength"].setText((self.ap_extra[self["menulist"].getSelectionIndex()])+"%")
			self["ap_quality"].setText(self.ap_quality[self["menulist"].getSelectionIndex()]) 		

	def ok(self):
		global selectap
		ifaces=self["menulist"].getCurrent()
		print 'select', ifaces
		selectap = ifaces
		self.close()

	def getAplist(self):
		self["OkCancelActions"].setEnabled(False)
		if iNetwork.getAdapterAttribute(self.iface, "up"):
			pass
		else:
			os_system('ifconfig '+self.iface+" up")
			time.sleep(1.5)
		self.wlanscanap = Console()
		cmd1 = "iwlist "+self.iface+" scan"
		self.wlanscanap.ePopen(cmd1, self.iwlistfinnished,self.aplistparse)

	def iwlistfinnished(self, result, retval,extra_args):
		(statecallback) = extra_args
		try:
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
						statecallback(result)
					else:
						statecallback(0)					
				else:
					statecallback(0)
		except:
			self.close()


	def aplistparse(self,data):
		rlist = []
		essid_on = 0
		if data == 0:
			self.session.open(MessageBox, _("Scan AP Failed"), MessageBox.TYPE_INFO,2)
			self["menulist"].setList(rlist)
		else:
			list = data.splitlines()
			for x in list:
				for xx in x.split():
					if xx.startswith('ESSID:') and len(xx)>8:
						rlist.append(xx[7:-1])
						essid_on = 1
					if essid_on == 1 and xx.startswith('Extra:SignalStrength=') and len(xx)>21:
						self.ap_extra.append(xx[6:])
					if essid_on == 1 and xx.startswith('%,LinkQuality:') and len(xx)>14:
						self.ap_quality.append(xx[2:])
						essid_pm = 0
			if len(rlist) >0:
				self["menulist"].setList(rlist)
				if len(self.ap_extra) > 0 and len(self.ap_quality) > 0:
					self["ap_strength"].setText((self.ap_extra[self["menulist"].getSelectionIndex()])+"%")
					self["ap_quality"].setText(self.ap_quality[self["menulist"].getSelectionIndex()]) 
				else:
					self["ap_strength"].setText("Select AP")
					self["ap_quality"].setText(" ")
		if iNetwork.getAdapterAttribute(self.iface, "up"):
			pass
		else:
			os_system('ifconfig '+self.iface+" down")
		self["OkCancelActions"].setEnabled(True)

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
			self["InfoText"].setText(_("This test detects your configured LAN-Adapter."))
			self["InfoTextBorder"].show()
			self["InfoText"].show()
			self["key_red"].setText(_("Back"))
		if self.activebutton == 2: #LAN Check
			self["InfoText"].setText(_("This test checks whether a network cable is connected to your LAN-Adapter.\nIf you get a \"disconnected\" message:\n- verify that a network cable is attached\n- verify that the cable is not broken"))
			self["InfoTextBorder"].show()
			self["InfoText"].show()
			self["key_red"].setText(_("Back"))
		if self.activebutton == 3: #DHCP Check
			self["InfoText"].setText(_("This test checks whether your LAN Adapter is set up for automatic IP Address configuration with DHCP.\nIf you get a \"disabled\" message:\n - then your LAN Adapter is configured for manual IP Setup\n- verify thay you have entered correct IP informations in the AdapterSetup dialog.\nIf you get an \"enabeld\" message:\n-verify that you have a configured and working DHCP Server in your network."))
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
			if status == "No Connection" or status == "Not-Associated" or status == False:
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
		self.apState = False
		if self.iwconfigConsole is not None:
			if retval == 0:
				self.iwconfigConsole = None
				content=result.splitlines()
				for x in content:
					if 'Access Point' in x:
						self.apState = x[x.find('Access Point')+len('Access Point'):].strip(':').strip()
				callback(self.apState)
		
class Wlanstatus(Screen):
	skin = """
	<screen name="Wlanstatus" position="209,48" size="865,623" title="Wireless Network Status..." flags="wfNoBorder" backgroundColor="transparent">	
		<ePixmap pixmap="Vu_HD/Bg_EPG_view.png" zPosition="-1" position="0,0" size="865,623" alphatest="on" />
		<ePixmap pixmap="Vu_HD/menu/ico_title_Setup.png" position="32,41" size="40,40" alphatest="blend"  transparent="1" />
		<eLabel text="Wireless Network Status..." position="90,50" size="600,32" font="Semiboldit;32" foregroundColor="#5d5d5d" backgroundColor="#27b5b9bd" transparent="1" />
		<ePixmap pixmap="Vu_HD/icons/clock.png" position="750,55" zPosition="1" size="20,20" alphatest="blend" />
		<widget source="global.CurrentTime" render="Label" position="770,57" zPosition="1" size="50,20" font="Regular;20" foregroundColor="#1c1c1c" backgroundColor="#27d9dee2" halign="right" transparent="1">
			<convert type="ClockToText">Format:%H:%M</convert>
		</widget>
		<ePixmap pixmap="Vu_HD/buttons/red.png" position="45,98" size="25,25" alphatest="blend" />
		<widget source="key_red" render="Label" position="66,97" zPosition="1" size="150,25" font="Regular;20" halign="center" valign="center" backgroundColor="darkgrey" foregroundColor="#1c1c1c" transparent="1" />
		<widget source="status" render="Label" position="110,200" size="650,400" transparent="1" font="Regular;22" foregroundColor="#1c1c1c" backgroundColor="#27d9dee2" zPosition="1" />
	</screen>"""
	def __init__(self, session,iface):
		Screen.__init__(self,session)
		self.session = session
#		self.aplist = []
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
		rlist = []		
		if data == 0:
			self["status"].setText(_("No information..."))
		else:
			self["status"].setText(data)

	def ok(self):
		pass

def openconfig(session, **kwargs):
#	session.open(WlanSetup)
	session.open(WlanSelection)

def selSetup(menuid, **kwargs):
	if menuid != "system":
		return [ ]

	return [(_("Wireless LAN Setup"), openconfig, "wlansetup_config", 80)]

def Plugins(**kwargs):
	return 	PluginDescriptor(name=_("Wireless LAN Setup"), description="Fan Control", where = PluginDescriptor.WHERE_MENU, fnc=selSetup);
#	return [PluginDescriptor(name = "Fancontrols", description = "check Fan Control settings", where = PluginDescriptor.WHERE_AUTOSTART, fnc = setfancontrol),
#	PluginDescriptor(name=_("Wireless LAN Setup"), description="Fan Control", where = PluginDescriptor.WHERE_MENU, fnc=selSetup)]
