from enigma import eDVBResourceManager,\
	eDVBFrontendParametersSatellite, eDVBFrontendParameters

from Screens.Screen import Screen
from Screens.ScanSetup import ScanSetup
from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor

from Components.Label import Label
from Components.Sources.FrontendStatus import FrontendStatus
from Components.ActionMap import ActionMap
from Components.NimManager import nimmanager, getConfigSatlist
from Components.MenuList import MenuList
from Components.config import ConfigSelection, getConfigListEntry
from Components.TuneTest import Tuner

class Satfinder(ScanSetup):
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

	def __init__(self, session, feid):
		self.initcomplete = False
		self.feid = feid
		self.oldref = None

		if not self.openFrontend():
			self.oldref = session.nav.getCurrentlyPlayingServiceReference()
			session.nav.stopService() # try to disable foreground service
			if not self.openFrontend():
				if session.pipshown: # try to disable pip
					session.pipshown = False
					del session.pip
					if not self.openFrontend():
						self.frontend = None # in normal case this should not happen

		ScanSetup.__init__(self, session)
		self.tuner = Tuner(self.frontend)
		self["introduction"].setText("")
		self["Frontend"] = FrontendStatus(frontend_source = lambda : self.frontend, update_interval = 100)
		self.initcomplete = True
		self.onClose.append(self.__onClose)

	def __onClose(self):
		self.session.nav.playService(self.oldref)

	def createSetup(self):
		self.modulationEntry = None
		self.typeOfTuningEntry = None
		self.satEntry = None
		self.systemEntry = None
		self.is_id_boolEntry = None
		self.plsModeEntry = None
		self.list = []
		self.typeOfTuningEntry = getConfigListEntry(_('Tune'), self.tuning_type)
		self.list.append(self.typeOfTuningEntry)
		self.satEntry = getConfigListEntry(_('Satellite'), self.tuning_sat)
		self.list.append(self.satEntry)

		nim = nimmanager.nim_slots[self.feid]
		if self.tuning_type.value == "manual_transponder":
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
			self.list.append(getConfigListEntry(_('Frequency'), self.scan_sat.frequency))
			self.list.append(getConfigListEntry(_('Inversion'), self.scan_sat.inversion))
			self.list.append(getConfigListEntry(_('Symbol rate'), self.scan_sat.symbolrate))
			self.list.append(getConfigListEntry(_('Polarization'), self.scan_sat.polarization))
			if scan_sat_system_value == eDVBFrontendParametersSatellite.System_DVB_S:
				self.list.append(getConfigListEntry(_("FEC"), self.scan_sat.fec))
			elif scan_sat_system_value == eDVBFrontendParametersSatellite.System_DVB_S2:
				self.list.append(getConfigListEntry(_("FEC"), self.scan_sat.fec_s2))
				self.modulationEntry = getConfigListEntry(_('Modulation'), self.scan_sat.modulation)
				self.list.append(self.modulationEntry)
				self.list.append(getConfigListEntry(_('Roll-off'), self.scan_sat.rolloff))
				self.list.append(getConfigListEntry(_('Pilot'), self.scan_sat.pilot))
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
				self.modulationEntry = getConfigListEntry(_('Modulation'), self.scan_sat.modulation_dvbs2x)
				self.list.append(self.modulationEntry)
				self.list.append(getConfigListEntry(_('Roll-off'), self.scan_sat.rolloff))
				self.list.append(getConfigListEntry(_('Pilot'), self.scan_sat.pilot))
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
		elif self.tuning_transponder and self.tuning_type.value == "predefined_transponder":
			self.list.append(getConfigListEntry(_("Transponder"), self.tuning_transponder))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def newConfig(self):
		cur = self["config"].getCurrent()
		if cur in (self.typeOfTuningEntry, self.systemEntry, self.is_id_boolEntry, self.plsModeEntry):
			self.createSetup()
		elif cur == self.satEntry:
			self.updateSats()
			self.createSetup()
		elif self.modulationEntry and (cur == self.modulationEntry) and \
			self.systemEntry and (self.systemEntry[1].value == eDVBFrontendParametersSatellite.System_DVB_S2X):
			self.createSetup()

	def sat_changed(self, config_element):
		self.newConfig()
		self.retune(config_element)

	def retune(self, configElement):
		returnvalue = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 3, 0)
		satpos = int(self.tuning_sat.value)
		nim = nimmanager.nim_slots[self.feid]
		if self.tuning_type.value == "manual_transponder":
			system = self.scan_sat.system.value
			modulation = self.scan_sat.modulation.value
			if nim.isCompatible("DVB-S2X"):
				system = self.scan_sat.system_dvbs2x.value
				modulation = self.scan_sat.modulation_dvbs2x.value

			if system == eDVBFrontendParametersSatellite.System_DVB_S:
				fec = self.scan_sat.fec.value
			elif system == eDVBFrontendParametersSatellite.System_DVB_S2:
				fec = self.scan_sat.fec_s2.value
			elif system == eDVBFrontendParametersSatellite.System_DVB_S2X:
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

			returnvalue = (
				self.scan_sat.frequency.value,
				self.scan_sat.symbolrate.value,
				self.scan_sat.polarization.value,
				fec,
				self.scan_sat.inversion.value,
				satpos,
				system,
				modulation,
				self.scan_sat.rolloff.value,
				self.scan_sat.pilot.value,
				is_id,
				pls_mode,
				pls_code)
			self.tune(returnvalue)
		elif self.tuning_type.value == "predefined_transponder":
			tps = nimmanager.getTransponders(satpos)
			l = len(tps)
			if l > self.tuning_transponder.index:
				transponder = tps[self.tuning_transponder.index]
				returnvalue = (transponder[1] / 1000, transponder[2] / 1000,
					transponder[3], transponder[4], 2, satpos, transponder[5], transponder[6], transponder[8], transponder[9], transponder[10], transponder[11], transponder[12])
				self.tune(returnvalue)

	def createConfig(self, foo):
		self.tuning_transponder = None
		self.tuning_type = ConfigSelection(choices = [("manual_transponder", _("Manual transponder")), ("predefined_transponder", _("Predefined transponder"))])
		self.tuning_sat = getConfigSatlist(192, nimmanager.getSatListForNim(self.feid))
		ScanSetup.createConfig(self, None)
		
		self.updateSats()

		setup_list = [self.tuning_type, self.tuning_sat, self.scan_sat.frequency,
			self.scan_sat.inversion, self.scan_sat.symbolrate,
			self.scan_sat.polarization, self.scan_sat.fec, self.scan_sat.pilot,
			self.scan_sat.fec_s2, self.scan_sat.fec, self.scan_sat.modulation,
			self.scan_sat.rolloff, self.scan_sat.system,
			self.scan_sat.is_id_bool, self.scan_sat.is_id, self.scan_sat.pls_mode, self.scan_sat.pls_code]

		nim = nimmanager.nim_slots[self.feid]
		if nim.isCompatible("DVB-S2X"):
			dvbs2x_setup_list = [self.scan_sat.system_dvbs2x, self.scan_sat.modulation_dvbs2x, self.scan_sat.fec_s2x_qpsk,
				self.scan_sat.fec_s2x_8psk, self.scan_sat.fec_s2x_8apsk, self.scan_sat.fec_s2x_16apsk, self.scan_sat.fec_s2x_32apsk]
			setup_list.extend(dvbs2x_setup_list)

		for x in setup_list:
			x.addNotifier(self.retune, initial_call = False)

	def updateSats(self):
		orb_pos = self.tuning_sat.orbital_position
		if orb_pos is not None:
			transponderlist = nimmanager.getTransponders(orb_pos)
			list = []
			default = None
			index = 0
			for x in transponderlist:
				if x[3] == 0:
					pol = "H"
				elif x[3] == 1:
					pol = "V"
				elif x[3] == 2:
					pol = "CL"
				elif x[3] == 3:
					pol = "CR"
				else:
					pol = "??"
				if x[4] == 0:
					fec = "FEC Auto"
				elif x[4] == 1:
					fec = "FEC 1/2"
				elif x[4] == 2:
					fec = "FEC 2/3"
				elif x[4] == 3:
					fec = "FEC 3/4"
				elif x[4] == 4:
					fec = "FEC 5/6"
				elif x[4] == 5:
					fec = "FEC 7/8"
				elif x[4] == 6:
					fec = "FEC 8/9"
				elif x[4] == 7:
					fec = "FEC 3/5"
				elif x[4] == 8:
					fec = "FEC 4/5"
				elif x[4] == 9:
					fec = "FEC 9/10"
				elif x[4] == 15:
					fec = "FEC None"
				else:
					fec = "FEC Unknown"
				e = str(x[1]) + "," + str(x[2]) + "," + pol + "," + fec
				if default is None:
					default = str(index)
				list.append((str(index), e))
				index += 1
			self.tuning_transponder = ConfigSelection(choices = list, default = default)
			self.tuning_transponder.addNotifier(self.retune, initial_call = False)

	def keyGo(self):
		self.retune(self.tuning_type)

	def restartPrevService(self, yesno):
		if yesno:
			if self.frontend:
				self.frontend = None
				del self.raw_channel
		else:
			self.oldref = None
		self.close(None)

	def keyCancel(self):
		if self.oldref:
			self.session.openWithCallback(self.restartPrevService, MessageBox, _("Zap back to service before satfinder?"), MessageBox.TYPE_YESNO)
		else:
			self.restartPrevService(False)

	def tune(self, transponder):
		if self.initcomplete:
			if transponder is not None:
				self.tuner.tune(transponder)

class SatNimSelection(Screen):
	skin = """
		<screen position="140,165" size="400,130" title="select Slot">
			<widget name="nimlist" position="20,10" size="360,100" />
		</screen>"""
		
	def __init__(self, session):
		Screen.__init__(self, session)

		nimlist = nimmanager.getNimListOfType("DVB-S")
		nimMenuList = []
		for x in nimlist:
			nimMenuList.append((nimmanager.nim_slots[x].friendly_full_description, x))

		self["nimlist"] = MenuList(nimMenuList)

		self["actions"] = ActionMap(["OkCancelActions"],
		{
			"ok": self.okbuttonClick ,
			"cancel": self.close
		}, -1)

	def okbuttonClick(self):
		selection = self["nimlist"].getCurrent()[1]
		self.session.open(Satfinder, selection)

def SatfinderMain(session, **kwargs):
	nims = nimmanager.getNimListOfType("DVB-S")

	nimList = []
	for x in nims:
		if not nimmanager.getNimConfig(x).configMode.value in ("loopthrough", "satposdepends", "nothing"):
			nimList.append(x)

	if len(nimList) == 0:
		session.open(MessageBox, _("No satellite frontend found!!"), MessageBox.TYPE_ERROR)
	else:
		if session.nav.RecordTimer.isRecording():
			session.open(MessageBox, _("A recording is currently running. Please stop the recording before trying to start the satfinder."), MessageBox.TYPE_ERROR)
		else:
			if len(nimList) == 1:
				session.open(Satfinder, nimList[0])
			else:
				session.open(SatNimSelection)

def SatfinderStart(menuid, **kwargs):
	if menuid == "scan":
		return [(_("Satfinder"), SatfinderMain, "satfinder", None)]
	else:
		return []

def Plugins(**kwargs):
	if (nimmanager.hasNimType("DVB-S")):
		return PluginDescriptor(name=_("Satfinder"), description="Helps setting up your dish", where = PluginDescriptor.WHERE_MENU, needsRestart = False, fnc=SatfinderStart)
	else:
		return []
