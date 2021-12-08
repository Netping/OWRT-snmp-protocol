SECTION="NetPing modules"
CATEGORY="Base"
TITLE="EPIC5 OWRT_SNMP_Protocol"

PKG_NAME="OWRT_SNMP_Protocol"
PKG_VERSION="Epic5.V1.S1"
PKG_RELEASE=1

MODULE_FILES=owrt_snmp_protocol.py
MODULE_FILES_DIR=/usr/lib/python3.7/

.PHONY: all install

all: install
	
install:
	for f in $(MODULE_FILES); do cp $${f} $(MODULE_FILES_DIR); done

clean:
	for f in $(MODULE_FILES); do rm -f $(MODULE_FILES_DIR)$${f}; done
