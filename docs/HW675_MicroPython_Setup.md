# HW-675 ESP32-C3 — MicroPython Setup Guide

## Board Info

| Detail | Value |
|--------|-------|
| **Board** | HW-675 |
| **Chip** | ESP32-C3 (QFN32, revision v0.4) |
| **Features** | Wi-Fi, BT 5 (LE), Single Core, 160MHz |
| **Flash** | 4MB embedded (XMC) |
| **OLED** | 128×64 SSD1306 (I2C: SCL=Pin 6, SDA=Pin 5, Address 0x3C) |
| **USB** | USB-Serial/JTAG |
| **MAC** | 08:92:72:8c:52:70 |

---

## Prerequisites

- macOS (or Linux/Windows with equivalent commands)
- Python 3 installed
- USB cable to connect the HW-675

---

## Step 1: Install Flashing & Remote Tools

```bash
pip install esptool mpremote
```

- **esptool** — Espressif's official tool for flashing firmware to ESP32 chips
- **mpremote** — Official MicroPython tool for managing boards remotely

---

## Step 2: Download MicroPython Firmware

Download the latest stable MicroPython firmware for **ESP32-C3**:

```bash
curl -L -o ESP32_GENERIC_C3-20250415-v1.25.0.bin \
  "https://micropython.org/resources/firmware/ESP32_GENERIC_C3-20250415-v1.25.0.bin"
```

> **Important:** The HW-675 uses an ESP32-**C3** chip, not a regular ESP32.  
> Always download the `ESP32_GENERIC_C3` firmware variant.  
> Check for the latest version at: https://micropython.org/download/ESP32_GENERIC_C3/

---

## Step 3: Connect the Board & Find the Serial Port

Plug the HW-675 into your Mac via USB, then find the port:

```bash
ls /dev/cu.usb*
```

Expected output:

```
/dev/cu.usbmodem101
```

> On Linux it will typically be `/dev/ttyUSB0` or `/dev/ttyACM0`.  
> On Windows it will be something like `COM3`.

---

## Step 4: Erase the Flash

Wipe the existing firmware so MicroPython can be written cleanly:

```bash
esptool --chip esp32c3 --port /dev/cu.usbmodem101 erase-flash
```

Expected output:

```
esptool v5.2.0
Connected to ESP32-C3 on /dev/cu.usbmodem101
Chip type:          ESP32-C3 (QFN32) (revision v0.4)
...
Flash memory erased successfully in 1.1 seconds.
Hard resetting via RTS pin...
```

---

## Step 5: Flash MicroPython Firmware

Write the MicroPython firmware to the board:

```bash
esptool --chip esp32c3 \
  --port /dev/cu.usbmodem101 \
  --baud 460800 \
  write-flash -z 0x0 ESP32_GENERIC_C3-20250415-v1.25.0.bin
```

Expected output:

```
Compressed 1835856 bytes to 1115756...
Writing at 0x00000000... 100%
Wrote 1835856 bytes (1115756 compressed) at 0x00000000 in 4.5 seconds
Hash of data verified.
Hard resetting via RTS pin...
```

> **Note:** For ESP32-C3, the flash offset is `0x0` (not `0x1000` like regular ESP32).

---

## Step 6: Install the SSD1306 OLED Driver

The SSD1306 driver is not bundled with MicroPython by default. Install it on the board using `mpremote`:

```bash
mpremote connect /dev/cu.usbmodem101 mip install ssd1306
```

Expected output:

```
Install ssd1306
Installing ssd1306 (latest) from https://micropython.org/pi/v2 to /lib
Installing: /lib/ssd1306.mpy
Done
```

---

## Step 7: Find the OLED I2C Pins

If you don't know which pins the OLED is wired to, run an I2C scan across common pin combinations:

```bash
mpremote connect /dev/cu.usbmodem101 exec "
from machine import Pin, SoftI2C

pin_combos = [
    (5, 4), (4, 5), (9, 8), (8, 9),
    (2, 3), (3, 2), (10, 8), (8, 10),
    (1, 0), (0, 1), (6, 5), (5, 6),
    (7, 6), (6, 7), (10, 9), (9, 10),
    (3, 1), (1, 3), (4, 3), (3, 4),
]

for scl_pin, sda_pin in pin_combos:
    try:
        i2c = SoftI2C(scl=Pin(scl_pin), sda=Pin(sda_pin), timeout=50000)
        devices = i2c.scan()
        if devices:
            print(f'SCL={scl_pin}, SDA={sda_pin} -> {[hex(d) for d in devices]}')
    except:
        pass

print('Scan complete.')
"
```

### How to read the results

- Pin combos that return **a single device** (e.g., `['0x3c']`) are the correct OLED pins
- Combos that return **dozens of addresses** are false positives (floating pins)
- `0x3c` is the standard I2C address for SSD1306 OLED displays

**Result for HW-675:**

```
SCL=6, SDA=5 -> ['0x3c']   ← ✅ This is the OLED
```

---

## Step 8: Display "Hello!" on the OLED

```bash
mpremote connect /dev/cu.usbmodem101 exec "
from machine import Pin, SoftI2C
import ssd1306

i2c = SoftI2C(scl=Pin(6), sda=Pin(5))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

oled.fill(0)
oled.text('Hello!', 35, 28, 1)
oled.show()

print('Done! Hello displayed on OLED')
"
```

### Code Breakdown

| Line | Description |
|------|-------------|
| `SoftI2C(scl=Pin(6), sda=Pin(5))` | Initialize I2C bus on the correct pins |
| `SSD1306_I2C(128, 64, i2c)` | Create OLED object (128×64 resolution) |
| `oled.fill(0)` | Clear the screen (fill with black) |
| `oled.text('Hello!', 35, 28, 1)` | Draw text at x=35, y=28 (roughly centered), color=white |
| `oled.show()` | Push the frame buffer to the display |

---

## Quick Reference

### Run any MicroPython code on the board

```bash
mpremote connect /dev/cu.usbmodem101 exec "<your code>"
```

### Open an interactive MicroPython REPL

```bash
mpremote connect /dev/cu.usbmodem101 repl
```

> Press **Ctrl+]** to exit the REPL.

### Upload a `.py` file to the board

```bash
mpremote connect /dev/cu.usbmodem101 cp my_script.py :main.py
```

> Files named `main.py` run automatically on boot.

### List files on the board

```bash
mpremote connect /dev/cu.usbmodem101 ls
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `esptool` can't find the port | Unplug and replug USB. Run `ls /dev/cu.usb*` to find the port. |
| `OSError: [Errno 116] ETIMEDOUT` on I2C | Wrong SCL/SDA pins. Re-run the pin scan from Step 7. |
| `ImportError: no module named 'ssd1306'` | Run `mpremote mip install ssd1306` (Step 6). |
| `Device not configured` error | The board may have reset. Unplug and replug, then retry. |
| Garbled OLED output | Try `oled.fill(0)` then `oled.show()` to reset the display. |

---

# HW-675 Multi-Mode Watch — Development Guide

## Overview

The HW-675 board runs a custom multi-mode watch with 5 display modes, controlled by the **BOOT button** (GPIO9). The project consists of three key files:

| File | Purpose | Runs on |
|------|---------|---------|
| `write_clock.py` | Helper script that generates `clock.py` | Your Mac (Python 3) |
| `boot.py` | Sets the RTC time on power-up | ESP32 (runs first) |
| `clock.py` / `main.py` | The watch application | ESP32 (runs after boot) |

---

## How the Files Work

### `write_clock.py` — Code Generator

This is a **host-side Python script** (runs on your Mac, not the ESP32). It exists because writing MicroPython files via shell heredocs can get corrupted by special characters. Instead, the code is stored as a Python string and written cleanly to `clock.py`:

```python
import pathlib

code = """<entire clock.py MicroPython code>"""

pathlib.Path('clock.py').write_text(code.lstrip())
print('clock.py written successfully')
```

**When to use it:**
- After making changes to the clock code inside `write_clock.py`
- If `clock.py` gets corrupted

**How to run it:**
```bash
cd /Users/long/Documents/Chunker
python3 write_clock.py
```

This regenerates `clock.py`, which you then upload to the board.

---

### `boot.py` — Time & Date Setter

MicroPython runs `boot.py` **first** on every power-up, before `main.py`. We use it to set the RTC (Real-Time Clock):

```python
from machine import RTC

rtc = RTC()
# Format: (year, month, day, weekday, hour, minute, second, subsecond)
# weekday: 0=Monday, 1=Tuesday, ..., 6=Sunday
rtc.datetime((2026, 2, 19, 3, 23, 35, 0, 0))
```

---

### `clock.py` → uploaded as `main.py`

The main watch application. MicroPython runs `main.py` automatically after `boot.py`.

#### Architecture

```
clock.py
├── Font Data (DIGITS, LETTERS)    — Block-style digit/letter patterns
├── Drawing Functions
│   ├── draw_digit()               — Renders a 3×5 block digit
│   ├── draw_letter()              — Renders a 3×3 block letter (a/p)
│   ├── draw_colon()               — Blinking colon for clock
│   └── draw_dot()                 — Dot separator for date
├── Button Handler
│   └── check_button()             — Detects BOOT button press (GPIO9)
├── Display Modes
│   ├── draw_mode_clock(blink)     — HH:MM with AM/PM
│   ├── draw_mode_date()           — MM.DD
│   ├── draw_mode_year()           — YYYY
│   ├── draw_mode_seconds(blink)   — SS with blinking dot
│   └── draw_mode_secret(frame)    — Skull & "we are pirates"
└── main()                         — Main loop
```

#### Block-Style Font System

Digits are defined as a 3-column × 5-row grid where `1` = filled block and `0` = empty:

```
Digit "0":         Digit "1":         Digit "2":
███                 █                 ███
█ █                ██                   █
█ █                 █                 ███
█ █                 █                 █
███                ███                ███
```

Each block is `BW=4` × `BH=6` pixels with `GAP=1` pixel between blocks:
- **Single digit size:** 14px wide × 34px tall
- **Four digits + colon:** ~66px wide (fits within 128px)

#### Display Modes

| Mode | BOOT Presses | Content | Update Rate |
|------|-------------|---------|-------------|
| 0 | — | `HH:MM` + blinking `:` + `a`/`p` | 1 sec |
| 1 | 1× | `MM.DD` + "date" label | 1 sec |
| 2 | 2× | `YYYY` + "year" label | 1 sec |
| 3 | 3× | `SS` + blinking dot + "sec" label | 0.5 sec |
| 4 | 4× | Skull & crossbones + "we are pirates" | 1 sec |
| — | 5× | Back to clock | — |

---

## Setting the Time and Date

### Method 1: Edit `boot.py` (Persistent across reboots)

Update the time in `boot.py`, then upload:

```bash
# Edit boot.py with the current time
# Format: (year, month, day, weekday, hour24, minute, second, 0)
# weekday: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
```

```python
# boot.py
from machine import RTC
rtc = RTC()
rtc.datetime((2026, 2, 19, 3, 23, 35, 0, 0))
#             year  mo  dy  wd  hr  mn  sc
```

Upload to the board:

```bash
mpremote connect /dev/cu.usbmodem101 cp boot.py :boot.py
mpremote connect /dev/cu.usbmodem101 reset
```

### Method 2: Set time live via REPL (Temporary, lost on reset)

```bash
mpremote connect /dev/cu.usbmodem101 exec "
from machine import RTC
rtc = RTC()
rtc.datetime((2026, 2, 20, 4, 14, 30, 0, 0))
print('RTC set to:', rtc.datetime())
"
```

### Method 3: Auto-set from your Mac's clock (Temporary)

Uses shell substitution to grab the current time from your Mac:

```bash
mpremote connect /dev/cu.usbmodem101 exec "
from machine import RTC
rtc = RTC()
rtc.datetime((2026, 2, 19, 3, $(date +%H), $(date +%M), $(date +%S), 0))
print('RTC set to:', rtc.datetime())
"
```

> **Note:** You still need to manually set the year, month, day, and weekday. Only HH:MM:SS is auto-filled.

---

## The RTC Reset Problem

### The Problem

The ESP32-C3 has **no battery-backed RTC**. This means:

- ❌ Time resets to `2000-01-01 00:00:00` on every **power loss**
- ❌ Time resets on every **hard reset** (reset button or `mpremote reset`)
- ✅ Time survives **soft resets** (`machine.soft_reset()`)
- ✅ Time survives **BOOT button presses** (it's just a GPIO, not a reset)

### How We Handle It: `boot.py`

We use `boot.py` to set the time on every boot. MicroPython's boot sequence is:

```
Power On → boot.py (sets RTC) → main.py (starts clock)
```

**Limitation:** The time in `boot.py` is static — it's always the time you last saved it. The clock will start from that time on every reboot, so it will drift from reality over time.

### Better Solution: Wi-Fi NTP Sync (Optional)

For accurate time that survives reboots, replace `boot.py` with NTP (Network Time Protocol) sync:

```python
# boot.py with NTP sync
import network
import ntptime
from machine import RTC

# Connect to Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('YOUR_WIFI_NAME', 'YOUR_WIFI_PASSWORD')

# Wait for connection (max 10 seconds)
import time
for _ in range(20):
    if wlan.isconnected():
        break
    time.sleep(0.5)

if wlan.isconnected():
    # Sync time from NTP server (UTC)
    ntptime.settime()
    
    # Adjust for your timezone (e.g., UTC-5 for EST)
    rtc = RTC()
    t = list(rtc.datetime())
    t[4] += -5  # your UTC offset
    if t[4] < 0:
        t[4] += 24
        t[2] -= 1
    rtc.datetime(tuple(t))
    
    # Disconnect Wi-Fi to save power
    wlan.active(False)
```

This fetches the exact time from the internet every time the board powers on.

---

## Complete Upload Workflow

### First-time setup

```bash
# 1. Install tools
pip install esptool mpremote

# 2. Flash MicroPython (see Steps 2-5 in the setup guide above)

# 3. Install the OLED driver
mpremote connect /dev/cu.usbmodem101 mip install ssd1306

# 4. Generate clock.py from the template
python3 write_clock.py

# 5. Upload both files
mpremote connect /dev/cu.usbmodem101 cp boot.py :boot.py
mpremote connect /dev/cu.usbmodem101 cp clock.py :main.py

# 6. Reset to start
mpremote connect /dev/cu.usbmodem101 reset
```

### After making changes

```bash
# If you edited write_clock.py:
python3 write_clock.py

# Upload and restart:
mpremote connect /dev/cu.usbmodem101 cp clock.py :main.py
mpremote connect /dev/cu.usbmodem101 reset

# If you changed the time in boot.py:
mpremote connect /dev/cu.usbmodem101 cp boot.py :boot.py
mpremote connect /dev/cu.usbmodem101 reset
```

### Files on the ESP32

```bash
# List files on the board
mpremote connect /dev/cu.usbmodem101 ls

# Expected:
#   boot.py    — RTC time setter
#   main.py    — Watch application (copy of clock.py)
#   lib/
#     ssd1306.mpy  — OLED display driver
```

---

## Hardware Pin Reference

| Pin | Function |
|-----|----------|
| GPIO5 | I2C SDA (OLED display) |
| GPIO6 | I2C SCL (OLED display) |
| GPIO9 | BOOT button (active low, internal pull-up) |
| RESET | Reset button (hardware reset, not programmable) |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Clock shows wrong time | Update `boot.py` with the correct time and re-upload |
| Time resets after unplug | This is normal — ESP32-C3 has no battery RTC. Use `boot.py` or NTP sync |
| BOOT button doesn't work | Make sure the clock script is running (`main.py` on board). The button only works while the watch app is active |
| `write_clock.py` errors | Check you're running it with `python3` on your Mac, not on the ESP32 |
| Can't upload files | Run `mpremote connect /dev/cu.usbmodem101 reset` first, wait 2 seconds, then try uploading |
| `Permission denied` on clock.py | Run `xattr -c clock.py` then retry, or regenerate with `python3 write_clock.py` |
