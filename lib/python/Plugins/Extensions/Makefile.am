installdir = $(pkglibdir)/python/Plugins/Extensions

SUBDIRS = TuxboxPlugins CutListEditor PicturePlayer MediaScanner MediaPlayer GraphMultiEPG SocketMMI DVDBurn Modem WebBrowser \
	VuplusEvent StreamTV DLNABrowser DLNAServer HbbTV BackupSuiteUSB BackupSuiteHDD

if HAVE_LIBDDVD
SUBDIRS += DVDPlayer
endif

install_PYTHON =	\
	__init__.py
