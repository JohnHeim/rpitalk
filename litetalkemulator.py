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
LiteTalkEmulator
Emulate a LiteTalk hardware synth
"""

import logging
import os
import speechd
import sys
from hardwaresynthemulator import HardwareSynthEmulator

class LiteTalkEmulator(HardwareSynthEmulator):

    ReturnChar = 0x0D
    CommandCode = 0x01
    CancelCommand = 0x18
    InterrogationCommand = 0x3F
    ResetCommand = 0x40
    IndexCommand = 0x45
    IdCommand = 0x49
    PitchCommand = 0x70
    PunctCommand = 0x62
    RateCommand = 0x73
    VolumeCommand = 0x76

    def __init__(self, serialDevice, debug=0, rate=5, pitch=50, punctuation="n", volume=5):
        super().__init__(serialDevice, debug)   # call Parent.__init__

        self.rate = rate
        self.pitch = pitch
        self.punctuation = punctuation
        self.volume = volume
        self .commandMode = None

        self.setSpeechRate(f"{rate}")
        self.setSpeechPitch(f"{pitch}")
        # self.setSpeechPunctuation(f"{punctuation}")
        # self.setSpeechVolume(f"{volume}")

    #=== Speech  Functions ===#
    def setSpeechRate(self, strValue):
        """
        Converts the LiteTalk speech rate, a number between 0 and 9
        to a Speech Dispatcher speech rate, a number between -100 and +100,
        and sets the Speech Dispatcher speech rate.
        """
        if strValue and (strValue[0] == 0x2B or strValue[0] == 0x2D):
            newValue = self.rate + self.toInteger(strValue, 0)
        else:
            newValue = self.toInteger(strValue, 8)
        setValue = self.convertWithinRange(newValue, 0, 9)
        try:
            self.speechClient.set_rate(setValue)
            self.rate = newValue
            logging.info(f"Set speech rate to {newValue} ({setValue}).")
        except Exception as error:
            logging.warning(f"Error setting rate to {newValue} ({setValue}): {error}")

    def setSpeechPitch(self, strValue):
        """
        Converts the  LiteTalk pitch, a number between 0 and 99
        to a Speech Dispatcher pitch, a number between -100 and +100,
        and sets the Speech Dispatcher speech pitch.
        """
        if strValue and (strValue[0] == 0x2B or strValue[0] == 0x2D):
            newValue = self.pitch + self.toInteger(strValue, 0)
        else:
            newValue = self.toInteger(strValue, 50)
        setValue = self.convertWithinRange(newValue , 0, 99)
        try:
            self.speechClient.set_pitch(setValue)
            self.pitch = newValue
            logging.info(f"Set speech pitch to {newValue} ({setValue}).")
        except Exception as error:
            logging.warning(f"Error setting pitch to {newValue} ({setValue}): {error}")

    def setSpeechVolume(self, strValue):
        """
        Takes a LiteTalk volume setting, a number between 0 and 9
        and converts it to a Speech Dispatcher volume setting, a number between -100 and 100,
        and sets the  Speech dispatcher volume.
    """
        if strValue and (strValue[0] == 0x2B or strValue[0] == 0x2D):
            newValue = self.volume + self.toInnteger(strValue, 0)
        else:
            newValue = self.toInteger(strValue, 5)
        setValue = self.convertWithinRange(newValue , 0, 9)
        try:
            self.speechClient.set_volume(setValue)
            self.volume = newValue
            logging.info(f"Set speech volume to {newValue} ({setValue}).")
        except Exception as error:
            logging.warning(f"Error setting volume to {newValue} ({setValue}): {error}")

    def setSpeechPunctuation(self, strValue):
        """
        Map LiteTalk punctuation level to Speech Dispatcher punctuation level and set the value.
        """
        mapping = ["all", "most",  "some", "none"]
        key = self.toInteger(strValue, 7)
        if key < 0 or key > 15:
            raise ValueError(f"Invalid LiteTalk punctuation level: {strValue}, ({key}).")
        else:
            setValue = mapping[key % 4]
            try:
                self.speechClient.set_punctuation(setValue)
                self.punctuation = key
                logging.info(f"Set punctuation to {key} ({setValue}).")
            except Exception as error:
                logging.warning(f"Error setting  punctuation to {key} ({setValue}): {error}")

    #=== Emulation Functions ===#
    def parse(self, data):
        for byte in data:
            if byte == self.CancelCommand:
                self.speechClient.cancel()
                self.received.clear()
                self.response += b"\r"

            elif byte == self.CommandCode:
                self.speak(self.received.decode(errors="ignore"))
                self.received.clear()
                self.commandMode = True

            elif self.commandMode:
                if byte == self.InterrogationCommand:
                    self.response += b"\x00\x20" + self.DeviceIdString.encode("ascii") + b"\r\x7F"
                    self.commandMode = False

                elif byte == self.IdCommand:
                    self.response += self.DeviceIdString.encode("ascii") + b"\r"
                    self.commandMode = False

                elif byte == self.IndexCommand:
                    self.response += b"\r"
                    self.commandMode = False

                elif byte == self.RateCommand:
                    self.setSpeechRate(self.received)
                    self.received.clear()
                    self.commandMode = False

                elif byte == self.PitchCommand:
                    self.setSpeechPitch(self.received)
                    self.received.clear()
                    self.commandMode = False

                elif byte == self.VolumeCommand:
                    self.setSpeechVolume(self.received)
                    self.received.clear()
                    self.commandMode = False

                elif byte == self.PunctCommand:
                    self.setSpeechPunctuation(self.received)
                    self.received.clear()
                    self.commandMode = False

                elif 0x30 <= byte <= 0x39 or byte == 0x2B or byte == 0x2D:
                    self.received.append(byte)

                else:
                    logging.info(f"Unhandled command, '{chr(byte)}'.")
                    self.received.clear()
                    self.commandMode = False

            # Not in commandMode
            # Printable char
            elif 0x20 <= byte <= 0x7E:
                self.received.append(byte)

            if byte == 0x00 or byte == self.ReturnChar or len(self.received) >= self.MaxBufferSize:
                self.speak(self.received.decode(errors="ignore"))
                self.received.clear()

"""
End  of LiteTalkEmulator class
"""
