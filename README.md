# rpitalk

rpitalk is a Python-based DECtalk-compatible speech synthesizer emulator for Raspberry Pi.
It is intended for use on a Raspberry Pi with a USB OTG (gadget) port, but can also run on a machine with a standard serial port.
It communicates with Speech Dispatcher to provide text-to-speech output.

---

## Hardware Requirements

- A Raspberry Pi with a USB OTG (gadget) port (recommended)
- Functional audio output (headphones, speakers, or HAT)
  **Example:** Raspberry Pi Zero 2 W with a Pimoroni PIM485 HAT

---

## Software Requirements

- **Speech Dispatcher** must be installed and configured.
- Suggested TTS engine: **espeak-ng**, but any compatible Speech Dispatcher TTS engine can be used.
- Verify Speech Dispatcher is working:

```bash
spd-say "Test message"

