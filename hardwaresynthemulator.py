# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 John G Heim
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
HardwareSynthEmulator class definition
Emulates a hardware speech synthesizer.
"""

import inspect
import logging
import os
import select
import speechd
import sys
import termios
import time
import tty

# termios attribute indices (Linux / POSIX)
IFLAG = 0
OFLAG = 1
CFLAG = 2
LFLAG = 3
ISPEED = 4
OSPEED = 5
CC = 6

class HardwareSynthEmulator:

    Identity  = "RPItalk"
    Version = "0.9"
    DeviceIdString = f"{Identity} {Version}\r"
    MaxBufferSize = 4096

    def __init__(self, serialDevice, debug=0):
        self.serialDevice = serialDevice

        self.serialPort = None
        self.received = bytearray()
        self.response = bytearray()

        logging.basicConfig(format="%(message)s")
        self.debugLevel = int(os.getenv("DEBUG", f"{debug}"))
        self.setDebugLevel(self.debugLevel)

        message = f"Starting {self.Identity}, version {self.Version}."
        try:
            self.speechClient = speechd.SSIPClient(self.Identity, socket_path="/run/speech-dispatcher/speechd.sock", autospawn=False)
        except Exception as error:
            logging.critical(f"Error initializing Speech Dispatcher: {error}")
            sys.exit(1)
        self.speak(message)
        logging.info(message)

    def setDebugLevel (self, debug):
        self.debugLevel = debug
        if self.debugLevel >= 2:
            logLevel = logging.DEBUG
        elif self.debugLevel >= 1:
            logLevel = logging.INFO
        else:
            logLevel = logging.WARNING
        logging.getLogger().setLevel(logLevel)
        logging.info(f"Debug/log  level set to {self.debugLevel}/{logLevel}.")

    def dumpBytes(self, data: bytes, key: str) -> None:
        numBytes = len(data)
        hexBytes = " ".join(f"{b:02x}" for b in data)
        asciiBytes = "".join(chr(b) if 32 <= b <= 126 else "." for b in data)
        print(f"{key} {numBytes} bytes: {hexBytes} |{asciiBytes}|", file=sys.stderr, flush=True)

    def toInteger(self, bytes, dflt=None):
        try:
            return int(bytes)
        except (TypeError, ValueError):
            return dflt

    def convertWithinRange(self, oldValue, r1m, r1x, r2m=-100, r2x=100):
        """
        Takes a value in one range(like  75 to 650 (the acceptable range for speech rate for a  DECtalk)
        and mathematically converts it to  another range, (like -100 to 100, the range of values for Speech Dispatcher).
        """
        newValue = int((oldValue - (r1x - r1m)/2 - r1m) / ((r1x - r1m)/(r2x - r2m)) + (r2x +r2m)/2)
        return max(r2m, min(r2x, newValue))

    #=== Speech  Functions ===#
    def speak(self, text):
        if text.strip():
            self.speechClient.speak(text)

    def endSpeech(self):
        self.speechClient.stop()
        self.speechClient.close()

    def testSpeech(self):
        """
        Reads user input and sends it to Speech Dispatcher.
        """
        print("Type text and press Enter to speak.")
        print("Press Ctrl+D or Ctrl+C to exit.")

        try:
            while True:
                try:
                    text = input("> ")
                    data = text.encode('ascii') + b"\r"
                    response = self.parse(data)
                    logging.info(f"Response is '{response}'.")
                except EOFError:
                    print()
                    break

        except KeyboardInterrupt:
            print()

        finally:
            self.endSpeech()
    #=== Host I/O functions ===#
    def openSerialPort2(self):
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

    def openSerialPort(self):
        while not os.path.exists(self.serialDevice):
            logging.info(f"Waiting for USB device, {self.serialDevice} ...")
            time.sleep(1.0)

        try:
            self.serialPort = os.open(self.serialDevice, os.O_RDWR | os.O_NOCTTY)

            # Prevent CR/LF munging, ^C handling, etc.
            tty.setraw(self.serialPort)

            # Fetch  serial port attributes
            attrs = termios.tcgetattr(self.serialPort)
            attrs[CFLAG] |= (termios.CLOCAL | termios.CREAD)

            #  Set baud  rate to 9600
            attrs[ISPEED] = termios.B9600
            attrs[OSPEED] = termios.B9600

            # Make reads block until at least 1 byte arrives.
            attrs[CC][termios.VMIN] = 1
            attrs[CC][termios.VTIME] = 0

            # Disable software flow control.
            attrs[IFLAG] &= ~(termios.IXON | termios.IXOFF | termios.IXANY)
            termios.tcsetattr(self.serialPort, termios.TCSANOW, attrs)
        except OSError as e:
            raise RuntimeError(f"Failed to open/configure serial device {self.serialDevice}: {e}")
        logging.info(f"Opened serial port on device, {self.serialDevice}.")

    def writeToHost(self, data: bytes) -> bool:
        """
        Write bytes to the host
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
        return success

    def testConnection(self, count=40):
        cnt = 0
        idx = 0
        while True:
            self.openSerialPort()
            print("Beginning test...", file=sys.stderr, flush=True)
            while (self.serialPort):
                try:
                    readableList, _, _ = select.select([self.serialPort], [], [])
                    if self.serialPort in readableList:
                        data = os.read(self.serialPort, 1024)
                        if not data:
                            raise OSError("Host disconnected")
                        else:
                            for byte in data:
                                self.received.append(byte)
                                idx += 1
                                if idx >= 5:
                                    hexBytes = " ".join(f"{b:02x}" for b in self.received)
                                    asciiBytes = "".join(chr(b) if 32 <= b <= 126 else "." for b in self.received)
                                    cnt += 1
                                    print(f"{cnt:02d}: {hexBytes} '{asciiBytes}'", file=sys.stderr, flush=True)
                                    self.received.clear()
                                    idx  = 0
                                    if cnt >= count:
                                        sys.exit()

                except OSError:
                    print("Detected host disconnect.", file=sys.stderr, flush=True)
                    os.close(self.serialPort)
                    self.serialPort = None

#=== Emulation functions ===#
    def parse(self, data):

        for byte in data:
            if 0x20 <= byte <= 0x7E:
                self.received.append(byte)

            if byte in [0x01, 0x03, 0x0b, 0x0D] or  len(self.received) >= self.MaxBufferSize:
                self.speak(self.received.decode(errors="ignore"))
                self.received.clear()

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
                            if self.debugLevel >= 3:
                                self.dumpBytes(data, 'RX')
                            self.parse(data)
                            if self.response:
                                if self.debugLevel >= 3:
                                    self.dumpBytes(self.response, 'AK')
                                self.writeToHost(self.response)
                                self.response.clear()

                except OSError:
                    logging.warn("Detected host disconnect.")
                    os.close(self.serialPort)
                    self.serialPort = None

        self.endSpeech()

"""
End of HardwareSynthEmulator class definition
"""

