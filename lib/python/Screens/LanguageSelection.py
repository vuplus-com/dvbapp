from Screen import Screen

#	ikseong
from Components.ActionMap import ActionMap,NumberActionMap
from Components.Language import language
from Components.config import config
from Components.Sources.List import List
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.language_cache import LANG_TEXT

def _cached(x):
	return LANG_TEXT.get(config.osd.language.value, {}).get(x, "")

from Screens.Rc import Rc

from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN

from Tools.LoadPixmap import LoadPixmap

def LanguageEntryComponent(file, name, index):
	png = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "countries/" + file + ".png"))
	if png == None:
		png = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "countries/missing.png"))
	res = (index, name, png)
	return res
#	ikseong
from Plugins.SystemPlugins.FactoryTest.plugin import FactoryTest

class LanguageSelection(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)

		self.oldActiveLanguage = language.getActiveLanguage()

		self.list = []
		self["languages"] = List(self.list)
		self["languages"].onSelectionChanged.append(self.changed)

		self.updateList()
		self.onLayoutFinish.append(self.selectActiveLanguage)
#	ikseong
		self["actions"] = NumberActionMap(["OkCancelActions","NumberActions"], 
		{
			"ok": self.save,
			"cancel": self.cancel,
			"1": self.keyNumberGlobal,
			"2": self.keyNumberGlobal,
			"3": self.keyNumberGlobal,
			"4": self.keyNumberGlobal,
			"5": self.keyNumberGlobal,
			"6": self.keyNumberGlobal,
			"7": self.keyNumberGlobal,
			"8": self.keyNumberGlobal,
			"9": self.keyNumberGlobal,
			"0": self.keyNumberGlobal,
		}, -1)
		self.testkey=0
		
#	ikseong
	def keyNumberGlobal(self, number):
		self.testkey = self.testkey * 10 + number
		if self.testkey > 10000:
			self.testkey = self.testkey%10000
		if self.testkey == 4599:
			self.session.open(FactoryTest)
		print "testkey", self.testkey

	def selectActiveLanguage(self):
		activeLanguage = language.getActiveLanguage()
		pos = 0
		for x in self.list:
			if x[0] == activeLanguage:
				self["languages"].index = pos
				break
			pos += 1

	def save(self):
		self.run()
		self.close()

	def cancel(self):
		language.activateLanguage(self.oldActiveLanguage)
		self.close()

	def run(self, justlocal = False):
		print "updating language..."
		lang = self["languages"].getCurrent()[0]
		config.osd.language.value = lang
		config.osd.language.save()
		self.setTitle(_cached("T2"))
		
		if justlocal:
			return

		language.activateLanguage(lang)
		config.misc.languageselected.value = 0
		config.misc.languageselected.save()
		print "ok"

	def updateList(self):
		first_time = not self.list

		languageList = language.getLanguageList()
		if not languageList: # no language available => display only english
			list = [ LanguageEntryComponent("en", _cached("en_EN"), "en_EN") ]
		else:
			list = [ LanguageEntryComponent(file = x[1][2].lower(), name = _cached("%s_%s" % x[1][1:3]), index = x[0]) for x in languageList]
		self.list = list

		#list.sort(key=lambda x: x[1][7])

		print "updateList"
		if first_time:
			self["languages"].list = list
		else:
			self["languages"].updateList(list)
		print "done"

	def changed(self):
		self.run(justlocal = True)
		self.updateList()

class LanguageWizard(LanguageSelection, Rc):
	def __init__(self, session):
		LanguageSelection.__init__(self, session)
		Rc.__init__(self)
		self.onLayoutFinish.append(self.selectKeys)
				
		self["wizard"] = Pixmap()
		self["text"] = Label()
		self.setText()
		
	def selectKeys(self):
		self.clearSelectedKeys()
		self.selectKey("UP")
		self.selectKey("DOWN")
		
	def changed(self):
		self.run(justlocal = True)
		self.updateList()
		self.setText()
		
	def setText(self):
		
		self["text"].setText(_cached("T1"))
