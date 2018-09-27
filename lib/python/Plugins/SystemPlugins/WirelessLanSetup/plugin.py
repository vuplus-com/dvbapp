from Plugins.Plugin import PluginDescriptor
from Components.Network import iNetwork
from Components.config import config
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Components.ActionMap import ActionMap
from Components.ActionMap import HelpableActionMap
from Components.Sources.StaticText import StaticText
from Components.MenuList import MenuList
from enigma import eTimer
from Wlan import iWlan, iStatus, wpaSupplicant
from pythonwifi.iwlibs import Wireless
from pythonwifi import flags as wifi_flags
import copy

import os

SHOW_HIDDEN_NETWORK = False
class WlanScan(Screen, HelpableScreen):
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

			<widget name="aplist" position="20,20" size="230,275" backgroundColor="#371e1c1a" transparent="1" zPosition="10" scrollbarMode="showOnDemand" />

			<widget source="ESSID" render="Label" position="265,70" zPosition="1" size="240,30" font="Regular;18" halign="center" valign="center" />
			<widget source="Address" render="Label" position="265,100" zPosition="1" size="240,30" font="Regular;18" halign="center" valign="center" />
			<widget source="Protocol" render="Label" position="265,130" zPosition="1" size="240,30" font="Regular;18" halign="center" valign="center" />
			<widget source="Frequency" render="Label" position="265,160" zPosition="1" size="240,30" font="Regular;18" halign="center" valign="center" />
			<widget source="Channel" render="Label" position="265,190" zPosition="1" size="240,30" font="Regular;18" halign="center" valign="center" />
			<widget source="Encryption key" render="Label" position="265,220" zPosition="1" size="240,30" font="Regular;18" halign="center" valign="center" />
			<widget source="BitRate" render="Label" position="265,250" zPosition="1" size="240,30" font="Regular;18" halign="center" valign="center" />
			<widget source="Status" render="Label" position="115,310" zPosition="1" size="300,30" font="Regular;18" halign="center" valign="center" />
		</screen>
		"""
	def __init__(self, session, iface):
		Screen.__init__(self,session)
		HelpableScreen.__init__(self)
		self.skinName = "WlanScanAp"
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
			"cancel": (self.cancel, _("exit")),
			"ok": (self.ok, "select AP"),
		})

		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
		{
			"red": (self.cancel, _("exit")),
			"green": (self.ok, "select AP"),
			"blue": (self.startWlanConfig, "Edit Wireless settings"),
		})

		self["aplist"] = MenuList([])
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Select"))
		self["key_blue"] = StaticText(_("EditSetting"))
		self["Status"] = StaticText(_(" "))
		self["ESSID"] = StaticText(" ")
		self["Address"] = StaticText(" ")
		self["Protocol"] = StaticText(" ")
		self["Frequency"] = StaticText(" ")
		self["Channel"] = StaticText(" ")
		self["Encryption key"] = StaticText(" ")
		self["BitRate"] = StaticText(" ")
		self.oldInterfaceState = iNetwork.getAdapterAttribute(self.iface, "up")

		self.startupTimer = eTimer()
		self.startupTimer.callback.append(self.startup)

		self.activateIfaceTimer = eTimer()
		self.activateIfaceTimer.callback.append(self.activateIface)

		self.updateStatusTimer = eTimer()
		self.updateStatusTimer.callback.append(self.updateStatus)
		
		self.scanAplistTimer = eTimer()
		self.scanAplistTimer.callback.append(self.scanApList)
		
		self.onClose.append(self.__onClose)
		self.onShown.append(lambda: self.startupTimer.start(10, True))

	def startup(self):
		iWlan.setInterface(self.iface)
		if self.oldInterfaceState is not True:
			self["Status"].setText(("Please wait for activating interface..."))
			self.activateIfaceTimer.start(10, True)
		else:
			self.updateStatusTimer.start(10, True)

	def activateIface(self):
		iWlan.activateIface()
		self.updateStatusTimer.start(10, True)

	def updateStatus(self):
		self["Status"].setText(("Please wait for scanning AP..."))
		self.scanAplistTimer.stop()
		self.scanAplistTimer.start(10, True)

	def updateAPList(self):
		self.updateStatusTimer.stop()
		self.updateStatusTimer.start(7000, True)

	def left(self):
		self["aplist"].pageUp()
		self.displayApInfo()
	
	def right(self):
		self["aplist"].pageDown()
		self.displayApInfo()

	def up(self):
		self["aplist"].up()
		self.displayApInfo()
		
	def down(self):
		self["aplist"].down()
		self.displayApInfo()

	def ok(self):
		essid = None
		if self["aplist"].getCurrent() is not None:
			essid = self["aplist"].getCurrent()[0]
		self.close(essid)

	def cancel(self):
		self.close(None)

	def startWlanConfig(self): # key blue
		if self["aplist"].getCurrent() is not None:
			essid = self["aplist"].getCurrent()[0]
			self.close(essid)

	def scanApList(self):	
		self.apList = iWlan.getNetworkList()
		print "GET APLIST %d" % len(self.apList)
		old_aplist = self.setApList

		new_bssid_list = self.apList.keys()
		old_bssid_list = [x[1] for x in old_aplist]

		remove_bssid_list = [x for x in old_aplist if x[1] not in new_bssid_list]
		add_bssid_list = [x for x in new_bssid_list if x not in old_bssid_list]

		for x in remove_bssid_list:
			self.setApList.remove(x)

		for bssid in add_bssid_list:
			essid = self.apList[bssid].get("ESSID", None)
			if essid is None:
				global SHOW_HIDDEN_NETWORK
				if SHOW_HIDDEN_NETWORK:
					essid = "# Hidden Network"
				else:
					continue
			else:
				essid = essid.strip('\x00').strip('\\x00')
				if essid == "":
					continue
			self.setApList.append( (essid, bssid) )

		self.setApList = sorted(self.setApList, key=lambda x: int(self.apList[x[1]]['Quality'].split('/')[0]), reverse=True)

		self["aplist"].setList(self.setApList)
		self["Status"].setText(("%d AP detected" % len(self.setApList)))
		self.displayApInfo()
		self.updateAPList()

	def displayApInfo(self):
		if self["aplist"].getCurrent() is not None:
			bssid = self["aplist"].getCurrent()[1]
			for key in ["Address", "ESSID", "Protocol", "Frequency", "Encryption key", "BitRate", "Channel"]:
				if self.apList[bssid].has_key(key) and self.apList[bssid][key] is not None:
					value = str(self.apList[bssid][key])
				else:
					value = "None"
				self[key].setText(( "%s:  %s" % (key, value) ))

	def __onClose(self):
		iWlan.deActivateIface()
		iWlan.setInterface()

class WlanStatus(Screen):
	skin =  """
		<screen position="center,center" size="510,400" title="Wireless Network Status..." >
			<widget source="status" render="Label" position="5,15" size="500,350" font="Regular;18" zPosition="1" />

			<ePixmap pixmap="skin_default/buttons/red.png" position="185,360" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="185,360" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
		</screen>
		"""
	def __init__(self, session, iface):
		Screen.__init__(self,session)
		self.skinName = "Wlanstatus"
		self.session = session
		self.iface = iface

		self["actions"] = ActionMap(["ShortcutActions", "SetupActions"],
		{
			"cancel": self.close,
			"ok": self.close,
			"red": self.close,
		}, -1)

		self["status"] = StaticText(_("Reading..."))
		self["key_red"] = StaticText(_("Close"))

		self.startupTimer = eTimer()
		self.startupTimer.callback.append(self.startup)
		self.updateTimer = eTimer()
		self.updateTimer.callback.append(self.update)
		self.onClose.append(self.__onClose)
		self.onShown.append(lambda: self.startupTimer.start(10, True))

	def startup(self):
		self.update()

	def __onClose(self):
		self.updateTimer.stop()
		iStatus.stopWlanConsole()

	def update(self):
		self.updateTimer.stop()
		iStatus.getDataForInterface(self.iface, self.getInfoCB)
		self.updateTimer.start(5000, True)

	def getInfoCB(self, retval, data):
		#print "[getInfoCB] ", data
		_text = ""
		if retval and data and self.iface:
			data = data[self.iface]
			_text += "Interface : %s\n" % self.iface
			if data["frequency"]:
				_text += "Frequency : %s\n" % data["frequency"]
			elif data["channel"]:
				_text += "Channel : %s\n" % data["channel"]
			
			_text += "Access point : %s\n" % data["accesspoint"]
			_text += "Bit Rate : %s\n" % data["bitrate"]
			_text += "Link Quality : %s\n" % data["link_quality"]
			_text += "Signal level : %s\n" % data["signal_level"]
			_text += "Noise level : %s\n" % data["noise_level"]
			_text += "Ip address : %s\n" % (data["ip_addr"] or "None")
		else:
			_text += "No data\n"

		self["status"].setText(_text)

def getConfigStrings(iface):
	contents = ''
	if iNetwork.useWlCommand(iface):
		essid = config.plugins.wlan.essid.value
		encryption = config.plugins.wlan.encryption.value
		key = config.plugins.wlan.psk.value
		encryption = {"Unencrypted" : "None", "WEP" : "wep", "WPA" : "wpa", "WPA2" : "wpa2"}.get(encryption, "wpa2")
		contents = '\tpre-up wl-config.sh -m %s -k "%s" -s "%s" \n' % (encryption, key, essid)
		contents += '\tpost-down wl-down.sh\n'
	else:
		ws = wpaSupplicant()
		wpaSupplicantName = ws.getWpaSupplicantName(iface)
		contents = "\tpre-up wpa_supplicant -i"+iface+" -c%s -B -D" % (wpaSupplicantName)  +iNetwork.detectWlanModule(iface)+"\n"
		contents += "\tpost-down wpa_cli terminate\n"

	#print "[getConfigStrings] : ", contents
	return contents

def Plugins(**kwargs):
	fnc = {}
	fnc ["ifaceSupported"] = lambda iface: iNetwork.isWirelessInterface(iface) or None
	fnc ["configStrings"] = getConfigStrings
	fnc ["WlanPluginEntry"] = None

	return PluginDescriptor(name=_("Wireless LAN Setup"), description="Wireless LAN Setup", where = [PluginDescriptor.WHERE_NETWORKSETUP], fnc = fnc)
