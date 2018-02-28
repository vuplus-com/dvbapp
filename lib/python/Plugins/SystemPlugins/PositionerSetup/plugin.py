from enigma import eTimer, eDVBSatelliteEquipmentControl, eDVBResourceManager, \
	eDVBDiseqcCommand, eDVBFrontendParametersSatellite, eDVBFrontendParameters,\
	iDVBFrontend

from Screens.Screen import Screen
from Screens.ScanSetup import ScanSetup
from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor

from Components.Label import Label
from Components.ConfigList import ConfigList
from Components.TunerInfo import TunerInfo
from Components.ActionMap import NumberActionMap, ActionMap
from Components.NimManager import nimmanager
from Components.MenuList import MenuList
from Components.config import ConfigSatlist, ConfigNothing, ConfigSelection, ConfigSubsection, KEY_LEFT, KEY_RIGHT, getConfigListEntry
from Components.TuneTest import Tuner
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigInteger, getConfigListEntry
from Tools.Transponder import ConvertToHumanReadable

from time import sleep

class PositionerSetup(Screen):
	skin = """
		<screen position="100,100" size="560,400" title="Positioner setup..." >
			<widget name="list" position="100,0" size="350,155" />

			<widget name="red" position="0,155" size="140,80" backgroundColor="red" halign="center" valign="center" font="Regular;21" />
			<widget name="green" position="140,155" size="140,80" backgroundColor="green" halign="center" valign="center" font="Regular;21" />
			<widget name="yellow" position="280,155" size="140,80" backgroundColor="yellow" halign="center" valign="center" font="Regular;21" />
			<widget name="blue" position="420,155" size="140,80" backgroundColor="blue" halign="center" valign="center" font="Regular;21" />

			<widget name="snr_db" position="60,245" size="150,22" halign="center" valign="center" font="Regular;21" />
			<eLabel text="SNR:" position="0,270" size="60,22" font="Regular;21" />
			<eLabel text="BER:" position="0,295" size="60,22" font="Regular;21" />
			<eLabel text="Lock:" position="0,320" size="60,22" font="Regular;21" />
			<widget name="snr_percentage" position="220,270" size="60,22" font="Regular;21" />
			<widget name="ber_value" position="220,295" size="60,22" font="Regular;21" />
			<widget name="lock_state" position="60,320" size="150,22" font="Regular;21" />
			<widget name="snr_bar" position="60,270" size="150,22" />
			<widget name="ber_bar" position="60,295" size="150,22" />

			<eLabel text="Frequency:" position="300,245" size="120,22" font="Regular;21" />
			<eLabel text="Symbolrate:" position="300,270" size="120,22" font="Regular;21" />
			<eLabel text="FEC:" position="300,295" size="120,22" font="Regular;21" />
			<widget name="frequency_value" position="420,245" size="120,22" font="Regular;21" />
			<widget name="symbolrate_value" position="420,270" size="120,22" font="Regular;21" />
			<widget name="fec_value" position="420,295" size="120,22" font="Regular;21" />
		</screen>"""
	def __init__(self, session, feid):
		self.skin = PositionerSetup.skin
		Screen.__init__(self, session)
		self.feid = feid
		self.oldref = None

		cur = { }
		if not self.openFrontend():
			self.oldref = session.nav.getCurrentlyPlayingServiceReference()
			service = session.nav.getCurrentService()
			feInfo = service and service.frontendInfo()
			if feInfo:
				cur = feInfo.getTransponderData(True)
			del feInfo
			del service
			session.nav.stopService() # try to disable foreground service
			if not self.openFrontend():
				if session.pipshown: # try to disable pip
					service = self.session.pip.pipservice
					feInfo = service and service.frontendInfo()
					if feInfo:
						cur = feInfo.getTransponderData()
					del feInfo
					del service
					session.pipshown = False
					del session.pip
					if not self.openFrontend():
						self.frontend = None # in normal case this should not happen
		
		self.frontendStatus = { }
		self.diseqc = Diseqc(self.frontend)
		self.tuner = Tuner(self.frontend, True) #True means we dont like that the normal sec stuff sends commands to the rotor!

		tp = ( cur.get("frequency", 0) / 1000,
			cur.get("symbol_rate", 0) / 1000,
			cur.get("polarization", eDVBFrontendParametersSatellite.Polarisation_Horizontal),
			cur.get("fec_inner", eDVBFrontendParametersSatellite.FEC_Auto),
			cur.get("inversion", eDVBFrontendParametersSatellite.Inversion_Unknown),
			cur.get("orbital_position", 0),
			cur.get("system", eDVBFrontendParametersSatellite.System_DVB_S),
			cur.get("modulation", eDVBFrontendParametersSatellite.Modulation_QPSK),
			cur.get("rolloff", eDVBFrontendParametersSatellite.RollOff_alpha_0_35),
			cur.get("pilot", eDVBFrontendParametersSatellite.Pilot_Unknown),
			cur.get("is_id", -1),
			cur.get("pls_mode", eDVBFrontendParametersSatellite.PLS_Unknown),
			cur.get("pls_code", 0))

		self.tuner.tune(tp)
		self.createConfig()
		
		self.isMoving = False
		self.stopOnLock = False
		
		self.red = Label("")
		self["red"] = self.red
		self.green = Label("")
		self["green"] = self.green
		self.yellow = Label("")
		self["yellow"] = self.yellow
		self.blue = Label("")
		self["blue"] = self.blue

		self.list = []
		self["list"] = ConfigList(self.list)
		self.createSetup()

		self["snr_db"] = TunerInfo(TunerInfo.SNR_DB, statusDict = self.frontendStatus)
		self["snr_percentage"] = TunerInfo(TunerInfo.SNR_PERCENTAGE, statusDict = self.frontendStatus)
		self["ber_value"] = TunerInfo(TunerInfo.BER_VALUE, statusDict = self.frontendStatus)
		self["snr_bar"] = TunerInfo(TunerInfo.SNR_BAR, statusDict = self.frontendStatus)
		self["ber_bar"] = TunerInfo(TunerInfo.BER_BAR, statusDict = self.frontendStatus)
		self["lock_state"] = TunerInfo(TunerInfo.LOCK_STATE, statusDict = self.frontendStatus)

		self["frequency_value"] = Label("")
		self["symbolrate_value"] = Label("")
		self["fec_value"] = Label("")
		
		self["actions"] = ActionMap(["DirectionActions", "OkCancelActions", "ColorActions"],
		{
			"ok": self.go,
			"cancel": self.keyCancel,
			"up": self.up,
			"down": self.down,
			"left": self.left,
			"right": self.right,
			"red": self.redKey,
			"green": self.greenKey,
			"yellow": self.yellowKey,
			"blue": self.blueKey,
		}, -1)
		
		self.updateColors("tune")
		
		self.statusTimer = eTimer()
		self.statusTimer.callback.append(self.updateStatus)
		self.statusTimer.start(50, True)
		self.onClose.append(self.__onClose)

	def __onClose(self):
		self.session.nav.playService(self.oldref)

	def restartPrevService(self, yesno):
		if yesno:
			if self.frontend:
				self.frontend = None
				del self.raw_channel
		else:
			self.oldref=None
		self.close(None)	

	def keyCancel(self):
		if self.oldref:
			self.session.openWithCallback(self.restartPrevService, MessageBox, _("Zap back to service before positioner setup?"), MessageBox.TYPE_YESNO)
		else:
			self.restartPrevService(False)

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

	def createConfig(self):
		self.positioner_tune = ConfigNothing()
		self.positioner_move = ConfigNothing()
		self.positioner_finemove = ConfigNothing()
		self.positioner_limits = ConfigNothing()
		self.positioner_goto0 = ConfigNothing()
		storepos = []
		for x in range(1,255):
			storepos.append(str(x))
		self.positioner_storage = ConfigSelection(choices = storepos)

	def createSetup(self):
		self.list.append((_("Tune"), self.positioner_tune, "tune"))
		self.list.append((_("Positioner movement"), self.positioner_move, "move"))
		self.list.append((_("Positioner fine movement"), self.positioner_finemove, "finemove"))
		self.list.append((_("Set limits"), self.positioner_limits, "limits"))
		self.list.append((_("Positioner storage"), self.positioner_storage, "storage"))
		self.list.append((_("Goto 0"), self.positioner_goto0, "goto0"))
		self["list"].l.setList(self.list)

	def go(self):
		pass

	def getCurrentConfigPath(self):
		return self["list"].getCurrent()[2]

	def up(self):
		if not self.isMoving:
			self["list"].instance.moveSelection(self["list"].instance.moveUp)
			self.updateColors(self.getCurrentConfigPath())

	def down(self):
		if not self.isMoving:
			self["list"].instance.moveSelection(self["list"].instance.moveDown)
			self.updateColors(self.getCurrentConfigPath())

	def left(self):
		self["list"].handleKey(KEY_LEFT)

	def right(self):
		self["list"].handleKey(KEY_RIGHT)

	def updateColors(self, entry):
		if entry == "tune":
			self.red.setText(_("Tune"))
			self.green.setText("")
			self.yellow.setText("")
			self.blue.setText("")
		elif entry == "move":
			if self.isMoving:
				self.red.setText(_("Stop"))
				self.green.setText(_("Stop"))
				self.yellow.setText(_("Stop"))
				self.blue.setText(_("Stop"))
			else:
				self.red.setText(_("Move west"))
				self.green.setText(_("Search west"))
				self.yellow.setText(_("Search east"))
				self.blue.setText(_("Move east"))
		elif entry == "finemove":
			self.red.setText("")
			self.green.setText(_("Step west"))
			self.yellow.setText(_("Step east"))
			self.blue.setText("")
		elif entry == "limits":
			self.red.setText(_("Limits off"))
			self.green.setText(_("Limit west"))
			self.yellow.setText(_("Limit east"))
			self.blue.setText(_("Limits on"))
		elif entry == "storage":
			self.red.setText("")
			self.green.setText(_("Store position"))
			self.yellow.setText(_("Goto position"))
			self.blue.setText("")
		elif entry == "goto0":
			self.red.setText(_("Goto 0"))
			self.green.setText("")
			self.yellow.setText("")
			self.blue.setText("")
		else:
			self.red.setText("")
			self.green.setText("")
			self.yellow.setText("")
			self.blue.setText("")

	def redKey(self):
		entry = self.getCurrentConfigPath()
		if entry == "move":
			if self.isMoving:
				self.diseqccommand("stop")
				self.isMoving = False
				self.stopOnLock = False
			else:
				self.diseqccommand("moveWest", 0)
				self.isMoving = True
			self.updateColors("move")
		elif entry == "limits":
			self.diseqccommand("limitOff")
		elif entry == "tune":
			fe_data = { }
			self.frontend.getFrontendData(fe_data)
			self.frontend.getTransponderData(fe_data, True)
			feparm = self.tuner.lastparm.getDVBS()
			fe_data["orbital_position"] = feparm.orbital_position
			self.session.openWithCallback(self.tune, TunerScreen, self.feid, fe_data)
		elif entry == "goto0":
			print "move to position 0"
			self.diseqccommand("moveTo", 0)

	def greenKey(self):
		entry = self.getCurrentConfigPath()
		if entry == "move":
			if self.isMoving:
				self.diseqccommand("stop")
				self.isMoving = False
				self.stopOnLock = False
			else:
				self.isMoving = True
				self.stopOnLock = True
				self.diseqccommand("moveWest", 0)
			self.updateColors("move")
		elif entry == "finemove":
			print "stepping west"
			self.diseqccommand("moveWest", 0xFF) # one step
		elif entry == "storage":
			print "store at position", int(self.positioner_storage.value)
			self.diseqccommand("store", int(self.positioner_storage.value))
			
		elif entry == "limits":
			self.diseqccommand("limitWest")

	def yellowKey(self):
		entry = self.getCurrentConfigPath()
		if entry == "move":
			if self.isMoving:
				self.diseqccommand("stop")
				self.isMoving = False
				self.stopOnLock = False
			else:
				self.isMoving = True
				self.stopOnLock = True
				self.diseqccommand("moveEast", 0)
			self.updateColors("move")
		elif entry == "finemove":
			print "stepping east"
			self.diseqccommand("moveEast", 0xFF) # one step
		elif entry == "storage":
			print "move to position", int(self.positioner_storage.value)
			self.diseqccommand("moveTo", int(self.positioner_storage.value))
		elif entry == "limits":
			self.diseqccommand("limitEast")

	def blueKey(self):
		entry = self.getCurrentConfigPath()
		if entry == "move":
			if self.isMoving:
				self.diseqccommand("stop")
				self.isMoving = False
				self.stopOnLock = False
			else:
				self.diseqccommand("moveEast", 0)
				self.isMoving = True
			self.updateColors("move")
			print "moving east"
		elif entry == "limits":
			self.diseqccommand("limitOn")

	def diseqccommand(self, cmd, param = 0):
		self.diseqc.command(cmd, param)
		self.tuner.retune()

	def updateStatus(self):
		if self.frontend:
			self.frontend.getFrontendStatus(self.frontendStatus)
		self["snr_db"].update()
		self["snr_percentage"].update()
		self["ber_value"].update()
		self["snr_bar"].update()
		self["ber_bar"].update()
		self["lock_state"].update()
		transponderdata = ConvertToHumanReadable(self.tuner.getTransponderData(), "DVB-S")
		self["frequency_value"].setText(str(transponderdata.get("frequency")))
		self["symbolrate_value"].setText(str(transponderdata.get("symbol_rate")))
		self["fec_value"].setText(str(transponderdata.get("fec_inner")))
		if self.frontendStatus.get("tuner_locked", 0) == 1 and self.isMoving and self.stopOnLock:
			self.diseqccommand("stop")
			self.isMoving = False
			self.stopOnLock = False
			self.updateColors(self.getCurrentConfigPath())
		self.statusTimer.start(50, True)

	def tune(self, transponder):
		if transponder is not None:
			self.tuner.tune(transponder)

class Diseqc:
	def __init__(self, frontend):
		self.frontend = frontend

	def command(self, what, param = 0):
		if self.frontend:
			cmd = eDVBDiseqcCommand()
			if what == "moveWest":
				string = 'e03169' + ("%02x" % param)
			elif what == "moveEast":
				string = 'e03168' + ("%02x" % param)
			elif what == "moveTo":
				string = 'e0316b' + ("%02x" % param)
			elif what == "store":
				string = 'e0316a' + ("%02x" % param)
			elif what == "limitOn":
				string = 'e0316a00'
			elif what == "limitOff":
				string = 'e03163'
			elif what == "limitEast":
				string = 'e03166'
			elif what == "limitWest":
				string = 'e03167'
			else:
				string = 'e03160' #positioner stop
			
			print "diseqc command:",
			print string
			cmd.setCommandString(string)
			self.frontend.setTone(iDVBFrontend.toneOff)
			sleep(0.015) # wait 15msec after disable tone
			self.frontend.sendDiseqc(cmd)
			if string == 'e03160': #positioner stop
				sleep(0.05)
				self.frontend.sendDiseqc(cmd) # send 2nd time

class TunerScreen(ConfigListScreen, Screen):
	skin = """
		<screen position="90,100" size="520,400" title="Tune">
			<widget name="config" position="20,10" size="460,350" scrollbarMode="showOnDemand" />
			<widget name="introduction" position="20,360" size="350,30" font="Regular;23" />
		</screen>"""

	def __init__(self, session, feid, fe_data):
		self.feid = feid
		self.fe_data = fe_data
		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, None)
		self.createConfig(fe_data)
		self.createSetup()
		self.tuning.sat.addNotifier(self.tuningSatChanged)
		self.tuning.type.addNotifier(self.tuningTypeChanged)
		self.scan_sat.system.addNotifier(self.systemChanged)
		self.scan_sat.system_dvbs2x.addNotifier(self.systemChanged)
		self.scan_sat.is_id_bool.addNotifier(self.isIdChanged, initial_call = False)
		self.scan_sat.pls_mode.addNotifier(self.plsModeChanged, initial_call = False)

		self["actions"] = NumberActionMap(["SetupActions"],
		{
			"ok": self.keyGo,
			"cancel": self.keyCancel,
		}, -2)

		self["introduction"] = Label(_(" "))

	def createSetup(self):
		self.list = []
		self.list.append(getConfigListEntry(_('Tune'), self.tuning.type) )
		self.list.append(getConfigListEntry(_('Satellite'), self.tuning.sat)	)

		self.is_id_boolEntry = None
		self.plsModeEntry = None
		nim = nimmanager.nim_slots[self.feid]
		if self.tuning.type.value == "manual_transponder":
			scan_sat_system_value = self.scan_sat.system.value
			if nim.isCompatible("DVB-S2X"):
				scan_sat_system_value = self.scan_sat.system_dvbs2x.value
				self.list.append(getConfigListEntry(_('System'), self.scan_sat.system_dvbs2x))
			elif nim.isCompatible("DVB-S2"):
				self.list.append(getConfigListEntry(_('System'), self.scan_sat.system))
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
		elif self.tuning.type.value == "predefined_transponder":
			self.list.append(getConfigListEntry(_("Transponder"), self.tuning.transponder))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def createConfig(self, frontendData):
		satlist = nimmanager.getRotorSatListForNim(self.feid)
		orb_pos = self.fe_data.get("orbital_position", None)
		self.tuning = ConfigSubsection()
		self.tuning.type = ConfigSelection(
			default = "manual_transponder",
			choices = { "manual_transponder" : _("Manual transponder"),
						"predefined_transponder" : _("Predefined transponder") } )
		self.tuning.sat = ConfigSatlist(list = satlist)
		if orb_pos is not None:
			for x in satlist:
				opos = str(orb_pos)
				if x[0] == orb_pos and self.tuning.sat.value != opos:
					self.tuning.sat.value = opos
			del self.fe_data["orbital_position"]

		self.updateTransponders()

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

		if frontendData is not None:
			ttype = frontendData.get("tuner_type", "UNKNOWN")
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

		self.scan_sat = ConfigSubsection()

		sat_choices = [
				(eDVBFrontendParametersSatellite.System_DVB_S, _("DVB-S")),
				(eDVBFrontendParametersSatellite.System_DVB_S2, _("DVB-S2"))]

		sat_choices_dvbs2x = [
			(eDVBFrontendParametersSatellite.System_DVB_S, _("DVB-S")),
			(eDVBFrontendParametersSatellite.System_DVB_S2, _("DVB-S2")),
			(eDVBFrontendParametersSatellite.System_DVB_S2X, _("DVB-S2X"))]

		self.scan_sat.system = ConfigSelection(default = defaultSat["system"], choices = sat_choices)
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

	def tuningSatChanged(self, *parm):
		self.updateTransponders()
		self.createSetup()

	def tuningTypeChanged(self, *parm):
		self.createSetup()

	def systemChanged(self, *parm):
		self.createSetup()

	def isIdChanged(self, *parm):
		self.createSetup()

	def plsModeChanged(self, *parm):
		self.createSetup()

	def updateTransponders(self):
		if len(self.tuning.sat.choices):
			transponderlist = nimmanager.getTransponders(int(self.tuning.sat.value))
			tps = []
			cnt=0
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

				fec_desc = ("FEC Auto", "FEC 1/2", "FEC 2/3", "FEC 3/4", "FEC 5/6", "FEC 7/8", "FEC 8/9", "FEC 3/5", "FEC 4/5", "FEC 9/10", \
							"FEC Unknown", "FEC Unknown", "FEC Unknown", "FEC Unknown", "FEC Unknown", "FEC None", \
							"FEC_13_45", "FEC_9_20", "FEC_11_20", "FEC_23_36", "FEC_25_36", \
							"FEC_13_18", "FEC_26_45", "FEC_28_45", "FEC_7_9", "FEC_77_90", \
							"FEC_32_45", "FEC_11_15", "FEC_1_2_L", "FEC_8_15_L", "FEC_3_5_L", \
							"FEC_2_3_L", "FEC_5_9_L", "FEC_26_45_L")
				if x[4] > len(fec_desc)-1:
					fec = "FEC Unknown"
				else:
					fec = fec_desc[x[4]]
				tps.append(str(x[1]) + "," + str(x[2]) + "," + pol + "," + fec)
			self.tuning.transponder = ConfigSelection(choices=tps)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)

	def keyRight(self):
		ConfigListScreen.keyRight(self)

	def keyGo(self):
		returnvalue = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 3, 0)
		satpos = int(self.tuning.sat.value)
		nim = nimmanager.nim_slots[self.feid]
		if self.tuning.type.value == "manual_transponder":
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
			else:
				fec = self.scan_sat.fec.value

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
		elif self.tuning.type.value == "predefined_transponder":
			transponder = nimmanager.getTransponders(satpos)[self.tuning.transponder.index]
			returnvalue = (transponder[1] / 1000, transponder[2] / 1000,
				transponder[3], transponder[4], 2, satpos, transponder[5], transponder[6], transponder[8], transponder[9], transponder[10], transponder[11], transponder[12])
		self.close(returnvalue)

	def keyCancel(self):
		self.close(None)

class RotorNimSelection(Screen):
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
		selection = self["nimlist"].getCurrent()
		self.session.open(PositionerSetup, selection[1])

def PositionerMain(session, **kwargs):
	nimList = nimmanager.getNimListOfType("DVB-S")
	if len(nimList) == 0:
		session.open(MessageBox, _("No positioner capable frontend found."), MessageBox.TYPE_ERROR)
	else:
		if session.nav.RecordTimer.isRecording():
			session.open(MessageBox, _("A recording is currently running. Please stop the recording before trying to configure the positioner."), MessageBox.TYPE_ERROR)
		else:
			usableNims = []
			for x in nimList:
				configured_rotor_sats = nimmanager.getRotorSatListForNim(x)
				if len(configured_rotor_sats) != 0:
					usableNims.append(x)
			if len(usableNims) == 1:
				session.open(PositionerSetup, usableNims[0])
			elif len(usableNims) > 1:
				session.open(RotorNimSelection)
			else:
				session.open(MessageBox, _("No tuner is configured for use with a diseqc positioner!"), MessageBox.TYPE_ERROR)

def PositionerSetupStart(menuid, **kwargs):
	if menuid == "scan":
		return [(_("Positioner setup"), PositionerMain, "positioner_setup", None)]
	else:
		return []

def Plugins(**kwargs):
	if (nimmanager.hasNimType("DVB-S")):
		return PluginDescriptor(name=_("Positioner setup"), description="Setup your positioner", where = PluginDescriptor.WHERE_MENU, needsRestart = False, fnc=PositionerSetupStart)
	else:
		return []
