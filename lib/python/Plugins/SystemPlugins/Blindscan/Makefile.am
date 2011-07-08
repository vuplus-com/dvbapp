installdir = $(pkglibdir)/python/Plugins/SystemPlugins/Blindscan

SUBDIRS = meta

install_PYTHON =	 \
	__init__.py \
	plugin.py 

dist_install_DATA =	\
	vuplus_blindscan

install-data-hook:
	@chmod +x $(DESTDIR)$(installdir)/vuplus_blindscan
