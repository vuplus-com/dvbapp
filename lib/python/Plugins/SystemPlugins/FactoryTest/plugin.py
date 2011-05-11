from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor
from Components.MenuList import MenuList
from Tools.Directories import fileExists
from Components.ServiceList import ServiceList
from Components.ActionMap import ActionMap,NumberActionMap
from Components.config import config
from os import system,access,F_OK,R_OK,W_OK
from Components.Label import Label
from Components.AVSwitch import AVSwitch
from time import sleep
from Components.Console import Console
from enigma import eTimer
from Components.HTMLComponent import HTMLComponent
from Components.GUIComponent import GUIComponent
from enigma import eListboxPythonStringContent, eListbox, gFont, eServiceCenter, eDVBResourceManager
from enigma import eServiceReference
from enigma import eMemtest
from enigma import eSctest
from enigma import eDVBDB
from Components.NimManager import nimmanager
from enigma import eDVBCI_UI,eDVBCIInterfaces

class TestResultList(HTMLComponent, GUIComponent):
	def __init__(self, list, enableWrapAround=False, content=eListboxPythonStringContent):
		GUIComponent.__init__(self)
		self.list = list
		self.l = content()
		self.l.setList(self.list)
		self.onSelectionChanged = [ ]
		self.enableWrapAround = enableWrapAround

	def getCurrent(self):
		return self.l.getCurrentSelection()

	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		self.instance.setSelectionEnable(0)
		instance.setContent(self.l)
		instance.selectionChanged.get().append(self.selectionChanged)
		if self.enableWrapAround:
			self.instance.setWrapAround(True)

	def preWidgetRemove(self, instance):
		instance.setContent(None)
		instance.selectionChanged.get().remove(self.selectionChanged)

	def selectionChanged(self):
		for f in self.onSelectionChanged:
			f()

	def getSelectionIndex(self):
		return self.l.getCurrentSelectionIndex()

	def getSelectedIndex(self):
		return self.l.getCurrentSelectionIndex()

	def setList(self, list):
		self.list = list
		self.l.setList(self.list)

	def updateList(self, list):
		self.list = list
		self.l.setList(self.list)

	def moveToIndex(self, idx):
		if self.instance is not None:
			self.instance.moveSelectionTo(idx)

	def pageUp(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.pageUp)

	def pageDown(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.pageDown)

	def up(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.moveUp)

	def down(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.moveDown)

	def selectionEnabled(self, enabled):
		if self.instance is not None:
			self.instance.setSelectionEnable(enabled)

class FactoryTest(Screen):
	skin = """
		<screen position="120,125" size="440,400" title="Test Menu" >
			<widget name="testlist" position="10,0" size="340,350" />
			<widget name="resultlist" position="370,0" size="60,350" />
			<widget name="testdate" position="20,350" size="150,25" font="Regular;22" />
			<widget name="testversion" position="20,375" size="150,25" font="Regular;22" />
			<widget name="mactext" position="180,350" size="230,25" font="Regular;22" />			
		</screen>"""
	def __init__(self, session):

		self["actions"] = NumberActionMap(["OkCancelActions","WizardActions","NumberActions","ColorActions",],
		{
			"left": self.nothing,
			"right":self.nothing,
			"ok": self.TestAction,
			"testexit": self.keyCancel,
			"agingstart": self.Agingmode,
			"up": self.keyup,
			"down": self.keydown,
			"0": self.numberaction,
			"1": self.numberaction,	
			"2": self.numberaction,			
			"3": self.numberaction,			
			"4": self.numberaction,			
			"5": self.numberaction,			
			"6": self.numberaction,			
			"7": self.numberaction,			
			"8": self.numberaction,			
			"9": self.numberaction,			
			"red": self.shutdownaction,
		}, -2)

		Screen.__init__(self, session)
		TESTPROGRAM_DATE = "2010-04-28"
		TESTPROGRAM_VERSION = "Version 01.10"

		self.model = 0
		self.getModelInfo()
		
		self["testdate"]=Label((TESTPROGRAM_DATE))
		self["testversion"]=Label(("Loading version..."))
		self["mactext"]=Label(("Loading mac address..."))
		if self.model == 0 or self.model == 1:
			nimConfig = nimmanager.getNimConfig(0)
			nimConfig.configMode.slot_id=0
			nimConfig.configMode.value= "simple"
			nimConfig.diseqcMode.value="diseqc_a_b"
			nimConfig.diseqcA.value="160"
			nimConfig.diseqcB.value="100"
		if self.model == 0:
			nimConfig = nimmanager.getNimConfig(1)
			nimConfig.configMode.slot_id=1		
			nimConfig.configMode.value= "simple"
			nimConfig.diseqcMode.value="diseqc_a_b"
			nimConfig.diseqcA.value="130"
			nimConfig.diseqcB.value="192"
		if self.model == 2:
			pass
		if self.model == 3 or self.model == 4:
			self.NimType = {}
			sat_list = ["160","100","130","192","620","642"]
			try:
				nimfile = open("/proc/bus/nim_sockets")
			except IOError:
				nimfile = None
			if nimfile is None:
				self.session.openWithCallback(self.close, MessageBox, _("File not Found!\n/proc/bus/nim_sockets"), MessageBox.TYPE_ERROR)
			for line in nimfile.readlines():
				print line
				if line == "":
					break
				if line.strip().startswith("NIM Socket"):
					parts = line.strip().split(" ")
					current_slot = int(parts[2][:-1])
					self.NimType[current_slot]={}
					self.NimType[current_slot]["slot"] = current_slot
				elif line.strip().startswith("Type:"):
					print str(line.strip())
					self.NimType[current_slot]["type"] = str(line.strip()[6:])
					if self.NimType[current_slot]["type"].startswith("DVB-S"):
						self.NimType[current_slot]["sat1"] = sat_list.pop(0)
						self.NimType[current_slot]["sat2"] = sat_list.pop(0)
					else:
						self.NimType[current_slot]["sat1"] = None
						self.NimType[current_slot]["sat2"] = None
				elif line.strip().startswith("empty"):
					self.NimType.pop(current_slot)	
			nimfile.close()
			if True:
				for (key, val) in self.NimType.items():
					print key
					print val
					if val["type"].startswith("DVB-S"):
						print "nimConfig (dvb-s): ",key
						nimConfig = nimmanager.getNimConfig(key)
						nimConfig.configMode.slot_id=key
						nimConfig.configMode.value= "simple"
						nimConfig.diseqcMode.value="diseqc_a_b"
						nimConfig.diseqcA.value = val["sat1"]
						nimConfig.diseqcB.value = val["sat2"]
					else :
						nimConfig = nimmanager.getNimConfig(key)
						print "configMode check : ",nimConfig.configMode.value
			
		nimmanager.sec.update()
		
		system("cp /usr/lib/enigma2/python/Plugins/SystemPlugins/FactoryTest/testdb /etc/enigma2/lamedb")
		db = eDVBDB.getInstance()
		db.reloadServicelist()
		self.createConfig()
		
		self.rlist = []
		for x in range(self.menulength):
			self.rlist.append((".."))
		self["resultlist"] = TestResultList(self.rlist)

		self.avswitch = AVSwitch()
		self.scTest= eSctest()
		
		self.testing = 0

		self.servicelist = ServiceList()
		self.oldref = session.nav.getCurrentlyPlayingServiceReference()
		print "oldref",self.oldref
		session.nav.stopService() # try to disable foreground service
		
		self.tunemsgtimer = eTimer()
		self.tunemsgtimer.callback.append(self.tunemsg)

		self.camstep = 1
		self.camtimer = eTimer()
		self.camtimer.callback.append(self.cam_state)
		self.mactry = 1
		self.getmacaddr()
		self.getversion()
		
		self.tunerlock = 0
		self.tuningtimer = eTimer()
		self.tuningtimer.callback.append(self.updateStatus)

		self.satatry = 8
		self.satatimer = eTimer()
		self.satatimer.callback.append(self.sataCheck)

		self.usbtimer = eTimer()
		self.usbtimer.callback.append(self.usbCheck)

		self.agingtimer = eTimer()
		self.agingtimer.callback.append(self.agingCheck)
		self.setSourceVar()

	def createConfig(self):
		tlist = []
		self.satetestIndex = -1
		self.scarttestIndex = -1
		if self.model == 0:
			self.satetestIndex=0
			tlist.append((" 0. Sata & extend hdd test",self.satetestIndex))
			self.usbtestIndex=1
			tlist.append((" 1. USB test",self.usbtestIndex))
			self.fronttestIndex=2
			tlist.append((" 2. Front test",self.fronttestIndex))
			self.smarttestIndex=3
			tlist.append((" 3. Smartcard test",self.smarttestIndex))
			self.tuner1_1testIndex=4
			tlist.append((" 4. T1 H 22K x 4:3 CVBS",self.tuner1_1testIndex))
			self.tuner1_2testIndex=5
			tlist.append((" 5. T1 V 22k o 16:9 RGB",self.tuner1_2testIndex))
			self.tuner2_1testIndex=6
			tlist.append((" 6. T2 H 22k x 4:3 YC",self.tuner2_1testIndex))
			self.tuner2_2testIndex=7
			tlist.append((" 7. T2 V 22k o 16:9 CVBS CAM",self.tuner2_2testIndex))
			self.scarttestIndex=8
			tlist.append((" 8. VCR Scart loop",self.scarttestIndex))
			self.rs232testIndex=9
			tlist.append((" 9. RS232 test",self.rs232testIndex))
			self.ethernettestIndex=10
			tlist.append(("10. Ethernet & mac test",self.ethernettestIndex))
			self.fdefaultIndex=11
			tlist.append(("11. Factory default",self.fdefaultIndex))
			self.shutdownIndex=12
			tlist.append(("12. Shutdown",self.shutdownIndex))
			self.tuner_test_first_index = 4
			self.tuner_test_last_index = 7
			
		elif self.model == 1:
			self.usbtestIndex=0
			tlist.append((" 0. USB test",self.usbtestIndex))
			self.fronttestIndex=1
			tlist.append((" 1. Front test",self.fronttestIndex))
			self.smarttestIndex=2
			tlist.append((" 2. Smartcard test",self.smarttestIndex))
			self.tuner1_1testIndex=3
			tlist.append((" 3. T1 H 22K x 4:3 CVBS",self.tuner1_1testIndex))
			self.tuner2_2testIndex = self.tuner1_2testIndex=4
			tlist.append((" 4. T1 V 22k o 16:9 RGB CAM",self.tuner1_2testIndex))
			self.rs232testIndex=5
			tlist.append((" 5. RS232 test",self.rs232testIndex))
			self.ethernettestIndex=6
			tlist.append((" 6. Ethernet & mac test",self.ethernettestIndex))
			self.fdefaultIndex=7
			tlist.append((" 7. Factory default",self.fdefaultIndex))
			self.shutdownIndex=8
			tlist.append((" 8. Shutdown",self.shutdownIndex))
			self.tuner_test_first_index = 3
			self.tuner_test_last_index = 4

		elif self.model == 2:
			self.satetestIndex=0
			tlist.append((" 0. Sata & extend hdd test",self.satetestIndex))
			self.usbtestIndex=1
			tlist.append((" 1. USB test",self.usbtestIndex))
			self.fronttestIndex=2
			tlist.append((" 2. Front test",self.fronttestIndex))
			self.smarttestIndex=3
			tlist.append((" 3. Smartcard test",self.smarttestIndex))
			self.tuner1_1testIndex=4
			tlist.append((" 4. T1 H 22K x 4:3 CVBS",self.tuner1_1testIndex))
			self.tuner1_2testIndex=5
			tlist.append((" 5. T1 V 22k o 16:9 RGB",self.tuner1_2testIndex))
			self.tuner2_1testIndex = -1
			self.tuner2_2testIndex=6
			tlist.append((" 6. T2 DVB-C 4:3 YC CAM",self.tuner2_2testIndex))
			self.rs232testIndex=7
			tlist.append((" 7. RS232 test",self.rs232testIndex))
			self.ethernettestIndex=8
			tlist.append(("8. Ethernet & mac test",self.ethernettestIndex))
			self.fdefaultIndex=9
			tlist.append(("9. Factory default",self.fdefaultIndex))
			self.shutdownIndex=10
			tlist.append(("10. Shutdown",self.shutdownIndex))
			self.tuner_test_first_index = 4
			self.tuner_test_last_index = 6

		elif self.model == 3 or self.model == 4:
			self.satetestIndex=0
			tlist.append((" 0. Sata & extend hdd test",self.satetestIndex))
			self.usbtestIndex=1
			tlist.append((" 1. USB test",self.usbtestIndex))
			self.fronttestIndex=2
			tlist.append((" 2. Front test",self.fronttestIndex))
			self.smarttestIndex=3
			tlist.append((" 3. Smartcard test",self.smarttestIndex))
			self.tuner_test_first_index = current_index = 4
			AspectRatio=["4:3", "16:9"]
			ColorFormat=["CVBS","RGB","YC","CVBS","CVBS","CVBS","CVBS","CVBS"]	
			self.tuneInfo={}
			for (key, val) in self.NimType.items():
				if val["type"].startswith("DVB-S"):
# Chang : DVB -S setting diseqc A
					getRatio = AspectRatio.pop(0) # ratio
					AspectRatio.append(getRatio)
					getColorFormat=ColorFormat.pop(0) # colorFormat
					menuname=" %d. T%d %s H 22k 0 %s %s" % (current_index, key+1, val["type"], getRatio, getColorFormat)	#menuname
					print current_index
#						current_index=4
					self.setTuneInfo(index=current_index, slot=key, type=val["type"], sat=val["sat1"], pol="H", tone=True, ratio=getRatio, color=getColorFormat, cam=False) # setTuneInfo
#						self.setTuneInfo(current_index, key, val["type"], val["sat1"], "H", True, getRatio, getColorFormat, False) # setTuneInfo
					tlist.append((menuname,current_index))
					current_index+=1
# Chang : DVB -S setting diseqc B
					getRatio = AspectRatio.pop(0)
					AspectRatio.append(getRatio)
					getColorFormat=ColorFormat.pop(0)
					menuname=" %d. T%d %s V 22k x %s %s" % (current_index, key+1, val["type"], getRatio, getColorFormat)
					if len(self.NimType) == key+1: # CAM test on/off
						menuname+=" CAM"
						camtest = True
					else:
						camtest = False
					self.setTuneInfo( index=current_index, slot=key, type=val["type"], sat=val["sat2"], pol="V", tone=False, ratio=getRatio, color=getColorFormat, cam=camtest)
					tlist.append((menuname,current_index))
					current_index+=1
# Chang : DVB -T or DVB-C
				elif val["type"].startswith("DVB-T") or val["type"].startswith("DVB-C"):
					additionalMenu = None
					menulen = 1
					if len(self.NimType) == 1:
						additionalMenu = True
						menulen +=1
					for x in range(menulen):
						getRatio = AspectRatio.pop(0)
						AspectRatio.append(getRatio)
						getColorFormat=ColorFormat.pop(0)
						menuname=" %d. T%d %s %s %s" % (current_index, key+1, val["type"], getRatio, getColorFormat)
						if len(self.NimType) == key+1 and (additionalMenu is None or x != 0): # CAM test on/off
							menuname+=" CAM"
							camtest = True
						else:
							camtest = False
						self.setTuneInfo( index=current_index, slot=key, type=val["type"], sat=None, pol=None, tone=None, ratio=getRatio, color=getColorFormat, cam=camtest)
						tlist.append((menuname,current_index))
						current_index+=1
			self.tuner_test_last_index = current_index-1
			self.rs232testIndex=current_index
			tlist.append((" %d. RS232 test" % current_index,self.rs232testIndex))
			current_index+=1
			self.ethernettestIndex=current_index
			tlist.append((" %d. Ethernet & mac test" % current_index,self.ethernettestIndex))
			current_index+=1
			self.fdefaultIndex=current_index
			tlist.append((" %d. Factory default" % current_index,self.fdefaultIndex))
			current_index+=1
			self.shutdownIndex=current_index
			tlist.append((" %d. Shutdown" % current_index,self.shutdownIndex))
			
		self.menulength= len(tlist)
		self["testlist"] = MenuList(tlist)
	
	def setTuneInfo(self,index=0,slot=0,type="DVB-S2",sat="160",pol="H",tone=True,ratio="4:3",color="CVBS",cam=False):
		self.tuneInfo[index]={}
		self.tuneInfo[index]["slot"]=slot
		self.tuneInfo[index]["type"]=type
		self.tuneInfo[index]["sat"]=sat
		self.tuneInfo[index]["pol"]=pol
		self.tuneInfo[index]["22k"]=tone
		self.tuneInfo[index]["ratio"]=ratio
		self.tuneInfo[index]["color"]=color
		self.tuneInfo[index]["cam"]=cam

	def getModelInfo(self):
		getmodel = 0
		if fileExists("/proc/stb/info/vumodel"):
			info = open("/proc/stb/info/vumodel").read().strip()
			if info == "duo":
				self.model = 0
				getmodel = 1
				print "getModelInfo : duo"
			if info == "solo":
				self.model = 1
				getmodel = 1
				print "getModelInfo : solo"
			if info == "combo":
				self.model = 2
				getmodel = 1
				print "getModelInfo : combo"
			if info == "uno":
				self.model = 3
				getmodel = 1
				print "getModelInfo : uno"
			if info == "ultimo":
				self.model = 4
				getmodel = 1
				print "getModelInfo : ultimo"
		if getmodel == 0 and fileExists("/proc/stb/info/version"):
			info = open("/proc/stb/info/version").read()
			if info[:2] == "14":
				self.model = 1
				print "getModelInfo : solo_"
			elif info[:2] == "12":
				self.model = 0
				print "getModelInfo : duo_"

	def nothing(self):
		print "nothing"

	def keyup(self):
		print "self.menulength = ",self.menulength
		print "self[\"testlist\"].getCurrent()[1] = ",self["testlist"].getCurrent()[1]
		if self.testing==1:
			return
		if self["testlist"].getCurrent()[1]==0:
			self["testlist"].moveToIndex(self.menulength-1)
			self["resultlist"].moveToIndex(self.menulength-1)
		else:
			self["testlist"].up()
			self["resultlist"].up()


	def keydown(self):
		print "self.menulength = ",self.menulength
		print "self[\"testlist\"].getCurrent()[1] = ",self["testlist"].getCurrent()[1]
		if self.testing==1:
			return
		if self["testlist"].getCurrent()[1]==(self.menulength-1):
			self["testlist"].moveToIndex(0)
			self["resultlist"].moveToIndex(0)
		else:
			self["testlist"].down()
			self["resultlist"].down()

	def numberaction(self, number):
		if self.testing==1:
			return
		if number >= self.menulength:
			return
		index = int(number)
		self["testlist"].moveToIndex(index)
		self["resultlist"].moveToIndex(index)

	def getversion(self):
		try:
			fd = open("/proc/stb/info/version","r")
			version = fd.read()
			self["testversion"].setText(("Version %s"%version))
		except:
			self["testversion"].setText(("Version no load"))
			

	def getmacaddr(self):
		try:
			if self.model == 2 or self.model == 3 or self.model == 4:
				cmd = "nanddump -s 0x" + str((self.mactry-1)*2) + "0000 -b -o -l 64 -p /dev/mtd5"
			elif self.model == 0 or self.model == 1:
				cmd = "nanddump -s 0x" + str((self.mactry-1)*2) + "0000 -b -o -l 64 -p /dev/mtd4"
			self.macConsole = Console()	
			self.macConsole.ePopen(cmd, self.readmac,self.checkReadmac)	
		except:
			return

	def readmac(self, result, retval,extra_args=None):
		(callback) = extra_args
		if self.macConsole is not None:
			if retval == 0:
				self.macConsole = None
				macline = None
				content =result.splitlines()
				for x in content:
					if x.startswith('0x000'+str((self.mactry-1)*2)+'0010:'):
						macline = x.split()
				if macline == None:
					callback(0)
				elif len(macline) < 10:	
					callback(1)
				else:	
					mac = macline[5]+":"+macline[6]+":"+macline[7]+":"+macline[8]+":"+macline[9]+":"+macline[10]
					self["mactext"].setText(("MAC : "+mac))
					callback(2)

	def checkReadmac(self,data):
		if data == 0:
			print "block %d is bad block" % self.mactry
			self.mactry = self.mactry + 1
			if self.mactry > 4:
				self.session.open(MessageBox, _("FLASH IS BROKEN"), type = MessageBox.TYPE_INFO, enable_input = False)
				return
			else:
				self.getmacaddr()
		elif data == 1:
			print 'mac dump read error'
			return
		elif data == 2:
			print 'mac address read ok'
			return
		
	def TestAction(self):
		if self.testing==1:
			return
		print "line - ",self["testlist"].getCurrent()[1]
		self.currentindex = index = self["testlist"].getCurrent()[1]
		result = 0
		if index==self.satetestIndex:
			self.Test0()
		elif index==self.fronttestIndex:
			self.Test1()
		elif index>=self.tuner_test_first_index and index<=self.tuner_test_last_index:
			self.TestTune(index)
		elif index==self.scarttestIndex:
			self.Test6()
		elif index==self.rs232testIndex:
			self.Test7()
		elif index==self.usbtestIndex:
			self.Test8()
		elif index==self.ethernettestIndex:
			self.Test9()
		elif index == self.smarttestIndex:
			self.Test10()
#		elif index == 11:
#			self.Test11()
#		elif index ==12:
#			self.Test12()
#		elif index==13:
#			self.Test13()
		elif index==self.fdefaultIndex:
			self.Test14()
#		elif index==self.shutdownIndex:
#			self.Test15()
		else:
			pass

	def shutdownaction(self):
		if self["testlist"].getCurrent()[1] == self.shutdownIndex:
			self.Test15()


	def Test0(self):
		self.satatry = 8
		self.satatimer.start(100,True)

	def sataCheck(self):
#		print "try", self.satatry
		if self.satatry == 0:
			displayerror = 1
		else:
			self.rlist[self["testlist"].getCurrent()[1]]="try %d"%self.satatry
			self["resultlist"].updateList(self.rlist)
			self.satatry -= 1
			displayerror = 0
		result =0
		try:
			if fileExists("/autofs/sdb1"):
				if access("/autofs/sdb1",F_OK|R_OK|W_OK):
					dummy=open("/autofs/sdb1/dummy03","w")
					dummy.write("complete")
					dummy.close()
					dummy=open("/autofs/sdb1/dummy03","r")
					if dummy.readline()=="complete":
						print "/autofs/sdb1 - complete"
					else:
						print "/autofs/sdb1 - readline error"
						result = 1
						displayerror = 1
					dummy.close()
					system("rm /autofs/sdb1/dummy03")
				else:
					print "/autofs/sdb1 - rw access error"
					result = 1
					displayerror = 1
			else:
				print "/autofs/sdb1 - file not exist"
				result = 1
		except:
			print "/autofs/sdb1 - exceptional error"
			result = 1
			displayerror = 1
		try:
			if fileExists("/media/hdd"):
				if access("/media/hdd",F_OK|R_OK|W_OK):
					dummy=open("/media/hdd/dummy03","w")
					dummy.write("complete")
					dummy.close()
					dummy=open("/media/hdd/dummy03","r")
					if dummy.readline()=="complete":
						print "/media/hdd - complete"
					else:
						print "/media/hdd - readline error"
						result += 1
						displayerror = 1
					dummy.close()
					system("rm /media/hdd/dummy03")
				else:
					print "/media/hdd - rw access error"
					result += 1
					displayerror = 1
			else:
				print "/media/hdd - file not exist"
				result += 1
		except:
			print "/media/hdd - exceptional error"
			result += 1
			displayerror = 1
		
		if result == 0:
			self.session.open( MessageBox, _("Sata & extend hdd test pass"), MessageBox.TYPE_INFO)
			self.rlist[self["testlist"].getCurrent()[1]]="pass"
		elif result == 1:
			if displayerror==1:
				self.session.open( MessageBox, _("One hdd test error"), MessageBox.TYPE_ERROR)
				self.rlist[self["testlist"].getCurrent()[1]]="fail"
			else:
				self.satatimer.start(1100,True)
		else:
			if displayerror==1:
				self.session.open( MessageBox, _("Sata & extend hdd test error"), MessageBox.TYPE_ERROR)
				self.rlist[self["testlist"].getCurrent()[1]]="fail"
			else:
				self.satatimer.start(1100,True)

	def Test1(self):
		if self.model== 0:
			self.session.openWithCallback(self.displayresult ,FrontTest)
		elif self.model == 1:
			self.session.openWithCallback(self.displayresult ,FrontTest_solo)
		elif self.model == 2 or self.model == 3 or self.model == 4:
			self.session.openWithCallback(self.displayresult ,FrontTest_solo)

	def displayresult(self):
		global fronttest
		if fronttest == 1:
			self.rlist[self["testlist"].getCurrent()[1]]="pass"
		else:
			self.rlist[self["testlist"].getCurrent()[1]]="fail"

	def TestTune(self,index):	
		if self.oldref is None:
			eref = eServiceReference("1:0:19:1324:3EF:1:C00000:0:0:0")
			serviceHandler = eServiceCenter.getInstance()
			servicelist = serviceHandler.list(eref)
			if not servicelist is None:
				ref = servicelist.getNext()
			else:
				ref = self.getCurrentSelection() # raise error
				print "servicelist none"
		else:
			ref = self.oldref
		self.session.nav.stopService() # try to disable foreground service
		if self.model == 0 or self.model == 1:
			if index==self.tuner1_1testIndex:
				ref.setData(0,1)
				ref.setData(1,0x6D3)
				ref.setData(2,0x3)
				ref.setData(3,0xA4)
				ref.setData(4,0xA00000)
				self.session.nav.playService(ref)
				self.avswitch.setColorFormat(0)
				self.avswitch.setAspectRatio(0)
			elif index==self.tuner1_2testIndex:
				if self.model == 1:
					self.camstep = 1
					self.camtimer.start(100,True)
				ref.setData(0,0x19)
				ref.setData(1,0x1325)
				ref.setData(2,0x3ef)
				ref.setData(3,0x1)
				ref.setData(4,0x64af79)
				self.session.nav.playService(ref)
				self.avswitch.setColorFormat(1)
				self.avswitch.setAspectRatio(6)			
			elif index==self.tuner2_1testIndex:
				ref.setData(0,1)
				ref.setData(1,0x6D3)
				ref.setData(2,0x3)
				ref.setData(3,0xA4)
				ref.setData(4,0x820000)
				self.session.nav.playService(ref)
				self.avswitch.setColorFormat(2)			
				self.avswitch.setAspectRatio(0)			
			elif index==self.tuner2_2testIndex:
				self.camstep = 1
				self.camtimer.start(100,True)
				ref.setData(0,0x19)
				ref.setData(1,0x1325)
				ref.setData(2,0x3ef)
				ref.setData(3,0x1)
				ref.setData(4,0xC00000)
				self.session.nav.playService(ref)
				self.avswitch.setColorFormat(0)			
				self.avswitch.setAspectRatio(6)
			self.tuningtimer.start(2000,True)
			self.tunemsgtimer.start(3000, True)
		elif self.model == 3 or self.model == 4:
			getTuneInfo=self.tuneInfo[index]
			if getTuneInfo["cam"] is True:
				self.camstep = 1
				self.camtimer.start(100,True)
			if getTuneInfo["type"].startswith("DVB-S"):
				if getTuneInfo["pol"] == "H":
					ref.setData(0,1)
					ref.setData(1,0x6D3)
					ref.setData(2,0x3)
					ref.setData(3,0xA4)
				else:
					ref.setData(0,0x19)
					ref.setData(1,0x1325)
					ref.setData(2,0x3ef)
					ref.setData(3,0x1)
				if getTuneInfo["sat"] == "160": # Eutelsat W2
					ref.setData(4,0xA00000)
				elif getTuneInfo["sat"] == "100": # Eutelsat
					ref.setData(4,0x64af79)
				elif getTuneInfo["sat"] == "130": # Hotbird
					ref.setData(4,0x820000)
				elif getTuneInfo["sat"] == "192": # Astra
					ref.setData(4,0xC00000)
				elif getTuneInfo["sat"] == "620": # Intelsat 902
					ref.setData(4,0x26c0000) # need to fix later
				elif getTuneInfo["sat"] == "642": # Intelsat 906
					ref.setData(4,0x282AF79) # need to fix later
			elif getTuneInfo["type"].startswith("DVB-C"):
				ref.setData(0,0x19)
				ref.setData(1,0x1325)
				ref.setData(2,0x3ef)
				ref.setData(3,0x1)
				ref.setData(4,-64870) # ffff029a
			elif getTuneInfo["type"].startswith("DVB-T"):
				ref.setData(0,0x19)
				ref.setData(1,0x1325)
				ref.setData(2,0x3ef)
				ref.setData(3,0x1)
				ref.setData(4,-286391716) # eeee025c
			self.session.nav.playService(ref)
			if getTuneInfo["color"]=="CVBS":
				self.avswitch.setColorFormat(0)
			elif getTuneInfo["color"]=="RGB":
				self.avswitch.setColorFormat(1)
			elif getTuneInfo["color"]=="YC":
				self.avswitch.setColorFormat(2)
			if getTuneInfo["ratio"] == "4:3":
				self.avswitch.setAspectRatio(0)
			elif getTuneInfo["ratio"] == "16:9":
				self.avswitch.setAspectRatio(6)
			self.tuningtimer.start(2000,True)
			self.tunemsgtimer.start(3000, True) 
		
	def cam_state(self):
		current_index = self.currentindex
		if self.camstep == 1:
			slot = 0
			state = eDVBCI_UI.getInstance().getState(slot)
			print '-1-stat',state
			if state > 0:
				self.camstep=2
				self.camtimer.start(100,True)
			else:
				self.session.nav.stopService()
				self.session.open( MessageBox, _("CAM1_NOT_INSERTED\nPress exit!"), MessageBox.TYPE_ERROR)
				self.rlist[current_index]="fail"
				self.tunemsgtimer.stop()
		elif self.camstep == 2:
			slot = 0
			appname = eDVBCI_UI.getInstance().getAppName(slot)
			print 'appname',appname
			if appname is None:
				self.session.nav.stopService()
				self.session.open( MessageBox, _("NO_GET_APPNAME\nPress exit!"), MessageBox.TYPE_ERROR)
				self.rlist[current_index]="fail"
				self.tunemsgtimer.stop()				
			else:
				self.camstep=3
				self.camtimer.start(100,True)		
		elif self.camstep==3:
			slot = 1
			state = eDVBCI_UI.getInstance().getState(slot)
			print '-2-stat',state
			if state > 0:
				self.camstep=4
				self.camtimer.start(100,True)
			else:
				self.session.nav.stopService()
				self.session.open( MessageBox, _("CAM2_NOT_INSERTED\nPress exit!"), MessageBox.TYPE_ERROR)
				self.rlist[current_index]="fail"
				self.tunemsgtimer.stop()				
		elif self.camstep == 4:
			slot = 1
			appname = eDVBCI_UI.getInstance().getAppName(slot)
			print 'appname',appname
			if appname is None:
				self.session.nav.stopService()
				self.session.open( MessageBox, _("NO_GET_APPNAME\nPress exit!"), MessageBox.TYPE_ERROR)
				self.rlist[current_index]="fail"
				self.tunemsgtimer.stop()				
			else:
				self.setSource()
				self.camstep = 5

	def updateStatus(self):
		current_index = self.currentindex
		if self.model == 0 or self.model == 1:
			if current_index ==self.tuner1_1testIndex or current_index==self.tuner1_2testIndex:
				tunno = 1
				result = eSctest.getInstance().getFrontendstatus(0)
			else:
				tunno = 2
				result = eSctest.getInstance().getFrontendstatus(1)
			if current_index == self.tuner1_2testIndex or current_index==self.tuner2_2testIndex:
				hv = "Ver"
			else:
				hv = "Hor"

		elif self.model == 3 or self.model == 4:
			getTuneInfo=self.tuneInfo[current_index]
			result = eSctest.getInstance().getFrontendstatus(getTuneInfo["slot"])
			tunno = getTuneInfo["slot"]+1
			hv = getTuneInfo["pol"]
			if hv == "H":
				hv = "Hor"
			elif hv == "V":
				hv = "Ver"
			else :
				hv == ""
				
		print "eSctest.getInstance().getFrontendstatus - %d"%result
		if result == 0:
			self.tunerlock = 0
			self.tunemsgtimer.stop()
			self.session.nav.stopService()
			self.avswitch.setColorFormat(0)
			self.session.open( MessageBox, _("Tune%d %s Locking Fail..."%(tunno,hv)), MessageBox.TYPE_ERROR)
			self.rlist[current_index]="fail"
		else : 
			self.tunerlock = 1

	def tuneback(self,yesno):
		current_index=self.currentindex
		self.session.nav.stopService() # try to disable foreground service
		if yesno and self.tunerlock == 1:
			if current_index == self.tuner_test_last_index and self.camstep < 5: # need fix to depending about CAM exist
				self.rlist[current_index]="fail"
			else :
				self.rlist[current_index]="pass"
		else:
			self.rlist[current_index]="fail"
		if self.model == 0 and current_index == 6: # YC
			self.avswitch.setColorFormat(0)
		elif ( self.model == 3 or self.model == 4 ) and self.tuneInfo[current_index]["color"] == "YC":
			self.avswitch.setColorFormat(0)
		self.resetSource()
		self["resultlist"].updateList(self.rlist)

	def tunemsg(self):
		self.tuningtimer.stop()
		self.session.openWithCallback(self.tuneback, MessageBox, _("%s ok?" %(self["testlist"].getCurrent()[0])), MessageBox.TYPE_YESNO)

	def setSourceVar(self):
		if self.model == 0:
			self.input_pad_num=1
			self.setTuner = 'B'
		elif self.model == 1:
			self.input_pad_num=0
			self.setTuner = 'A'
		else:
			self.input_pad_num=len(self.NimType)-1
			if self.input_pad_num == 0:
				self.setTuner = 'A'
			elif self.input_pad_num == 1:
				self.setTuner = 'B'
			elif self.input_pad_num == 2:
				self.setTuner = 'C'

#	ikseong - for 22000 tp
	def setSource(self):
# fix input source
		inputname = ("/proc/stb/tsmux/input%d" % self.input_pad_num)
		print "<setsource> inputname : ",inputname
		fd=open(inputname,"w")
		fd.write("CI0")
		fd.close()
# fix ci_input Tuner
		filename = ("/proc/stb/tsmux/ci0_input")
		fd = open(filename,'w')
		fd.write(self.setTuner)
		print "setTuner(CI0) : ",self.setTuner
		fd.close()
		print "CI loop test!!!!!!!!!!!!!!"
			
	def resetSource(self):
		inputname = ("/proc/stb/tsmux/input%d" % self.input_pad_num)
		print "<resetsource> inputname : ",inputname
		fd=open(inputname,"w")
		fd.write(self.setTuner)
		fd.close()
		print "CI loop test end!!!!!!!!!!!!!!"
				
	def Test6(self):
		self.avswitch.setInput("SCART")
		sleep(2)
		self.session.openWithCallback(self.check6, MessageBox, _("Scart loop ok?"), MessageBox.TYPE_YESNO)

	def check6(self,yesno):
		if yesno:
			self.rlist[self["testlist"].getCurrent()[1]]="pass"
		else:
			self.rlist[self["testlist"].getCurrent()[1]]="fail"
		self.avswitch.setInput("ENCODER")

	def check7(self):
		global rstest
		if rstest == 1:
			self.rlist[self["testlist"].getCurrent()[1]]="pass"
		else:
			self.rlist[self["testlist"].getCurrent()[1]]="fail"

	def Test7(self):
		self.session.openWithCallback(self.check7,RS232Test)

	def Agingmode(self):
		if self.testing==1:
			return
		if self.oldref is None:
			eref = eServiceReference("1:0:19:1324:3EF:1:C00000:0:0:0")
			serviceHandler = eServiceCenter.getInstance()
			servicelist = serviceHandler.list(eref)
			if not servicelist is None:
				ref = servicelist.getNext()
			else:
				ref = self.getCurrentSelection()
				print "servicelist none"
		else:
			ref = self.oldref
		self.session.nav.stopService() # try to disable foreground service
		if self.model == 0 or self.model == 1 or self.NimType[0]["type"].startswith("DVB-S"):
			ref.setData(0,0x19)
			ref.setData(1,0x1325)
			ref.setData(2,0x3ef)
			ref.setData(3,0x1)
			ref.setData(4,0x64af79)
		elif self.NimType[0]["type"].startswith("DVB-C"):
			ref.setData(0,0x19)
			ref.setData(1,0x1325)
			ref.setData(2,0x3ef)
			ref.setData(3,0x1)
			ref.setData(4,-64870) # ffff029a
		elif self.NimType[0]["type"].startswith("DVB-T"):
			ref.setData(0,0x19)
			ref.setData(1,0x1325)
			ref.setData(2,0x3ef)
			ref.setData(3,0x1)
			ref.setData(4,-286391716) # eeee025c
		self.session.nav.playService(ref)
		self.avswitch.setColorFormat(0)
		self.avswitch.setAspectRatio(0)
		self.agingtimer.start(2000,True)

	def agingCheck(self):
		result = eSctest.getInstance().getFrontendstatus(0)		
		hv = "Ver"	
		print "eSctest.getInstance().getFrontendstatus - %d"%result
		if result == 0:
			self.session.nav.stopService()
			self.session.open( MessageBox, _("Tune 1 Ver Locking Fail..."), MessageBox.TYPE_ERROR)
		elif result == 1 :
			self.session.openWithCallback(self.agingResult,AgingTest)
		else:
			self.session.nav.stopService()
			self.session.open( MessageBox, _("Tune 1 Ver Error %d..."%result), MessageBox.TYPE_ERROR)

	def agingResult(self):
		global Agingresult
		if(Agingresult ==1):
			self["testlist"].moveToIndex(self.fdefaultIndex)
			self.Test14()
			self["testlist"].moveToIndex(self.shutdownIndex)	
	
	def Test8(self):
		self.usbtry = 9
		self.usbtimer.start(100,True)

	def usbCheck(self):
		if self.usbtry == 0:
			displayerror = 1
		else:
			self.rlist[self["testlist"].getCurrent()[1]]="try %d"%self.usbtry
			self["resultlist"].updateList(self.rlist)
			self.usbtry -= 1
			displayerror = 0

		if self.model==0 or self.model==3 or self.model==4:
			devices = [ "/autofs/sdc1", "/autofs/sdd1", "/autofs/sde1" ]
		elif self.model==1:
			devices = [ "/autofs/sda1", "/autofs/sdb1" ]
		elif self.model==2:
			devices = [ "/autofs/sdc1", "/autofs/sdd1" ]
		else :
			self.session.open( MessageBox, _("invalid model"), MessageBox.TYPE_ERROR)			
			self.rlist[self["testlist"].getCurrent()[1]]="fail"
			return

		result=len(devices)
		
		for dev in devices:
			try:
				if fileExists(dev):
					if access(dev,F_OK|R_OK|W_OK):
						dummy=open(dev+"/dummy03","w")
						dummy.write("complete")
						dummy.close()
						dummy=open(dev+"/dummy03","r")
						if dummy.readline()=="complete":
							print dev," - complete"
						else:
							print dev," - readline error"
							result=result -1
							displayerror = 1
						dummy.close()
						system("rm "+dev+"/dummy03")
					else:
						print dev," - rw access error"
						result=result -1
						displayerror = 1
				else:
					print dev," - file not exist"
					result=result-1
			except:
				print dev," - exceptional error"
				result=result -1
				displayerror = 1
	
		if result < 0 :
			result = 0
		elif result == len(devices):
			self.session.open( MessageBox, _("USB test pass %d devices\nPress OK!"%result), MessageBox.TYPE_INFO)			
			self.rlist[self["testlist"].getCurrent()[1]]="pass"
		else:
			if displayerror == 1:
				self.session.open( MessageBox, _("USB test error : Success-%d"%result+" Fail-%d\nPress EXIT!"%(len(devices)-result)), MessageBox.TYPE_ERROR)
				self.rlist[self["testlist"].getCurrent()[1]]="fail"
			else:
				self.usbtimer.start(1100,True)

	def pingtest(self):
		self.testing = 1
#		system("/etc/init.d/networking stop")
		system("ifconfig eth0 192.168.0.10")
#		system("/etc/init.d/networking start")
		cmd1 = "ping -c 1 192.168.0.100"
		self.PingConsole = Console()
		self.PingConsole.ePopen(cmd1, self.checkNetworkStateFinished,self.NetworkStatedataAvail)
		
	def checkNetworkStateFinished(self, result, retval,extra_args):
		(statecallback) = extra_args
		if self.PingConsole is not None:
			if retval == 0:
				self.PingConsole = None
				content = result.splitlines()
#				print 'content',content
				x = content[4].split()
#				print 'x',x
				if x[0]==x[3]:
					statecallback(1)
				else:
					statecallback(0)					
			else:
				statecallback(0)


	def NetworkStatedataAvail(self,data):
		global ethtest
		if data == 1:
			ethtest = 1
			print "success"
			self.session.openWithCallback(self.openMacConfig ,MessageBox, _("Ping test pass"), MessageBox.TYPE_INFO,2)
		
		else:
			ethtest = 0
			print "fail"
			self.session.open( MessageBox, _("Ping test fail\nPress exit"), MessageBox.TYPE_ERROR)
			self.macresult()

	def Test9(self):
		self.pingtest()

	def openMacConfig(self, ret=False):
		self.session.openWithCallback(self.macresult ,MacConfig,mactry=self.mactry)	
			
	def macresult(self):
		global ethtest
		if ethtest == 1:
			self.rlist[self.ethernettestIndex]="pass"		
		else:
			self.rlist[self.ethernettestIndex]="fail"		
		self.getmacaddr()
		self.testing = 0			
	
	def MemTest(self, which):
		index = which
		result = 0
		if index==0:
			result = eMemtest.getInstance().dramtest()
		elif index==1:
			result = eMemtest.getInstance().flashtest()
			result = 0	#	temp
		else:
			result = eMemtest.getInstance().dramtest()
			result = eMemtest.getInstance().flashtest()
			result = 0	#	temp
			
		index = index+10
		
		if result == 0:
			print index,self.rlist[index]
			self.rlist[index]="pass"
		else:
			print index,self.rlist[index]
			self.rlist[index]="fail"
		self["resultlist"].updateList(self.rlist)
			
	def scciresult(self):
		global smartcardtest
		if smartcardtest == 1:
			self.rlist[self["testlist"].getCurrent()[1]]="pass"
		else:
			self.rlist[self["testlist"].getCurrent()[1]]="fail"

	def Test10(self):
		self.session.openWithCallback(self.scciresult ,SmartCardTest,stbmodel=self.model)

	def Test11(self):
		self.MemTest(1)
		
	def Test12(self):
		self.MemTest(2)

	def Test13(self):
		self.MemTest(3)	


	def Test14(self):
		try:
			print "test14"
			system("rm -R /etc/enigma2")
			system("ls /")
			system("cp -R /usr/share/enigma2/defaults /etc/enigma2")
			self.rlist[self["testlist"].getCurrent()[1]]="pass"
			self["resultlist"].updateList(self.rlist)
		except:
			print "test14 except"
			self.rlist[self["testlist"].getCurrent()[1]]="fail"
			self["resultlist"].updateList(self.rlist)
			self.session.open( MessageBox, _("Factory reset fail"), MessageBox.TYPE_ERROR)

	def Test15(self):
		self.session.openWithCallback(self.shutdown ,MessageBox, _("Do you want to shut down?"), MessageBox.TYPE_YESNO)

	def shutdown(self, yesno):
		if yesno :
			from os import _exit
			system("/usr/bin/showiframe /boot/backdrop.mvi")
			_exit(1)
		else:
			return
		
	def keyCancel(self):
		if self.testing==1:
			return
		print "exit"
		self.close()
#		if self.oldref is not None:
#			self.session.nav.playService(self.oldref)

ethtest = 0
class MacConfig(Screen):
	skin = """
		<screen position="100,250" size="520,100" title="Mac Config" >
			<eLabel text="Mac Address " position="10,15" size="200,40" font="Regular;30" />		
			<widget name="text" position="230,15" size="230,40" font="Regular;30" />
			<widget name="text1" position="470,15" size="40,40" font="Regular;30" />		
			<eLabel text=" " position="5,55" zPosition="-1" size="510,5" backgroundColor="#02e1e8e6" />		
			<widget name="stattext" position="30,75" size="400,25" font="Regular;20" />
		</screen>"""

	def __init__(self, session, mactry = 1):
		self["actions"] = ActionMap(["DirectionActions","OkCancelActions"],
		{
			"ok": self.keyOk,
			"left": self.keyleft,
			"right": self.keyright,
			"cancel": self.keyCancel,
		}, -2)

		Screen.__init__(self, session)

		self.mactry = mactry
		self.model = 0
		self.getModelInfo()
		self.macfd = 0
		self.macaddr = "000000000000"
		self.ReadMacinfo = 0
		self["text"]=Label((self.macaddr))
		self["text1"]= Label(("< >"))
		self["stattext"]= Label((""))
		self.displaymac()
		self.loadmacaddr()
		self.getmacaddr()
		global ethtest
		ethtest = 1

	def getModelInfo(self):
		getmodel = 0
		if fileExists("/proc/stb/info/vumodel"):
			info = open("/proc/stb/info/vumodel").read().strip()
			if info == "combo":
				self.model = 2
				getmodel = 1
				print "MacConfig, model : combo"
			elif info == "solo":
				self.model = 1
				getmodel = 1
				print "MacConfig, model : solo"
			elif info == "duo":
				self.model = 0
				getmodel = 1
				print "MacConfig, model : duo"
			elif info == "uno":
				self.model = 3
				getmodel = 1
				print "getModelInfo : uno"
			elif info == "ultimo":
				self.model = 4
				getmodel = 1
				print "getModelInfo : ultimo"


		if getmodel == 0 and fileExists("/proc/stb/info/version"):
			info = open("/proc/stb/info/version").read()
#			print info,info[:2]
			if info[:2] == "14":
				self.model = 1
				print "MacConfig, model : solo_"
			elif info[:2] == "12":
				self.model = 0
				print "MacConfig, model: duo_"

	def loadmacaddr(self):
		try:
			self.macfd = 0

			if self.model==0 or self.model==3 or self.model==4 :
				devices = ["/autofs/sdb1", "/autofs/sdc1", "/autofs/sdd1", "/autofs/sde1" ]
			elif self.model==1:
				devices = [ "/autofs/sda1", "/autofs/sdb1" ]
			elif self.model==2:
				devices = [ "/autofs/sdb1", "/autofs/sdc1", "/autofs/sdd1" ]

			for dev in devices:
				print 'try..',dev
				if  fileExists(dev+"/macinfo.txt"):
					print "<open>"+dev+"/macinfo.txt"
					self.macfd = open(dev+"/macinfo.txt","r+")
					break

			if self.macfd == 0:
				self["text"].setText(("cannot read usb!!"))
				self["text1"].setText((" "))
				self["stattext"].setText((" Press Exit Key."))
				self.ReadMacinfo=0
				return
			
			macaddr=self.macfd.readline().split(":")
			self.macaddr=macaddr[1]+macaddr[2]+macaddr[3]+macaddr[4]+macaddr[5]+macaddr[6]
			self.displaymac()
			self.ReadMacinfo = 1
		except:
			self["text"].setText(("cannot read usb!!"))
			self["text1"].setText((" "))
			self["stattext"].setText((" Press Exit Key."))
			self.ReadMacinfo=0
 	
	def getmacaddr(self):
		if self.ReadMacinfo==0:
			return
		try:
			if self.model == 2 or self.model == 3 or self.model == 4:
				cmd = "nanddump -s 0x" + str((self.mactry-1)*2) + "0000 -b -o -l 64 -p /dev/mtd5"
			elif self.model == 0 or self.model == 1:
				cmd = "nanddump -s 0x" + str((self.mactry-1)*2) + "0000 -b -o -l 64 -p /dev/mtd4"
			self.macConsole = Console()	
			self.macConsole.ePopen(cmd, self.readmac,self.checkReadmac)
		except:
			return

	def readmac(self, result, retval,extra_args=None):
		(callback) = extra_args
		if self.macConsole is not None:
			if retval == 0:
				self.macConsole = None
				macline = None
				content =result.splitlines()
				for x in content:
					if x.startswith('0x000'+str((self.mactry-1)*2)+'0010:'):
						macline = x.split()
				if macline == None:
					callback(0)
				elif len(macline) < 10:	
					callback(1)
				else:	
					mac = macline[5]+":"+macline[6]+":"+macline[7]+":"+macline[8]+":"+macline[9]+":"+macline[10]
					self["stattext"].setText(("now : "+mac))
					callback(2)

	def checkReadmac(self,data):
		if data == 0:
			print "block %d is bad block" % self.mactry
			self.mactry = self.mactry + 1
			if self.mactry > 4:
				self.session.open(MessageBox, _("FLASH IS BROKEN"), type = MessageBox.TYPE_INFO, enable_input = False)
				return
			else:
				self.getmacaddr()
		elif data == 1:
			print 'mac dump read error'
			return
		elif data == 2:
			print 'mac address read ok'
			return

			
	def keyleft(self):
		if self.ReadMacinfo==0 :
			return
		macaddress = long(self.macaddr,16)-1
		if macaddress < 0 :
			macaddress = 0xffffffffffff
		self.macaddr = "%012x"%macaddress
		self.displaymac()

	def keyright(self):
		if self.ReadMacinfo==0 :
			return
		macaddress = long(self.macaddr,16)+1
		if macaddress > 0xffffffffffff:
			macaddress = 0
		self.macaddr = "%012x"%macaddress
		self.displaymac()

	def displaymac(self):
		macaddr= self.macaddr
		self["text"].setText(("%02x:%02x:%02x:%02x:%02x:%02x"%(int(macaddr[0:2],16),int(macaddr[2:4],16),int(macaddr[4:6],16),int(macaddr[6:8],16),int(macaddr[8:10],16),int(macaddr[10:12],16))))

	def keyOk(self):
		if self.ReadMacinfo==0 :
			return
		try:
			macaddr = self.macaddr
#make_mac_sector 00-99-99-99-00-00 > /tmp/mac.sector
#flash_eraseall /dev/mtd4
#nandwrite /dev/mtd4 /tmp/mac.sector -p			
			cmd = "make_mac_sector %02x-%02x-%02x-%02x-%02x-%02x > /tmp/mac.sector"%(int(macaddr[0:2],16),int(macaddr[2:4],16),int(macaddr[4:6],16),int(macaddr[6:8],16),int(macaddr[8:10],16),int(macaddr[10:12],16))
			system(cmd)
			if self.model == 2 or self.model == 3 or self.model == 4:
				system("flash_eraseall /dev/mtd5")
				system("nandwrite /dev/mtd5 /tmp/mac.sector -p")
			elif self.model == 0 or self.model ==1 :
				system("flash_eraseall /dev/mtd4")
				system("nandwrite /dev/mtd4 /tmp/mac.sector -p")
			macaddress = long(macaddr,16)+1
			if macaddress > 0xffffffffffff:
				macaddress = 0
			macaddr = "%012x"%macaddress
			macwritetext = "MAC:%02x:%02x:%02x:%02x:%02x:%02x"%(int(macaddr[0:2],16),int(macaddr[2:4],16),int(macaddr[4:6],16),int(macaddr[6:8],16),int(macaddr[8:10],16),int(macaddr[10:12],16))
			self.macfd.seek(0)
			self.macfd.write(macwritetext)
			self.macfd.close()
			system("sync")
			self.macaddr = macaddr
			self.close()
		except:
			self.session.open( MessageBox, _("Mac address fail"), MessageBox.TYPE_ERROR)
			global ethtest
			ethtest = 0
			self.close()		

	def keyCancel(self):
		if self.macfd != 0:
			self.macfd.close()
		global ethtest
		ethtest = 0
		self.close()

smartcardtest = 0
class SmartCardTest(Screen):
	skin = """
		<screen position="300,240" size="160,120" title="SmartCard Test" >
			<widget name="text" position="10,10" size="140,100" font="Regular;22" />
		</screen>"""

	def __init__(self, session, stbmodel = 0):
		self["actions"] = ActionMap(["DirectionActions", "OkCancelActions"],
		{
			"cancel": self.keyCancel,
			"ok" : self.keyCancel
		}, -2)

		Screen.__init__(self, session)
		self["text"]=Label(("Testing Smartcard 1..."))
		self.step = 0
		self.smartcardtimer = eTimer()
		self.smartcardtimer.callback.append(self.check_smart_card)
		self.closetimer = eTimer()
		self.closetimer.callback.append(self.close)
		self.smartcard=0
		global smartcardtest
		smartcardtest = 0
		self.model = stbmodel
		self.Testmode = 1
		self.smartcardtimer.start(100,True)

	def check_smart_card(self):
		global smartcardtest
		index = self.smartcard
		result  = 0
		if index==0:
			if self.Testmode==0:
				result = eSctest.getInstance().check_smart_card("/dev/sci0")
			else:
				result = eSctest.getInstance().n_check_smart_card("/dev/sci0")			
		elif index ==1:
			if self.Testmode==0:
				result = eSctest.getInstance().check_smart_card("/dev/sci1")
			else:
				result = eSctest.getInstance().n_check_smart_card("/dev/sci1")			
		else:
			result = -1

		print result			
		
		if result == 0:
			print 'pass'
			if(index== 0 and ( self.model== 0 or self.model==2 or self.model == 3 or self.model == 4) ):
				self.smartcard = 1
				self["text"].setText(_("Testing Smartcard 2..."))
				self.smartcardtimer.start(100,True)
				return
			elif (index==1 or self.model==1):
				smartcardtest = 1
				self.step = 1
				self["text"].setText(_("Smart Card OK!!"))
				self.closetimer.start(2000,True)
				self.smartcardtimer.stop()
			else :
				
				self["text"].setText(_("Smart Card model type error"))
				self.closetimer.start(2000,True)
				self.smartcardtimer.stop()
		else:
#			if result ==-1:
#				self.session.open( MessageBox, _("%d:NO_DEV_FOUND"%(index+1)), MessageBox.TYPE_ERROR)
#			elif result == -2:
#				self.session.open( MessageBox, _("%d:SC_NOT_INSERTED"%(index+1)), MessageBox.TYPE_ERROR)
#			elif result == -3:
#				self.session.open( MessageBox, _("%d:SC_NOT_VALID_ATR"%(index+1)), MessageBox.TYPE_ERROR)
#			elif result == -5:
#				self.session.open( MessageBox, _("%d:SC_READ_TIMEOUT"%(index+1)), MessageBox.TYPE_ERROR)
			if(index==0):
				self["text"].setText(_("Smart Card 1 Error!\nerrorcode=%d"%result))
			elif (index==1):
				self["text"].setText(_("Smart Card 2 Error!\nerrorcode=%d"%result))
			self.closetimer.start(2000,True)
			self.smartcardtimer.stop()

				
	def keyCancel(self):
		self.close()

	

fronttest = 0

class FrontTest(Screen):
	skin = """
		<screen position="260,240" size="200,180" title="Front Test" >
			<widget name="text" position="10,10" size="180,160" font="Regular;22" />
		</screen>"""

	def __init__(self, session):
		self["actions"] = ActionMap(["DirectionActions", "OkCancelActions"],
		{
			"ok": self.keyOk,
			"up":self.keyUp,
			"down":self.keyDown,			
			"cancel": self.keyCancel,
		}, -2)

		Screen.__init__(self, session)
		self["text"]=Label(("Wheel LEFT"))
		self.step = 1
		
		self.fronttimer= eTimer()
		self.fronttimer.callback.append(self.FrontAnimate)
		self.frontturnonoff = 0
		eSctest.getInstance().VFD_Open()
		self.keytimeout = eTimer()
		self.keytimeout.callback.append(self.KeyTimeOut)
		self.keytimeout.start(5000,True)

	def KeyTimeOut(self):
		if self.step == 1:
			self["text"].setText(("Wheel LEFT ERROR"))
		elif self.step ==2 :
			self["text"].setText(("Wheel RIGHT ERROR"))
		elif self.step == 3:
			self["text"].setText(("Wheel BUTTON ERROR"))
		self.step = 0
#		self.keyCancel()
				
	def keyCancel(self):
		global fronttest
		self.fronttimer.stop()
		eSctest.getInstance().VFD_Close()
		if self.step==4:
			fronttest = 1
		else:
			fronttest = 0
		self.close()

	def keyDown(self):
		if self.step==2:
			self.keytimeout.stop()
			self.keytimeout.start(5000,True)
			self.step = 3
			self["text"].setText(_("Press Front Wheel"))

	def keyUp(self):
		if self.step==1:
			self.keytimeout.stop()
			self.keytimeout.start(5000,True)
			self.step=2
			self["text"].setText(_("Wheel RIGHT"))

	def keyOk(self):
		if self.step == 3:
			self.keytimeout.stop()
			self.step =4
			self.fronttimer.start(1000,True)
			self["text"].setText(("Front Test OK!\nPress Exit Key"))
#		elif self.step==4:
#			global fronttest
#			self.fronttimer.stop()
#			eSctest.getInstance().VFD_Close()
#			fronttest = 1
#			self.close()

	def FrontAnimate(self):
		if (self.frontturnonoff==0):
			eSctest.getInstance().turnon_VFD()
			self.frontturnonoff = 1
		else:
			self.frontturnonoff = 0
			eSctest.getInstance().turnoff_VFD()
		self.fronttimer.start(1000,True)
		

class FrontTest_solo(Screen):
	skin = """
		<screen position="260,240" size="200,180" title="Front Test" >
			<widget name="text" position="10,10" size="180,160" font="Regular;22" />
		</screen>"""

	def __init__(self, session):
		self["actions"] = ActionMap(["DirectionActions", "OkCancelActions","GlobalActions"],
		{
			"ok": self.keyOk,
			"cancel": self.keyCancel,
			"left": self.keyleft,
			"right": self.keyright,
			"power_down": self.keypower,
			"volumeUp": self.keyvolup,
			"volumeDown": self.keyvoldown,
		}, -2)

		Screen.__init__(self, session)
		self["text"]=Label(("Press Front STANDBY"))
		self.step = 1
		
		self.fronttimer= eTimer()
		self.fronttimer.callback.append(self.FrontAnimate)
		self.frontturnonoff = 0
		eSctest.getInstance().VFD_Open()
		self.keytimeout = eTimer()
		self.keytimeout.callback.append(self.KeyTimeOut)
		self.keytimeout.start(5000,True)

	def KeyTimeOut(self):
		if self.step == 1:
			self["text"].setText(("Front STANDBY ERROR\nPress exit!"))
		elif self.step == 2 :
			self["text"].setText(("Front CH - ERROR\nPress exit!"))
		elif self.step == 3:
			self["text"].setText(("Front CH + ERROR\nPress exit!"))
		elif self.step == 4 :
			self["text"].setText(("Front VOL - ERROR\nPress exit!"))
		elif self.step == 5:
			self["text"].setText(("Front VOL + ERROR\nPress exit!"))
			
		self.step = 0
#		self.keyCancel()

	def keypower(self):
		if self.step== 1:
			self.keytimeout.stop()
			self.keytimeout.start(5000,True)
			self.step = 2
			self["text"].setText(_("Press Front CH -"))
			
	def keyright(self):
		if self.step== 3:
			self.keytimeout.stop()
			self.keytimeout.start(5000,True)
			self.step = 4
			self["text"].setText(_("Press Front VOL -"))
			
	def keyleft(self):
		if self.step== 2:
			self.keytimeout.stop()
			self.keytimeout.start(5000,True)
			self.step = 3
			self["text"].setText(_("Press Front CH +"))

	def keyvolup(self):
		if self.step== 5:
			self.keytimeout.stop()
			self.step = 6
			self.fronttimer.start(1000,True)
			self["text"].setText(_("Front LED OK?\n\nyes-ok\nno-exit"))			
#			self["text"].setText(("Front Test OK!\nPress Exit Key"))
		
	def keyvoldown(self):
		if self.step== 4:
			self.keytimeout.stop()
			self.keytimeout.start(5000,True)
			self.step = 5
			self["text"].setText(_("Press Front VOL +"))

	def checkled(self, yesno):
		if yesno :
			self.step=6
		else:
			self.step=0
		self.keyCancel()
			
	def keyCancel(self):
		global fronttest
		self.fronttimer.stop()
		eSctest.getInstance().VFD_Close()
		fronttest = 0
		self.close()

	def keyOk(self):
		global fronttest
		self.fronttimer.stop()
		eSctest.getInstance().VFD_Close()
		if self.step == 6:
			fronttest = 1
		self.close()

	def FrontAnimate(self):
		if (self.frontturnonoff==0):
			eSctest.getInstance().turnon_VFD()
			self.frontturnonoff = 1
		else:
			self.frontturnonoff = 0
			eSctest.getInstance().turnoff_VFD()
		self.fronttimer.start(1000,True)


	

rstest = 0

import select

class RS232Test(Screen):
	skin = """
		<screen position="300,240" size="160,100" title="RS232 Test" >
			<widget name="text" position="10,10" size="140,80" font="Regular;22" />
		</screen>"""
	step=1
	def __init__(self, session):
		self["actions"] = ActionMap(["DirectionActions", "OkCancelActions"],
		{
			"cancel": self.keyCancel,
		}, -2)

		Screen.__init__(self, session)
		self["text"]=Label(("Press \"Enter\" Key"))
		self.timer = eTimer()
		self.timer.callback.append(self.checkrs232)
		self.timer.start(100, True)

	def checkrs232(self):
		global rstest
		try:
			rs=open('/dev/ttyS0','r')
			rd = [rs]
			r,w,e = select.select(rd, [], [], 10)
			if r:
				input = rs.read(1)
				if input == "\n":
					rstest = 1
				else:
					rstest = 0 
			else:
				rstest = 0
		except:
			print 'error'
			rstest = 0
		self.close()

	def keyCancel(self):
		self.close()

Agingresult = 0

class AgingTest(Screen):
	skin = """
		<screen position="200,240" size="250,100" title="Aging Test" >
			<widget name="text1" position="10,10" size="230,40" font="Regular;22" />
			<widget name="text2" position="10,50" size="230,40" font="Regular;22" />
		</screen>"""
	step=1
	def __init__(self, session):
		self["actions"] = ActionMap(["MediaPlayerActions","GlobalActions"],
		{
			"pause": self.keyEnd,
			"stop": self.keyFinish,
			"volumeUp": self.nothing,
			"volumeDown": self.nothing,
			"volumeMute": self.nothing,		
		}, -2)

		Screen.__init__(self, session)
		self["text1"]=Label(("Exit - Press Pause Key"))
		self["text2"]=Label(("Reset - Press Stop Key"))
#		self.servicelist = ServiceList()
#		self.oldref = session.nav.getCurrentlyPlayingServiceReference()
#		print "oldref",self.oldref
#		session.nav.stopService() # try to disable foreground service
#		self.chstart()
		self.tunerlock = 0
		self.tuningtimer = eTimer()
		self.tuningtimer.callback.append(self.updateStatus)
#		self.tuningtimer.start(200,True)


	def updateStatus(self):
		result = eSctest.getInstance().getFrontendstatus(0)		
		hv = "Ver"
			
		print "eSctest.getInstance().getFrontendstatus - %d"%result
		if result == 0:
			self.tunerlock = 0
			self.session.nav.stopService()
			self.session.open( MessageBox, _("Tune 1 Ver Locking Fail..."), MessageBox.TYPE_ERROR)
		elif result==1 :
			self.tunerlock = 1
		else:
			self.tunerlock = 0
			self.session.nav.stopService()
			self.session.open( MessageBox, _("Tune 1 Ver Error %d..."%result), MessageBox.TYPE_ERROR)


	def nothing(self):
		print "nothing"

	def chstart(self):
		if self.oldref is None:
			eref = eServiceReference("1:0:19:1324:3EF:1:C00000:0:0:0")
			serviceHandler = eServiceCenter.getInstance()
			servicelist = serviceHandler.list(eref)
			if not servicelist is None:
				ref = servicelist.getNext()
			else:
				ref = self.getCurrentSelection()
				print "servicelist none"
		else:
			ref = self.oldref
		self.session.nav.stopService() # try to disable foreground service
		ref.setData(0,0x19)
		ref.setData(1,0x83)
		ref.setData(2,0x6)
		ref.setData(3,0x85)
		ref.setData(4,0x640000)
		self.session.nav.playService(ref)

	def keyEnd(self):
		global Agingresult
		Agingresult = 0
		self.session.nav.stopService() # try to disable foreground service
		self.close()

	def keyFinish(self):
		global Agingresult
		Agingresult = 1
		self.session.nav.stopService() # try to disable foreground service
		self.close()
		
session = None

	
def cleanup():
	global Session
	Session = None
	global Servicelist
	Servicelist = None

def main(session, servicelist, **kwargs):
	global Session
	Session = session
	global Servicelist
	Servicelist = servicelist
	bouquets = Servicelist.getBouquetList()
	global bouquetSel
	bouquetSel = Session.openWithCallback(cleanup, FactoryTest)

#def Plugins(**kwargs):
#	return PluginDescriptor(name=_("Factory Test"), description="Test App for Factory", where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)

def Plugins(**kwargs):
	return []
