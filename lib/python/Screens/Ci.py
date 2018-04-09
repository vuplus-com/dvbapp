from Screen import Screen
from Components.ActionMap import ActionMap
from Components.ActionMap import NumberActionMap
from Components.Label import Label

from Components.config import config, ConfigSubsection, ConfigSelection, ConfigSubList, getConfigListEntry, KEY_LEFT, KEY_RIGHT, KEY_0, ConfigNothing, ConfigPIN, ConfigYesNo
from Components.ConfigList import ConfigList

from Components.SystemInfo import SystemInfo
from Tools.Directories import fileExists

from enigma import eTimer, eDVBCI_UI, eDVBCIInterfaces

def setCIBitrate(configElement):
	eDVBCI_UI.getInstance().setClockRate(configElement.slotid, eDVBCI_UI.rateHigh if configElement.value else eDVBCI_UI.rateNormal)

def setRelevantPidsRouting(configElement):
	open(SystemInfo["CI%dRelevantPidsRoutingSupport" % configElement.slotid], "w").write("yes" if configElement.value else "no")

def setdvbCiDelay(configElement):
	open(SystemInfo["CommonInterfaceCIDelay"], "w").write(configElement.value)
	configElement.save()

def InitCiConfig():
	config.ci = ConfigSubList()
	config.cimisc = ConfigSubsection()
	if SystemInfo["CommonInterface"]:
		for slot in range(SystemInfo["CommonInterface"]):
			config.ci.append(ConfigSubsection())
			config.ci[slot].canDescrambleMultipleServices = ConfigSelection(choices = [("auto", _("Auto")), ("no", _("No")), ("yes", _("Yes"))], default = "auto")
			if SystemInfo["CI%dSupportsHighBitrates" % slot]:
				config.ci[slot].canHandleHighBitrates = ConfigYesNo(default = False)
				config.ci[slot].canHandleHighBitrates.slotid = slot
				config.ci[slot].canHandleHighBitrates.addNotifier(setCIBitrate)

			if SystemInfo["CI%dRelevantPidsRoutingSupport" % slot]:
				config.ci[slot].relevantPidsRouting = ConfigYesNo(default = False)
				config.ci[slot].relevantPidsRouting.slotid = slot
				config.ci[slot].relevantPidsRouting.addNotifier(setRelevantPidsRouting)

		if SystemInfo["CommonInterfaceCIDelay"]:
			config.cimisc.dvbCiDelay = ConfigSelection(default = "256", choices = [("16"), ("32"), ("64"), ("128"), ("256")])
			config.cimisc.dvbCiDelay.addNotifier(setdvbCiDelay)
			
class MMIDialog(Screen):
	def __init__(self, session, slotid, action, handler = eDVBCI_UI.getInstance(), wait_text = _("wait for ci...") ):
		Screen.__init__(self, session)

		print "MMIDialog with action" + str(action)

		self.mmiclosed = False
		self.tag = None
		self.slotid = slotid

		self.timer = eTimer()
		self.timer.callback.append(self.keyCancel)

		#else the skins fails
		self["title"] = Label("")
		self["subtitle"] = Label("")
		self["bottom"] = Label("")
		self["entries"] = ConfigList([ ])

		self["actions"] = NumberActionMap(["SetupActions"],
			{
				"ok": self.okbuttonClick,
				"cancel": self.keyCancel,
				#for PIN
				"left": self.keyLeft,
				"right": self.keyRight,
				"1": self.keyNumberGlobal,
				"2": self.keyNumberGlobal,
				"3": self.keyNumberGlobal,
				"4": self.keyNumberGlobal,
				"5": self.keyNumberGlobal,
				"6": self.keyNumberGlobal,
				"7": self.keyNumberGlobal,
				"8": self.keyNumberGlobal,
				"9": self.keyNumberGlobal,
				"0": self.keyNumberGlobal
			}, -1)

		self.action = action

		self.handler = handler
		self.wait_text = wait_text

		if action == 2:		#start MMI
			handler.startMMI(self.slotid)
			self.showWait()
		elif action == 3:		#mmi already there (called from infobar)
			self.showScreen()

	def addEntry(self, list, entry):
		if entry[0] == "TEXT":		#handle every item (text / pin only?)
			list.append( (entry[1], ConfigNothing(), entry[2]) )
		if entry[0] == "PIN":
			pinlength = entry[1]
			if entry[3] == 1:
				# masked pins:
				x = ConfigPIN(0, len = pinlength, censor = "*")
			else:
				# unmasked pins:
				x = ConfigPIN(0, len = pinlength)
			self["subtitle"].setText(entry[2])
			list.append( getConfigListEntry("", x) )
			self["bottom"].setText(_("please press OK when ready"))

	def okbuttonClick(self):
		self.timer.stop()
		if not self.tag:
			return
		if self.tag == "WAIT":
			print "do nothing - wait"
		elif self.tag == "MENU":
			print "answer MENU"
			cur = self["entries"].getCurrent()
			if cur:
				self.handler.answerMenu(self.slotid, cur[2])
			else:
				self.handler.answerMenu(self.slotid, 0)
			self.showWait()
		elif self.tag == "LIST":
			print "answer LIST"
			self.handler.answerMenu(self.slotid, 0)
			self.showWait()
		elif self.tag == "ENQ":
			cur = self["entries"].getCurrent()
			answer = str(cur[1].value)
			length = len(answer)
			while length < cur[1].getLength():
				answer = '0'+answer
				length+=1
			self.handler.answerEnq(self.slotid, answer)
			self.showWait()

	def closeMmi(self):
		self.timer.stop()
		self.close(self.slotid)

	def keyCancel(self):
		self.timer.stop()
		if not self.tag or self.mmiclosed:
			self.closeMmi()
		elif self.tag == "WAIT":
			self.handler.stopMMI(self.slotid)
			self.closeMmi()
		elif self.tag in ( "MENU", "LIST" ):
			print "cancel list"
			self.handler.answerMenu(self.slotid, 0)
			self.showWait()
		elif self.tag == "ENQ":
			print "cancel enq"
			self.handler.cancelEnq(self.slotid)
			self.showWait()
		else:
			print "give cancel action to ci"

	def keyConfigEntry(self, key):
		self.timer.stop()
		try:
			self["entries"].handleKey(key)
		except:
			pass

	def keyNumberGlobal(self, number):
		self.timer.stop()
		self.keyConfigEntry(KEY_0 + number)

	def keyLeft(self):
		self.timer.stop()
		self.keyConfigEntry(KEY_LEFT)

	def keyRight(self):
		self.timer.stop()
		self.keyConfigEntry(KEY_RIGHT)

	def updateList(self, list):
		List = self["entries"]
		try:
			List.instance.moveSelectionTo(0)
		except:
			pass
		List.l.setList(list)

	def showWait(self):
		self.tag = "WAIT"
		self["title"].setText("")
		self["subtitle"].setText("")
		self["bottom"].setText("")
		list = [ ]
		list.append( (self.wait_text, ConfigNothing()) )
		self.updateList(list)

	def showScreen(self):
		screen = self.handler.getMMIScreen(self.slotid)

		list = [ ]

		self.timer.stop()
		if len(screen) > 0 and screen[0][0] == "CLOSE":
			timeout = screen[0][1]
			self.mmiclosed = True
			if timeout > 0:
				self.timer.start(timeout*1000, True)
			else:
				self.keyCancel()
		else:
			self.mmiclosed = False
			self.tag = screen[0][0]
			for entry in screen:
				if entry[0] == "PIN":
					self.addEntry(list, entry)
				else:
					if entry[0] == "TITLE":
						self["title"].setText(entry[1])
					elif entry[0] == "SUBTITLE":
						self["subtitle"].setText(entry[1])
					elif entry[0] == "BOTTOM":
						self["bottom"].setText(entry[1])
					elif entry[0] == "TEXT":
						self.addEntry(list, entry)
			self.updateList(list)

	def ciStateChanged(self):
		do_close = False
		if self.action == 0:			#reset
			do_close = True
		if self.action == 1:			#init
			do_close = True

		#module still there ?
		if self.handler.getState(self.slotid) != 2:
			do_close = True

		#mmi session still active ?
		if self.handler.getMMIState(self.slotid) != 1:
			do_close = True

		if do_close:
			self.closeMmi()
		elif self.action > 1 and self.handler.availableMMI(self.slotid) == 1:
			self.showScreen()

		#FIXME: check for mmi-session closed

class CiMessageHandler:
	def __init__(self):
		self.session = None
		self.ci = { }
		self.dlgs = { }
		eDVBCI_UI.getInstance().ciStateChanged.get().append(self.ciStateChanged)

	def setSession(self, session):
		self.session = session

	def ciStateChanged(self, slot):
		if slot in self.ci:
			self.ci[slot](slot)
		else:
			if slot in self.dlgs:
				self.dlgs[slot].ciStateChanged()
			elif eDVBCI_UI.getInstance().availableMMI(slot) == 1:
				if self.session:
					self.dlgs[slot] = self.session.openWithCallback(self.dlgClosed, MMIDialog, slot, 3)

	def dlgClosed(self, slot):
		if slot in self.dlgs:
			del self.dlgs[slot]

	def registerCIMessageHandler(self, slot, func):
		self.unregisterCIMessageHandler(slot)
		self.ci[slot] = func

	def unregisterCIMessageHandler(self, slot):
		if slot in self.ci:
			del self.ci[slot]

CiHandler = CiMessageHandler()

class CiSelection(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["OkCancelActions", "CiSelectionActions"],
			{
				"left": self.keyLeft,
				"right": self.keyLeft,
				"ok": self.okbuttonClick,
				"cancel": self.cancel
			},-1)

		self.dlg = None
		self.state = { }
		self.slots = []
		self.HighBitrateEntry = {}
		self.RelevantPidsRoutingEntry = {}

		self.entryData = []
		self.DVBCiDelayEntry = None

		self.list = [ ]
		self["entries"] = ConfigList(self.list)
		self["entries"].list = self.list
		self["entries"].l.setList(self.list)
		self["text"] = Label(_("Slot %d")%(1))
		self.onLayoutFinish.append(self.initialUpdate)

	def initialUpdate(self):
		for slot in range(SystemInfo["CommonInterface"]):
			state = eDVBCI_UI.getInstance().getState(slot)
			if state != -1:
				self.slots.append(slot)
				self.state[slot] = state
				self.createEntries(slot)
				CiHandler.registerCIMessageHandler(slot, self.ciStateChanged)

		self.slots.sort()
		self.updateEntries()
		if self.slots:
			self["text"].setText(_("Slot %d")% (int(self.slots[0])+1))

	def selectionChanged(self):
		entryData = self.entryData[self["entries"].getCurrentIndex()]
		self["text"].setText(_("Slot %d")%(entryData[1] + 1))

	def keyConfigEntry(self, key):
		current = self["entries"].getCurrent()
		try:
			self["entries"].handleKey(key)
			current[1].save()
		except:
			pass

	def keyLeft(self):
		self.keyConfigEntry(KEY_LEFT)

	def keyRight(self):
		self.keyConfigEntry(KEY_RIGHT)

	def createEntries(self, slot):
		if SystemInfo["CI%dSupportsHighBitrates" % slot]:
			self.HighBitrateEntry[slot] = getConfigListEntry(_("High bitrate support"), config.ci[slot].canHandleHighBitrates)
		if SystemInfo["CI%dRelevantPidsRoutingSupport" % slot]:
			self.RelevantPidsRoutingEntry[slot] = getConfigListEntry(_("Relevant PIDs Routing"), config.ci[slot].relevantPidsRouting)
		if SystemInfo["CommonInterfaceCIDelay"] and self.DVBCiDelayEntry is None:
			self.DVBCiDelayEntry = getConfigListEntry(_("DVB CI Delay"), config.cimisc.dvbCiDelay)

	def addToList(self, data, action, slotid):
		self.list.append(data)
		self.entryData.append((action, slotid))

	def updateEntries(self):
		self.list = []
		self.entryData = []

		for slot in self.slots:
			self.addToList((_("Reset"), ConfigNothing()), 0, slot)
			self.addToList((_("Init"), ConfigNothing()), 1, slot)

			if self.state[slot] == 0:			#no module
				self.addToList((_("no module found"), ConfigNothing()), 2, slot)
			elif self.state[slot] == 1:		#module in init
				self.addToList((_("init module"), ConfigNothing()), 2, slot)
			elif self.state[slot] == 2:		#module ready
				#get appname
				appname = eDVBCI_UI.getInstance().getAppName(slot)
				self.addToList((appname, ConfigNothing()), 2, slot)

			self.addToList(getConfigListEntry(_("Multiple service support"), config.ci[slot].canDescrambleMultipleServices), -1, slot)

			if SystemInfo["CI%dSupportsHighBitrates" % slot]:
				self.addToList(self.HighBitrateEntry[slot], -1, slot)
			if SystemInfo["CI%dRelevantPidsRoutingSupport" % slot]:
				self.addToList(self.RelevantPidsRoutingEntry[slot], -1, slot)
			if SystemInfo["CommonInterfaceCIDelay"]:
				self.addToList(self.DVBCiDelayEntry, -1, slot)

		self["entries"].list = self.list
		self["entries"].l.setList(self.list)
		if self.selectionChanged not in self["entries"].onSelectionChanged:
			self["entries"].onSelectionChanged.append(self.selectionChanged)

	def ciStateChanged(self, slot):
		if self.dlg:
			self.dlg.ciStateChanged()
		else:
			state = eDVBCI_UI.getInstance().getState(slot)
			if self.state[slot] != state:
				#print "something happens"
				self.state[slot] = state
				self.updateEntries()

	def dlgClosed(self, slot):
		self.dlg = None

	def okbuttonClick(self):
		cur = self["entries"].getCurrent()
		if cur:
			idx = self["entries"].getCurrentIndex()
			entryData = self.entryData[idx]
			action = entryData[0]
			slot = entryData[1]
			if action == 0:		#reset
				eDVBCI_UI.getInstance().setReset(slot)
			elif action == 1:		#init
				eDVBCI_UI.getInstance().setInit(slot)
			elif action == 2 and self.state[slot] == 2:
				self.dlg = self.session.openWithCallback(self.dlgClosed, MMIDialog, slot, action)

	def cancel(self):
		for slot in range(SystemInfo["CommonInterface"]):
			state = eDVBCI_UI.getInstance().getState(slot)
			if state != -1:
				CiHandler.unregisterCIMessageHandler(slot)
		self.close()
