from Plugins.Plugin import PluginDescriptor

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.DefaultWizard import DefaultWizard
from Screens.Standby import TryQuitMainloop
from Screens.VirtualKeyBoard import VirtualKeyBoard

from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.ActionMap import NumberActionMap, ActionMap
from Components.Network import iNetwork
from Components.MenuList import MenuList
from Components.config import config, getConfigListEntry, ConfigInteger, ConfigSubsection, ConfigSelection, ConfigText, ConfigYesNo, NoSave, ConfigNothing
from Components.ConfigList import ConfigListScreen
from Components.Pixmap import Pixmap

from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_CURRENT_PLUGIN

from enigma import eTimer, eConsoleAppContainer, eSocketNotifier, getDesktop
from select import POLLIN, POLLPRI
from xml.sax import make_parser, handler
import os, socket, time

debug_mode_modem_mgr = False
def printDebugModemMgr(msg):
	global debug_mode_modem_mgr
	if debug_mode_modem_mgr:
		print "[ModemManager Plugin] Debug >>", msg

def printInfoModemMgr(msg):
	print "[ModemManager Plugin] Info >>", msg

class DeviceEventListener:
	notifyCallbackFunctionList = []
	def __init__(self):
		self.sock = socket.socket(socket.AF_NETLINK, socket.SOCK_DGRAM, 15)
		try:		
			self.sock.bind((os.getpid(), 1))
			self.notifier = eSocketNotifier(self.sock.fileno(), POLLIN|POLLPRI)
			self.notifier.callback.append(self.cbEventHandler)
		except Exception, msg:
			print "[ModemManager Plugin] Error >>", msg
			self.sock.close()

	def cbEventHandler(self, sockfd):
		recv = self.sock.recv(65536)
		#printDebugModemMgr(str(recv.splitlines()))
		if recv.startswith("add@/block") or recv.startswith("remove@/block"):
			for x in self.notifyCallbackFunctionList:
				try: 	x(recv)
				except:	self.notifyCallbackFunctionList.remove(x)

	def addCallback(self, func):
		if func is not None:
			self.notifyCallbackFunctionList.append(func)

	def delCallback(self, func):
		if func is not None:
			self.notifyCallbackFunctionList.remove(func)

	def close(self):
		try:
			self.notifier.callback.remove(self.cbEventHandler)
			self.sock.close()
		except: pass

class TaskManager:
	def __init__(self):
		self.taskIdx = 0
		self.taskList = []
		self.gTaskInstance = None
		self.occurError = False
		self.cbSetStatusCB = None

	def append(self, command, cbDataFunc, cbCloseFunc):
		self.taskList.append([command+'\n', cbDataFunc, cbCloseFunc])

	def dump(self):
		print "############### TASK ###############"
		print "Current Task Index :", self.taskIdx
		print "Current Task Instance :", self.gTaskInstance
		print "Occur Error :", self.occurError
		print "Task List:\n", self.taskList
		print "####################################"

	def error(self):
		printInfoModemMgr("set task error!!")
		self.occurError = True

	def reset(self):
		self.taskIdx = 0
		self.gTaskInstance = None
		self.occurError = False

	def clean(self):
		self.reset()
		self.taskList = []
		self.cbSetStatusCB = None
		print "clear task!!"

	def index(self):
		self.taskIdx

	def setStatusCB(self, cbfunc):
		self.cbSetStatusCB = cbfunc
		
	def next(self):
		if self.taskIdx >= len(self.taskList) or self.occurError:
			printInfoModemMgr("can't run task!!")
			return False
		command     = self.taskList[self.taskIdx][0]
		cbDataFunc  = self.taskList[self.taskIdx][1]
		cbCloseFunc = self.taskList[self.taskIdx][2]

		self.gTaskInstance = eConsoleAppContainer()
		if cbDataFunc is not None:
			self.gTaskInstance.dataAvail.append(cbDataFunc)
		if cbCloseFunc is not None:
			self.gTaskInstance.appClosed.append(cbCloseFunc)
		if self.cbSetStatusCB is not None:
			self.cbSetStatusCB(self.taskIdx)

		printInfoModemMgr("prepared command :%s"%(command))
		self.gTaskInstance.execute(command)
		self.taskIdx += 1
		return True

class ParserHandler(handler.ContentHandler):
	nodeList = []
	def startDocument(self):
		pass
	def endDocument(self):  
		pass
	def startElement(self, name, attrs):
		if name == 'apn':
			node = {}
			for attr in attrs.getNames():
				node[attr] = attrs.getValue(attr)
			self.nodeList.append(node)
	def endElement(self, name):
		pass
	def characters(self, content):
		pass
	def setDocumentLocator(self, locator):
		pass
	def getNodeList(self):
		return self.nodeList

class EditModemManual(ConfigListScreen, Screen):
	param = int(getDesktop(0).size().height()) >= 720 and (450,360) or (160,300)
	skin = 	"""
		<screen position="center,center" size="600,360" title="3G Modem Manager Config Edit">
			<widget name="config" zPosition="2" position="0,0" size="600,300" scrollbarMode="showOnDemand" transparent="1" />

			<ePixmap pixmap="skin_default/buttons/red.png" position="5,320" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="155,320" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="305,320" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="455,320" size="140,40" alphatest="on" />

			<widget source="key_red" render="Label" position="5,320" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="155,320" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />

			<widget name="VKeyIcon" pixmap="skin_default/buttons/key_text.png" position="50,200" zPosition="10" size="35,25" transparent="1" alphatest="on" />
			<widget name="HelpWindow" pixmap="skin_default/vkey_icon.png" position="%d,%d" zPosition="1" size="1,1" transparent="1" alphatest="on" />
		</screen>
		""" % param

	def __init__(self, session, cbFuncClose, uid=None, pwd=None, pin=None, apn=None, phone='*99#'):
		Screen.__init__(self, session)
		self.cbFuncClose,self.uid,self.pwd,self.pin,self.apn,self.phone = cbFuncClose,uid,pwd,pin,apn,phone

		self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions", "WizardActions", "ColorActions", "SetupActions",],
		{
			"ok":     self.keyOK,
			"cancel": self.keyExit,
			"red":    self.keyExit,
			"green":  self.keyOK,
		}, -2)

		self["VirtualKB"] = ActionMap(["VirtualKeyboardActions" ],
		{
			"showVirtualKeyboard": self.KeyText,
		}, -1)

		self.configList = []
		ConfigListScreen.__init__(self, self.configList, session=session)
		self.createConfigList()

		self["key_red"]    = StaticText(_("Cancel"))
		self["key_green"]  = StaticText(_("Save"))
		self["VKeyIcon"]   = Pixmap()
		self["HelpWindow"] = Pixmap()
		self["VirtualKB"].setEnabled(False)

	def createConfigList(self):
		self.configUserName = ConfigText(default=str(self.uid), visible_width=50, fixed_size=False)
		self.configPassword = ConfigText(default=str(self.pwd), visible_width=50, fixed_size=False)
		self.configAPN      = ConfigText(default=str(self.apn), visible_width=50, fixed_size=False)
		self.configPIN      = ConfigText(default=str(self.pin), visible_width=50, fixed_size=False)
		self.configPhone    = ConfigText(default=str(self.phone), visible_width=50, fixed_size=False)

		self.configEntryUserName = getConfigListEntry(_("User :"),     self.configUserName)
		self.configEntryPassword = getConfigListEntry(_("Password :"), self.configPassword)
		self.configEntryAPN      = getConfigListEntry(_("APN :"),      self.configAPN)
		self.configEntryPIN      = getConfigListEntry(_("PIN :"),      self.configPIN)
		self.configEntryPhone    = getConfigListEntry(_("Phone :"),    self.configPhone)

		self.configList.append(self.configEntryUserName)
		self.configList.append(self.configEntryPassword)
		self.configList.append(self.configEntryAPN)
		self.configList.append(self.configEntryPIN)
		self.configList.append(self.configEntryPhone)

		self["config"].list = self.configList
		self["config"].l.setList(self.configList)

	def getCurrentItem(self):
		currentPosition = self["config"].getCurrent()
		if currentPosition == self.configEntryUserName:
			return self.configUserName
		elif currentPosition == self.configEntryPassword:
			return self.configPassword
		elif currentPosition == self.configEntryAPN:
			return self.configAPN
		elif currentPosition == self.configEntryPIN:
			return self.configPIN
		elif currentPosition == self.configEntryPhone:
			return self.configPhone
		return None

	def KeyText(self):
		currentItemValue = ""
		currentItem = self.getCurrentItem()
		if currentItem is None:
			currentItemValue = currentItem.value
		self.session.openWithCallback(self.cbKeyText, VirtualKeyBoard, title=("Please enter ap-info here"), text=currentItemValue)

	def cbKeyText(self, data=None):
		if data is not None:
			currentItem = self.getCurrentItem()
			if currentItem is not None:
				currentItem.setValue(data)

	def keyExit(self):
		self.close()

	def keyOK(self):
		if self.cbFuncClose is not None:
			self.uid = self.configUserName.value
			self.pwd = self.configPassword.value
			self.pin = self.configPIN.value
			self.apn = self.configAPN.value
			self.phone = self.configPhone.value
			self.cbFuncClose(self.uid,self.pwd,self.pin,self.apn,self.phone)
		self.close()


class ModemManual(Screen):
	skin = 	"""
		<screen position="center,center" size="600,360" title="3G Modem Manager Config">
			<widget name="menulist" position="0,0" size="300,300" backgroundColor="#000000" zPosition="10" scrollbarMode="showOnDemand" />
			<widget name="apnInfo" position="310,0" size="290,300" font="Regular;20" halign="left" backgroundColor="#a08500" transparent="1" />

			<ePixmap pixmap="skin_default/buttons/red.png" position="5,320" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="155,320" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="305,320" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="455,320" size="140,40" alphatest="on" />

			<widget source="key_red" render="Label" position="5,320" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="155,320" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_yellow" render="Label" position="305,320" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#a08500"  foregroundColor="#ffffff" transparent="1" />
		</screen>
		"""

	def __init__(self, session, cbFuncClose, uid=None, pwd=None, pin=None, apn=None, phone='*99#'):
		Screen.__init__(self, session)
		self.cbFuncClose,self.uid,self.pwd,self.pin,self.apn,self.phone = cbFuncClose,uid,pwd,pin,apn,phone
		self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions", "WizardActions", "ColorActions", "SetupActions"],
		{
			"ok":     self.keyOK,
			"cancel": self.keyExit,
			"red":    self.keyExit,
			"green":  self.keyOK,
			"yellow": self.keyEdit,
			"left":   self.keyLeft,
			"right":  self.keyRight,
			"up":     self.keyUp,
			"down":   self.keyDown,
		}, -2)

		self.apnItems = self.setListOnView()
		self["menulist"]   = MenuList(self.apnItems)
		self["key_red"]    = StaticText(_("Cancel"))
		self["key_green"]  = StaticText(_("OK"))
		self["key_yellow"] = StaticText(_("Edit"))
		self["apnInfo"]    = Label(' ')

		self.updateAPNInfo()

	def keyEdit(self):
		self.session.open(EditModemManual, self.cb3GManualSetting, self.uid,self.pwd,self.pin,self.apn,self.phone)

	def cb3GManualSetting(self, uid=None, pwd=None, pin=None, apn=None, phone='*99#'):
		self.uid,self.pwd,self.pin,self.apn,self.phone = uid, pwd, pin, apn, phone
		self.updateAPNInfo()

	def keyLeft(self):
		self['menulist'].pageUp()
		self.setAPNInfo()

	def keyRight(self):
		self['menulist'].pageDown()
		self.setAPNInfo()

	def keyUp(self):
		self['menulist'].up()
		self.setAPNInfo()

	def keyDown(self):
		self['menulist'].down()
		self.setAPNInfo()

	def keyOK(self):
		if self.cbFuncClose is not None:
			self.cbFuncClose(self.uid,self.pwd,self.pin,self.apn,self.phone)
		self.close()

	def keyExit(self):
		self.close()

	def setAPNInfo(self):
		try:
			x = self["menulist"].getCurrent()[1]
			self.apn, self.uid, self.pwd = x.get("apn"), x.get("user"), x.get("password")
		except Exception, err: 
			pass
		self.updateAPNInfo()

	def updateAPNInfo(self):
		info = 'APN : %s\nUSER : %s\nPASSWD : %s\nPIN : %s\nPHONE : %s\n' % (str(self.apn), str(self.uid), str(self.pwd), str(self.pin), str(self.phone))
		self["apnInfo"].setText(info)

	def setListOnView(self):
		lvApnItems = []
		def uppercaseCompare(a,b):
			aa = str(a.get("carrier"))
			bb = str(b.get("carrier"))
			return cmp(aa.upper(),bb.upper())
		def isExistAPN(name):
			for x in lvApnItems:
				if x[0] == name:
					return True
			return False
		try:
			handle = ParserHandler()
			parser = make_parser()
			parser.setContentHandler(handle)
			parser.parse(resolveFilename(SCOPE_CURRENT_PLUGIN, "SystemPlugins/3GModemManager/apnlist.xml"))

			apnList = handle.getNodeList()
			apnList.sort(uppercaseCompare)
			for x in apnList:
				name = str(x.get('carrier'))
				if name is None or name == 'None':
					continue
				if isExistAPN(name):
					continue
				d = {}
				d['apn'] = str(x.get('apn'))
				d['user'] = str(x.get('user'))
				d['password'] = str(x.get('password'))
				lvApnItems.append((name,d))
		except Exception, err: 
			print "ERROR >>", err
			pass
		return lvApnItems

class ModemManager(Screen):
	skin = 	"""
		<screen position="center,center" size="600,360" title="3G Modem Manager">
			<widget name="menulist" position="0,0" size="300,150" backgroundColor="#000000" zPosition="10" scrollbarMode="showOnDemand" />
			<widget name="usbinfo" position="310,0" size="290,150" font="Regular;18" halign="left" />

			<widget name="statusTitle" position="0,160" size="600,120" font="Regular;20" halign="center" backgroundColor="#a08500" transparent="1" />
			<widget name="statusInfo" position="0,185" size="600,120" font="Regular;20" halign="left" backgroundColor="#a08500" transparent="1" />

			<ePixmap pixmap="skin_default/buttons/red.png" position="5,320" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="155,320" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="305,320" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="455,320" size="140,40" alphatest="on" />

			<widget source="key_red" render="Label" position="5,320" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_green" render="Label" position="155,320" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" foregroundColor="#ffffff" transparent="1" />
			<widget source="key_yellow" render="Label" position="305,320" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#a08500"  foregroundColor="#ffffff" transparent="1" />
			<widget source="key_blue" render="Label" position="455,320" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#18188b"  foregroundColor="#ffffff" transparent="1" />
		</screen>
		"""
	uid,pwd,pin,apn,phone = None,None,None,None,'*99#'
	connectionStatus = 0
	def __init__(self, session): 
		Screen.__init__(self, session)
		self.usb_lv_items = self.setListOnView()

		self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions", "WizardActions", "ColorActions", "SetupActions", "NumberActions"],
		{
			"ok":     self.keyOK,
			"cancel": self.keyExit,
			"red":    self.keyExit,
			"green":  self.keyOK,
			"yellow": self.keyManual,
			"blue":   self.keyReset,
			"up":     self.keyUp,
			"down":   self.keyDown,
			"left":   self.keyLeft,
			"right":  self.keyRight,
			"0":      self.keyNumber,
		}, -2)
		self["menulist"] = MenuList(self.usb_lv_items)
		self['usbinfo'] = Label(' ')
		self['statusTitle'] = Label('[ Status ]')
		self['statusInfo'] = Label(' ')
		self["key_red"] = StaticText(_("Exit"))
		if self.isConnected():
			self["key_green"] = StaticText("Disconnect")
			self.setDisconnectStatus(0)
		else:
			self["key_green"] = StaticText("Connect")
			self.setConnectStatus(0)
		self["key_yellow"] = StaticText(_("Manual"))
		self["key_blue"] = StaticText(_("Reset"))

		self.updateUSBInfo()

		self.udevListener = DeviceEventListener()
		self.udevListener.addCallback(self.cbUdevListener)

		self.taskManager = TaskManager()

		self.refreshStatusTimer = eTimer()
		self.refreshStatusTimer.callback.append(self.cbRefreshStatus)

		#self.restartAppTimer = eTimer()
		#self.restartAppTimer.callback.append(self.cbRestartAppTimer)

		self.forceStop = False

	def cbRestartAppTimer(self):
		self.restartAppTimer.stop()
		model = file('/proc/stb/info/vumodel').read().strip()
		if model is not None:
			if model == 'solo' or model == 'bm750':
				self.session.open(TryQuitMainloop, 3)

	def cbRefreshStatus(self):
		self.refreshStatusTimer.stop()
		if self["key_green"].getText() == 'Connect':
			self.setConnectStatus(0)
		elif self["key_green"].getText() == 'Disconnect': 
			self.setDisconnectStatus(0)

	def cbUdevListener(self, data):
		printDebugModemMgr('Udev Listener Refresh!!')
		time.sleep(2)
		self["menulist"].setList(self.setListOnView())
		self.updateUSBInfo()

	def isAttemptConnect(self):
		if self.connectionStatus == 0 or self.forceStop:
			return False
		maxIdx = 4
		if self["key_green"].getText() == 'Disconnect':
			maxIdx = 2
		if self.connectionStatus < maxIdx:
			printInfoModemMgr("can't excute a command during connecting...")
			return True
		return False

	def keyManual(self):
		if self.isAttemptConnect():
			return
		self.session.open(ModemManual, self.cb3GManualSetting, self.uid,self.pwd,self.pin,self.apn,self.phone)

	def keyReset(self):
		if self.isAttemptConnect():
			return
		self.cb3GManualSetting()

	def cb3GManualSetting(self, uid=None, pwd=None, pin=None, apn=None, phone='*99#'):
		self.uid,self.pwd,self.pin,self.apn,self.phone = uid,pwd,pin,apn,phone
		self.updateUSBInfo()

	def keyNumber(self, num=None):
		global debug_mode_modem_mgr
		debug_mode_modem_mgr = not debug_mode_modem_mgr
		printInfoModemMgr('changed log mode, debug %s'%(debug_mode_modem_mgr and 'on' or 'off'))

	def keyExit(self):
		if self.isAttemptConnect():
			message = "Can't disconnect doring connecting.."
			self.session.open(MessageBox, _(message), MessageBox.TYPE_INFO)
			return
		self.udevListener.close()
		self.close()

	def keyLeft(self):
		self["menulist"].pageUp()
		self.updateUSBInfo()

	def keyRight(self):
		self["menulist"].pageDown()
		self.updateUSBInfo()

	def keyUp(self):
		self["menulist"].up()
		self.updateUSBInfo()

	def keyDown(self):
		self["menulist"].down()
		self.updateUSBInfo()

	def keyOK(self):
		self.forceStop = False
		if self.isAttemptConnect():
			return

		def areadyExistAnotherAdapter():
			networkAdapters = iNetwork.getConfiguredAdapters()
			for x in networkAdapters:
				if x[:3] != 'ppp':
					return True
			return False

		if self["key_green"].getText() == 'Disconnect':
			message = "Do you want to disconnect?"
			self.session.openWithCallback(self.cbConfirmDone, MessageBox, _(message), default = False)
			return

		if areadyExistAnotherAdapter():
			message = "Another adapter connected has been found.\n\nA connection is attempted after disconnect all of other device. Do you want to?"
			self.session.openWithCallback(self.cbConfirmDone, MessageBox, _(message), default = True)
		else:	self.cbConfirmDone(True)

	def cbConfirmDone(self, ret):
		if not ret: return
		if self["key_green"].getText() == 'Connect':
			networkAdapters = iNetwork.getConfiguredAdapters()
			for x in networkAdapters:
				if x[:3] == 'ppp': continue
				iNetwork.setAdapterAttribute(x, "up", False)
				iNetwork.deactivateInterface(x)

		x = {}
		try: x = self["menulist"].getCurrent()[1]
		except:
			printInfoModemMgr('no selected device..')
			return

		devFile = '/usr/share/usb_modeswitch/%s:%s' % (x.get("Vendor"), x.get("ProdID"))
		if not os.path.exists(devFile) :
			message = "Can't found device file!! [%s]" % (devFile)
			printInfoModemMgr(message)
			self.session.open(MessageBox, _(message), MessageBox.TYPE_INFO)
			return

		commandBin = resolveFilename(SCOPE_CURRENT_PLUGIN, "SystemPlugins/3GModemManager/3gcommand")
		if self["key_green"].getText() == 'Disconnect':
			cmd = "%s -s 0" % (commandBin)
			self.taskManager.append(cmd, self.cbPrintAvail, self.cbPrintClose)

			cmd = "%s -s 1" % (commandBin)
			self.taskManager.append(cmd, self.cbPrintAvail, self.cbUnloadClose)
			self.taskManager.setStatusCB(self.setDisconnectStatus)
		else:
			cmd = "%s -s 2 -e vendor=0x%s -e product=0x%s" % (commandBin, x.get("Vendor"), x.get("ProdID"))
			self.taskManager.append(cmd, self.cbStep1PrintAvail, self.cbPrintClose)

			cmd = "%s -s 3 -e %s:%s" % (commandBin, x.get("Vendor"), x.get("ProdID"))
			self.taskManager.append(cmd, self.cbPrintAvail, self.cbPrintClose)

			cmd = "%s -s 4" % (commandBin)
			self.taskManager.append(cmd, self.cbStep3PrintAvail, self.cbMakeWvDialClose)

			cmd = "%s -s 5" % (commandBin)
			self.taskManager.append(cmd, self.cbRunWvDialAvail, self.cbPrintClose)
			self.taskManager.setStatusCB(self.setConnectStatus)
		
		self.taskManager.next()

	def printStatus(self, idx, STATUS):
		message = ''
		self.connectionStatus = idx
		for x in range(0,len(STATUS)):
			if idx == x:
				message += '  > '
			else: 	message += '      '
			message += STATUS[x]
			message += '\n'
		self['statusInfo'].setText(message)

	def setConnectStatus(self, idx):
		STATUS = {
		 0:'1. Load a Mobile Broadband Device'
		,1:'2. Set up a Mobile Broadband Device'
		,2:'3. Generate a WvDial profile'
		,3:'4. Attempt to connect'
		,4:'5. Done'
		}
		self.printStatus(idx, STATUS)

	def setDisconnectStatus(self, idx):
		STATUS = {
		 0:'1. Drop WvDial'
		,1:'2. Unload a Mobile Broadband Device'
		,2:'3. Done'
		}
		self.printStatus(idx, STATUS)

	def cbStep1PrintAvail(self, data):
		print data
		if data.find('modules.dep') > -1:
			self.forceStop = True

	def cbStep3PrintAvail(self, data):
		print data
		if data.find('Sorry, no modem was detected') > -1:
			self.forceStop = True

	def cbPrintAvail(self, data):
		print data

	def cbPrintClose(self, ret):
		if self.forceStop:
			self.taskManager.clean()
			time.sleep(2)
			message = "Occur error during connection...\nPlease, check log!!"
			self.session.open(MessageBox, _(message), MessageBox.TYPE_INFO)
			return
		self.taskManager.next()

	def cbUnloadClose(self, ret):
		self.taskManager.clean()
		time.sleep(2)
		self["key_green"].setText('Connect')
		self.setDisconnectStatus(2)
		self.refreshStatusTimer.start(1000)

	def cbRunWvDialAvail(self, data):
		print data
		if data.find('Pid of pppd:') > -1:
			self.taskManager.clean()
			time.sleep(2)
			self["key_green"].setText('Disconnect')
			self.setConnectStatus(4)
			self.refreshStatusTimer.start(1000)
			#self.restartAppTimer.start(3000)

	def cbMakeWvDialClose(self, ret):
		info = {}
		try:
	
			datalist = file('/etc/wvdial.conf').read().splitlines()
			for x in datalist:
				if x.startswith('Modem ='):
					print x
					info['Modem'] = x[7:].strip()
				elif x.startswith('Init2 ='):
					print x
					info['Init'] = x[7:].strip()
				elif x.startswith('Baud ='):
					print x
					info['Baud'] = x[6:].strip()
		except Exception, err: 
			printDebugModemMgr("getModemInfo Error : [%s]" % (str(err)))
			# TODO : occur error!!
			return

		if self.apn is not None:
			info['apn'] = self.apn
		if self.uid is not None:
			info['uid'] = self.uid
		if self.pwd is not None:
			info['pwd'] = self.pwd
		if self.pin is not None:
			info['pin'] = self.pin
		if self.phone is not None:
			info['phone'] = self.phone
		#info['phone'] = '*99#'
		self.makeWvDialConf(info)
		self.taskManager.next()

	def writeConf(self, data, oper='>>'):
		confFile = '/etc/wvdial.conf'
		if oper == '>':
			os.system('mv %s %s.bak' % (confFile, confFile))
		cmd = "echo '%s' %s %s" % (data, oper, confFile)
		os.system(cmd)

	def makeWvDialConf(self, params):
		baud  = params.get('Baud')
		init  = params.get('Init')
		modem = params.get('Modem')
		phone = params.get('phone')
		apn = params.get('apn')
		uid = params.get('uid')
		pwd = params.get('pwd')
		pin = params.get('pin')
		idxInit = 1

		self.writeConf('','>')

		self.writeConf('[Dialer Defaults]')
		if modem is None or init is None or baud is None:
			return False
		self.writeConf('Modem = %s' % (modem))
		self.writeConf('Baud = %s' % (baud))
		self.writeConf('Dial Command = ATDT')
		self.writeConf('Init%d = ATZ' % (idxInit))
		idxInit = idxInit + 1
		if pin is not None:
			writeConf('Init%d = AT+CPIN=%s' % (init_idx, pin))
			idxInit = idxInit + 1
		self.writeConf('Init%d = %s' % (idxInit, init))
		idxInit = idxInit + 1
		if apn is None and uid is None and pwd is None and pin is None:
			self.writeConf('Init%d = AT&F' % (idxInit))
			idxInit = idxInit + 1
		if apn is not None:
			self.writeConf('Init%d = AT+CGDCONT=1,"IP","%s"' % (idxInit, apn))
			idxInit = idxInit + 1
		self.writeConf('Init%d = AT+CFUN = 1' % (idxInit))
		self.writeConf('Username = %s' % (uid))
		self.writeConf('Password = %s' % (pwd))
		self.writeConf('Phone = %s' % (phone)) #*99#
		self.writeConf('Modem Type = Analog Modem')
		self.writeConf('ISDN = 0')
		self.writeConf('Carrier Check = 0')
		self.writeConf('Abort on No Dialtone = 0')
		self.writeConf('Stupid Mode = 1')
		self.writeConf('Check DNS = 1')
		self.writeConf('Check Def Route = 1')
		self.writeConf('Auto DNS = 1')

	def isConnected(self):
		return len(os.popen('ifconfig -a | grep ppp').read().strip()) > 0

	def updateUSBInfo(self):
		info = ' '
		try:
			x = self["menulist"].getCurrent()[1]
			info = 'Vendor : %s/%s\nAPN : %s\nUser : %s\nPassword : %s\nPin : %s\nPhone : %s' % (
					x.get("Vendor"), 
					x.get("ProdID"), 
					str(self.apn),
					str(self.uid),
					str(self.pwd),
					str(self.pin),
					str(self.phone)
				)
		except: pass
		self['usbinfo'].setText(info)

	def setListOnView(self):
		lv_usb_items = []
		try:
			for x in self.getUSBList():
				lv_usb_items.append((x.get("Product"),x))
		except: pass
		return lv_usb_items

	def getUSBList(self):
		parsed_usb_list = []
		usb_devices = os.popen('cat /proc/bus/usb/devices').read()
		tmp_device = {}
		for x in usb_devices.splitlines():
			if x is None or len(x) == 0:
				printDebugModemMgr("TMP DEVICE : [%s]" % (tmp_device))
				if len(tmp_device):
					parsed_usb_list.append(tmp_device)
				tmp_device = {}
				continue
			try:
				if x[0] in ('P', 'S', 'I', 'T'):
					tmp = x[2:].strip()
					printDebugModemMgr("TMP : [%s]" % (tmp))
					if tmp.startswith('Bus='):
						#printDebugModemMgr("TMP SPLIT for BUS : [%s]" % (str(tmp.split())))
						for xx in tmp.split():
							if xx.startswith('Bus='):
								tmp_device['Bus'] = xx[4:]
								break
					if tmp.startswith('Manufacturer='):
						tmp_device['Manufacturer'] = tmp[13:]
					if tmp.startswith('Product='):
						tmp_device['Product'] = tmp[8:]
					elif tmp.startswith('SerialNumber='):
						tmp_device['SerialNumber'] = tmp[13:]
					elif tmp.startswith('Vendor='):
						#printDebugModemMgr("TMP SPLIT for BUS : [%s]" % (str(tmp.split())))
						for xx in tmp.split():
							if xx.startswith('Vendor='):
								tmp_device['Vendor'] = xx[7:]
							elif xx.startswith('ProdID='):
								tmp_device['ProdID'] = xx[7:]
						#tmp_device['Vendor'] = tmp
					elif tmp.find('Driver=') > 0:
						d = tmp[tmp.find('Driver=')+7:]
						if d != '(none)':
							tmp_device['Interface'] = d
			except Exception, errmsg:
				print errmsg
		if len(tmp_device):
			parsed_usb_list.append(tmp_device)
		printDebugModemMgr("PARSED DEVICE LIST : " + str(parsed_usb_list))
		rt_usb_list = []
		for x in parsed_usb_list:
			printDebugModemMgr('Looking >> ' + str(x))
			try:
				xx = x.get("Interface")
				if xx.startswith('usb'):
					rt_usb_list.append(x)
			except: pass
		printInfoModemMgr("USB DEVICE LIST : " + str(rt_usb_list))
		return rt_usb_list

def main(session, **kwargs):
	session.open(ModemManager)
                                                           
def Plugins(**kwargs):            
	return PluginDescriptor(name=_("Modem Manager"), description="management 3g modem", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main)

