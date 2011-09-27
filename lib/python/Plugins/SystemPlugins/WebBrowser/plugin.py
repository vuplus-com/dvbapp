from Plugins.Plugin import PluginDescriptor

import time, os, socket, thread
from socket import gaierror, error
from os import path as os_path, remove as os_remove

import gdata.youtube
import gdata.youtube.service
from gdata.service import BadAuthentication

from twisted.web import client
from twisted.internet import reactor

from urlparse import parse_qs
from urllib import quote, unquote_plus, unquote
from urllib2 import Request, URLError, urlopen as urlopen2
from httplib import HTTPConnection, CannotSendRequest, BadStatusLine, HTTPException

from Components.Button import Button
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.ActionMap import NumberActionMap, ActionMap
from Components.ServiceEventTracker import ServiceEventTracker
from Components.config import config, ConfigSelection, getConfigListEntry

from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.DefaultWizard import DefaultWizard
from Screens.InfoBarGenerics import InfoBarNotifications

from enigma import eTimer, eServiceReference, iPlayableService, fbClass, eRCInput, eConsoleAppContainer

HTTPConnection.debuglevel = 1

lock = False
def player_lock():
	global lock
	lock = True
	fbClass.getInstance().unlock()

def player_unlock():
	global lock
	fbClass.getInstance().lock()
	lock = False

def player_islock():
	global lock
	return lock

class VuPlayer(Screen, InfoBarNotifications):
	skin = 	"""
		<screen name="VuPlayer" flags="wfNoBorder" position="center,620" size="455,53" title="VuPlayer" backgroundColor="transparent">
			<ePixmap pixmap="Vu_HD/mp_wb_background.png" position="0,0" zPosition="-1" size="455,53" />
			<ePixmap pixmap="Vu_HD/icons/mp_wb_buttons.png" position="40,23" size="30,13" alphatest="on" />

			<widget source="session.CurrentService" render="PositionGauge" position="80,25" size="220,10" zPosition="2" pointer="skin_default/position_pointer.png:540,0" transparent="1" foregroundColor="#20224f">
				<convert type="ServicePosition">Gauge</convert>
			</widget>
			
			<widget source="session.CurrentService" render="Label" position="310,20" size="50,20" font="Regular;18" halign="center" valign="center" backgroundColor="#4e5a74" transparent="1" >
				<convert type="ServicePosition">Position</convert>
			</widget>
			<widget name="sidebar" position="362,20" size="10,20" font="Regular;18" halign="center" valign="center" backgroundColor="#4e5a74" transparent="1" />
			<widget source="session.CurrentService" render="Label" position="374,20" size="50,20" font="Regular;18" halign="center" valign="center" backgroundColor="#4e5a74" transparent="1" > 
				<convert type="ServicePosition">Length</convert>
			</widget>
		</screen>
		"""
	PLAYER_IDLE	= 0
	PLAYER_PLAYING 	= 1
	PLAYER_PAUSED 	= 2

	def __init__(self, session, service, lastservice):
		Screen.__init__(self, session)
		InfoBarNotifications.__init__(self)

		self.session     = session
		self.service     = service
		self.lastservice = lastservice
		self["actions"] = ActionMap(["OkCancelActions", "InfobarSeekActions", "MediaPlayerActions", "MovieSelectionActions"],
		{
			"ok": self.doInfoAction,
			"cancel": self.doExit,
			"stop": self.doExit,
			"playpauseService": self.playpauseService,
		}, -2)
		self["sidebar"] = Label(_("/"))

		self.__event_tracker = ServiceEventTracker(screen = self, eventmap =
		{
			iPlayableService.evSeekableStatusChanged: self.__seekableStatusChanged,
			iPlayableService.evStart: self.__serviceStarted,
			iPlayableService.evEOF: self.__evEOF,
		})

		self.hidetimer = eTimer()
		self.hidetimer.timeout.get().append(self.doInfoAction)

		self.state = self.PLAYER_PLAYING
		self.lastseekstate = self.PLAYER_PLAYING
		self.__seekableStatusChanged()
	
		self.onClose.append(self.__onClose)
		self.doPlay()

	def __onClose(self):
		self.session.nav.stopService()

	def __seekableStatusChanged(self):
		service = self.session.nav.getCurrentService()
		if service is not None:
			seek = service.seek()
			if seek is None or not seek.isCurrentlySeekable():
				self.setSeekState(self.PLAYER_PLAYING)

	def __serviceStarted(self):
		self.state = self.PLAYER_PLAYING
		self.__seekableStatusChanged()

	def __evEOF(self):
		self.doExit()

	def __setHideTimer(self):
		self.hidetimer.start(5000)

	def doExit(self):
		list = ((_("Yes"), "y"), (_("No, but play video again"), "n"),)
		self.session.openWithCallback(self.cbDoExit, ChoiceBox, title=_("Stop playing this movie?"), list = list)

	def cbDoExit(self, answer):
		answer = answer and answer[1]
		if answer == "y":
			player_unlock()
			self.close()
		elif answer == "n":
			if self.state != self.PLAYER_IDLE:
				self.session.nav.stopService()
				self.state = self.PLAYER_IDLE
			self.doPlay()

	def setSeekState(self, wantstate):
		service = self.session.nav.getCurrentService()
		if service is None:
			print "No Service found"
			return

		pauseable = service.pause()
		if pauseable is not None:
			if wantstate == self.PLAYER_PAUSED:
				pauseable.pause()
				self.state = self.PLAYER_PAUSED
				if not self.shown:
					self.hidetimer.stop()
					self.show()
			elif wantstate == self.PLAYER_PLAYING:
				pauseable.unpause()
				self.state = self.PLAYER_PLAYING
				if self.shown:
					self.__setHideTimer()
		else:
			self.state = self.PLAYER_PLAYING

	def doInfoAction(self):
		if self.shown:
			self.hide()
			self.hidetimer.stop()
		else:
			self.show()
			if self.state == self.PLAYER_PLAYING:
				self.__setHideTimer()

	def doPlay(self):
		if self.state == self.PLAYER_PAUSED:
			if self.shown:
				self.__setHideTimer()	
		self.state = self.PLAYER_PLAYING
		self.session.nav.playService(self.service)
		if self.shown:
			self.__setHideTimer()

	def playpauseService(self):
		if self.state == self.PLAYER_PLAYING:
			self.setSeekState(self.PLAYER_PAUSED)
		elif self.state == self.PLAYER_PAUSED:
			self.setSeekState(self.PLAYER_PLAYING)

VIDEO_FMT_PRIORITY_MAP = {
	'38' : 1, #MP4 Original (HD)
	'37' : 2, #MP4 1080p (HD)
	'22' : 3, #MP4 720p (HD)
	'18' : 4, #MP4 360p
	'35' : 5, #FLV 480p
	'34' : 6, #FLV 360p
}
std_headers = {
	'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	'Accept-Language': 'en-us,en;q=0.5',
}

class VuPlayerLauncher:
	def getVideoUrl(self, video_id):
		video_url = None

		if video_id is None or video_id == "":
			return video_url

		# Getting video webpage
		watch_url = 'http://www.youtube.com/watch?v=%s&gl=US&hl=en' % video_id
		watchrequest = Request(watch_url, None, std_headers)
		try:
			#print "trying to find out if a HD Stream is available",watch_url
			watchvideopage = urlopen2(watchrequest).read()
		except (URLError, HTTPException, socket.error), err:
			print "Error: Unable to retrieve watchpage - Error code: ", str(err)
			return video_url

		# Get video info
		for el in ['&el=embedded', '&el=detailpage', '&el=vevo', '']:
			info_url = ('http://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en' % (video_id, el))
			request = Request(info_url, None, std_headers)
			try:
				infopage = urlopen2(request).read()
				videoinfo = parse_qs(infopage)
				if ('url_encoded_fmt_stream_map' or 'fmt_url_map') in videoinfo:
					break
			except (URLError, HTTPException, socket.error), err:
				print "Error: unable to download video infopage",str(err)
				return video_url

		if ('url_encoded_fmt_stream_map' or 'fmt_url_map') not in videoinfo:
			if 'reason' not in videoinfo:
				print 'Error: unable to extract "fmt_url_map" or "url_encoded_fmt_stream_map" parameter for unknown reason'
			else:
				reason = unquote_plus(videoinfo['reason'][0])
				print 'Error: YouTube said: %s' % reason.decode('utf-8')
			return video_url

		video_fmt_map = {}
		fmt_infomap = {}
		if videoinfo.has_key('url_encoded_fmt_stream_map'):
			tmp_fmtUrlDATA = videoinfo['url_encoded_fmt_stream_map'][0].split(',url=')
		else:
			tmp_fmtUrlDATA = videoinfo['fmt_url_map'][0].split(',')
		for fmtstring in tmp_fmtUrlDATA:
			if videoinfo.has_key('url_encoded_fmt_stream_map'):
				(fmturl, fmtid) = fmtstring.split('&itag=')
				if fmturl.find("url=") !=-1:
					fmturl = fmturl.replace("url=","")
			else:
				(fmtid,fmturl) = fmtstring.split('|')
			if VIDEO_FMT_PRIORITY_MAP.has_key(fmtid):
				video_fmt_map[VIDEO_FMT_PRIORITY_MAP[fmtid]] = { 'fmtid': fmtid, 'fmturl': unquote_plus(fmturl) }
			fmt_infomap[int(fmtid)] = unquote_plus(fmturl)
		print "got",sorted(fmt_infomap.iterkeys())
		if video_fmt_map and len(video_fmt_map):
			video_url = video_fmt_map[sorted(video_fmt_map.iterkeys())[0]]['fmturl'].split(';')[0]
			#print "found best available video format:",video_fmt_map[sorted(video_fmt_map.iterkeys())[0]]['fmtid']
			#print "found best available video url:",video_url
		return video_url

	def run(self, tubeid, session, service):
		try:
			myurl = self.getVideoUrl(tubeid)
			print "Playing URL", myurl
			if myurl is None:
				session.open(MessageBox, _("Sorry, video is not available!"), MessageBox.TYPE_INFO)
				return

			player_lock()
			myreference = eServiceReference(4097, 0, myurl)
			session.open(VuPlayer, myreference, service)
		except Exception, msg:
			player_unlock()
			print "Error >>", msg

class VuPlayerService:
	def __init__(self, session):
		self.enable = False
		self.socket_timeout = 0
		self.max_buffer_size = 1024
		self.uds_file = "/tmp/vuplus.tmp"
		self.session = session
		try:
			os.remove(self.uds_file)
		except OSError:
			pass
	
	def start(self, timeout = 1):
		self.socket_timeout = timeout
		thread.start_new_thread(self.run, (True,))

	def stop(self):
		self.enable = False

	def isRunning(self):
		return self.enable

	def run(self, e = True):
		if self.enable:
			return
		self.enable = e
		self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		self.sock.settimeout(self.socket_timeout)
		self.sock.bind(self.uds_file)
		self.sock.listen(1)
		while(self.enable):
			try:
				conn, addr = self.sock.accept()
				self.parseHandle(conn, addr)
				conn.close()
			except socket.timeout:
				#print "[socket timeout]"
				pass

	def parseHandle(self, conn, addr):
		# [http://www.youtube.com/watch?v=BpThu778qB4&feature=related]
		data = conn.recv(self.max_buffer_size)
		print "[%s]" % (data) 
		tmp = data.split("?")
		print tmp # ['http://www.youtube.com/watch', 'v=BpThu778qB4&feature=related']
		service = self.session.nav.getCurrentlyPlayingServiceReference()
		if len(tmp) == 2 and tmp[0] == "http://www.youtube.com/watch":
			tmp = tmp[1].split("&")
			print tmp # ['v=BpThu778qB4', 'feature=related']
			if len(tmp) == 2:
				tmp = tmp[0].split("=")
				print tmp # ['v', 'BpThu778qB4']
				if len(tmp) == 2 and tmp[0] == "v":
					player = VuPlayerLauncher()
					player.run(tmp[1], self.session, service)
					while player_islock():
						time.sleep(1)
					self.session.nav.playService(service)
					data = "ok$"
				else:
					data = "nok$parsing fail"
			else:
				data = "nok$parsing fail"
		else:
			data = "nok$parsing fail"
		conn.send(data)

class BrowserLauncher(ConfigListScreen, Screen):
	skin=   """
		<screen name="BrowserLauncher" position="center,center" size="300,160" title="Web Browser">
			<ePixmap pixmap="Vu_HD/buttons/red.png" position="50,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="Vu_HD/buttons/green.png" position="170,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="50,0" zPosition="1" size="115,30" font="Regular;20" halign="center" valign="center" transparent="1" />
			<widget source="key_green" render="Label" position="170,0" zPosition="1" size="115,30" font="Regular;20" halign="center" valign="center" transparent="1" />
			<widget name="config" position="0,50" size="300,70" scrollbarMode="showOnDemand" />
			<widget name="introduction" position="0,120" size="300,40" font="Regular;20" halign="center" backgroundColor="#a08500" transparent="1" />
		</screen>
		"""
	def __init__(self, session): 
		Screen.__init__(self, session)
                self.session = session

		self.browser_root = "/usr/bin"
		self.browser_name = "arora"
		self.mouse_cond = "/proc/stb/fp/mouse"
		self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions", "WizardActions", "ColorActions", "SetupActions", ],
                {	"red": self.keyCancel,
			"cancel": self.keyCancel,
			"green": self.keyGo,
                }, -2)

		self.list = []
		ConfigListScreen.__init__(self, self.list)

		self["key_red"] = StaticText(_("Exit"))
		self["key_green"] = StaticText(_("Start"))
		self.introduntion = Label(_(" "))
		self["introduction"] = self.introduntion

		self.devices_string = ""
		self.mouse_choice_list = []
		self.mouse_device_list = []
		self.keyboard_choice_list = []
		self.keyboard_device_list = []
		self.makeConfig()
		#time.sleep(2)

		self.lock = False
		self.vu_service = VuPlayerService(self.session)
		self.vu_service.start(timeout=5)

	def enableRCMouse(self, mode): #mode=[0|1]|[False|True]
		if os.path.exists(self.mouse_cond):
			self.cmd("echo %d > %s" % (mode, self.mouse_cond))

	def cmd(self, cmd):
		print "prepared cmd:", cmd
		os.system(cmd)

	def keyNone(self):
		None

	def keyCancel(self):
		#if self.lock == False:
			self.vu_service.stop()
			self.cmd("killall -9 %s"%(self.browser_name))
			self.cmd("echo 60 > /proc/sys/vm/swappiness")
			self.introduntion.setText(" ")
			if self.mouse.value == 0:
				self.enableRCMouse(False) #rc-mouse off
			fbClass.getInstance().unlock()
			#eRCInput.getInstance().unlock()
			self.close()

	def makeConfig(self):
		self.devices = eConsoleAppContainer()
		self.devices.dataAvail.append(self.callbackDevicesDataAvail)
		self.devices.appClosed.append(self.callbakcDevicesAppClose)
		self.devices.execute(_("cat /proc/bus/input/devices"))

	def callbackDevicesDataAvail(self, ret_data):
		self.devices_string = self.devices_string + ret_data

	def callbakcDevicesAppClose(self, retval):
		self.parseDeviceData(self.devices_string)
		self.makeHandlerList()

		# none : -1, rc : 0, usb : 1
		self.mouse_choice_list.append((2, _("None")))
		self.keyboard_choice_list.append((2, _("None")))
		
		print self.mouse_choice_list
		print self.keyboard_choice_list
		print self.mouse_device_list
		print self.keyboard_device_list

		self.mouse = ConfigSelection(default = self.mouse_choice_list[0][0], choices = self.mouse_choice_list)
		self.keyboard = ConfigSelection(default = self.mouse_choice_list[0][0], choices = self.keyboard_choice_list)
		
		self.list.append(getConfigListEntry(_('Mouse'), self.mouse))		
		self.list.append(getConfigListEntry(_('Keyboard'), self.keyboard))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def parseDeviceData(self, data):
		n = ""
		p = ""
		h = ""
		self.devices=[]
		lines=data.split('\n')
		for line in lines:
			if line == None or line == "":
				if h != None and len(h) != 0:
					print "find driver >> name[%s], phys[%s], handler[%s]" % (n, p, h)
					self.devices.append([n, p, h])
				n = ""
				p = ""
				h = ""
				continue
			if line[0] == 'N':
				n = line[8:].strip()
			elif line[0] == 'P':
				p = line[8:].strip()
			elif line[0] == 'H':
				h = line[12:].strip()

	def makeHandlerList(self):
		if self.devices == None or self.devices == []:
			return False

		mouse_pc_h = []
		mouse_rc_h = []
		keyboard_pc_h = []
		keyboard_rc_h = []
		for dev in self.devices:
			n = dev[0]
			p = dev[1]
			h = dev[2]
			if p.startswith("usb-ohci-brcm"):
				if h.rfind("mouse") >= 0:
					mouse_pc_h = [(1, _("USB Mouse")), self.getHandlerName(h, "mouse")]
				else:
					if len(keyboard_pc_h) == 0:
						keyboard_pc_h = [(1, _("USB Keyboard")), self.getHandlerName(h, "event")]
			else:
				if n[1:].startswith("dreambox") and os.path.exists(self.mouse_cond) :
					mouse_rc_h    = [(0, _("RemoteControl")), self.getHandlerName(h, "event")]
					keyboard_rc_h = [(0, _("RemoteControl")), self.getHandlerName(h, "event")]
		if len(mouse_rc_h) > 0:
			self.mouse_choice_list.append(mouse_rc_h[0])
			self.mouse_device_list.append(mouse_rc_h[1])
		if len(mouse_pc_h) > 0:
			self.mouse_choice_list.append(mouse_pc_h[0])
			self.mouse_device_list.append(mouse_pc_h[1])

		if len(keyboard_rc_h) > 0:
			self.keyboard_choice_list.append(keyboard_rc_h[0])
			self.keyboard_device_list.append(keyboard_rc_h[1])
		if len(keyboard_pc_h) > 0:
			self.keyboard_choice_list.append(keyboard_pc_h[0])
			self.keyboard_device_list.append(keyboard_pc_h[1])
		return True

	def getHandlerName(self, h, s):
		if h is None or len(h) == 0:
			return ""

		handles = h.split()                                                
		#print "handles >> ", handles
		for tmp_h in handles:                                                                                                    
			#print "handle_item >> ", tmp_h
			if tmp_h.startswith(s):          
				#print "detected : [%s]" % tmp_h
				return tmp_h
		return ""

	def keyGo(self):
		if self.lock == False:
			self.lock = True
			
			self.introduntion.setText("Run web-browser.\nPlease, wait...")
			self.cmd("echo 0 > /proc/sys/vm/swappiness")

			kbd_cmd = ""
			mouse_cmd = ""
			extra_cmd = "" 
			browser_cmd = "%s/%s -qws" % (self.browser_root, self.browser_name)

			fbClass.getInstance().lock()
			#eRCInput.getInstance().lock()

			if self.mouse.value == 0:
				self.enableRCMouse(True) #rc-mouse on
				idx = self.getListIndex(self.mouse_choice_list, 0)
				mouse_cmd = "export QWS_MOUSE_PROTO=LinuxInput:/dev/input/%s; " % (self.mouse_device_list[idx])
			elif self.mouse.value == 1:
				mouse_cmd = " "
				#mouse_cmd = "export QWS_MOUSE_PROTO=Auto:/dev/input/%s; " % (m)
			elif self.mouse.value == 2:
				mouse_cmd = "export QWS_MOUSE_PROTO=None; "

			if self.keyboard.value == 0:
				idx = self.getListIndex(self.keyboard_choice_list, 0)
				kbd_cmd = "export QWS_KEYBOARD=LinuxInput:/dev/input/%s; " % (self.keyboard_device_list[idx])
			elif self.keyboard.value == 1:
				idx = self.getListIndex(self.keyboard_choice_list, 1)
				kbd_cmd = "export QWS_KEYBOARD=LinuxInput:/dev/input/%s; " % (self.keyboard_device_list[idx])
			elif self.keyboard.value == 2:
				kbd_cmd = " "
			print "mouse cmd >>", mouse_cmd, " >> ", self.mouse.value
			print "keyboard cmd >>", kbd_cmd, " >> ", self.keyboard.value

			cmd = "%s%s%s%s" % (extra_cmd, kbd_cmd, mouse_cmd, browser_cmd)
			print "prepared command : [%s]" % cmd

			self.launcher = eConsoleAppContainer()
			self.launcher.appClosed.append(self.callbackLauncherAppClosed)
			self.launcher.dataAvail.append(self.callbackLauncherDataAvail)
			self.launcher.execute(cmd)
			print "running arora..."

	def getListIndex(self, l, v):
		idx = 0
		for i in l:
			if i[0] == v:
				return idx;
			idx = idx + 1
		return -1

	def callbackLauncherDataAvail(self, ret_data):
		print ret_data
		if ret_data.startswith("--done--"):
			self.lock = False
			self.keyCancel()
		
	def callbackLauncherAppClosed(self, retval = 1):
		None

def main(session, **kwargs):
	session.open(BrowserLauncher)
                                                           
def Plugins(**kwargs):            
	return PluginDescriptor(name=_("Web Browser"), description="start web browser", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main)


