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

class DECtalkEmulator:

    Identity  = "RPItalk"
    Version = "0.9"
    DeviceIdString = f"{Identity} {Version}\r"
    MaxBufferSize = 4096

    BreakChar = 0x03
    IndexChar = 0x0B
    CommandStart = 0x5B    # left bracket "["
    CommandEnd = 0x5D    # right bracket "]"

    def __init__(self, rate=400, pitch=200, volume=50, debug=0):

        self.rate = rate
        self.pitch = pitch
        self.volume = volume
        self.g5 = None
        self.punctuation = None

        self .commandMode = None
        self.characterBuffer = bytearray()

        self.debugLevel = int(os.getenv("DEBUG", f"{debug}"))
        if self.debugLevel >= 2:
            self.logLevel = logging.DEBUG
        elif self.debugLevel >= 1:
            self.logLevel = logging.INFO
        else:
            self.logLevel = logging.WARNING
        logging.basicConfig(level=self.logLevel, format="%(message)s")
        logging.debug(f"Debug  level set to  {self.logLevel}.")

        message = f"Starting {self.Identity}, version {self.Version}."
        try:
            self.speechClient = speechd.SSIPClient(self.Identity)
        except Exception as error:
            logging.critical(f"Error initializing Speech Dispatcher: {error}")
            exit()

        self.setSpeechRate(f"{rate}")
        self.setSpeechPitch(f"{pitch}")
        self.setSpeechVolume(f"{volume}")
        self.speak(message)
        logging.info(message)

    #=== Speech  Functions ===#
    def endSpeech(self):
        self.speechClient.stop()
        self.speechClient.close()

    def convertWithinRange(self, oldValue, r1m, r1x, r2m=-100, r2x=100):
        """
        Takes a value in one range(like  75 to 650 (the acceptable range for speech rate for a  DECtalk)
        and mathematically converts it to  another range, (like -100 to 100, the range of values for Speech Dispatcher).
        """
        newValue = int((oldValue - (r1x - r1m)/2 - r1m) / ((r1x - r1m)/(r2x - r2m)) + (r2x +r2m)/2)
        return max(r2m, min(r2x, newValue))

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

        setValue = self.convertWithinRange(newValue + 40, 50, 200)
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

    def speak(self, text):
        if text.strip():
            self.speechClient.speak(text)

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
        response = bytearray()

        for byte in data:
            # This bloc of code processes the byte.  There is another comment at the end of the bloc of code.
            if byte == self.BreakChar:
                self.speechClient.cancel()
                response.append(0x01)

            elif byte == self.IndexChar:
                response.append(self.IndexChar)

            elif byte == self.CommandStart:
                self.commandMode = True

            elif byte == self.CommandEnd:
                if self.characterBuffer:
                    self.processCommands(self.characterBuffer.decode("utf-8"))
                    self.characterBuffer.clear()
                self.commandMode = False

            # Printable char
            elif 0x20 <= byte <= 0x7E:
                self.characterBuffer.append(byte)
            # End of byte processing code block.

            if byte == self.BreakChar or byte == self.IndexChar or byte == self.CommandStart or len(self.characterBuffer) >= self.MaxBufferSize:
                self.speak(self.characterBuffer.decode(errors="ignore"))
                self.characterBuffer.clear()
        return  response
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
                    data = text.encode('ascii') + bytes([self.IndexChar])
                    response = self.parse(data)
                    logging.info(f"Response is '{response}'.")
                except EOFError:
                    print()
                    break

        except KeyboardInterrupt:
            print()

        finally:
            self.endSpeech()
"""
End of DECtalkEmulator class
"""
