# ⏰ Clock-ESP32

An advanced clock application for **ESP32-C3** with **SSD1306 128×64 OLED**, built with MicroPython.

Features custom pixel-art digits, a countdown timer with Mario timeout alert, a centisecond chronograph, and a full time-setting interface — all controlled with a single boot button using single, double, triple, and long press gestures.

---

## ✨ Features

| Mode | Description |
|------|-------------|
| 🕐 **Clock** | 12-hour `HH:MM` with blinking colon and AM/PM |
| 📅 **Date** | `MM.DD` with dot separator |
| 📆 **Year** | `YYYY` four-digit year |
| ⏱️ **Seconds** | `SS` live seconds with blinking dot |
| ⏳ **Timer** | Countdown timer with pause/resume, background counting, and Mario timeout alert |
| 🏁 **Chrono** | Stopwatch with `MM:SS.cc` centisecond precision |

### Additional Capabilities

- **Set Time** — long press on clock mode to adjust hour, minute, second, month, day, and year
- **Background running** — timer and chronograph keep running when you switch to other modes
- **NTP sync** — automatic time sync via Wi-Fi on boot

---

## 🎮 Button Controls

Everything is controlled with the **boot button** (GPIO9):

| Gesture | How |
|---------|-----|
| **Single press** | Quick tap |
| **Double press** | Two quick taps |
| **Triple press** | Three quick taps |
| **Long press** | Hold ≥ 800ms |

### Quick Reference

| Context | Single | Double | Long | Triple |
|---------|--------|--------|------|--------|
| **Normal modes** | Next mode | — | Set time (clock only) | — |
| **Set time** | +1 value | Next field | Auto-repeat +1 | Save & exit |
| **Timer view** | Next mode | — | Enter set | Back to clock |
| **Timer set** | +30s | −30s | Start countdown | Back to clock |
| **Timer play** | Pause/Resume | — | Stop+Reset / Enter set | Back to clock |
| **Chrono idle** | Next mode | — | Start / Re-enter | — |
| **Chrono running** | Stop | — | — | Back to clock (bg) |
| **Chrono stopped** | Resume | — | Reset | Back to clock |

---

## 🔧 Hardware

| Component | Detail |
|-----------|--------|
| **Board** | HW-675 (ESP32-C3) |
| **Display** | SSD1306 128×64 OLED (I2C: SCL=GPIO6, SDA=GPIO5) |
| **Button** | Boot button on GPIO9 |
| **Firmware** | MicroPython for ESP32-C3 |

> See [docs/HW675_MicroPython_Setup.md](docs/HW675_MicroPython_Setup.md) for full flashing and setup instructions.

---

## 🚀 Getting Started

### 1. Install tools

```bash
pip install esptool mpremote
```

### 2. Create your config

Create a `config.py` file in the project root with your Wi-Fi credentials:

```python
WIFI_SSID     = 'your-ssid'
WIFI_PASSWORD = 'your-password'
UTC_OFFSET    = 1  # your timezone offset from UTC
```

> This file is gitignored to protect your credentials.

### 3. Deploy to board

```bash
# Copy config, boot, and clock to the board
mpremote connect /dev/cu.usbmodem2101 cp config.py :config.py
mpremote connect /dev/cu.usbmodem2101 cp boot.py :boot.py
mpremote connect /dev/cu.usbmodem2101 cp clock_advance.py :main.py

# Reset to start
mpremote connect /dev/cu.usbmodem2101 reset
```

### 4. Run without installing

```bash
mpremote connect /dev/cu.usbmodem2101 run clock_advance.py
```

---

## 📁 Project Structure

```
Clock-ESP32/
├── boot.py              # Wi-Fi + NTP time sync (runs on startup)
├── clock_advance.py     # Main clock application
├── config.py            # Wi-Fi credentials (gitignored, create your own)
├── docs/
│   ├── clock_advance_doc.md      # Detailed feature documentation
│   └── HW675_MicroPython_Setup.md # Hardware setup & flashing guide
└── proto/
    ├── chrono_proto.py   # Chronograph refresh rate test
    ├── chunker.ipynb     # Jupyter exploration notebook
    ├── clock.py          # Original basic clock (5 modes)
    └── clock_simple.py   # Earliest clock-only prototype
```

---

## 📖 Documentation

- **[Feature Documentation](docs/clock_advance_doc.md)** — detailed description of all modes, controls, state machines, and architecture
- **[Hardware Setup Guide](docs/HW675_MicroPython_Setup.md)** — flashing MicroPython firmware, installing drivers, board pinout

---

## 📜 License

MIT
