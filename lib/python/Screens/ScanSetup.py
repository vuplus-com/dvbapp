from Screen import Screen
from Screens.DefaultWizard import DefaultWizard
from ServiceScan import ServiceScan
from Components.config import config, ConfigSubsection, ConfigSelection, \
	ConfigYesNo, ConfigInteger, getConfigListEntry, ConfigSlider, ConfigEnableDisable
from Components.ActionMap import NumberActionMap, ActionMap
from Components.ConfigList import ConfigListScreen
from Components.NimManager import nimmanager, getConfigSatlist
from Components.Label import Label
from Components.SystemInfo import SystemInfo
from Tools.Directories import resolveFilename, SCOPE_DEFAULTPARTITIONMOUNTDIR, SCOPE_DEFAULTDIR, SCOPE_DEFAULTPARTITION
from Tools.HardwareInfo import HardwareInfo
from Screens.MessageBox import MessageBox
from enigma import eTimer, eDVBFrontendParametersSatellite, eComponentScan, \
	eDVBSatelliteEquipmentControl, eDVBFrontendParametersTerrestrial, \
	eDVBFrontendParametersCable, eConsoleAppContainer, eDVBResourceManager

def buildTerTransponder(frequency, 
		inversion=2, bandwidth = 3, fechigh = 6, feclow = 6,
		modulation = 2, transmission = 2, guard = 4,
		hierarchy = 4, system = 0, plpid = 0):
#	print "freq", frequency, "inv", inversion, "bw", bandwidth, "fech", fechigh, "fecl", feclow, "mod", modulation, "tm", transmission, "guard", guard, "hierarchy", hierarchy
	parm = eDVBFrontendParametersTerrestrial()
	parm.frequency = frequency
	parm.inversion = inversion
	parm.bandwidth = bandwidth
	parm.code_rate_HP = fechigh
	parm.code_rate_LP = feclow
	parm.modulation = modulation
	parm.transmission_mode = transmission
	parm.guard_interval = guard
	parm.hierarchy = hierarchy
	parm.system = system
	parm.plpid = plpid
	return parm

def getInitialTransponderList(tlist, pos):
	list = nimmanager.getTransponders(pos)
	for x in list:
		if x[0] == 0:		#SAT
			parm = eDVBFrontendParametersSatellite()
			parm.frequency = x[1]
			parm.symbol_rate = x[2]
			parm.polarisation = x[3]
			parm.fec = x[4]
			parm.inversion = x[7]
			parm.orbital_position = pos
			parm.system = x[5]
			parm.modulation = x[6]
			parm.rolloff = x[8]
			parm.pilot = x[9]
			parm.is_id = x[10]
			parm.pls_mode = x[11]
			parm.pls_code = x[12]
			tlist.append(parm)

def getInitialCableTransponderList(tlist, nim):
	list = nimmanager.getTranspondersCable(nim)
	for x in list:
		if x[0] == 1: #CABLE
			parm = eDVBFrontendParametersCable()
			parm.frequency = x[1]
			parm.symbol_rate = x[2]
			parm.modulation = x[3]
			parm.fec_inner = x[4]
			parm.inversion = parm.Inversion_Unknown
			#print "frequency:", x[1]
			#print "symbol_rate:", x[2]
			#print "modulation:", x[3]
			#print "fec_inner:", x[4]
			#print "inversion:", 2
			tlist.append(parm)

def getInitialTerrestrialTransponderList(tlist, region, skip_t2 = False):
	list = nimmanager.getTranspondersTerrestrial(region)

	#self.transponders[self.parsedTer].append((2,freq,bw,const,crh,crl,guard,transm,hierarchy,inv,system,plpid))

	#def buildTerTransponder(frequency, inversion = 2, bandwidth = 3, fechigh = 6, feclow = 6,
				#modulation = 2, transmission = 2, guard = 4, hierarchy = 4, system = 0, plpid = 0):):

	for x in list:
		if x[0] == 2: #TERRESTRIAL
			if skip_t2 and x[10] == eDVBFrontendParametersTerrestrial.System_DVB_T2:
				# Should be searching on TerrestrialTransponderSearchSupport.
				continue
			parm = buildTerTransponder(x[1], x[9], x[2], x[4], x[5], x[3], x[7], x[6], x[8], x[10], x[11])
			tlist.append(parm)

cable_bands = {
	"DVBC_BAND_EU_VHF_I" : 1 << 0,
	"DVBC_BAND_EU_MID" : 1 << 1,
	"DVBC_BAND_EU_VHF_III" : 1 << 2,
	"DVBC_BAND_EU_SUPER" : 1 << 3,
	"DVBC_BAND_EU_HYPER" : 1 << 4,
	"DVBC_BAND_EU_UHF_IV" : 1 << 5,
	"DVBC_BAND_EU_UHF_V" : 1 << 6,
	"DVBC_BAND_US_LO" : 1 << 7,
	"DVBC_BAND_US_MID" : 1 << 8,
	"DVBC_BAND_US_HI" : 1 << 9,
	"DVBC_BAND_US_SUPER" : 1 << 10,
	"DVBC_BAND_US_HYPER" : 1 << 11,
}

cable_autoscan_nimtype = {
'SSH108' : 'ssh108',
'TT3L10' : 'tt3l10',
'TURBO' : 'vuplus_turbo_c',
'TURBO2' : 'vuplus_turbo2_c',
'TT2L08' : 'tt2l08',
'BCM3148' : 'bcm3148',
'BCM3158' : 'bcm3148',
}

terrestrial_autoscan_nimtype = {
'SSH108' : 'ssh108_t2_scan',
'TT3L10' : 'tt3l10_t2_scan',
'TURBO' : 'vuplus_turbo_t',
'TURBO2' : 'vuplus_turbo2_t',
'TT2L08' : 'tt2l08_t2_scan',
'BCM3466' : 'bcm3466'
}

dual_tuner_list = ('TT3L10', 'BCM3466')
vtuner_need_idx_list = ('TURBO2')

def GetDeviceId(filter, nim_idx):
	tuners={}
	device_id = 0
	socket_id = 0
	for nim in nimmanager.nim_slots:
		name_token = nim.description.split(' ')
		name = name_token[-1][4:-1]
		if name == filter:
			if socket_id == nim_idx:
				break

			if device_id:	device_id = 0
			else:			device_id = 1
		socket_id += 1
	return device_id

def getVtunerId(filter, nim_idx):
	idx_count = 1
	for slot in nimmanager.nim_slots:
		slot_idx = slot.slot
		if filter in slot.description:
			if slot_idx == nim_idx :
				return "--idx " + str(idx_count)
			else:
				idx_count += 1
	return ""

def GetTerrestrial5VEnable(nim_idx):
	nim = nimmanager.nim_slots[nim_idx]
	return int(nim.config.terrestrial_5V.value)

class CableTransponderSearchSupport:
#	def setCableTransponderSearchResult(self, tlist):
#		pass

#	def cableTransponderSearchFinished(self):
#		pass

	def tryGetRawFrontend(self, feid):
		res_mgr = eDVBResourceManager.getInstance()
		if res_mgr:
			raw_channel = res_mgr.allocateRawChannel(self.feid)
			if raw_channel:
				frontend = raw_channel.getFrontend()
				if frontend:
					frontend.closeFrontend() # immediate close... 
					del frontend
					del raw_channel
					return True
		return False

	def cableTransponderSearchSessionClosed(self, *val):
		print "cableTransponderSearchSessionClosed, val", val
		self.cable_search_container.appClosed.remove(self.cableTransponderSearchClosed)
		self.cable_search_container.dataAvail.remove(self.getCableTransponderData)
		if val and len(val):
			if val[0]:
				self.setCableTransponderSearchResult(self.__tlist)
			else:
				self.cable_search_container.sendCtrlC()
				self.setCableTransponderSearchResult(None)
		self.cable_search_container = None
		self.cable_search_session = None
		self.__tlist = None
		self.cableTransponderSearchFinished()

	def cableTransponderSearchClosed(self, retval):
		print "cableTransponderSearch finished", retval
		self.cable_search_session.close(True)

	def getCableTransponderData(self, str):
		data = str.split()
		if len(data):
			if data[0] == 'OK':
				print str
				parm = eDVBFrontendParametersCable()
				qam = { "QAM16" : parm.Modulation_QAM16,
					"QAM32" : parm.Modulation_QAM32,
					"QAM64" : parm.Modulation_QAM64,
					"QAM128" : parm.Modulation_QAM128,
					"QAM256" : parm.Modulation_QAM256 }
				inv = { "INVERSION_OFF" : parm.Inversion_Off,
					"INVERSION_ON" : parm.Inversion_On,
					"INVERSION_AUTO" : parm.Inversion_Unknown }
				fec = { "FEC_AUTO" : parm.FEC_Auto,
					"FEC_1_2" : parm.FEC_1_2,
					"FEC_2_3" : parm.FEC_2_3,
					"FEC_3_4" : parm.FEC_3_4,
					"FEC_5_6": parm.FEC_5_6,
					"FEC_7_8" : parm.FEC_7_8,
					"FEC_8_9" : parm.FEC_8_9,
					"FEC_NONE" : parm.FEC_None }
				parm.frequency = int(data[1])
				parm.symbol_rate = int(data[2])
				parm.fec_inner = fec[data[3]]
				parm.modulation = qam[data[4]]
				parm.inversion = inv[data[5]]
				self.__tlist.append(parm)
			tmpstr = _("Try to find used Transponders in cable network.. please wait...")
			tmpstr += "\n\n"
			tmpstr += data[1]
			tmpstr += " kHz "
			tmpstr += data[0]
			self.cable_search_session["text"].setText(tmpstr)

	def startCableTransponderSearch(self, nim_idx):
		def GetCommand(nim_idx):
			global cable_autoscan_nimtype
			try:
				nim_name = nimmanager.getNimName(nim_idx)
				if nim_name is not None and nim_name != "":
					device_id = ""
					nim_name = nim_name.strip(':VTUNER').split(' ')[-1][4:-1]
					if nim_name == 'TT3L10':
						try:
							device_id = GetDeviceId('TT3L10', nim_idx)
							device_id = "--device=%s" % (device_id)
						except Exception, err:
							print "GetCommand ->", err
							device_id = "--device=0"
#						print nim_idx, nim_name, cable_autoscan_nimtype[nim_name], device_id
					elif nim_name in vtuner_need_idx_list:
						device_id = getVtunerId(nim_name, nim_idx)
					command = "%s %s" % (cable_autoscan_nimtype[nim_name], device_id)
					return command
			except Exception, err:
				print "GetCommand ->", err
			return "tda1002x"

		if not self.tryGetRawFrontend(nim_idx):
			self.session.nav.stopService()
			if not self.tryGetRawFrontend(nim_idx):
				if self.session.pipshown: # try to disable pip
					self.session.pipshown = False
					del self.session.pip
				if not self.tryGetRawFrontend(nim_idx):
					self.cableTransponderSearchFinished()
					return
		self.__tlist = [ ]
		self.cable_search_container = eConsoleAppContainer()
		self.cable_search_container.appClosed.append(self.cableTransponderSearchClosed)
		self.cable_search_container.dataAvail.append(self.getCableTransponderData)
		cableConfig = config.Nims[nim_idx].cable
		tunername = nimmanager.getNimName(nim_idx)
		bus = nimmanager.getI2CDevice(nim_idx)
		if bus is None:
			print "ERROR: could not get I2C device for nim", nim_idx, "for cable transponder search"
			bus = 2

		if tunername == "CXD1981":
			cmd = "cxd1978 --init --scan --verbose --wakeup --inv 2 --bus %d" % bus
		else:
			bin_name = GetCommand(nim_idx)
			cmd = "%(BIN_NAME)s --init --scan --verbose --wakeup --inv 2 --bus %(BUS)d" % {'BIN_NAME':bin_name , 'BUS':bus}

		if cableConfig.scan_type.value == "bands":
			cmd += " --scan-bands "
			bands = 0
			if cableConfig.scan_band_EU_VHF_I.value:
				bands |= cable_bands["DVBC_BAND_EU_VHF_I"]
			if cableConfig.scan_band_EU_MID.value:
				bands |= cable_bands["DVBC_BAND_EU_MID"]
			if cableConfig.scan_band_EU_VHF_III.value:
				bands |= cable_bands["DVBC_BAND_EU_VHF_III"]
			if cableConfig.scan_band_EU_UHF_IV.value:
				bands |= cable_bands["DVBC_BAND_EU_UHF_IV"]
			if cableConfig.scan_band_EU_UHF_V.value:
				bands |= cable_bands["DVBC_BAND_EU_UHF_V"]
			if cableConfig.scan_band_EU_SUPER.value:
				bands |= cable_bands["DVBC_BAND_EU_SUPER"]
			if cableConfig.scan_band_EU_HYPER.value:
				bands |= cable_bands["DVBC_BAND_EU_HYPER"]
			if cableConfig.scan_band_US_LOW.value:
				bands |= cable_bands["DVBC_BAND_US_LO"]
			if cableConfig.scan_band_US_MID.value:
				bands |= cable_bands["DVBC_BAND_US_MID"]
			if cableConfig.scan_band_US_HIGH.value:
				bands |= cable_bands["DVBC_BAND_US_HI"]
			if cableConfig.scan_band_US_SUPER.value:
				bands |= cable_bands["DVBC_BAND_US_SUPER"]
			if cableConfig.scan_band_US_HYPER.value:
				bands |= cable_bands["DVBC_BAND_US_HYPER"]
			cmd += str(bands)
		else:
			cmd += " --scan-stepsize "
			cmd += str(cableConfig.scan_frequency_steps.value)
		if cableConfig.scan_mod_qam16.value:
			cmd += " --mod 16"
		if cableConfig.scan_mod_qam32.value:
			cmd += " --mod 32"
		if cableConfig.scan_mod_qam64.value:
			cmd += " --mod 64"
		if cableConfig.scan_mod_qam128.value:
			cmd += " --mod 128"
		if cableConfig.scan_mod_qam256.value:
			cmd += " --mod 256"
		if cableConfig.scan_sr_6900.value:
			cmd += " --sr 6900000"
		if cableConfig.scan_sr_6875.value:
			cmd += " --sr 6875000"
		if cableConfig.scan_sr_ext1.value > 450:
			cmd += " --sr "
			cmd += str(cableConfig.scan_sr_ext1.value)
			cmd += "000"
		if cableConfig.scan_sr_ext2.value > 450:
			cmd += " --sr "
			cmd += str(cableConfig.scan_sr_ext2.value)
			cmd += "000"
		print bin_name, " CMD is", cmd

		self.cable_search_container.execute(cmd)
		tmpstr = _("Try to find used transponders in cable network.. please wait...")
		tmpstr += "\n\n..."
		self.cable_search_session = self.session.openWithCallback(self.cableTransponderSearchSessionClosed, MessageBox, tmpstr, MessageBox.TYPE_INFO)

class TerrestrialTransponderSearchSupport:
#	def setTerrestrialTransponderSearchResult(self, tlist):
#		pass

#	def terrestrialTransponderSearchFinished(self):
#		pass

	def terrestrialTransponderSearchSessionClosed(self, *val):
		print "TerrestrialTransponderSearchSessionClosed, val", val
		self.terrestrial_search_container.appClosed.remove(self.terrestrialTransponderSearchClosed)
		self.terrestrial_search_container.dataAvail.remove(self.getTerrestrialTransponderData)
		if val and len(val):
			if val[0]:
				self.setTerrestrialTransponderSearchResult(self.__tlist)
			else:
				self.terrestrial_search_container.sendCtrlC()
				self.setTerrestrialTransponderSearchResult(None)
		self.terrestrial_search_container = None
		self.terrestrial_search_session = None
		self.__tlist = None
		self.terrestrialTransponderSearchFinished()

	def terrestrialTransponderSearchClosed(self, retval):
		self.setTerrestrialTransponderData()
		opt = self.terrestrialTransponderGetOpt()
		if opt is None:
			print "terrestrialTransponderSearch finished", retval
			self.terrestrial_search_session.close(True)
		else:
			(freq, bandWidth) = opt
			self.terrestrialTransponderSearch(freq, bandWidth)

	def getTerrestrialTransponderData(self, str):
		self.terrestrial_search_data += str

	def setTerrestrialTransponderData(self):
		print self.terrestrial_search_data
		data = self.terrestrial_search_data.split()
		if len(data):
#			print "[setTerrestrialTransponderData] data : ", data
			if data[0] == 'OK':
				# DVB-T : OK frequency bandwidth delivery system -1
				# DVB-T2 : OK frequency bandwidth delivery system number_of_plp plp_id0:plp_type0
				if data[3] == 1: # DVB-T
					parm = eDVBFrontendParametersTerrestrial()
					parm.frequency = int(data[1])
					parm.bandwidth = int(data[2])
					parm.inversion = parm.Inversion_Unknown
					parm.code_rate_HP = parm.FEC_Auto
					parm.code_rate_LP = parm.FEC_Auto
					parm.modulation = parm.Modulation_Auto
					parm.transmission_mode = parm.TransmissionMode_Auto
					parm.guard_interval = parm.GuardInterval_Auto
					parm.hierarchy = parm.Hierarchy_Auto
					parm.system = parm.System_DVB_T
					parm.plpid = 0
					self.__tlist.append(parm)
				else:
					plp_list = data[5:]
					plp_num = int(data[4])
					if len(plp_list) > plp_num:
						plp_list = plp_list[:plp_num]
					for plp in plp_list:
						(plp_id, plp_type) = plp.split(':')
						if plp_type == '0': # common PLP:
							continue
						parm = eDVBFrontendParametersTerrestrial()
						parm.frequency = int(data[1])
						parm.bandwidth = self.terrestrialTransponderconvBandwidth_P(int(data[2]))
						parm.inversion = parm.Inversion_Unknown
						parm.code_rate_HP = parm.FEC_Auto
						parm.code_rate_LP = parm.FEC_Auto
						parm.modulation = parm.Modulation_Auto
						parm.transmission_mode = parm.TransmissionMode_Auto
						parm.guard_interval = parm.GuardInterval_Auto
						parm.hierarchy = parm.Hierarchy_Auto
						parm.system = parm.System_DVB_T2
						parm.plpid = int(plp_id)
						self.__tlist.append(parm)

			tmpstr = _("Try to find used Transponders in terrestrial network.. please wait...")
			tmpstr += "\n\n"
			tmpstr += data[1][:-3]
			tmpstr += " kHz "
			tmpstr += data[0]
			self.terrestrial_search_session["text"].setText(tmpstr)

	def terrestrialTransponderInitSearchList(self, searchList, region):
		tpList = nimmanager.getTranspondersTerrestrial(region)
		for x in tpList:
			if x[0] == 2: #TERRESTRIAL
				freq = x[1] # frequency
				bandWidth = self.terrestrialTransponderConvBandwidth_I(x[2]) # bandWidth
				parm = (freq, bandWidth)
				searchList.append(parm)

	def terrestrialTransponderConvBandwidth_I(self, _bandWidth):
		bandWidth = {
			eDVBFrontendParametersTerrestrial.Bandwidth_8MHz : 8000000,
			eDVBFrontendParametersTerrestrial.Bandwidth_7MHz : 7000000,
			eDVBFrontendParametersTerrestrial.Bandwidth_6MHz : 6000000,
			eDVBFrontendParametersTerrestrial.Bandwidth_5MHz : 5000000,
			eDVBFrontendParametersTerrestrial.Bandwidth_1_712MHz : 1712000,
			eDVBFrontendParametersTerrestrial.Bandwidth_10MHz : 10000000,
		}.get(_bandWidth, 8000000)
		return bandWidth

	def terrestrialTransponderconvBandwidth_P(self, _bandWidth):
		bandWidth = {
			8000000 : eDVBFrontendParametersTerrestrial.Bandwidth_8MHz,
			7000000 : eDVBFrontendParametersTerrestrial.Bandwidth_7MHz,
			6000000 : eDVBFrontendParametersTerrestrial.Bandwidth_6MHz,
			5000000 : eDVBFrontendParametersTerrestrial.Bandwidth_5MHz,
			1712000 : eDVBFrontendParametersTerrestrial.Bandwidth_1_712MHz,
			10000000 : eDVBFrontendParametersTerrestrial.Bandwidth_10MHz,
		}.get(_bandWidth, eDVBFrontendParametersTerrestrial.Bandwidth_8MHz)
		return bandWidth

	def terrestrialTransponderGetOpt(self):
		if len(self.terrestrial_search_list) > 0:
			return self.terrestrial_search_list.pop(0)
		else:
			return None

	def terrestrialTransponderGetCmd(self, nim_idx):
		global terrestrial_autoscan_nimtype
		try:
			nim_name = nimmanager.getNimName(nim_idx)
			if nim_name is not None and nim_name != "":
				device_id = ""
				nim_name = nim_name.strip(':VTUNER').split(' ')[-1][4:-1]
				if nim_name in dual_tuner_list:
					try:
						device_id = GetDeviceId(nim_name, nim_idx)
						device_id = "--device %s" % (device_id)
					except Exception, err:
						print "terrestrialTransponderGetCmd ->", err
						device_id = "--device 0"
#					print nim_idx, nim_name, terrestrial_autoscan_nimtype[nim_name], device_id
				elif nim_name in vtuner_need_idx_list:
					device_id = getVtunerId(nim_name, nim_idx)
				command = "%s %s" % (terrestrial_autoscan_nimtype[nim_name], device_id)
				return command
		except Exception, err:
			print "terrestrialTransponderGetCmd ->", err
		return ""

	def startTerrestrialTransponderSearch(self, nim_idx, region):
		if not self.tryGetRawFrontend(nim_idx):
			self.session.nav.stopService()
			if not self.tryGetRawFrontend(nim_idx):
				if self.session.pipshown: # try to disable pip
					self.session.pipshown = False
					del self.session.pip
				if not self.tryGetRawFrontend(nim_idx):
					self.terrestrialTransponderSearchFinished()
					return
		self.__tlist = [ ]
		self.terrestrial_search_container = eConsoleAppContainer()
		self.terrestrial_search_container.appClosed.append(self.terrestrialTransponderSearchClosed)
		self.terrestrial_search_container.dataAvail.append(self.getTerrestrialTransponderData)

		self.terrestrial_search_binName = self.terrestrialTransponderGetCmd(nim_idx)

		self.terrestrial_search_bus = nimmanager.getI2CDevice(nim_idx)
		if self.terrestrial_search_bus is None:
#			print "ERROR: could not get I2C device for nim", nim_idx, "for terrestrial transponder search"
			self.terrestrial_search_bus = 2

		self.terrestrial_search_feid = nim_idx
		self.terrestrial_search_enable_5v = GetTerrestrial5VEnable(nim_idx)

		self.terrestrial_search_list = []
		self.terrestrialTransponderInitSearchList(self.terrestrial_search_list ,region)
		(freq, bandWidth) = self.terrestrialTransponderGetOpt()
		self.terrestrialTransponderSearch(freq, bandWidth)

		tmpstr = _("Try to find used transponders in terrestrial network.. please wait...")
		tmpstr += "\n\n..."
		self.terrestrial_search_session = self.session.openWithCallback(self.terrestrialTransponderSearchSessionClosed, MessageBox, tmpstr, MessageBox.TYPE_INFO)

	def terrestrialTransponderSearch(self, freq, bandWidth):
		self.terrestrial_search_data = ""
		cmd = "%s --freq %d --bw %d --bus %d --ds 2" % (self.terrestrial_search_binName, freq, bandWidth, self.terrestrial_search_bus)
		if self.terrestrial_search_enable_5v:
			cmd += " --feid %d --5v %d" % (self.terrestrial_search_feid, self.terrestrial_search_enable_5v)
		print "SCAN CMD : ",cmd
		self.terrestrial_search_container.execute(cmd)

class DefaultSatLists(DefaultWizard):
	def __init__(self, session, silent = True, showSteps = False):
		self.xmlfile = "defaultsatlists.xml"
		DefaultWizard.__init__(self, session, silent, showSteps, neededTag = "services")
		print "configuredSats:", nimmanager.getConfiguredSats()

	def setDirectory(self):
		self.directory = []
		self.directory.append(resolveFilename(SCOPE_DEFAULTDIR))
		import os
		os.system("mount %s %s" % (resolveFilename(SCOPE_DEFAULTPARTITION), resolveFilename(SCOPE_DEFAULTPARTITIONMOUNTDIR)))
		self.directory.append(resolveFilename(SCOPE_DEFAULTPARTITIONMOUNTDIR))
				
	def statusCallback(self, status, progress):
		print "statusCallback:", status, progress
		from Components.DreamInfoHandler import DreamInfoHandler
		if status == DreamInfoHandler.STATUS_DONE:
			self["text"].setText(_("The installation of the default services lists is finished.") + "\n\n" + _("Please press OK to continue."))
			self.markDone()
			self.disableKeys = False	

class ScanSetup(ConfigListScreen, Screen, CableTransponderSearchSupport, TerrestrialTransponderSearchSupport):
	def __init__(self, session):
		Screen.__init__(self, session)

		self.finished_cb = None
		self.updateSatList()
		self.service = session.nav.getCurrentService()
		self.feinfo = None
		frontendData = None
		if self.service is not None:
			self.feinfo = self.service.frontendInfo()
			frontendData = self.feinfo and self.feinfo.getAll(True)
		
		self.createConfig(frontendData)

		del self.feinfo
		del self.service

		self["actions"] = NumberActionMap(["SetupActions"],
		{
			"ok": self.keyGo,
			"cancel": self.keyCancel,
		}, -2)

		self.statusTimer = eTimer()
		self.statusTimer.callback.append(self.updateStatus)
		#self.statusTimer.start(5000, True)

		self.list = []
		ConfigListScreen.__init__(self, self.list)
		if not self.scan_nims.value == "":
			self.createSetup()
			self["introduction"] = Label(_("Press OK to start the scan"))
		else:
			self["introduction"] = Label(_("Nothing to scan!\nPlease setup your tuner settings before you start a service scan."))

	def runAsync(self, finished_cb):
		self.finished_cb = finished_cb
		self.keyGo()

	def updateSatList(self):
		self.satList = []
		for slot in nimmanager.nim_slots:
			if slot.isCompatible("DVB-S"):
				self.satList.append(nimmanager.getSatListForNim(slot.slot))
			else:
				self.satList.append(None)

	def createSetup(self):
		self.list = []
		self.multiscanlist = []
		index_to_scan = int(self.scan_nims.value)
		print "ID: ", index_to_scan

		self.tunerEntry = getConfigListEntry(_("Tuner"), self.scan_nims)
		self.list.append(self.tunerEntry)
		
		if self.scan_nims == [ ]:
			return
		
		self.typeOfScanEntry = None
		self.systemEntry = None
		self.modulationEntry = None
		self.is_id_boolEntry = None
		self.plsModeEntry = None
		nim = nimmanager.nim_slots[index_to_scan]
		if nim.isCompatible("DVB-S"):
			self.typeOfScanEntry = getConfigListEntry(_("Type of scan"), self.scan_type)
			self.list.append(self.typeOfScanEntry)
		elif nim.isCompatible("DVB-C"):
			self.typeOfScanEntry = getConfigListEntry(_("Type of scan"), self.scan_typecable)
			self.list.append(self.typeOfScanEntry)
		elif nim.isCompatible("DVB-T"):
			self.typeOfScanEntry = getConfigListEntry(_("Type of scan"), self.scan_typeterrestrial)
			self.list.append(self.typeOfScanEntry)

		self.scan_networkScan.value = False
		if nim.isCompatible("DVB-S"):
			if self.scan_type.value == "single_transponder":
				self.updateSatList()

				scan_sat_system_value = self.scan_sat.system.value
				if nim.isCompatible("DVB-S2X"):
					scan_sat_system_value = self.scan_sat.system_dvbs2x.value
					self.systemEntry = getConfigListEntry(_('System'), self.scan_sat.system_dvbs2x)
					self.list.append(self.systemEntry)
				elif nim.isCompatible("DVB-S2"):
					self.systemEntry = getConfigListEntry(_('System'), self.scan_sat.system)
					self.list.append(self.systemEntry)
				else:
					# downgrade to dvb-s, in case a -s2 config was active
					self.scan_sat.system.value = eDVBFrontendParametersSatellite.System_DVB_S
				self.list.append(getConfigListEntry(_('Satellite'), self.scan_satselection[index_to_scan]))
				self.list.append(getConfigListEntry(_('Frequency'), self.scan_sat.frequency))
				self.list.append(getConfigListEntry(_('Inversion'), self.scan_sat.inversion))
				self.list.append(getConfigListEntry(_('Symbol rate'), self.scan_sat.symbolrate))
				self.list.append(getConfigListEntry(_('Polarization'), self.scan_sat.polarization))

				if scan_sat_system_value == eDVBFrontendParametersSatellite.System_DVB_S2:
					self.modulationEntry = getConfigListEntry(_('Modulation'), self.scan_sat.modulation)
					self.list.append(self.modulationEntry)
					self.list.append(getConfigListEntry(_('Roll-off'), self.scan_sat.rolloff))
					self.list.append(getConfigListEntry(_('Pilot'), self.scan_sat.pilot))
				elif scan_sat_system_value == eDVBFrontendParametersSatellite.System_DVB_S2X:
					self.modulationEntry = getConfigListEntry(_('Modulation'), self.scan_sat.modulation_dvbs2x)
					self.list.append(self.modulationEntry)
					self.list.append(getConfigListEntry(_('Roll-off'), self.scan_sat.rolloff))
					self.list.append(getConfigListEntry(_('Pilot'), self.scan_sat.pilot))

				if scan_sat_system_value == eDVBFrontendParametersSatellite.System_DVB_S:
					self.list.append(getConfigListEntry(_("FEC"), self.scan_sat.fec))
				elif scan_sat_system_value == eDVBFrontendParametersSatellite.System_DVB_S2:
					self.list.append(getConfigListEntry(_("FEC"), self.scan_sat.fec_s2))
				elif scan_sat_system_value == eDVBFrontendParametersSatellite.System_DVB_S2X:
					if self.scan_sat.modulation_dvbs2x.value == eDVBFrontendParametersSatellite.Modulation_QPSK:
						self.list.append(getConfigListEntry(_("FEC"), self.scan_sat.fec_s2x_qpsk))
					elif self.scan_sat.modulation_dvbs2x.value == eDVBFrontendParametersSatellite.Modulation_8PSK:
						self.list.append(getConfigListEntry(_("FEC"), self.scan_sat.fec_s2x_8psk))
					elif self.scan_sat.modulation_dvbs2x.value == eDVBFrontendParametersSatellite.Modulation_8APSK:
						self.list.append(getConfigListEntry(_("FEC"), self.scan_sat.fec_s2x_8apsk))
					elif self.scan_sat.modulation_dvbs2x.value == eDVBFrontendParametersSatellite.Modulation_16APSK:
						self.list.append(getConfigListEntry(_("FEC"), self.scan_sat.fec_s2x_16apsk))
					elif self.scan_sat.modulation_dvbs2x.value == eDVBFrontendParametersSatellite.Modulation_32APSK:
						self.list.append(getConfigListEntry(_("FEC"), self.scan_sat.fec_s2x_32apsk))

				if scan_sat_system_value in (eDVBFrontendParametersSatellite.System_DVB_S2, eDVBFrontendParametersSatellite.System_DVB_S2X):
					if nim.isMultistream():
						self.is_id_boolEntry = getConfigListEntry(_('Transport Stream Type'), self.scan_sat.is_id_bool)
						self.list.append(self.is_id_boolEntry)
						if self.scan_sat.is_id_bool.value:
							self.list.append(getConfigListEntry(_('Input Stream ID'), self.scan_sat.is_id))
							self.plsModeEntry = getConfigListEntry(_('PLS Mode'), self.scan_sat.pls_mode)
							self.list.append(self.plsModeEntry)
							if self.scan_sat.pls_mode.value != eDVBFrontendParametersSatellite.PLS_Unknown:
								self.list.append(getConfigListEntry(_('PLS Code'), self.scan_sat.pls_code))

			elif self.scan_type.value == "single_satellite":
				self.updateSatList()
				print self.scan_satselection[index_to_scan]
				self.list.append(getConfigListEntry(_("Satellite"), self.scan_satselection[index_to_scan]))
				self.scan_networkScan.value = True
			elif self.scan_type.value.find("multisat") != -1:
				tlist = []
				SatList = nimmanager.getSatListForNim(index_to_scan)
				for x in SatList:
					if self.Satexists(tlist, x[0]) == 0:
						tlist.append(x[0])
						sat = ConfigEnableDisable(default = self.scan_type.value.find("_yes") != -1 and True or False)
						configEntry = getConfigListEntry(nimmanager.getSatDescription(x[0]), sat)
						self.list.append(configEntry)
						self.multiscanlist.append((x[0], sat))
				self.scan_networkScan.value = True
		elif nim.isCompatible("DVB-C"):
			if self.scan_typecable.value == "single_transponder":
				self.list.append(getConfigListEntry(_("Frequency"), self.scan_cab.frequency))
				self.list.append(getConfigListEntry(_("Inversion"), self.scan_cab.inversion))
				self.list.append(getConfigListEntry(_("Symbol rate"), self.scan_cab.symbolrate))
				self.list.append(getConfigListEntry(_("Modulation"), self.scan_cab.modulation))
				self.list.append(getConfigListEntry(_("FEC"), self.scan_cab.fec))
		elif nim.isCompatible("DVB-T"):
			if self.scan_typeterrestrial.value == "single_transponder":
				if nim.isCompatible("DVB-T2"):
					self.systemEntry = getConfigListEntry(_('System'), self.scan_ter.system)
					self.list.append(self.systemEntry)
				else:
					self.scan_ter.system.value = eDVBFrontendParametersTerrestrial.System_DVB_T
				if self.scan_ter.system.value == eDVBFrontendParametersTerrestrial.System_DVB_T:
					self.list.append(getConfigListEntry(_("Frequency"), self.scan_ter.frequency))
					self.list.append(getConfigListEntry(_("Inversion"), self.scan_ter.inversion))
					self.list.append(getConfigListEntry(_("Bandwidth"), self.scan_ter.bandwidth))
					self.list.append(getConfigListEntry(_("Code rate HP"), self.scan_ter.fechigh))
					self.list.append(getConfigListEntry(_("Code rate LP"), self.scan_ter.feclow))
					self.list.append(getConfigListEntry(_("Modulation"), self.scan_ter.modulation))
					self.list.append(getConfigListEntry(_("Transmission mode"), self.scan_ter.transmission))
					self.list.append(getConfigListEntry(_("Guard interval"), self.scan_ter.guard))
					self.list.append(getConfigListEntry(_("Hierarchy info"), self.scan_ter.hierarchy))
				else: # DVB-T2
					self.list.append(getConfigListEntry(_("Frequency"), self.scan_ter.frequency))
					self.list.append(getConfigListEntry(_("Inversion"), self.scan_ter.inversion))
					self.list.append(getConfigListEntry(_("Bandwidth"), self.scan_ter.bandwidth_t2))
					self.list.append(getConfigListEntry(_("Code rate HP"), self.scan_ter.fechigh_t2))
					self.list.append(getConfigListEntry(_("Code rate LP"), self.scan_ter.feclow_t2))
					self.list.append(getConfigListEntry(_("Modulation"), self.scan_ter.modulation_t2))
					self.list.append(getConfigListEntry(_("Transmission mode"), self.scan_ter.transmission_t2))
					self.list.append(getConfigListEntry(_("Guard interval"), self.scan_ter.guard_t2))
					self.list.append(getConfigListEntry(_("Hierarchy info"), self.scan_ter.hierarchy))
					self.list.append(getConfigListEntry(_('PLP ID'), self.scan_ter.plp_id))
		self.list.append(getConfigListEntry(_("Network scan"), self.scan_networkScan))
		self.list.append(getConfigListEntry(_("Clear before scan"), self.scan_clearallservices))
		self.list.append(getConfigListEntry(_("Only Free scan"), self.scan_onlyfree))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def Satexists(self, tlist, pos):
		for x in tlist:
			if x == pos:
				return 1
		return 0

	def newConfig(self):
		cur = self["config"].getCurrent()
		print "cur is", cur
		if cur is None:
			return

		if cur == self.typeOfScanEntry or \
			cur == self.tunerEntry or \
			cur == self.systemEntry or \
			(self.modulationEntry and \
			(self.systemEntry[1].value in (eDVBFrontendParametersSatellite.System_DVB_S2, eDVBFrontendParametersSatellite.System_DVB_S2X)) and \
			cur == self.modulationEntry) or \
			cur == self.is_id_boolEntry or \
			cur == self.plsModeEntry:
			self.createSetup()

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
				"fec_s2x_qpsk": eDVBFrontendParametersSatellite.FEC_13_45,
				"fec_s2x_8psk": eDVBFrontendParametersSatellite.FEC_23_36,
				"fec_s2x_8apsk": eDVBFrontendParametersSatellite.FEC_5_9_L,
				"fec_s2x_16apsk": eDVBFrontendParametersSatellite.FEC_1_2_L,
				"fec_s2x_32apsk": eDVBFrontendParametersSatellite.FEC_2_3_L,
				"modulation": eDVBFrontendParametersSatellite.Modulation_QPSK,
				"modulation_s2x": eDVBFrontendParametersSatellite.Modulation_QPSK,
				"is_id": -1,
				"pls_mode": eDVBFrontendParametersSatellite.PLS_Unknown,
				"pls_code": 0 }
			defaultCab = {
				"frequency": 466,
				"inversion": eDVBFrontendParametersCable.Inversion_Unknown,
				"modulation": eDVBFrontendParametersCable.Modulation_QAM64,
				"fec": eDVBFrontendParametersCable.FEC_Auto,
				"symbolrate": 6900 }
			defaultTer = {
				"frequency" : 466000,
				"inversion" : eDVBFrontendParametersTerrestrial.Inversion_Unknown,
				"bandwidth" : eDVBFrontendParametersTerrestrial.Bandwidth_7MHz,
				"fechigh" : eDVBFrontendParametersTerrestrial.FEC_Auto,
				"feclow" : eDVBFrontendParametersTerrestrial.FEC_Auto,
				"modulation" : eDVBFrontendParametersTerrestrial.Modulation_Auto,
				"transmission_mode" : eDVBFrontendParametersTerrestrial.TransmissionMode_Auto,
				"guard_interval" : eDVBFrontendParametersTerrestrial.GuardInterval_Auto,
				"hierarchy": eDVBFrontendParametersTerrestrial.Hierarchy_Auto,
				"system": eDVBFrontendParametersTerrestrial.System_DVB_T,
				"plp_id": 0 }

			if frontendData is not None:
				ttype = frontendData.get("tuner_type", "UNKNOWN")
				if ttype == "DVB-S":
					defaultSat["system"] = frontendData.get("system", eDVBFrontendParametersSatellite.System_DVB_S)
					defaultSat["frequency"] = frontendData.get("frequency", 0) / 1000
					defaultSat["inversion"] = frontendData.get("inversion", eDVBFrontendParametersSatellite.Inversion_Unknown)
					defaultSat["symbolrate"] = frontendData.get("symbol_rate", 0) / 1000
					defaultSat["polarization"] = frontendData.get("polarization", eDVBFrontendParametersSatellite.Polarisation_Horizontal)
					defaultSat["orbpos"] = frontendData.get("orbital_position", 0)

					defaultSat["modulation"] = frontendData.get("modulation", eDVBFrontendParametersSatellite.Modulation_QPSK)
					defaultSat["modulation_s2x"] = frontendData.get("modulation", eDVBFrontendParametersSatellite.Modulation_QPSK)

					if defaultSat["modulation"] > eDVBFrontendParametersSatellite.Modulation_8PSK:
						defaultSat["modulation"] = eDVBFrontendParametersSatellite.Modulation_8PSK

					if defaultSat["system"] == eDVBFrontendParametersSatellite.System_DVB_S2:
						defaultSat["fec_s2"] = frontendData.get("fec_inner", eDVBFrontendParametersSatellite.FEC_Auto)
					elif defaultSat["system"] == eDVBFrontendParametersSatellite.System_DVB_S2X:
						if defaultSat["modulation_s2x"] == eDVBFrontendParametersSatellite.Modulation_QPSK:
							defaultSat["fec_s2x_qpsk"] = frontendData.get("fec_inner", eDVBFrontendParametersSatellite.FEC_13_45)
						elif defaultSat["modulation_s2x"] == eDVBFrontendParametersSatellite.Modulation_8PSK:
							defaultSat["fec_s2x_8psk"] = frontendData.get("fec_inner", eDVBFrontendParametersSatellite.FEC_23_36)
						elif defaultSat["modulation_s2x"] == eDVBFrontendParametersSatellite.Modulation_8APSK:
							defaultSat["fec_s2x_8apsk"] = frontendData.get("fec_inner", eDVBFrontendParametersSatellite.FEC_5_9_L)
						elif defaultSat["modulation_s2x"] == eDVBFrontendParametersSatellite.Modulation_16APSK:
							defaultSat["fec_s2x_16apsk"] = frontendData.get("fec_inner", eDVBFrontendParametersSatellite.FEC_1_2_L)
						elif defaultSat["modulation_s2x"] == eDVBFrontendParametersSatellite.Modulation_32APSK:
							defaultSat["fec_s2x_32apsk"] = frontendData.get("fec_inner", eDVBFrontendParametersSatellite.FEC_2_3_L)
					else:
						defaultSat["fec"] = frontendData.get("fec_inner", eDVBFrontendParametersSatellite.FEC_Auto)

					if defaultSat["system"] in (eDVBFrontendParametersSatellite.System_DVB_S2, eDVBFrontendParametersSatellite.System_DVB_S2X):
						defaultSat["rolloff"] = frontendData.get("rolloff", eDVBFrontendParametersSatellite.RollOff_alpha_0_35)
						defaultSat["pilot"] = frontendData.get("pilot", eDVBFrontendParametersSatellite.Pilot_Unknown)
						defaultSat["is_id"] = frontendData.get("is_id", defaultSat["is_id"])
						defaultSat["pls_mode"] = frontendData.get("pls_mode", defaultSat["pls_mode"])
						defaultSat["pls_code"] = frontendData.get("pls_code", defaultSat["pls_code"])

				elif ttype == "DVB-C":
					defaultCab["frequency"] = frontendData.get("frequency", 0) / 1000
					defaultCab["symbolrate"] = frontendData.get("symbol_rate", 0) / 1000
					defaultCab["inversion"] = frontendData.get("inversion", eDVBFrontendParametersCable.Inversion_Unknown)
					defaultCab["fec"] = frontendData.get("fec_inner", eDVBFrontendParametersCable.FEC_Auto)
					defaultCab["modulation"] = frontendData.get("modulation", eDVBFrontendParametersCable.Modulation_QAM16)
				elif ttype == "DVB-T":
					defaultTer["frequency"] = frontendData.get("frequency", 0) / 1000
					defaultTer["inversion"] = frontendData.get("inversion", eDVBFrontendParametersTerrestrial.Inversion_Unknown)
					defaultTer["bandwidth"] = frontendData.get("bandwidth", eDVBFrontendParametersTerrestrial.Bandwidth_7MHz)
					defaultTer["fechigh"] = frontendData.get("code_rate_hp", eDVBFrontendParametersTerrestrial.FEC_Auto)
					defaultTer["feclow"] = frontendData.get("code_rate_lp", eDVBFrontendParametersTerrestrial.FEC_Auto)
					defaultTer["modulation"] = frontendData.get("constellation", eDVBFrontendParametersTerrestrial.Modulation_Auto)
					defaultTer["transmission_mode"] = frontendData.get("transmission_mode", eDVBFrontendParametersTerrestrial.TransmissionMode_Auto)
					defaultTer["guard_interval"] = frontendData.get("guard_interval", eDVBFrontendParametersTerrestrial.GuardInterval_Auto)
					defaultTer["hierarchy"] = frontendData.get("hierarchy_information", eDVBFrontendParametersTerrestrial.Hierarchy_Auto)
					defaultTer["system"] = frontendData.get("system", eDVBFrontendParametersTerrestrial.System_DVB_T)
					defaultTer["plp_id"] = frontendData.get("plp_id", 0)

			self.scan_sat = ConfigSubsection()
			self.scan_cab = ConfigSubsection()
			self.scan_ter = ConfigSubsection()

			self.scan_type = ConfigSelection(default = "single_transponder", choices = [("single_transponder", _("Single transponder")), ("single_satellite", _("Single satellite")), ("multisat", _("Multisat")), ("multisat_yes", _("Multisat"))])
			self.scan_typecable = ConfigSelection(default = "single_transponder", choices = [("single_transponder", _("Single transponder")), ("complete", _("Complete"))])
			self.scan_typeterrestrial = ConfigSelection(default = "single_transponder", choices = [("single_transponder", _("Single transponder")), ("complete", _("Complete"))])
			self.scan_clearallservices = ConfigSelection(default = "no", choices = [("no", _("no")), ("yes", _("yes")), ("yes_hold_feeds", _("yes (keep feeds)"))])
			self.scan_onlyfree = ConfigYesNo(default = False)
			self.scan_networkScan = ConfigYesNo(default = False)

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
			sat_choices = [
				(eDVBFrontendParametersSatellite.System_DVB_S, _("DVB-S")),
				(eDVBFrontendParametersSatellite.System_DVB_S2, _("DVB-S2"))]

			sat_choices_dvbs2x = [
				(eDVBFrontendParametersSatellite.System_DVB_S, _("DVB-S")),
				(eDVBFrontendParametersSatellite.System_DVB_S2, _("DVB-S2")),
				(eDVBFrontendParametersSatellite.System_DVB_S2X, _("DVB-S2X"))]

			default_sat_system = defaultSat["system"]
			if default_sat_system not in sat_choices:
				default_sat_system = eDVBFrontendParametersSatellite.System_DVB_S

			self.scan_sat.system = ConfigSelection(default = default_sat_system, choices = sat_choices)
			self.scan_sat.system_dvbs2x = ConfigSelection(default = defaultSat["system"], choices = sat_choices_dvbs2x)
			self.scan_sat.frequency = ConfigInteger(default = defaultSat["frequency"], limits = (1, 99999))
			self.scan_sat.inversion = ConfigSelection(default = defaultSat["inversion"], choices = [
				(eDVBFrontendParametersSatellite.Inversion_Off, _("Off")),
				(eDVBFrontendParametersSatellite.Inversion_On, _("On")),
				(eDVBFrontendParametersSatellite.Inversion_Unknown, _("Auto"))])
			self.scan_sat.symbolrate = ConfigInteger(default = defaultSat["symbolrate"], limits = (1, 99999))
			self.scan_sat.polarization = ConfigSelection(default = defaultSat["polarization"], choices = [
				(eDVBFrontendParametersSatellite.Polarisation_Horizontal, _("horizontal")),
				(eDVBFrontendParametersSatellite.Polarisation_Vertical, _("vertical")),
				(eDVBFrontendParametersSatellite.Polarisation_CircularLeft, _("circular left")),
				(eDVBFrontendParametersSatellite.Polarisation_CircularRight, _("circular right"))])
			self.scan_sat.fec = ConfigSelection(default = defaultSat["fec"], choices = [
				(eDVBFrontendParametersSatellite.FEC_Auto, _("Auto")),
				(eDVBFrontendParametersSatellite.FEC_1_2, "1/2"),
				(eDVBFrontendParametersSatellite.FEC_2_3, "2/3"),
				(eDVBFrontendParametersSatellite.FEC_3_4, "3/4"),
				(eDVBFrontendParametersSatellite.FEC_5_6, "5/6"),
				(eDVBFrontendParametersSatellite.FEC_7_8, "7/8"),
				(eDVBFrontendParametersSatellite.FEC_None, _("None"))])
			self.scan_sat.fec_s2 = ConfigSelection(default = defaultSat["fec_s2"], choices = [
				(eDVBFrontendParametersSatellite.FEC_1_2, "1/2"),
				(eDVBFrontendParametersSatellite.FEC_2_3, "2/3"),
				(eDVBFrontendParametersSatellite.FEC_3_4, "3/4"),
				(eDVBFrontendParametersSatellite.FEC_3_5, "3/5"),
				(eDVBFrontendParametersSatellite.FEC_4_5, "4/5"),
				(eDVBFrontendParametersSatellite.FEC_5_6, "5/6"),
				(eDVBFrontendParametersSatellite.FEC_7_8, "7/8"),
				(eDVBFrontendParametersSatellite.FEC_8_9, "8/9"),
				(eDVBFrontendParametersSatellite.FEC_9_10, "9/10")])

			self.scan_sat.fec_s2x_qpsk = ConfigSelection(default = defaultSat["fec_s2x_qpsk"], choices = [
				(eDVBFrontendParametersSatellite.FEC_13_45, "13/45"),
				(eDVBFrontendParametersSatellite.FEC_9_20, "9/20"),
				(eDVBFrontendParametersSatellite.FEC_11_20, "11/20")])

			self.scan_sat.fec_s2x_8psk = ConfigSelection(default = defaultSat["fec_s2x_8psk"], choices = [
				(eDVBFrontendParametersSatellite.FEC_23_36, "23/36"),
				(eDVBFrontendParametersSatellite.FEC_25_36, "25/36"),
				(eDVBFrontendParametersSatellite.FEC_13_18, "13/28")])

			self.scan_sat.fec_s2x_8apsk = ConfigSelection(default = defaultSat["fec_s2x_8apsk"], choices = [
				(eDVBFrontendParametersSatellite.FEC_5_9_L, "5/9-L"),
				(eDVBFrontendParametersSatellite.FEC_26_45_L, "26/45-L")])

			self.scan_sat.fec_s2x_16apsk = ConfigSelection(default = defaultSat["fec_s2x_16apsk"], choices = [
				(eDVBFrontendParametersSatellite.FEC_1_2_L, "1/2-L"),
				(eDVBFrontendParametersSatellite.FEC_8_15_L, "8/15-L"),
				(eDVBFrontendParametersSatellite.FEC_5_9_L, "5/9-L"),
				(eDVBFrontendParametersSatellite.FEC_26_45, "26/45"),
				(eDVBFrontendParametersSatellite.FEC_3_5, "3/5"),
				(eDVBFrontendParametersSatellite.FEC_3_5_L, "3/5-L"),
				(eDVBFrontendParametersSatellite.FEC_28_45, "28/45"),
				(eDVBFrontendParametersSatellite.FEC_23_36, "23/36"),
				(eDVBFrontendParametersSatellite.FEC_2_3_L, "2/3-L"),
				(eDVBFrontendParametersSatellite.FEC_25_36, "25/36"),
				(eDVBFrontendParametersSatellite.FEC_13_18, "13/18"),
				(eDVBFrontendParametersSatellite.FEC_7_9, "7/9"),
				(eDVBFrontendParametersSatellite.FEC_77_90, "77/90")])

			self.scan_sat.fec_s2x_32apsk = ConfigSelection(default = defaultSat["fec_s2x_32apsk"], choices = [
				(eDVBFrontendParametersSatellite.FEC_2_3_L, "2/3-L"),
				(eDVBFrontendParametersSatellite.FEC_32_45, "32/45"),
				(eDVBFrontendParametersSatellite.FEC_11_15, "11/15"),
				(eDVBFrontendParametersSatellite.FEC_7_9, "7/9")])

			self.scan_sat.modulation = ConfigSelection(default = defaultSat["modulation"], choices = [
				(eDVBFrontendParametersSatellite.Modulation_QPSK, "QPSK"),
				(eDVBFrontendParametersSatellite.Modulation_8PSK, "8PSK")])
			self.scan_sat.modulation_dvbs2x = ConfigSelection(default = defaultSat["modulation_s2x"], choices = [
				(eDVBFrontendParametersSatellite.Modulation_QPSK, "QPSK"),
				(eDVBFrontendParametersSatellite.Modulation_8PSK, "8PSK"),
				(eDVBFrontendParametersSatellite.Modulation_8APSK, "8APSK"),
				(eDVBFrontendParametersSatellite.Modulation_16APSK, "16APSK"),
				(eDVBFrontendParametersSatellite.Modulation_32APSK, "32APSK")])
			self.scan_sat.rolloff = ConfigSelection(default = defaultSat.get("rolloff", eDVBFrontendParametersSatellite.RollOff_alpha_0_35), choices = [
				(eDVBFrontendParametersSatellite.RollOff_alpha_0_35, "0.35"),
				(eDVBFrontendParametersSatellite.RollOff_alpha_0_25, "0.25"),
				(eDVBFrontendParametersSatellite.RollOff_alpha_0_20, "0.20")])
			self.scan_sat.pilot = ConfigSelection(default = defaultSat.get("pilot", eDVBFrontendParametersSatellite.Pilot_Unknown), choices = [
				(eDVBFrontendParametersSatellite.Pilot_Off, _("Off")),
				(eDVBFrontendParametersSatellite.Pilot_On, _("On")),
				(eDVBFrontendParametersSatellite.Pilot_Unknown, _("Auto"))])
			self.scan_sat.is_id = ConfigInteger(default = defaultSat["is_id"] if defaultSat["is_id"] != -1 else 0, limits = (0, 255))
			self.scan_sat.is_id_bool = ConfigSelection(default = defaultSat["is_id"] != -1, choices = [(True, _("Multistream")),(False, _("Ordinary"))])
			self.scan_sat.pls_mode = ConfigSelection(default = defaultSat["pls_mode"], choices = [
				(eDVBFrontendParametersSatellite.PLS_Root, _("Root")),
				(eDVBFrontendParametersSatellite.PLS_Gold, _("Gold")),
				(eDVBFrontendParametersSatellite.PLS_Combo, _("Combo")),
				(eDVBFrontendParametersSatellite.PLS_Unknown, _("Auto"))])
			self.scan_sat.pls_code = ConfigInteger(default = defaultSat["pls_code"], limits = (0, 262143))

			# cable
			self.scan_cab.frequency = ConfigInteger(default = defaultCab["frequency"], limits = (50, 999))
			self.scan_cab.inversion = ConfigSelection(default = defaultCab["inversion"], choices = [
				(eDVBFrontendParametersCable.Inversion_Off, _("Off")),
				(eDVBFrontendParametersCable.Inversion_On, _("On")),
				(eDVBFrontendParametersCable.Inversion_Unknown, _("Auto"))])
			self.scan_cab.modulation = ConfigSelection(default = defaultCab["modulation"], choices = [
				(eDVBFrontendParametersCable.Modulation_QAM16, "16-QAM"),
				(eDVBFrontendParametersCable.Modulation_QAM32, "32-QAM"),
				(eDVBFrontendParametersCable.Modulation_QAM64, "64-QAM"),
				(eDVBFrontendParametersCable.Modulation_QAM128, "128-QAM"),
				(eDVBFrontendParametersCable.Modulation_QAM256, "256-QAM")])
			self.scan_cab.fec = ConfigSelection(default = defaultCab["fec"], choices = [
				(eDVBFrontendParametersCable.FEC_Auto, _("Auto")),
				(eDVBFrontendParametersCable.FEC_1_2, "1/2"),
				(eDVBFrontendParametersCable.FEC_2_3, "2/3"),
				(eDVBFrontendParametersCable.FEC_3_4, "3/4"),
				(eDVBFrontendParametersCable.FEC_5_6, "5/6"),
				(eDVBFrontendParametersCable.FEC_7_8, "7/8"),
				(eDVBFrontendParametersCable.FEC_8_9, "8/9"),
				(eDVBFrontendParametersCable.FEC_None, _("None"))])
			self.scan_cab.symbolrate = ConfigInteger(default = defaultCab["symbolrate"], limits = (1, 99999))

			# terrestial
			self.scan_ter.frequency = ConfigInteger(default = defaultTer["frequency"], limits = (50000, 999000))
			self.scan_ter.inversion = ConfigSelection(default = defaultTer["inversion"], choices = [
				(eDVBFrontendParametersTerrestrial.Inversion_Off, _("Off")),
				(eDVBFrontendParametersTerrestrial.Inversion_On, _("On")),
				(eDVBFrontendParametersTerrestrial.Inversion_Unknown, _("Auto"))])
			# WORKAROUND: we can't use BW-auto
			self.scan_ter.bandwidth = ConfigSelection(default = defaultTer["bandwidth"], choices = [
				(eDVBFrontendParametersTerrestrial.Bandwidth_8MHz, "8MHz"),
				(eDVBFrontendParametersTerrestrial.Bandwidth_7MHz, "7MHz"),
				(eDVBFrontendParametersTerrestrial.Bandwidth_6MHz, "6MHz")])
			self.scan_ter.bandwidth_t2 = ConfigSelection(default = defaultTer["bandwidth"], choices = [
				(eDVBFrontendParametersTerrestrial.Bandwidth_10MHz, "10MHz"),
				(eDVBFrontendParametersTerrestrial.Bandwidth_8MHz, "8MHz"),
				(eDVBFrontendParametersTerrestrial.Bandwidth_7MHz, "7MHz"),
				(eDVBFrontendParametersTerrestrial.Bandwidth_6MHz, "6MHz"),
				(eDVBFrontendParametersTerrestrial.Bandwidth_5MHz, "5MHz"),
				(eDVBFrontendParametersTerrestrial.Bandwidth_1_712MHz, "1.712MHz")])
			#, (eDVBFrontendParametersTerrestrial.Bandwidth_Auto, _("Auto"))))
			self.scan_ter.fechigh = ConfigSelection(default = defaultTer["fechigh"], choices = [
				(eDVBFrontendParametersTerrestrial.FEC_1_2, "1/2"),
				(eDVBFrontendParametersTerrestrial.FEC_2_3, "2/3"),
				(eDVBFrontendParametersTerrestrial.FEC_3_4, "3/4"),
				(eDVBFrontendParametersTerrestrial.FEC_5_6, "5/6"),
				(eDVBFrontendParametersTerrestrial.FEC_7_8, "7/8"),
				(eDVBFrontendParametersTerrestrial.FEC_Auto, _("Auto"))])
			self.scan_ter.fechigh_t2 = ConfigSelection(default = defaultTer["fechigh"], choices = [
				(eDVBFrontendParametersTerrestrial.FEC_1_2, "1/2"),
				(eDVBFrontendParametersTerrestrial.FEC_2_3, "2/3"),
				(eDVBFrontendParametersTerrestrial.FEC_3_4, "3/4"),
				(eDVBFrontendParametersTerrestrial.FEC_5_6, "5/6"),
				(eDVBFrontendParametersTerrestrial.FEC_6_7, "6/7"),
				(eDVBFrontendParametersTerrestrial.FEC_7_8, "7/8"),
				(eDVBFrontendParametersTerrestrial.FEC_8_9, "8/9"),
				(eDVBFrontendParametersTerrestrial.FEC_Auto, _("Auto"))])
			self.scan_ter.feclow = ConfigSelection(default = defaultTer["feclow"], choices = [
				(eDVBFrontendParametersTerrestrial.FEC_1_2, "1/2"),
				(eDVBFrontendParametersTerrestrial.FEC_2_3, "2/3"),
				(eDVBFrontendParametersTerrestrial.FEC_3_4, "3/4"),
				(eDVBFrontendParametersTerrestrial.FEC_5_6, "5/6"),
				(eDVBFrontendParametersTerrestrial.FEC_7_8, "7/8"),
				(eDVBFrontendParametersTerrestrial.FEC_Auto, _("Auto"))])
			self.scan_ter.feclow_t2 = ConfigSelection(default = defaultTer["feclow"], choices = [
				(eDVBFrontendParametersTerrestrial.FEC_1_2, "1/2"),
				(eDVBFrontendParametersTerrestrial.FEC_2_3, "2/3"),
				(eDVBFrontendParametersTerrestrial.FEC_3_4, "3/4"),
				(eDVBFrontendParametersTerrestrial.FEC_5_6, "5/6"),
				(eDVBFrontendParametersTerrestrial.FEC_6_7, "6/7"),
				(eDVBFrontendParametersTerrestrial.FEC_7_8, "7/8"),
				(eDVBFrontendParametersTerrestrial.FEC_8_9, "8/9"),
				(eDVBFrontendParametersTerrestrial.FEC_Auto, _("Auto"))])
			self.scan_ter.modulation = ConfigSelection(default = defaultTer["modulation"], choices = [
				(eDVBFrontendParametersTerrestrial.Modulation_QPSK, "QPSK"),
				(eDVBFrontendParametersTerrestrial.Modulation_QAM16, "QAM16"),
				(eDVBFrontendParametersTerrestrial.Modulation_QAM64, "QAM64"),
				(eDVBFrontendParametersTerrestrial.Modulation_Auto, _("Auto"))])
			self.scan_ter.modulation_t2 = ConfigSelection(default = defaultTer["modulation"], choices = [
				(eDVBFrontendParametersTerrestrial.Modulation_QPSK, "QPSK"),
				(eDVBFrontendParametersTerrestrial.Modulation_QAM16, "QAM16"),
				(eDVBFrontendParametersTerrestrial.Modulation_QAM64, "QAM64"),
				(eDVBFrontendParametersTerrestrial.Modulation_QAM256, "QAM256"),
				(eDVBFrontendParametersTerrestrial.Modulation_Auto, _("Auto"))])
			self.scan_ter.transmission = ConfigSelection(default = defaultTer["transmission_mode"], choices = [
				(eDVBFrontendParametersTerrestrial.TransmissionMode_2k, "2K"),
				(eDVBFrontendParametersTerrestrial.TransmissionMode_8k, "8K"),
				(eDVBFrontendParametersTerrestrial.TransmissionMode_Auto, _("Auto"))])
			self.scan_ter.transmission_t2 = ConfigSelection(default = defaultTer["transmission_mode"], choices = [
				(eDVBFrontendParametersTerrestrial.TransmissionMode_1k, "1K"),
				(eDVBFrontendParametersTerrestrial.TransmissionMode_2k, "2K"),
				(eDVBFrontendParametersTerrestrial.TransmissionMode_4k, "4K"),
				(eDVBFrontendParametersTerrestrial.TransmissionMode_8k, "8K"),
				(eDVBFrontendParametersTerrestrial.TransmissionMode_16k, "16K"),
				(eDVBFrontendParametersTerrestrial.TransmissionMode_32k, "32K"),
				(eDVBFrontendParametersTerrestrial.TransmissionMode_Auto, _("Auto"))])
			self.scan_ter.guard = ConfigSelection(default = defaultTer["guard_interval"], choices = [
				(eDVBFrontendParametersTerrestrial.GuardInterval_1_32, "1/32"),
				(eDVBFrontendParametersTerrestrial.GuardInterval_1_16, "1/16"),
				(eDVBFrontendParametersTerrestrial.GuardInterval_1_8, "1/8"),
				(eDVBFrontendParametersTerrestrial.GuardInterval_1_4, "1/4"),
				(eDVBFrontendParametersTerrestrial.GuardInterval_Auto, _("Auto"))])
			self.scan_ter.guard_t2 = ConfigSelection(default = defaultTer["guard_interval"], choices = [
				(eDVBFrontendParametersTerrestrial.GuardInterval_19_256, "19/256"),
				(eDVBFrontendParametersTerrestrial.GuardInterval_19_128, "19/128"),
				(eDVBFrontendParametersTerrestrial.GuardInterval_1_128, "1/128"),
				(eDVBFrontendParametersTerrestrial.GuardInterval_1_32, "1/32"),
				(eDVBFrontendParametersTerrestrial.GuardInterval_1_16, "1/16"),
				(eDVBFrontendParametersTerrestrial.GuardInterval_1_8, "1/8"),
				(eDVBFrontendParametersTerrestrial.GuardInterval_1_4, "1/4"),
				(eDVBFrontendParametersTerrestrial.GuardInterval_Auto, _("Auto"))])
			self.scan_ter.hierarchy = ConfigSelection(default = defaultTer["hierarchy"], choices = [
				(eDVBFrontendParametersTerrestrial.Hierarchy_None, _("None")),
				(eDVBFrontendParametersTerrestrial.Hierarchy_1, "1"),
				(eDVBFrontendParametersTerrestrial.Hierarchy_2, "2"),
				(eDVBFrontendParametersTerrestrial.Hierarchy_4, "4"),
				(eDVBFrontendParametersTerrestrial.Hierarchy_Auto, _("Auto"))])
			self.scan_ter.system = ConfigSelection(default = defaultTer["system"], choices = [
				(eDVBFrontendParametersTerrestrial.System_DVB_T, _("DVB-T")),
				(eDVBFrontendParametersTerrestrial.System_DVB_T2, _("DVB-T2"))])
			self.scan_ter.plp_id = ConfigInteger(default = defaultTer["plp_id"], limits = (0, 255))

			self.scan_scansat = {}
			for sat in nimmanager.satList:
				#print sat[1]
				self.scan_scansat[sat[0]] = ConfigYesNo(default = False)

			self.scan_satselection = []
			for slot in nimmanager.nim_slots:
				if slot.isCompatible("DVB-S"):
					self.scan_satselection.append(getConfigSatlist(defaultSat["orbpos"], self.satList[slot.slot]))
				else:
					self.scan_satselection.append(None)

			return True

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()

	def updateStatus(self):
		print "updatestatus"

	def addSatTransponder(self, tlist, frequency, symbol_rate, polarisation, fec, inversion, orbital_position, system, modulation, rolloff, pilot, is_id, pls_mode, pls_code):
		print "Add Sat: frequ: " + str(frequency) + " symbol: " + str(symbol_rate) + " pol: " + str(polarisation) + " fec: " + str(fec) + " inversion: " + str(inversion) + " modulation: " + str(modulation) + " system: " + str(system) + " rolloff" + str(rolloff) + " pilot" + str(pilot) + " is_id" + str(is_id) + " pls_mode" + str(pls_mode) + " pls_code" + str(pls_code)
		print "orbpos: " + str(orbital_position)
		parm = eDVBFrontendParametersSatellite()
		parm.modulation = modulation
		parm.system = system
		parm.frequency = frequency * 1000
		parm.symbol_rate = symbol_rate * 1000
		parm.polarisation = polarisation
		parm.fec = fec
		parm.inversion = inversion
		parm.orbital_position = orbital_position
		parm.rolloff = rolloff
		parm.pilot = pilot
		parm.is_id = is_id
		parm.pls_mode = pls_mode
		parm.pls_code = pls_code
		tlist.append(parm)

	def addCabTransponder(self, tlist, frequency, symbol_rate, modulation, fec, inversion):
		print "Add Cab: frequ: " + str(frequency) + " symbol: " + str(symbol_rate) + " pol: " + str(modulation) + " fec: " + str(fec) + " inversion: " + str(inversion)
		parm = eDVBFrontendParametersCable()
		parm.frequency = frequency * 1000
		parm.symbol_rate = symbol_rate * 1000
		parm.modulation = modulation
		parm.fec = fec
		parm.inversion = inversion
		tlist.append(parm)

	def addTerTransponder(self, tlist, *args, **kwargs):
		tlist.append(buildTerTransponder(*args, **kwargs))

	def keyGo(self):
		START_SCAN =0
		SEARCH_CABLE_TRANSPONDERS = 1
		SEARCH_TERRESTRIAL2_TRANSPONDERS = 2

		if self.scan_nims.value == "":
			return
		tlist = []
		flags = None
		action = START_SCAN
		removeAll = True
		index_to_scan = int(self.scan_nims.value)
		
		if self.scan_nims == [ ]:
			self.session.open(MessageBox, _("No tuner is enabled!\nPlease setup your tuner settings before you start a service scan."), MessageBox.TYPE_ERROR)
			return

		nim = nimmanager.nim_slots[index_to_scan]
		print "nim", nim.slot
		if nim.isCompatible("DVB-S"):
			print "is compatible with DVB-S"
			if self.scan_type.value == "single_transponder":
				# these lists are generated for each tuner, so this has work.
				assert len(self.satList) > index_to_scan
				assert len(self.scan_satselection) > index_to_scan
				
				nimsats = self.satList[index_to_scan]
				selsatidx = self.scan_satselection[index_to_scan].index

				modulation = self.scan_sat.modulation.value
				# however, the satList itself could be empty. in that case, "index" is 0 (for "None").
				if len(nimsats):
					orbpos = nimsats[selsatidx][0]

					system = self.scan_sat.system.value
					if nim.isCompatible("DVB-S2X"):
						system = self.scan_sat.system_dvbs2x.value

					if system == eDVBFrontendParametersSatellite.System_DVB_S:
						fec = self.scan_sat.fec.value
					elif system == eDVBFrontendParametersSatellite.System_DVB_S2:
						fec = self.scan_sat.fec_s2.value
					elif system == eDVBFrontendParametersSatellite.System_DVB_S2X:
						modulation = self.scan_sat.modulation_dvbs2x.value
						if modulation == eDVBFrontendParametersSatellite.Modulation_QPSK:
							fec = self.scan_sat.fec_s2x_qpsk.value
						elif modulation == eDVBFrontendParametersSatellite.Modulation_8PSK:
							fec = self.scan_sat.fec_s2x_8psk.value
						elif modulation == eDVBFrontendParametersSatellite.Modulation_8APSK:
							fec = self.scan_sat.fec_s2x_8apsk.value
						elif modulation == eDVBFrontendParametersSatellite.Modulation_16APSK:
							fec = self.scan_sat.fec_s2x_16apsk.value
						elif modulation == eDVBFrontendParametersSatellite.Modulation_32APSK:
							fec = self.scan_sat.fec_s2x_32apsk.value
					else:
						fec = self.scan_sat.fec_s2.value

					is_id = -1
					pls_mode = eDVBFrontendParametersSatellite.PLS_Unknown
					pls_code = 0
					if self.scan_sat.is_id_bool.value:
						is_id = self.scan_sat.is_id.value
						pls_mode = self.scan_sat.pls_mode.value
						if pls_mode == eDVBFrontendParametersSatellite.PLS_Unknown:
							pls_code = 0
						else:
							pls_code = self.scan_sat.pls_code.value

					print "add sat transponder"
					self.addSatTransponder(tlist, self.scan_sat.frequency.value,
								self.scan_sat.symbolrate.value,
								self.scan_sat.polarization.value,
								fec,
								self.scan_sat.inversion.value,
								orbpos,
								system,
								modulation,
								self.scan_sat.rolloff.value,
								self.scan_sat.pilot.value,
								is_id,
								pls_mode,
								pls_code)
				removeAll = False
			elif self.scan_type.value == "single_satellite":
				sat = self.satList[index_to_scan][self.scan_satselection[index_to_scan].index]
				getInitialTransponderList(tlist, sat[0])
			elif self.scan_type.value.find("multisat") != -1:
				SatList = nimmanager.getSatListForNim(index_to_scan)
				for x in self.multiscanlist:
					if x[1].value:
						print "   " + str(x[0])
						getInitialTransponderList(tlist, x[0])

		elif nim.isCompatible("DVB-C"):
			if self.scan_typecable.value == "single_transponder":
				self.addCabTransponder(tlist, self.scan_cab.frequency.value,
											  self.scan_cab.symbolrate.value,
											  self.scan_cab.modulation.value,
											  self.scan_cab.fec.value,
											  self.scan_cab.inversion.value)
				removeAll = False
			elif self.scan_typecable.value == "complete":
				if config.Nims[index_to_scan].cable.scan_type.value == "provider":
					getInitialCableTransponderList(tlist, index_to_scan)
				else:
					action = SEARCH_CABLE_TRANSPONDERS

		elif nim.isCompatible("DVB-T"):
			if self.scan_typeterrestrial.value == "single_transponder":
				if self.scan_ter.system.value == eDVBFrontendParametersTerrestrial.System_DVB_T:
					self.addTerTransponder(tlist,
							self.scan_ter.frequency.value * 1000,
							inversion = self.scan_ter.inversion.value,
							bandwidth = self.scan_ter.bandwidth.value,
							fechigh = self.scan_ter.fechigh.value,
							feclow = self.scan_ter.feclow.value,
							modulation = self.scan_ter.modulation.value,
							transmission = self.scan_ter.transmission.value,
							guard = self.scan_ter.guard.value,
							hierarchy = self.scan_ter.hierarchy.value,
							system = self.scan_ter.system.value,
							plpid = self.scan_ter.plp_id.value)
				else:
					self.addTerTransponder(tlist,
							self.scan_ter.frequency.value * 1000,
							inversion = self.scan_ter.inversion.value,
							bandwidth = self.scan_ter.bandwidth_t2.value,
							fechigh = self.scan_ter.fechigh_t2.value,
							feclow = self.scan_ter.feclow_t2.value,
							modulation = self.scan_ter.modulation_t2.value,
							transmission = self.scan_ter.transmission_t2.value,
							guard = self.scan_ter.guard_t2.value,
							hierarchy = self.scan_ter.hierarchy.value,
							system = self.scan_ter.system.value,
							plpid = self.scan_ter.plp_id.value)
				removeAll = False
			elif self.scan_typeterrestrial.value == "complete":
				skip_t2 = True
				if nim.isCompatible("DVB-T2"):
					scan_util = len(self.terrestrialTransponderGetCmd(nim.slot)) and True or False
					if scan_util:
						action = SEARCH_TERRESTRIAL2_TRANSPONDERS
					else:
						skip_t2 = False

				getInitialTerrestrialTransponderList(tlist, nimmanager.getTerrestrialDescription(index_to_scan), skip_t2)

		flags = self.scan_networkScan.value and eComponentScan.scanNetworkSearch or 0

		tmp = self.scan_clearallservices.value
		if tmp == "yes":
			flags |= eComponentScan.scanRemoveServices
		elif tmp == "yes_hold_feeds":
			flags |= eComponentScan.scanRemoveServices
			flags |= eComponentScan.scanDontRemoveFeeds

		if tmp != "no" and not removeAll:
			flags |= eComponentScan.scanDontRemoveUnscanned

		if self.scan_onlyfree.value:
			flags |= eComponentScan.scanOnlyFree

		for x in self["config"].list:
			x[1].save()

		if action == START_SCAN:
			self.startScan(tlist, flags, index_to_scan)
		elif action == SEARCH_CABLE_TRANSPONDERS:
			self.flags = flags
			self.feid = index_to_scan
			self.tlist = []
			self.startCableTransponderSearch(self.feid)
		elif action == SEARCH_TERRESTRIAL2_TRANSPONDERS:
			self.flags = flags
			self.feid = index_to_scan
			self.tlist = tlist
			self.startTerrestrialTransponderSearch(self.feid, nimmanager.getTerrestrialDescription(self.feid))

	def setCableTransponderSearchResult(self, tlist):
		self.tlist = tlist

	def cableTransponderSearchFinished(self):
		if self.tlist is None:
			self.tlist = []
		else:
			self.startScan(self.tlist, self.flags, self.feid)

	def setTerrestrialTransponderSearchResult(self, tlist):
		if tlist is not None:
			self.tlist.extend(tlist)

	def terrestrialTransponderSearchFinished(self):
		if self.tlist is None:
			self.tlist = []
		else:
			self.startScan(self.tlist, self.flags, self.feid)

	def startScan(self, tlist, flags, feid):
		if len(tlist):
			# flags |= eComponentScan.scanSearchBAT
			if self.finished_cb:
				self.session.openWithCallback(self.finished_cb, ServiceScan, [{"transponders": tlist, "feid": feid, "flags": flags}])
			else:
				self.session.open(ServiceScan, [{"transponders": tlist, "feid": feid, "flags": flags}])
		else:
			if self.finished_cb:
				self.session.openWithCallback(self.finished_cb, MessageBox, _("Nothing to scan!\nPlease setup your tuner settings before you start a service scan."), MessageBox.TYPE_ERROR)
			else:
				self.session.open(MessageBox, _("Nothing to scan!\nPlease setup your tuner settings before you start a service scan."), MessageBox.TYPE_ERROR)

	def keyCancel(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()

class ScanSimple(ConfigListScreen, Screen, CableTransponderSearchSupport, TerrestrialTransponderSearchSupport):
	def getNetworksForNim(self, nim):
		if nim.isCompatible("DVB-S"):
			networks = nimmanager.getSatListForNim(nim.slot)
		elif not nim.empty:
			networks = [ nim.getType() ] # "DVB-C" or "DVB-T". TODO: seperate networks for different C/T tuners, if we want to support that.
		else:
			# empty tuners provide no networks.
			networks = [ ]
		return networks

	def __init__(self, session):
		Screen.__init__(self, session)

		self["actions"] = ActionMap(["SetupActions"],
		{
			"ok": self.keyGo,
			"cancel": self.keyCancel,
		}, -2)

		self.list = []
		tlist = []

		known_networks = [ ]
		nims_to_scan = [ ]
		self.finished_cb = None

		for nim in nimmanager.nim_slots:
			# don't offer to scan nims if nothing is connected
			if not nimmanager.somethingConnected(nim.slot):
				continue

			# collect networks provided by this tuner
			need_scan = False
			networks = self.getNetworksForNim(nim)
			
			print "nim %d provides" % nim.slot, networks
			print "known:", known_networks

			# we only need to scan on the first tuner which provides a network.
			# this gives the first tuner for each network priority for scanning.
			for x in networks:
				if x not in known_networks:
					need_scan = True
					print x, "not in ", known_networks
					known_networks.append(x)

			if need_scan:
				nims_to_scan.append(nim)


		if "DVB-T2" in known_networks: # we need to remove "DVB-T" when networks have "DVB-T2"
			nims_dvb_t = []
			for nim in nims_to_scan:
				if nim.getType() == "DVB-T":
					nims_dvb_t.append(nim)

			for nim in nims_dvb_t:
				nims_to_scan.remove(nim)

		# we save the config elements to use them on keyGo
		self.nim_enable = [ ]

		if len(nims_to_scan):
			self.scan_clearallservices = ConfigSelection(default = "yes", choices = [("no", _("no")), ("yes", _("yes")), ("yes_hold_feeds", _("yes (keep feeds)"))])
			self.list.append(getConfigListEntry(_("Clear before scan"), self.scan_clearallservices))

			for nim in nims_to_scan:
				nimconfig = ConfigYesNo(default = True)
				nimconfig.nim_index = nim.slot
				self.nim_enable.append(nimconfig)
				self.list.append(getConfigListEntry(_("Scan ") + nim.slot_name + " (" + nim.friendly_type + ")", nimconfig))

		ConfigListScreen.__init__(self, self.list)
		self["header"] = Label(_("Automatic Scan"))
		self["footer"] = Label(_("Press OK to scan"))

	def runAsync(self, finished_cb):
		self.finished_cb = finished_cb
		self.keyGo()

	def keyGo(self):
		self.scanList = []
		self.known_networks = set()
		self.nim_iter=0
		self.buildTransponderList()

	def buildTransponderList(self): # this method is called multiple times because of asynchronous stuff
		APPEND_NOW = 0
		SEARCH_CABLE_TRANSPONDERS = 1
		SEARCH_TERRESTRIAL2_TRANSPONDERS = 2
		action = APPEND_NOW

		n = self.nim_iter < len(self.nim_enable) and self.nim_enable[self.nim_iter] or None
		self.nim_iter += 1
		if n:
			if n.value: # check if nim is enabled
				flags = 0
				nim = nimmanager.nim_slots[n.nim_index]
				networks = set(self.getNetworksForNim(nim))

				# don't scan anything twice
				networks.discard(self.known_networks)

				tlist = [ ]
				if nim.isCompatible("DVB-S"):
					# get initial transponders for each satellite to be scanned
					for sat in networks:
						getInitialTransponderList(tlist, sat[0])
				elif nim.isCompatible("DVB-C"):
					if config.Nims[nim.slot].cable.scan_type.value == "provider":
						getInitialCableTransponderList(tlist, nim.slot)
					else:
						action = SEARCH_CABLE_TRANSPONDERS
				elif nim.isCompatible("DVB-T"):
					skip_t2 = True
					if nim.isCompatible("DVB-T2"):
						scan_util = len(self.terrestrialTransponderGetCmd(nim.slot)) and True or False
						if scan_util:
							action = SEARCH_TERRESTRIAL2_TRANSPONDERS
						else:
							skip_t2 = False
					getInitialTerrestrialTransponderList(tlist, nimmanager.getTerrestrialDescription(nim.slot), skip_t2)
				else:
					assert False

				flags |= eComponentScan.scanNetworkSearch #FIXMEEE.. use flags from cables / satellites / terrestrial.xml
				tmp = self.scan_clearallservices.value
				if tmp == "yes":
					flags |= eComponentScan.scanRemoveServices
				elif tmp == "yes_hold_feeds":
					flags |= eComponentScan.scanRemoveServices
					flags |= eComponentScan.scanDontRemoveFeeds

				if action == APPEND_NOW:
					self.scanList.append({"transponders": tlist, "feid": nim.slot, "flags": flags})
				elif action == SEARCH_CABLE_TRANSPONDERS:
					self.flags = flags
					self.feid = nim.slot
					self.startCableTransponderSearch(nim.slot)
					return
				elif action == SEARCH_TERRESTRIAL2_TRANSPONDERS:
					self.tlist = tlist
					self.flags = flags
					self.feid = nim.slot
					self.startTerrestrialTransponderSearch(nim.slot, nimmanager.getTerrestrialDescription(nim.slot))
					return
				else:
					assert False

			self.buildTransponderList() # recursive call of this function !!!
			return
		# when we are here, then the recursion is finished and all enabled nims are checked
		# so we now start the real transponder scan
		self.startScan(self.scanList)

	def startScan(self, scanList):
		if len(scanList):
			if self.finished_cb:
				self.session.openWithCallback(self.finished_cb, ServiceScan, scanList = scanList)
			else:
				self.session.open(ServiceScan, scanList = scanList)
		else:
			if self.finished_cb:
				self.session.openWithCallback(self.finished_cb, MessageBox, _("Nothing to scan!\nPlease setup your tuner settings before you start a service scan."), MessageBox.TYPE_ERROR)
			else:
				self.session.open(MessageBox, _("Nothing to scan!\nPlease setup your tuner settings before you start a service scan."), MessageBox.TYPE_ERROR)

	def setCableTransponderSearchResult(self, tlist):
		if tlist is not None:
			self.scanList.append({"transponders": tlist, "feid": self.feid, "flags": self.flags})

	def cableTransponderSearchFinished(self):
		self.buildTransponderList()

	def setTerrestrialTransponderSearchResult(self, tlist):
		if tlist is not None:
			self.tlist.extend(tlist)
		if self.tlist is not None:
			self.scanList.append({"transponders": self.tlist, "feid": self.feid, "flags": self.flags})

	def terrestrialTransponderSearchFinished(self):
		self.buildTransponderList()

	def keyCancel(self):
		self.close()

	def Satexists(self, tlist, pos):
		for x in tlist:
			if x == pos:
				return 1
		return 0

