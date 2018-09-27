from enigma import eTimer

from Components.config import config, ConfigSubsection, NoSave, ConfigText, ConfigYesNo, ConfigSelection, ConfigPassword
from Components.Console import Console
from Components.Network import iNetwork

from pythonwifi.iwlibs import Wireless
from pythonwifi import flags as wifi_flags

import os
import re

encryptionlist = []
encryptionlist.append(("Unencrypted", _("Unencrypted")))
encryptionlist.append(("WEP", _("WEP")))
encryptionlist.append(("WPA", _("WPA")))
encryptionlist.append(("WPA/WPA2", _("WPA or WPA2")))
encryptionlist.append(("WPA2", _("WPA2")))

config.plugins.wlan = ConfigSubsection()
config.plugins.wlan.essid = NoSave(ConfigText(default = "", fixed_size = False))
config.plugins.wlan.hiddenessid = NoSave(ConfigYesNo(default = False))
config.plugins.wlan.encryption = NoSave(ConfigSelection(encryptionlist, default = "WPA2"))
config.plugins.wlan.wepkeytype = NoSave(ConfigSelection(["ASCII", "HEX"], default = "ASCII"))
config.plugins.wlan.psk = NoSave(ConfigPassword(default = "", fixed_size = False))

def search_pattern(data, p, s):
		if not isinstance(s, list):
			s = [s]

		res = ""
		m = p.search(data)
		if m:
			data = m.group()
			for x in s:
				if x in data:
					data = data[len(x):]
					break
			res = data.strip()
		return res

class wpaSupplicant:
	def __init__(self):
		pass

	def getWlConfName(self, iface):
		return "/etc/wl.conf.%s" % iface

	def getDefaultWlConf(self):
		wsconf = {
			"ssid" : "INPUTSSID",
			"hiddenessid" : False,
			"encryption" : "WPA2",
			"wepkeytype" : "ASCII",
			"key" : "XXXXXXXX"}
		return wsconf

	def readWlConf(self, iface):
		wsconf = self.getDefaultWlConf()
		wlConfName = self.getWlConfName(iface)
		if os.path.exists(wlConfName):
			data = open(wlConfName, "r").readlines()
			for x in data:
				try:
					(key, value) = x.strip().split('=',1)
				except:
					continue

				if key == 'ssid':
					wsconf["ssid"] = value.strip()
				if key == 'method':
					wsconf["encryption"] = value.strip()
				elif key == 'key':
					wsconf["key"] = value.strip()
				else:
					continue

		#for (k,v) in wsconf.items():
		#	print "[wsconf][%s] %s" % (k , v)

		return wsconf

	def writeWlConf(self, iface):
		essid = config.plugins.wlan.essid.value
		encryption = config.plugins.wlan.encryption.value
		psk = config.plugins.wlan.psk.value

		contents = ""
		contents += "ssid="+essid+"\n"
		contents += "method="+encryption+"\n"
		contents += "key="+psk+"\n"
		#print "[writeWlConf] content = \n"+contents

		wlConfName = self.getWlConfName(iface)
		try:
			fd = open(wlConfName, "w")
		except:
			self.session.open(MessageBox, _("%s open error." % wlConfName ), type = MessageBox.TYPE_ERROR, timeout = 10)
			return False
		else:
			fd.write(contents)
			fd.close()
		return True

	def getWpaSupplicantName(self, iface):
		return "/etc/wpa_supplicant.conf.%s" % iface

	def readWpaSupplicantConf(self, iface):
		wsconf = self.getDefaultWlConf()
		wpaSupplicantName = self.getWpaSupplicantName(iface)
		try:
			if os.path.exists(wpaSupplicantName):
				wpa_conf_data = open(wpaSupplicantName, "r").readlines()
				data = {}
				for line in wpa_conf_data:
					try:
						(key, value) = line.strip().split('=',1)
					except:
						continue

					if key not in ('ssid', 'scan_ssid', 'key_mgmt', 'proto', 'wep_key0', 'psk', '#psk'):
						continue
					elif key == 'ssid':
						data[key] = value.strip('"')
					else:
						data[key] = value.strip()

				wsconf["ssid"] = data.get("ssid", "INPUTSSID")
				wsconf["hiddenessid"] = data.get("scan_ssid") == '1' and True or False

				key_mgmt = data.get("key_mgmt")
				if key_mgmt == "NONE":
					wep_key = data.get("wep_key0")

					if wep_key is None:
						wsconf["encryption"] = "Unencrypted"
					else:
						wsconf["encryption"] = "WEP"

						if wep_key.startswith('"') and wep_key.endswith('"'):
							wsconf["wepkeytype"] = "ASCII"
							wsconf["key"] = wep_key.strip('"')
						else:
							wsconf["wepkeytype"] = "HEX"
							wsconf["key"] = wep_key

				elif key_mgmt == "WPA-PSK":
					proto = data.get("proto")

					if proto == "WPA":
						wsconf["encryption"] = "WPA"
					elif proto == "RSN":
						wsconf["encryption"] = "WPA2"
					elif proto in ( "WPA RSN", "WPA WPA2"):
						wsconf["encryption"] = "WPA/WPA2"
					else:
						wsconf["encryption"] = "WPA2"

					psk = data.get("#psk")
					if psk:
						wsconf["key"] = psk.strip('"')
					else:
						wsconf["key"] = data.get("psk")
				else:
					wsconf["encryption"] = "WPA2"
		except:
			pass

#		print ""
#		for (k,v) in wsconf.items():
#			print "[wsconf][%s] %s" % (k , v)

		return wsconf

	def getWpaPhrase(self):
		essid = config.plugins.wlan.essid.value
		psk = config.plugins.wlan.psk.value
		cmd = "wpa_passphrase '%s' '%s'" % (essid, psk)
#		print cmd
		data = os.popen(cmd).readlines()
		plainpwd = None
		psk = None
		for line in data:
#			print line,
			try:
				(key, value) = line.strip().split('=',1)
			except:
				continue

			if key == '#psk':
				plainpwd = line
			elif key == 'psk':
				psk = line

		return (psk, plainpwd)

	def writeWpasupplicantConf(self, iface):
		wpaSupplicantName = self.getWpaSupplicantName(iface)
		try:
			wpafd = open(wpaSupplicantName, "w")
		except:
			self.session.open(MessageBox, _("%s open error." % wpaSupplicantName ), type = MessageBox.TYPE_ERROR, timeout = 10)
			return False

		essid = config.plugins.wlan.essid.value
		hiddenessid = config.plugins.wlan.hiddenessid.value
		encryption = config.plugins.wlan.encryption.value
		wepkeytype = config.plugins.wlan.wepkeytype.value
		psk = config.plugins.wlan.psk.value

		contents = "#WPA Supplicant Configuration by STB\n"
		contents += "ctrl_interface=/var/run/wpa_supplicant\n"
		contents += "eapol_version=1\n"
		contents += "fast_reauth=1\n"
		contents += "ap_scan=1\n"
		contents += "network={\n"
# ssid
		contents += "\tssid=\""+essid+"\"\n"
# hidden ssid
		if hiddenessid is True:
			contents += "\tscan_ssid=1\n"
		else:
			contents += "\tscan_ssid=0\n"

		if encryption == "None":
			contents += "\tkey_mgmt=NONE\n"

		elif encryption == "WEP":
			contents += "\tkey_mgmt=NONE\n"
			contents += "\twep_key0="
			if wepkeytype == "ASCII":
				contents += "\""+psk+"\"\n"
			else:
				contents += psk+"\n"

		else:
			if encryption == "WPA":
				contents += "\tkey_mgmt=WPA-PSK\n"
				contents += "\tproto=WPA\n"
				contents += "\tpairwise=CCMP TKIP\n"
				contents += "\tgroup=CCMP TKIP\n"
			elif encryption == "WPA2":
				contents += "\tkey_mgmt=WPA-PSK\n"
				contents += "\tproto=RSN\n"
				contents += "\tpairwise=CCMP TKIP\n"
				contents += "\tgroup=CCMP TKIP\n"
			else:
				contents += "\tkey_mgmt=WPA-PSK\n"
				contents += "\tproto=WPA RSN\n"
				contents += "\tpairwise=CCMP TKIP\n"
				contents += "\tgroup=CCMP TKIP\n"


			(passphrasekey, plainpwd) = self.getWpaPhrase()

#			print "plainpwd : ",plainpwd
#			print "passphrasekey : ",passphrasekey
			if passphrasekey is not None and plainpwd is not None:
				contents += plainpwd
				contents += passphrasekey
			else:
				contents += "\tpsk=%s\n" % psk

		contents += "}\n"
#		print "content = \n"+contents
		wpafd.write(contents)
		wpafd.close()

		return True

	def loadConfig(self, iface):
		if iNetwork.useWlCommand(iface):
			wsconf = self.readWlConf(iface)
		else:
			wsconf = self.readWpaSupplicantConf(iface)
		return wsconf

	def writeConfig(self, iface):
		if iNetwork.useWlCommand(iface):
			res = self.writeWlConf(iface)
		else:
			res = self.writeWpasupplicantConf(iface)

class wlanApList:
	def __init__(self, iface = None):
		self.iface = iface
		self.oldInterfaceState = None

	def setInterface(self, iface = None):
		self.iface = iface

	def getInterface(self):
		return self.iface

	def activateIface(self):
		if self.oldInterfaceState is None:
			self.oldInterfaceState = iNetwork.getAdapterAttribute(self.iface, "up")

		if self.oldInterfaceState is not True:
			os.system("ifconfig "+self.iface+" up")
			iNetwork.setAdapterAttribute(self.iface, "up", True)

			if iNetwork.useWlCommand(self.iface):
				os.system("wl up")

	def deActivateIface(self):
		if self.oldInterfaceState is not True:
			os.system("ifconfig "+self.iface+" down")
			iNetwork.setAdapterAttribute(self.iface, "up", False)

			if iNetwork.useWlCommand(self.iface):
				os.system("wl down")

		self.oldInterfaceState = None

	def getScanResult(self, wirelessObj):
		Iwscanresult  = None
		try:
			Iwscanresult  = wirelessObj.scan()
		except IOError:
			print "%s Interface doesn't support scanning.."%self.iface
		return Iwscanresult

	def getNetworkList(self):
		apList = {}
		self.activateIface()
		wirelessObj = Wireless(self.iface)
		Iwscanresult=self.getScanResult(wirelessObj)

		if Iwscanresult is None or len(Iwscanresult.aplist) == 0:
			return apList

		try:
			(num_channels, frequencies) = wirelessObj.getChannelInfo()
		except:
			pass

		for ap in Iwscanresult:
			bssid = ap.bssid
			apList[bssid] = {}
			apList[bssid]['active'] = True
			apList[bssid]['bssid'] = bssid
			apList[bssid]['essid'] = ap.essid or None

			apList[bssid]['Address'] = apList[bssid]['bssid']
			apList[bssid]['ESSID'] = apList[bssid]['essid']
			apList[bssid]['Protocol'] = ap.protocol
			apList[bssid]['Frequency'] = wirelessObj._formatFrequency(ap.frequency.getFrequency())

			channel = "Unknown"
			try:
				channel = frequencies.index(self.apList[index]["Frequency"]) + 1
			except:
				channel = "Unknown"
			apList[bssid]['Channel'] = channel

			apList[bssid]['Quality'] = "%s/%s" % ( ap.quality.quality, wirelessObj.getQualityMax().quality )
			apList[bssid]['Signal Level'] = "%s/%s" % ( ap.quality.getSignallevel(), "100" )
			apList[bssid]['Noise Level'] = "%s/%s" % ( ap.quality.getNoiselevel(), "100" )

# get encryption key on/off
			key_status = "Unknown"
			if (ap.encode.flags & wifi_flags.IW_ENCODE_DISABLED):
				key_status = "off"
			elif (ap.encode.flags & wifi_flags.IW_ENCODE_NOKEY):
				if (ap.encode.length <= 0):
					key_status = "on"
			apList[bssid]['Encryption key'] = key_status

# get bitrate
			if ap.rate and ap.rate[0]:
				apList[bssid]['BitRate'] = wirelessObj._formatBitrate(ap.rate[0][-1])
			else:
				apList[bssid]['BitRate'] = ""

#		print apList

		return apList

	def stopGetNetworkList(self):
		self.deActivateIface()

iWlan = wlanApList()

class wlanStatus:
	def __init__(self):
		self.getStatusConsole = Console()
		self.essid_pattern = re.compile('ESSID:".+" ')
		self.frequency_pattern = re.compile('Frequency:[.0-9]+ [a-zA-Z]{2,3} ')
		self.channel_pattern = re.compile('Channel:\d+ ')
		self.accesspoint_pattren = re.compile('Access Point: .+')
		self.bitrate_pattern = re.compile("Bit Rate[=:][\d.]{1,5} [GMgmb/s]{1,5}")
		self.link_quality_pattern = re.compile('Link Quality=\d+/\d+')
		self.signal_level_pattern = re.compile('Signal level=\d+/\d+')
		self.noise_level_pattern = re.compile('Noise level=\d+/\d+')
		self.signal_level_dbm_pattern = re.compile('Signal level=.+ dBm ')
		self.noise_level_dbm_pattern = re.compile('Noise level=.+ dBm')
		self.inet_addr_pattern = re.compile('inet addr:[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}')

	def stopWlanConsole(self):
		if self.getStatusConsole is not None:
			if len(self.getStatusConsole.appContainers):
				for x in self.getStatusConsole.appContainers.keys():
					self.getStatusConsole.kill(x)

	def getDataForInterface(self, iface, callback = None):
		cmd = "iwconfig "+iface
		self.getStatusConsole.ePopen(cmd, self.getStatusFinished, (callback, iface))

	def getStatusFinished(self, result, retval, extra_args):
		(callback, iface) = extra_args
		if self.getStatusConsole is not None:
			self.handleStatusData(result, retval, callback, iface)

	def handleStatusData(self, result, retval, callback, iface):
		essid = "off"
		frequency = ""
		channel = ""
		accesspoint = False
		bitrate = ""
		link_quality = "0"
		signal_level = "0"
		noise_level = "0"

		retval = retval == 0

		if retval and result:
			for x in result.split('\n'):
				essid = search_pattern(x, self.essid_pattern, 'ESSID:').strip('"') or essid
				frequency = search_pattern(x, self.frequency_pattern, 'Frequency:') or frequency
				channel = search_pattern(x, self.channel_pattern, 'Channel:') or channel
				accesspoint = search_pattern(x, self.accesspoint_pattren, 'Access Point: ') or accesspoint
				bitrate = search_pattern(x, self.bitrate_pattern, ['Bit Rate:', 'Bit Rate=']) or bitrate
				link_quality = search_pattern(x, self.link_quality_pattern, 'Link Quality=') or link_quality
				signal_level = search_pattern(x, self.signal_level_pattern, 'Signal level=') or signal_level
				noise_level = search_pattern(x, self.noise_level_pattern, 'Noise level=') or noise_level
				signal_level = search_pattern(x, self.signal_level_dbm_pattern, 'Signal level=') or signal_level
				noise_level = search_pattern(x, self.noise_level_dbm_pattern, 'Noise level=') or noise_level

		data = {}
		data[iface] = {}
		data[iface]["essid"] = essid
		data[iface]["frequency"] = frequency
		data[iface]["channel"] = channel
		data[iface]["accesspoint"] = accesspoint
		data[iface]["bitrate"] = bitrate
		data[iface]["link_quality"] = link_quality
		data[iface]["signal_level"] = signal_level
		data[iface]["noise_level"] = noise_level

		self.getIfconfigData(iface, data, callback)

		#if callback:
		#	callback(retval, data)

	def getIfconfigData(self, iface, data, callback):
		cmd = "ifconfig "+iface
		self.getStatusConsole.ePopen(cmd, self.getIfconfigDataFinished, (iface, data, callback))

	def getIfconfigDataFinished(self, result, retval, extra_args):
		if self.getStatusConsole is not None:
			self.handleIfconfigData(result, retval, extra_args)

	def handleIfconfigData(self, result, retval, extra_args):
		(iface, data, callback) = extra_args
		ipaddr = ""
		retval = retval == 0

		if retval and result:
			for x in result.split('\n'):
				ipaddr = search_pattern(x, self.inet_addr_pattern, 'inet addr:') or ipaddr

		data[iface]["ip_addr"] = ipaddr

		if callback:
			callback(retval, data)

iStatus = wlanStatus()

