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
DECtalkEmulator
Emulate a DECtalk hardware synth
"""

import logging
import os
import speechd
import sys
from hardwaresynthemulator import HardwareSynthEmulator

class DECtalkEmulator(HardwareSynthEmulator):

    FlushChar = 0x01
    BreakChar = 0x03
    IndexChar = 0x0B
    XOnChar = 0x11
    XOffChar = 0x13
    CommandStart = 0x5B    # left bracket "["
    CommandEnd = 0x5D    # right bracket "]"

    def __init__(self, serialDevice,debug=0, rate=400, pitch=100, punctuation="n", volume=50):
        super().__init__(serialDevice, debug)   # call Parent.__init__

        self.rate = rate
        self.pitch = pitch
        self.punctuation = punctuation
        self.volume = volume
        self.g5 = 0
        self .commandMode = None

        self.setSpeechRate(f"{rate}")
        self.setSpeechPitch(f"{pitch}")
        self.setSpeechPunctuation(f"{punctuation}")
        self.setSpeechVolume(f"{volume}")

    #===Speech functions ===#
    def setSpeechRate(self, strValue):
        """
        Converts the DECtalk speech rate, a number btween 75 and 650
        to a Speech Dispatcher speech rate, a number between -100 and +100,
        and sets the Speech Dispatcher speech rate.
        """
        if strValue and (strValue[0] == 0x2B or strValue[0] == 0x2D):
            newValue = self.rate + int(strValue)
        else:
            newValue = int(strValue)
        setValue = self.convertWithinRange(newValue, 75, 650)
        try:
            self.speechClient.set_rate(setValue)
            self.rate = newValue
            logging.info(f"Set speech rate to {newValue} ({setValue}).")
        except Exception as error:
            logging.warning(f"Error setting rate to {newValue} ({setValue}): {error}")

    def setSpeechPitch(self, strValue):
        """
        Converts the DECtalk average speech pitch, a number in mHz btween 50 and 350,
        to a Speech Dispatcher pitch, a number between -100 and +100,
        and sets the Speech Dispatcher speech pitch.
        """
        if strValue and (strValue[0] == 0x2B or strValue[0] == 0x2D):
            newValue = self.pitch + int(strValue)
        else:
            newValue = int(strValue)

        # Klooge for Speakup:
        # Actual range is 50 to 350
        #  but by  setting range to 50 to 180,
        # we put the default, 122,  right in the middle
        # and we make the pitch changes more pronounced.
        setValue = self.convertWithinRange(newValue , 50, 180)
        try:
            self.speechClient.set_pitch(setValue)
            self.pitch = newValue
            logging.info(f"Set speech pitch to {newValue} ({setValue}).")
        except Exception as error:
            logging.warning(f"Error setting pitch to {newValue} ({setValue}): {error}")

    def setSpeechRange(self, strValue):
        """
        Sets the range of the speech pitch.
        The value is a percentage in both DECtalk and Speech Dispatcher so no conversion is necessary.
        """
        if strValue and (strValue[0] == 0x2B or strValue[0] == 0x2D):
            newValue = self.pitch + int(strValue)
        else:
            newValue = int(strValue)
        setValue = max(0, min(100, newValue))
        try:
            self.speechClient.set_pitch_range(setValue)
            self.range = newValue
            logging.info(f"Set speech pitch range to {newValue}.")
        except Exception as error:
            logging.warning(f"Error setting pitch range to {newValue}: {error}")

    def setSpeechVolume(self, strValue):
        """
        Converts the DECtalk volume, a number btween 0 and 100,
        to a Speech Dispatcher volume, a number between -100 and +100,
        and sets the Speech Dispatcher speech volume.
        """
        if strValue and (strValue[0] == 0x2B or strValue[0] == 0x2D):
            newValue = self.volume + int(strValue)
        else:
            newValue = int(strValue)
        setValue = self.convertWithinRange(newValue, 0, 100)
        try:
            self.speechClient.set_volume(setValue)
            self.volume = newValue
            logging.info(f"Set speech volume to {newValue} ({setValue}).")
        except Exception as error:
            logging.warning(f"Error setting volume to {newValue} ({setValue}): {error}")

    def setSpeechG5(self, strValue):
        """
        Converts the DECtalk design voice g5 value, a number btween 60 and 86,
        to a Speech Dispatcher volume, a number between -100 and +100,
        and sets the Speech Dispatcher speech volume.
        """
        if strValue and (strValue[0] == 0x2B or strValue[0] == 0x2D):
            newValue = self.g5 + int(strValue)
        else:
            newValue = int(strValue)
        setValue = self.convertWithinRange(newValue, 60, 86)
        try:
            self.speechClient.set_volume(setValue)
            self.volume = newValue
            logging.info(f"Set design voice g5 value to {newValue} ({setValue}).")
        except Exception as error:
            logging.warning(f"Error setting g5 value to {newValue} ({setValue}): {error}")

    def setSpeechPunctuation(self, strValue):
        """
        Map DECtalk punctuation level to Speech Dispatcher punctuation level and set the value.
        """
        mapping = {
            "n": "none",
            "s": "some",
            "a":  "all",
            "p": "none",   # closest approximation
        }

        key =strValue.lower()[:1]
        if key not in mapping:
            raise ValueError(f"Invalid DECtalk punctuation level: {strValue}, ({key}).")
        else:
            setValue = mapping[key]
            try:
                self.speechClient.set_punctuation(setValue)
                self.punctuation = key
                logging.info(f"Set punctuation to {key} ({setValue}).")
            except Exception as error:
                logging.warning(f"Error setting  punctuation to {key} ({setValue}): {error}")

    def setVoiceByName(self, voiceName):
        """
        Convert a voice name into a Speech Dispatcher voice number
        and call setVoiceByID
        """
        mapping = {
            "p": 1
        }
        key =voiceName.lower()[:1]
        if key not in mapping:
            raise ValueError(f"Invalid DECtalk voice name: {voiceName}, ({key}).")
        else:
            voiceID = mapping[key]
            self.setVoiceByID(voiceID)

    def setVoiceByID(self, voiceID):
        """
        """
        mapping = [
            "default",
            "MALE1",     # Paul
            "MALE2",   # Harry
            "MALE3",   # Frank
            "MALE3",   # Dennis
            "CHILD_MALE",   # Kit
            "FEMALE1",   # Betty
            "FEMALE2",   # Ursula
            "FEMALE3",   # Rita
            "CHILD_FEMALE",   # Wendy
        ]

        if voiceID >= 0 and voiceID <= 9:
            voice = mapping[voiceID]
            self.speechClient.set_voice(voice)
            logging.info(f"Set voice to {voice}, ID {voiceID}.")

    #=== Emulation Functions ===#
    def processCommands(self, buffer):
        logging.debug(f"Processing commands: [{buffer}]")
        commands = buffer.strip().split(":")
        for command in commands:
            if not command:
                continue

            parms = command.split()
            parms += [None] * (3 - len(parms)) # Pad to 3 values
            cmd = parms[0][:2]
            val = parms[1]

            if cmd == "ra" and val != "":
                self.setSpeechRate(val)

            elif cmd == "vo" and val != "":
                self.setSpeechVolume(val)

            elif cmd == "pu" and val != "":
                self.setSpeechPunctuation(val)

            elif cmd == "na" and val != "":
                self.setVoiceByName(val)

            elif cmd == "dv" and val != "":
                sbc = parms[1]
                val = parms[2]

                if sbc == "ap" and val != "":
                        self.setSpeechPitch(val)

                elif sbc == "g5" and val != "":
                    self.setSpeechG5(val)

                elif sbc == "pr" and val != "":
                    self.setSpeechRange(val)

            elif cmd[0] == "n" and cmd[1] >= "0" and cmd[1] <= "9":
                self.setVoiceByID(ord(cmd[1]) - ord("0"))

            else:
                logging.debug(f"Unprocessed command '{command}'/{cmd}.")

    def parse(self, data):

        for byte in data:
            # This bloc of code processes the byte.  There is another comment at the end of the bloc of code.
            if byte == self.BreakChar:
                self.speechClient.cancel()
                self.response.append(self.FlushChar)

            elif byte == self.IndexChar:
                self.response.append(self.IndexChar)

            elif byte == self.CommandStart:
                self.commandMode = True

            elif byte == self.CommandEnd:
                if self.received:
                    self.processCommands(self.received.decode("utf-8"))
                    self.received.clear()
                self.commandMode = False

            # Printable char
            elif 0x20 <= byte <= 0x7E:
                self.received.append(byte)
            # End of byte processing code block.

            if byte == self.BreakChar or byte == self.IndexChar or byte == self.CommandStart or len(self.received) >= self.MaxBufferSize:
                self.speak(self.received.decode(errors="ignore"))
                self.received.clear()
"""
End of DECtalkEmulator class
"""
