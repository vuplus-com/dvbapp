from Plugins.Plugin import PluginDescriptor

from Screens.Screen import Screen
from Screens.ServiceScan import ServiceScan
from Screens.MessageBox import MessageBox
from Screens.DefaultWizard import DefaultWizard

from Components.Label import Label
from Components.TuneTest import Tuner
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.ActionMap import NumberActionMap, ActionMap
from Components.NimManager import nimmanager, getConfigSatlist
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigYesNo, ConfigInteger, getConfigListEntry, ConfigSlider, ConfigEnableDisable

from Tools.HardwareInfo import HardwareInfo
from Tools.Directories import resolveFilename, SCOPE_DEFAULTPARTITIONMOUNTDIR, SCOPE_DEFAULTDIR, SCOPE_DEFAULTPARTITION

from enigma import eTimer, eDVBFrontendParametersSatellite, eComponentScan, eDVBSatelliteEquipmentControl, eDVBFrontendParametersTerrestrial, eDVBFrontendParametersCable, eConsoleAppContainer, eDVBResourceManager

class SatBlindscanSearchSupport:
	def blindTransponderSearchSessionClosed(self, *val):
		self.blind_search_container.appClosed.remove(self.blindScanSearchClosed)
		self.blind_search_container.dataAvail.remove(self.getBlindTransponderData)
		if val and len(val):
			if val[0]:
				self.tlist = self.__tlist
				print self.__tlist
		if self.frontend:
			self.frontend = None
			del self.raw_channel

		self.blind_search_container.sendCtrlC()
		import time
		time.sleep(2)

		self.blind_search_container = None
		self.blind_search_container = None
		self.__tlist = None

		if self.tlist is None:
			self.tlist = []
		else:
			self.startScan(self.tlist, self.flags, self.feid)
		
	def blindScanSearchClosed(self, retval):
		self.blind_search_session.close(True)

	def getBlindTransponderData(self, str):
		str = self.remainingdata + str
		#split in lines
		lines = str.split('\n')
		#'str' should end with '\n', so when splitting, the last line should be empty. If this is not the case, we received an incomplete line
		if len(lines[-1]):
			#remember this data for next time
			self.remainingdata = lines[-1]
			lines = lines[0:-1]
		else:
			self.remainingdata = ""

		for line in lines:
			data = line.split()
			if len(data):
				print data
				if data[0] == 'OK':
					parm = eDVBFrontendParametersSatellite()
					sys = { 	"DVB-S" : eDVBFrontendParametersSatellite.System_DVB_S,
							"DVB-S2" : eDVBFrontendParametersSatellite.System_DVB_S2 	}
					qam = { 	"QPSK" : parm.Modulation_QPSK,
							"8PSK" : parm.Modulation_8PSK }
					inv = { 	"INVERSION_OFF" : parm.Inversion_Off,
							"INVERSION_ON" : parm.Inversion_On,
							"INVERSION_AUTO" : parm.Inversion_Unknown }
					fec = { 	"FEC_AUTO" : parm.FEC_Auto,
							"FEC_1_2" : parm.FEC_1_2,
							"FEC_2_3" : parm.FEC_2_3,
							"FEC_3_4" : parm.FEC_3_4,
							"FEC_5_6": parm.FEC_5_6,
							"FEC_7_8" : parm.FEC_7_8,
							"FEC_8_9" : parm.FEC_8_9,
							"FEC_3_5" : parm.FEC_3_5,
							"FEC_9_10" : parm.FEC_9_10,
							"FEC_NONE" : parm.FEC_None }
					roll = { 	"ROLLOFF_20" : parm.RollOff_alpha_0_20,
							"ROLLOFF_25" : parm.RollOff_alpha_0_25,
							"ROLLOFF_35" : parm.RollOff_alpha_0_35 }
					pilot = { 	"PILOT_ON" : parm.Pilot_On,
						  	"PILOT_OFF" : parm.Pilot_Off }
					pol = {	"HORIZONTAL" : parm.Polarisation_Horizontal,
							"VERTICAL" : parm.Polarisation_Vertical }

					sat = self.satList[0][self.scan_satselection[0].index]
					parm.orbital_position = sat[0]
					
					parm.polarisation = pol[data[1]]
					parm.frequency = int(data[2])
					parm.symbol_rate = int(data[3])
					parm.system = sys[data[4]]
					parm.inversion = inv[data[5]]
					parm.pilot = pilot[data[6]]
					parm.fec = fec[data[7]]
					parm.modulation = qam[data[8]]
					parm.rolloff = roll[data[9]]
					self.__tlist.append(parm)
					flags = None

	def openFrontend(self):
		res_mgr = eDVBResourceManager.getInstance()
		if res_mgr:
			self.raw_channel = res_mgr.allocateRawChannel(self.feid)
			if self.raw_channel:
				self.frontend = self.raw_channel.getFrontend()
				if self.frontend:
					return True
				else:
					print "getFrontend failed"
			else:
				print "getRawChannel failed"
		else:
			print "getResourceManager instance failed"
		return False

	def startSatBlindscanSearch(self, nim_idx, orbpos, session):
		if self.blindscan_start_frequency.value < 950*1000000 or self.blindscan_start_frequency.value > 2150*1000000 :
			self.session.open(MessageBox, _("Please check again.\nStart frequency must be between 950 and 2150."), MessageBox.TYPE_ERROR)
			return
		if self.blindscan_stop_frequency.value < 950*1000000 or self.blindscan_stop_frequency.value > 2150*1000000 :
			self.session.open(MessageBox, _("Please check again.\nStop frequency must be between 950 and 2150."), MessageBox.TYPE_ERROR)
			return
		if self.blindscan_start_frequency.value > self.blindscan_stop_frequency.value :
			self.session.open(MessageBox, _("Please check again.\nFrequency : start value is larger than stop value."), MessageBox.TYPE_ERROR)
			return
		if self.blindscan_start_symbol.value < 2*1000000 or self.blindscan_start_symbol.value > 45*1000000 :
			self.session.open(MessageBox, _("Please check again.\nStart symbolrate must be between 2MHz and 45MHz."), MessageBox.TYPE_ERROR)
			return
		if self.blindscan_stop_symbol.value < 2*1000000 or self.blindscan_stop_symbol.value > 45*1000000 :
			self.session.open(MessageBox, _("Please check again.\nStop symbolrate must be between 2MHz and 45MHz."), MessageBox.TYPE_ERROR)
			return
		if self.blindscan_start_symbol.value > self.blindscan_stop_symbol.value :
			self.session.open(MessageBox, _("Please check again.\nSymbolrate : start value is larger than stop value."), MessageBox.TYPE_ERROR)
			return
		
		self.__tlist = [ ]
		self.remainingdata = ""
		self.feid = nim_idx
		if not self.openFrontend():
			self.oldref = session.nav.getCurrentlyPlayingServiceReference()
			session.nav.stopService() # try to disable foreground service
			if not self.openFrontend():
				if session.pipshown: # try to disable pip
					session.pipshown = False
					del session.pip
					if not self.openFrontend():
						self.frontend = None # in normal case this should not happen

		self.tuner = Tuner(self.frontend)
		sat = self.satList[0][self.scan_satselection[0].index]

		tab_hilow		= {"high" : 1, "low" : 0}
		returnvalue 	= (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
		if tab_hilow[self.blindscan_hi.value]:
			self.scan_sat.frequency.value = 12515
		else:
			self.scan_sat.frequency.value = 11015
		returnvalue = (self.scan_sat.frequency.value,
					 0,
					 self.scan_sat.polarization.value,
					 0,
					 0,
					 int(orbpos[0]),
					 eDVBFrontendParametersSatellite.System_DVB_S,
					 0,
					 0,
					 0)
		self.tuner.tune(returnvalue)

		self.blind_search_container = eConsoleAppContainer()
		self.blind_search_container.appClosed.append(self.blindScanSearchClosed)
		self.blind_search_container.dataAvail.append(self.getBlindTransponderData)
		cmd = "/usr/lib/enigma2/python/Plugins/SystemPlugins/Blindscan/vuplus_blindscan %d %d %d %d %d %d %d" % (self.blindscan_start_frequency.value/1000000, self.blindscan_stop_frequency.value/1000000, self.blindscan_start_symbol.value/1000000, self.blindscan_stop_symbol.value/1000000, self.scan_sat.polarization.value, tab_hilow[self.blindscan_hi.value], self.feid)
		print "prepared command : ", cmd
		self.blind_search_container.execute(cmd)
		
		tmpstr = _("Blindscan takes some minute.")
		self.blind_search_session = self.session.openWithCallback(self.blindTransponderSearchSessionClosed, MessageBox, tmpstr, MessageBox.TYPE_INFO)

class Blindscan(ConfigListScreen, Screen, SatBlindscanSearchSupport):
	skin="""
		<screen name="Blindscan" position="center,center" size="560,250" title="Blindscan">
			<ePixmap pixmap="Vu_HD/buttons/red.png" position="5,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="Vu_HD/buttons/green.png" position="145,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="Vu_HD/buttons/button_off.png" position="285,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="Vu_HD/buttons/button_off.png" position="425,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="20,0" zPosition="1" size="115,30" font="Regular;20" halign="center" valign="center" transparent="1" />
			<widget source="key_green" render="Label" position="160,0" zPosition="1" size="115,30" font="Regular;20" halign="center" valign="center" transparent="1" />
			<widget name="config" position="5,50" size="550,200" scrollbarMode="showOnDemand" />
		</screen>
		"""
	def __init__(self, session): 
		Screen.__init__(self, session)

		self.updateSatList()
		self.service = session.nav.getCurrentService()
		self.current_play_service = self.session.nav.getCurrentlyPlayingServiceReference()
		self.feinfo = None
		self.networkid = 0
		frontendData = None
		if self.service is not None:
			self.feinfo = self.service.frontendInfo()
			frontendData = self.feinfo and self.feinfo.getAll(True)
		
		self.createConfig(frontendData)

		del self.feinfo
		del self.service

		self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions", "WizardActions", "ColorActions", "SetupActions", ],
		{
			"red": self.keyCancel,
			"green": self.keyGo,
			"ok": self.keyGo,
			"cancel": self.keyCancel,
		}, -2)

		self.statusTimer = eTimer()
		self.statusTimer.callback.append(self.updateStatus)

		self.list = []
		ConfigListScreen.__init__(self, self.list)
		
		self["key_red"] = StaticText(_("Exit"))
		self["key_green"] = StaticText("Start")
		
		#if not self.scan_nims.value == "":
		#	self.createSetup()
		try:
			if not self.scan_nims.value == "":
				self.createSetup()
		except:
			self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions", "WizardActions", "ColorActions", "SetupActions", ],
			{
				"red": self.keyCancel,
				"green": self.keyNone,
				"ok": self.keyNone,
				"cancel": self.keyCancel,
			}, -2)
			self["key_red"] = StaticText(_("Exit"))
			self["key_green"] = StaticText(" ")

	def keyNone(self):
		None
		
	def updateSatList(self):
		self.satList = []
		for slot in nimmanager.nim_slots:
			if slot.isCompatible("DVB-S"):
				self.satList.append(nimmanager.getSatListForNim(slot.slot))
			else:
				self.satList.append(None)

	def createConfig(self, frontendData):
		defaultSat = {
			"orbpos": 192,
			"system": eDVBFrontendParametersSatellite.System_DVB_S,
			"frequency": 11836,
			"inversion": eDVBFrontendParametersSatellite.Inversion_Unknown,
			"symbolrate": 27500,
			"polarization": eDVBFrontendParametersSatellite.Polarisation_Horizontal,
			"fec": eDVBFrontendParametersSatellite.FEC_Auto,
			"fec_s2": eDVBFrontendParametersSatellite.FEC_9_10,
			"modulation": eDVBFrontendParametersSatellite.Modulation_QPSK }
		if frontendData is not None:
			ttype = frontendData.get("tuner_type", "UNKNOWN")
			if ttype == "DVB-S":
				defaultSat["system"] = frontendData.get("system", eDVBFrontendParametersSatellite.System_DVB_S)
				defaultSat["frequency"] = frontendData.get("frequency", 0) / 1000
				defaultSat["inversion"] = frontendData.get("inversion", eDVBFrontendParametersSatellite.Inversion_Unknown)
				defaultSat["symbolrate"] = frontendData.get("symbol_rate", 0) / 1000
				defaultSat["polarization"] = frontendData.get("polarization", eDVBFrontendParametersSatellite.Polarisation_Horizontal)
				if defaultSat["system"] == eDVBFrontendParametersSatellite.System_DVB_S2:
					defaultSat["fec_s2"] = frontendData.get("fec_inner", eDVBFrontendParametersSatellite.FEC_Auto)
					defaultSat["rolloff"] = frontendData.get("rolloff", eDVBFrontendParametersSatellite.RollOff_alpha_0_35)
					defaultSat["pilot"] = frontendData.get("pilot", eDVBFrontendParametersSatellite.Pilot_Unknown)
				else:
					defaultSat["fec"] = frontendData.get("fec_inner", eDVBFrontendParametersSatellite.FEC_Auto)
				defaultSat["modulation"] = frontendData.get("modulation", eDVBFrontendParametersSatellite.Modulation_QPSK)
				defaultSat["orbpos"] = frontendData.get("orbital_position", 0)
				
		self.scan_sat = ConfigSubsection()
		self.scan_networkScan = ConfigYesNo(default = False)
		
		# blindscan add
		self.blindscan_hi = ConfigSelection(default = "low", choices = [("low", _("low")), ("high", _("high"))])

		#ConfigYesNo(default = True)
		self.blindscan_start_frequency = ConfigInteger(default = 950*1000000)
		self.blindscan_stop_frequency = ConfigInteger(default = 2150*1000000)
		self.blindscan_start_symbol = ConfigInteger(default = 2*1000000)
		self.blindscan_stop_symbol = ConfigInteger(default = 45*1000000)

		nim_list = []
		# collect all nims which are *not* set to "nothing"
		for n in nimmanager.nim_slots:
			if n.config_mode == "nothing":
				continue
			if n.config_mode == "advanced" and len(nimmanager.getSatListForNim(n.slot)) < 1:
				continue
			if n.config_mode in ("loopthrough", "satposdepends"):
				root_id = nimmanager.sec.getRoot(n.slot_id, int(n.config.connectedTo.value))
				if n.type == nimmanager.nim_slots[root_id].type: # check if connected from a DVB-S to DVB-S2 Nim or vice versa
					continue
			nim_list.append((str(n.slot), n.friendly_full_description))

		self.scan_nims = ConfigSelection(choices = nim_list)
	
		# status
		self.scan_snr = ConfigSlider()
		self.scan_snr.enabled = False
		self.scan_agc = ConfigSlider()
		self.scan_agc.enabled = False
		self.scan_ber = ConfigSlider()
		self.scan_ber.enabled = False

		# sat
		self.scan_sat.frequency = ConfigInteger(default = defaultSat["frequency"], limits = (1, 99999))
		self.scan_sat.polarization = ConfigSelection(default = defaultSat["polarization"], choices = [
			(eDVBFrontendParametersSatellite.Polarisation_Horizontal, _("horizontal")),
			(eDVBFrontendParametersSatellite.Polarisation_Vertical, _("vertical")),
			(eDVBFrontendParametersSatellite.Polarisation_CircularLeft, _("circular left")),
			(eDVBFrontendParametersSatellite.Polarisation_CircularRight, _("circular right"))])
		self.scan_scansat = {}
		for sat in nimmanager.satList:
			self.scan_scansat[sat[0]] = ConfigYesNo(default = False)
		
		self.scan_satselection = []
		for slot in nimmanager.nim_slots:
			if slot.isCompatible("DVB-S"):
				self.scan_satselection.append(getConfigSatlist(defaultSat["orbpos"], self.satList[slot.slot]))
			else:
				self.scan_satselection.append(None)
		return True
			
			
	def newConfig(self):
		cur = self["config"].getCurrent()
		print "cur is", cur
		if cur == self.tunerEntry or \
			cur == self.systemEntry or \
			(self.modulationEntry and self.systemEntry[1].value == eDVBFrontendParametersSatellite.System_DVB_S2 and cur == self.modulationEntry):
			self.createSetup()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()
		
	def updateStatus(self):
		print "updatestatus"

	def keyGo(self):
		if self.scan_nims.value == "":
			return
		tlist = []
		flags = None
		removeAll = True
		index_to_scan = int(self.scan_nims.value)
		
		if self.scan_nims == [ ]:
			self.session.open(MessageBox, _("No tuner is enabled!\nPlease setup your tuner settings before you start a service scan."), MessageBox.TYPE_ERROR)
			return

		nim = nimmanager.nim_slots[index_to_scan]
		print "nim", nim.slot
		if nim.isCompatible("DVB-S") :
			print "is compatible with DVB-S"
		else:
			print "is not compatible with DVB-S"
			return

		flags = self.scan_networkScan.value and eComponentScan.scanNetworkSearch or 0
		for x in self["config"].list:
			x[1].save()

		self.flags = flags
		self.feid = index_to_scan
		self.tlist = []
		orbpos = self.satList[index_to_scan][self.scan_satselection[index_to_scan].index]
		self.startSatBlindscanSearch(index_to_scan, orbpos, self.session)
			
	def keyCancel(self):
		for x in self["config"].list:
			x[1].cancel()
		self.session.nav.playService(self.current_play_service)
		self.close()

	def startScan(self, tlist, flags, feid, networkid = 0):
		if len(tlist):
			self.session.open(ServiceScan, [{"transponders": tlist, "feid": feid, "flags": flags, "networkid": networkid}])
		else:
			self.session.open(MessageBox, _("Nothing to scan!\nPlease setup your tuner settings before you start a service scan."), MessageBox.TYPE_ERROR)

	def createSetup(self):
		self.list = []
		self.multiscanlist = []
		index_to_scan = int(self.scan_nims.value)
		print "ID: ", index_to_scan

		self.tunerEntry = getConfigListEntry(_("Tuner"), self.scan_nims)
		self.list.append(self.tunerEntry)
		
		if self.scan_nims == [ ]:
			return
		
		self.systemEntry = None
		self.modulationEntry = None
		nim = nimmanager.nim_slots[index_to_scan]
		
		self.scan_networkScan.value = False
		if nim.isCompatible("DVB-S") :
			self.list.append(getConfigListEntry(_('Satellite'), self.scan_satselection[index_to_scan]))
			self.list.append(getConfigListEntry(_('Scan start frequency'), self.blindscan_start_frequency))
			self.list.append(getConfigListEntry(_('Scan stop frequency'), self.blindscan_stop_frequency))
			self.list.append(getConfigListEntry(_("Polarity"), self.scan_sat.polarization))
			self.list.append(getConfigListEntry(_("Scan band"), self.blindscan_hi))
			self.list.append(getConfigListEntry(_('Scan start symbolrate'), self.blindscan_start_symbol))
			self.list.append(getConfigListEntry(_('Scan stop symbolrate'), self.blindscan_stop_symbol))
			self["config"].list = self.list
			self["config"].l.setList(self.list)
		else:
		 	self.session.open(MessageBox, _("Please setup DVB-S Tuner"), MessageBox.TYPE_ERROR)


def main(session, **kwargs):
	session.open(Blindscan)
                                                           
def Plugins(**kwargs):            
	return PluginDescriptor(name=_("Blindscan"), description="scan type(DVB-S)", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main)

