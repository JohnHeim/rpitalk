# rpitalk

rpitalk is a Python-based DECtalk emulator for Raspberry Pi. It works with an OTG (gadget) port and a functioning sound system, communicating with Speech Dispatcher to provide text-to-speech output.

---

## Hardware Requirements

- A Raspberry Pi with an OTG (gadget) port
- Functional audio output (headphones, speakers, or HAT)
  **Example:** Raspberry Pi Zero 2 W with a Pimoroni PIM485 HAT

---

## Software Requirements

- **Speech Dispatcher** must be installed and configured for your user account.
- Suggested TTS is espeak-ng but any TTS engine and language is fine.
- Verify it works with:

```bash
spd-say "Test message"

You should hear the spoken text. If not, make sure Speech Dispatcher is installed and your user has permission to access audio.
Installation Steps

    Clone the repository

git clone git@github.com:JohnHeim/rpitalk.git
cd rpitalk

    Copy the main files to system locations

sudo cp rpitalk-emulator /usr/local/bin/
sudo cp rpitalk.py /usr/local/lib/python3.13/dist-packages
sudo cp dectalkemulator.py /usr/local/lib/python3.13/dist-packages
cp rpitalk.service ~/.config/systemd/user/rpitalk.service

    Note: Adjust paths if you want to install somewhere else.

    Reload systemd to recognize the new service

systemctl --user enable rpitalk.service

    Enable the service to start automatically at boot

systemctl --user enable rpitalk.service


    Start the service now

systemctl --user start rpitalk.service

    Enable lingering so the service runs even when no user is logged in

loginctl enable-linger "$USER"

Testing rpitalk

    Run manually for testing:

python3 /usr/local/bin/rpitalk.py

    rpitalk will now listen on the OTG port and provide text-to-speech output automatically.

    You can integrate it with Speakup or other applications that expect DECtalk TTS.

License

This program is free software, licensed under the GNU General Public License version 3 or (at your option) any later version (GPL-3+).


---

If you want, I can also **append a small “Troubleshooting” section** for beginners that covers:

- OTG port detection issues
- Speech Dispatcher misconfiguration
- Audio output problems

This makes the README much more complete for new users. Do you want me to add that?


