# SPDX-License-Identifier: GPL-3.0-or-later
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

"""
RPItalk class definition
Emulates a DECtalk hardware synth for Speakup
"""

import inspect
import logging
import os
import select
import sys
import termios
import time
import tty
from dectalkemulator import DECtalkEmulator

# termios attribute indices (Linux / POSIX)
IFLAG = 0
OFLAG = 1
CFLAG = 2
LFLAG = 3
ISPEED = 4
OSPEED = 5
CC = 6

class RPItalk(DECtalkEmulator):

    def __init__(self, serialDevice, debug=0):
        self.serialDevice = serialDevice
        self.serialPort = None
        super().__init__(500, 200, 50, debug)   # call Parent.__init__

    def dumpBytes(self, data: bytes, key: str) -> None:
        numBytes = len(data)
        hexBytes = " ".join(f"{b:02x}" for b in data)
        asciiBytes = "".join(chr(b) if 32 <= b <= 126 else "." for b in data)
        print(f"{key} {numBytes} bytes: {hexBytes} |{asciiBytes}|", file=sys.stderr, flush=True)

    def openSerialPort(self):
        while not os.path.exists(self.serialDevice):
            logging.info(f"Waiting for USB device, {self.serialDevice} ...")
            time.sleep(1.0)

        try:
            self.serialPort = os.open(self.serialDevice, os.O_RDWR | os.O_NOCTTY)
            tty.setraw(self.serialPort)
            attrs = termios.tcgetattr(self.serialPort)
            attrs[CC][termios.VMIN] = 1
            attrs[CC][termios.VTIME] = 0
            attrs[IFLAG] &= ~(termios.IXON | termios.IXOFF | termios.IXANY)
            termios.tcsetattr(self.serialPort, termios.TCSANOW, attrs)
        except OSError as e:
            raise RuntimeError(f"Failed to open/configure serial device {self.serialDevice}: {e}")
        logging.info(f"Opened serial port on device, {self.serialDevice}.")

    def writeToHost(self, data: bytes) -> bool:
        """
        Write bytes to the Speakup host
        Returns True on success, False on failure.
        """
        success = False
        if self.serialPort is None:
            logging.warning("Serial port is None", 1)
        else:
            try:
                bytesRequested = len(data)
                bytesWritten = os.write(self.serialPort, data)
                if bytesWritten != bytesRequested:
                    logging.warn(f"Wrote ({bytesWritten} when {bytesRequested} were to be sent.")
                else:
                    success = True

            except OSError as error:
                logging.warning(f"Write failed: {error}")
        if self.debugLevel >= 3:
            self.dumpBytes(data, 'AK')
        return success

    def emulate(self):
        while True:
            self.openSerialPort()
            logging.info("Beginning emulation...")
            while (self.serialPort):
                try:
                    readableList, _, _ = select.select([self.serialPort], [], [])
                    if self.serialPort in readableList:
                        data = os.read(self.serialPort, 1024)
                        if not data:
                            raise OSError("Host disconnected")
                        else:
                            response = self.parse(data)
                            if response:
                                self.writeToHost(response)

                except OSError:
                    print("Detected host disconnect.")
                    os.close(self.serialPort)
                    self.serialPort = None

        self.endSpeech()

    def testConnection(self, count=10):
        idx = 0
        self.openSerialPort()
        while self.serialPort:
            try:
                readableList, _, _ = select.select([self.serialPort], [], [])
                if self.serialPort in readableList:
                    data = os.read(self.serialPort, 1024)
                    if not data:
                        raise OSError("Host disconnected")
                    else:
                        idx += 1
                        if idx <= count:
                            numBytes = len(data)
                            hexBytes = " ".join(f"{b:02x}" for b in data)
                            asciiBytes = "".join(chr(b) if 32 <= b <= 126 else "." for b in data)
                            print(f"{idx} {numBytes} bytes: {hexBytes} |{asciiBytes}|")
                        else:
                            raise OSError("Reached end of test.")

            except OSError:
                os.close(self.serialPort)
                self.serialPort = None

        self.endSpeech()

"""
End of RPItalk class definition
"""
