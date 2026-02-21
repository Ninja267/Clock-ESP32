# Clock Advance — Documentation

**File:** `clock_advance.py`
**Platform:** MicroPython on ESP32-C3 with SSD1306 128×64 OLED
**Hardware:** OLED on I2C (SCL=GPIO6, SDA=GPIO5), Boot button on GPIO9

---

## Overview

`clock_advance.py` is an advanced clock application that displays time, date, year, and seconds using custom pixel-art digits on an SSD1306 OLED. It extends the basic `clock.py` with three major features:

1. **Countdown Timer** — with hourglass icon, pause/resume, background countdown, and Mario timeout alert
2. **Chronograph (Stopwatch)** — with centisecond precision (MM:SS.cc), background running support
3. **Set Time Mode** — adjust hour, minute, second, month, day, and year with auto-repeat support

---

## Display Modes

The clock cycles through **6 modes** via single button presses:

| # | Mode | Display | Top Label |
|---|------|---------|-----------|
| 0 | **Clock** | 12-hour time `HH:MM` with blinking colon, AM/PM indicator | `a` or `p` |
| 1 | **Date** | `MM.DD` with dot separator | `date` |
| 2 | **Year** | `YYYY` four-digit year | `year` |
| 3 | **Seconds** | `SS` with blinking dot | `sec` |
| 4 | **Timer** | Countdown timer with hourglass icon | `timer` / `set` / `play` / `pause` |
| 5 | **Chrono** | Stopwatch `MM:SS.cc` with stopwatch icon | `chrono` / `run` / `stop` |

---

## Button Gestures

The boot button (GPIO9) supports four gesture types:

| Gesture | How to perform | Detection |
|---------|---------------|-----------|
| **Single press** | Quick tap & release | Fires after 350ms gap with no second tap |
| **Double press** | Two quick taps | Second tap within 350ms of first release |
| **Triple press** | Three quick taps | Third tap within 350ms of second release |
| **Long press** | Hold ≥ 800ms | Fires while button is still held |

### Timing Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| `LONG_MS` | 800ms | Threshold for long press detection |
| `DBLGAP_MS` | 350ms | Maximum gap between taps for multi-press |
| `REPEAT_MS` | 1000ms | Auto-repeat interval in set-time mode |

---

## Normal Mode Navigation

In normal display modes (not in set-time, timer, or chrono sub-states):

| Action | Result |
|--------|--------|
| **Single press** | Cycle to next mode (0 → 1 → 2 → 3 → 4 → 5 → 0) |
| **Long press** (on Clock mode only) | Enter **Set Time Mode** |

---

## Set Time Mode

Entered by **long pressing** the boot button while on the **Clock** screen.

### Field Order

| # | Field | Range | Display |
|---|-------|-------|---------|
| 0 | **Hour** | 0–23 (shown as 12h) | `HH:MM` with hour blinking |
| 1 | **Minute** | 0–59 | `HH:MM` with minute blinking |
| 2 | **Second** | 0–59 | `SS` blinking |
| 3 | **Month** | 1–12 | `MM.DD` with month blinking |
| 4 | **Day** | 1–31 | `MM.DD` with day blinking |
| 5 | **Year** | 2020–2099 | `YYYY` blinking |

### Controls in Set Time Mode

| Action | Result |
|--------|--------|
| **Single press** | Increase current field by 1 (wraps around). For seconds: resets to `00` |
| **Press & hold** | Auto-repeat: increases by 1 every 1000ms while held. For seconds: resets to `00` |
| **Double press** | Move to next field. After Year → saves & exits |
| **Triple press** | Save all values & exit set-time mode immediately |

### Display in Set Time Mode

- Top-left shows `set`
- Top-right shows the current field name (`hour`, `min`, `sec`, `month`, `day`, `year`)
- The active field **blinks** (toggles visibility every 500ms)
- Non-active fields on the same screen remain solid

---

## Timer Mode

The timer is **mode 4** in the mode cycle. It has three sub-states:

### Timer Sub-states

#### 1. VIEW (`T_VIEW`) — Landing page
- **If a timer is counting in background:** Shows the live countdown with blinking colon
- **If no timer is active:** Shows "long press / to set timer" prompt
- **Single press:** Cycle to next mode
- **Long press:** Enter Timer Set mode (starts at `00:30`)
- **Triple press:** Jump back to Clock mode

#### 2. SET (`T_SET`) — Setting the timer value
- **Display:** Hourglass icon + `set` label + blinking `MM:SS` value
- **Single press:** Add 30 seconds (wraps from `90:00` → `00:30`)
- **Double press:** Subtract 30 seconds (wraps from `00:30` → `90:00`)
- **Long press:** Start countdown → enter PLAY
- **Triple press:** Exit to Clock mode

**Timer range:** minimum `00:30` (30s), maximum `90:00` (5400s), always in `MM:SS` format.

#### 3. PLAY (`T_PLAY`) — Active timer control
The PLAY sub-state supports **running** and **paused** states:

**When running:**
| Action | Result |
|--------|--------|
| **Single press** | Pause the countdown |
| **Long press** | Stop & reset to the original set time (enters paused state) |
| **Triple press** | Exit to Clock mode (timer keeps counting in background) |

**When paused:**
| Action | Result |
|--------|--------|
| **Single press** | Resume countdown from where it paused |
| **Long press** | Enter SET mode (keeps the last set time for adjustment) |
| **Triple press** | Exit to Clock mode |

### Timeout Alert

When the countdown reaches zero (from **any** mode):

- **Display:** Mario pixel-art character + bouncing "time / out!" text + flashing border
- **Any button press:** Dismiss alert, return to current screen

The timeout alert takes priority over all other displays.

---

## Chronograph Mode

The chronograph is **mode 5** in the mode cycle. It displays elapsed time as `MM:SS.cc` (centisecond precision) using half-size pixel digits. It has three sub-states:

### Chronograph Sub-states

#### 1. IDLE (`C_IDLE`) — Preview / landing page
- **Display:** Stopwatch icon + `chrono` label + elapsed time (or `00:00.00`)
- **Single press:** Cycle to next mode
- **Long press:** Start chronograph (or re-enter if running in background)

#### 2. RUNNING (`C_RUNNING`) — Stopwatch counting
- **Display:** Stopwatch icon + `run` label + live `MM:SS.cc` (refreshes at ~10 FPS)
- **Single press:** Stop the chronograph
- **Triple press:** Exit to Clock mode (chronograph keeps running in background)

#### 3. STOPPED (`C_STOPPED`) — Stopwatch paused
- **Display:** Stopwatch icon + `stop` label + frozen `MM:SS.cc`
- **Single press:** Resume chronograph
- **Long press:** Reset to `00:00.00` (stays in chrono mode, ready to start again)
- **Triple press:** Exit to Clock mode

### Background Running

Both **timer** and **chronograph** can run in the background:
- **Timer:** Triple-press exits to clock; countdown continues; timeout alert fires from any mode
- **Chronograph:** Triple-press exits to clock; stopwatch keeps counting; re-enter via long press on IDLE

---

## Pixel Art & Icons

### Custom Digit Font
- Each digit is rendered as a 3×5 grid of blocks
- Normal size: block 4×6 pixels with 1px gap (clock, timer, set-time)
- Half size: block 2×3 pixels with 2px gap (chronograph)
- Supports digits 0–9

### AM/PM Letters
- Rendered as 3×3 grid with 2×3 pixel blocks
- Supports `a` (AM) and `p` (PM)

### Icons

| Icon | Size | Used in |
|------|------|---------|
| **Hourglass** | 9×11 px | Timer mode (top-left corner) |
| **Stopwatch** | 10×12 px | Chronograph mode (top-left corner) |
| **Mario** | ~11×12 px | Timeout alert |

---

## Architecture

### Main Loop

The main loop runs with adaptive polling:
- **30ms** polling interval (normal)
- **10ms** polling when chronograph is running on screen

1. **Poll button** — detect gestures via state machine
2. **Handle event** — dispatch to current mode/sub-state handler
3. **Check timer** — trigger timeout if countdown expired
4. **Check auto-repeat** — fire repeat increments if button still held in set-time mode
5. **Draw frame** — refresh display every 500ms (or 100ms when chrono is running)

### State Machine (Button Detection)

The button detector uses a 7-state FSM:

```
idle → down1 → gap1 → down2 → gap2 → down3
                 ↓        ↓        ↓        ↓
              single   (long)   double    triple
```

- `wait_rel` — waiting for button release after a long press

### Global State Variables

| Variable | Type | Purpose |
|----------|------|---------|
| `mode` | int (0–5) | Current display mode |
| `setting_time` | bool | Whether set-time overlay is active |
| `set_field` | int (0–5) | Which field is being edited |
| `set_vals` | list[6] | Editable values: [hour, min, sec, month, day, year] |
| `set_repeat` | bool | Auto-repeat active flag |
| `set_rep_next` | int | Next auto-repeat fire time (ticks_ms) |
| `timer_sub` | int (0–2) | Timer sub-state (VIEW/SET/PLAY) |
| `timer_set_s` | int | Timer duration in seconds |
| `timer_end_t` | int | Timer deadline (ticks_ms) |
| `timer_running` | bool | Whether countdown is active |
| `timer_paused` | bool | Whether timer is paused |
| `timer_pause_rem` | int | Remaining seconds when paused |
| `timeout_show` | bool | Whether timeout alert is displayed |
| `chrono_sub` | int (0–2) | Chronograph sub-state (IDLE/STOPPED/RUNNING) |
| `chrono_running` | bool | Whether chronograph is counting |
| `chrono_start` | int | Chronograph start time (ticks_ms) |
| `chrono_elapsed` | int | Accumulated elapsed ms when stopped |

---

## Deployment

### Copy and run directly:
```bash
mpremote connect /dev/cu.usbmodem2101 cp clock_advance.py :clock_advance.py
mpremote connect /dev/cu.usbmodem2101 run clock_advance.py
```

### Set as auto-start (rename to main.py on board):
```bash
mpremote connect /dev/cu.usbmodem2101 cp clock_advance.py :main.py
mpremote connect /dev/cu.usbmodem2101 reset
```

### Prerequisites
- `boot.py` should be loaded first to sync time via NTP (Wi-Fi)
- `ssd1306` driver must be installed on the board

---

## Dependencies

| Module | Source | Purpose |
|--------|--------|---------|
| `machine` | MicroPython built-in | GPIO, I2C, RTC |
| `ssd1306` | MicroPython library | OLED display driver |
| `time` | MicroPython built-in | Timing and delays |
