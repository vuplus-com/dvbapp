from Screen import Screen
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.Harddisk import harddiskmanager
from Components.NimManager import nimmanager
from Components.About import about

from Tools.DreamboxHardware import getFPVersion

class About(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)

		self["EnigmaVersion"] = StaticText("Version: " + about.getEnigmaVersionString())
		self["ImageVersion"] = StaticText("Image: " + about.getImageVersionString())

		self["TunerHeader"] = StaticText(_("Detected NIMs:"))

		fp_version = getFPVersion()
		if fp_version is None:
			fp_version = ""
		else:
			fp_version = _("Frontprocessor version: %d") % fp_version

		self["FPVersion"] = StaticText(fp_version)

		nims = nimmanager.nimList()
		for count in (0, 1, 2, 3):
			if count < len(nims):
				self["Tuner" + str(count)] = StaticText(nims[count])
			else:
				self["Tuner" + str(count)] = StaticText("")

		self["HDDHeader"] = StaticText(_("Detected HDD:"))
		hddlist = harddiskmanager.HDDList()
		hdd = hddlist and hddlist[0][1] or None
		if hdd is not None and hdd.model() != "":
			self["hddA"] = StaticText(_("%s\n(%s, %d MB free)") % (hdd.model(), hdd.capacity(),hdd.free()))
		else:
			self["hddA"] = StaticText(_("none"))

		self["actions"] = ActionMap(["SetupActions", "ColorActions"], 
			{
				"cancel": self.close,
				"ok": self.close,
			})
