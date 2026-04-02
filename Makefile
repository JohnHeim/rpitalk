# Makefile for rpitalk - Debian-compliant

PREFIX ?= /usr
DESTDIR ?=

PYDIR       = $(PREFIX)/lib/python3/dist-packages
BINDIR      = $(PREFIX)/bin
ETCDIR      = /etc/rpitalk
SYSDDIR     = $(PREFIX)/lib/systemd/system
LIBEXECDIR  = $(PREFIX)/lib/rpitalk

.PHONY: all install clean

all:
	@echo "Nothing to build"

install:
	# Python modules
	install -d $(DESTDIR)$(PYDIR)
	install -m 644 dectalkemulator.py $(DESTDIR)$(PYDIR)/
	install -m 644 hardwaresynthemulator.py $(DESTDIR)$(PYDIR)/
	install -m 644 litetalkemulator.py $(DESTDIR)$(PYDIR)/

	# Executables
	install -d $(DESTDIR)$(BINDIR)
	install -m 755 rpitalk-config $(DESTDIR)$(BINDIR)/
	install -m 755 rpitalk-emulator $(DESTDIR)$(BINDIR)/

	# Config files (conffiles handled by debian/rpitalk.conffiles)
	install -d $(DESTDIR)$(ETCDIR)
	install -m 644 emulator.conf $(DESTDIR)$(ETCDIR)/
	install -m 644 gadget.conf $(DESTDIR)$(ETCDIR)/

	# Internal script
	install -d $(DESTDIR)$(LIBEXECDIR)
	install -m 755 gadget.sh $(DESTDIR)$(LIBEXECDIR)/

	# Systemd units
	install -d $(DESTDIR)$(SYSDDIR)
	install -m 644 rpitalk.service $(DESTDIR)$(SYSDDIR)/
	install -m 644 rpitalk-gadget.service $(DESTDIR)$(SYSDDIR)/

clean:
	@echo "Nothing to clean"
