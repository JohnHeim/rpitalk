#!/bin/sh
# gadget.sh - USB gadget setup script for RPITalk
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2026 John Heim
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Install this file to /usr/lib/rpitalk/gadget.sh
#
set -e

# Load config file
ConfigFile=/etc/rpitalk/gadget.conf
if [ ! -f "$ConfigFile" ]; then
    echo "ERROR: Config file $ConfigFile not found" >&2
    exit 1
fi

# Tell  shellcheck not to warn about sourcing a file:
# shellcheck disable=SC1090
. "$ConfigFile"

if [ "${ENABLE_GADGET:-1}" -eq 0 ]; then
    echo "USB gadget mode disabled in $ConfigFile"
    exit 0
fi

# Validate mandatory variables
VENDOR_ID=${VENDOR_ID:-0x1d6b}
PRODUCT_ID=${PRODUCT_ID:-0x0104}
SERIAL=${SERIAL:-rpitalk-001}
MANUFACTURER=${MANUFACTURER:-RPITalk Development Team}
PRODUCT=${PRODUCT:-RPITalk Synth Emulator}
CONFIGURATION_NAME=${CONFIGURATION_NAME:-RPITalk Config}

# Load module
if ! modprobe libcomposite 2>/dev/null; then
    echo "RPITalk: USB gadget (libcomposite) not available" >&2
    exit 0
fi

# Mount configfs if needed
if ! mountpoint -q /sys/kernel/config; then
    mount -t configfs none /sys/kernel/config
fi

GadgetDir=/sys/kernel/config/usb_gadget/rpitalk
mkdir -p "$GadgetDir"

echo "$VENDOR_ID" > "$GadgetDir/idVendor"
echo "$PRODUCT_ID" > "$GadgetDir/idProduct"

mkdir -p "$GadgetDir/strings/0x409"
echo "$SERIAL" > "$GadgetDir/strings/0x409/serialnumber"
echo "$MANUFACTURER" > "$GadgetDir/strings/0x409/manufacturer"
echo "$PRODUCT" > "$GadgetDir/strings/0x409/product"

# Notify the  kernel that we are creating a configs directory:
mkdir -p "$GadgetDir/configs/c.1"

# Now put something in it:
mkdir -p "$GadgetDir/configs/c.1/strings/0x409"
echo "$CONFIGURATION_NAME" > "$GadgetDir/configs/c.1/strings/0x409/configuration"

# CDC ACM (serial) function
mkdir -p "$GadgetDir/functions/acm.usb0"
if [ ! -e "$GadgetDir/configs/c.1/acm.usb0" ]; then
    ln -s "$GadgetDir/functions/acm.usb0" "$GadgetDir/configs/c.1/"
fi

# Bind to USB controller
UDC=$(ls /sys/class/udc 2>/dev/null | head -n1)
if [ -z "$UDC" ]; then
    echo "RPITalk: no UDC found" >&2
    exit 0
fi

# Clean UDC on re-run -- unbind the previous gadget before rebinding:
if [ -f "$GadgetDir/UDC" ] && [ -n "$(cat $GadgetDir/UDC)" ]; then
    echo "" > "$GadgetDir/UDC"
fi

echo "$UDC" > "$GadgetDir/UDC"

echo "RPITalk: [$0] success." >&2
# EOF
