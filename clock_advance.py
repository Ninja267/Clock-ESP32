from machine import Pin, SoftI2C, RTC
import ssd1306
import time

# ── Hardware ─────────────────────────────────────────
i2c = SoftI2C(scl=Pin(6), sda=Pin(5))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
rtc = RTC()
btn = Pin(9, Pin.IN, Pin.PULL_UP)

# ── Mode Constants ───────────────────────────────────
MODE_CLOCK  = 0
MODE_DATE   = 1
MODE_YEAR   = 2
MODE_SEC    = 3
MODE_TIMER  = 4
MODE_CHRONO = 5
NUM_MODES   = 6

# ── Timer Sub-states ─────────────────────────────────
T_VIEW = 0   # passive view / landing page
T_SET  = 1   # setting timer value (blinking)
T_PLAY = 2   # active play (running / paused)

# ── State Variables ──────────────────────────────────
mode          = MODE_CLOCK
timer_sub       = T_VIEW
timer_set_s     = 30       # seconds chosen in set mode
timer_end_t     = 0        # ticks_ms deadline
timer_running   = False    # countdown active (even in bg)
timer_paused    = False    # paused inside T_PLAY
timer_pause_rem = 0        # remaining seconds when paused
timeout_show    = False    # "time out" overlay visible

# ── Set-Time State ───────────────────────────────────
setting_time = False
set_field    = 0          # 0=hour, 1=min, 2=sec, 3=month, 4=day, 5=year
set_vals     = [0, 0, 0, 0, 0, 0]  # [h24, m, s, mo, day, yr]
set_repeat   = False     # auto-repeat active (button held)
set_rep_next = 0         # ticks_ms of next repeat fire
REPEAT_MS    = 1000      # interval between repeats

# ── Chronograph State ────────────────────────────────
C_IDLE    = 0   # not entered yet (shows preview)
C_STOPPED = 1   # inside chrono, stopped
C_RUNNING = 2   # inside chrono, counting

chrono_sub     = C_IDLE
chrono_running = False   # background running flag
chrono_start   = 0       # ticks_ms of start
chrono_elapsed = 0       # accumulated ms when stopped

# ── Button Detection ─────────────────────────────────
LONG_MS   = 800
DBLGAP_MS = 350

btn_prev = 1
_bs      = 'idle'
_bd      = 0
_bu      = 0
_blong   = False


def poll_button():
    """Return button event: None | 'single' | 'double' | 'triple' | 'long'"""
    global btn_prev, _bs, _bd, _bu, _blong
    v   = btn.value()
    now = time.ticks_ms()
    evt = None

    if _bs == 'idle':
        if btn_prev == 1 and v == 0:
            _bs    = 'down1'
            _bd    = now
            _blong = False

    elif _bs == 'down1':
        if v == 0:
            if not _blong and time.ticks_diff(now, _bd) >= LONG_MS:
                evt    = 'long'
                _blong = True
                _bs    = 'wait_rel'
        else:
            _bu = now
            _bs = 'gap1'

    elif _bs == 'gap1':
        if btn_prev == 1 and v == 0:
            _bs = 'down2'
            _bd = now
        elif time.ticks_diff(now, _bu) >= DBLGAP_MS:
            evt = 'single'
            _bs = 'idle'

    elif _bs == 'down2':
        if v == 1:
            _bu = now
            _bs = 'gap2'
        elif time.ticks_diff(now, _bd) >= LONG_MS:
            evt    = 'long'
            _blong = True
            _bs    = 'wait_rel'

    elif _bs == 'gap2':
        if btn_prev == 1 and v == 0:
            _bs = 'down3'
            _bd = now
        elif time.ticks_diff(now, _bu) >= DBLGAP_MS:
            evt = 'double'
            _bs = 'idle'

    elif _bs == 'down3':
        if v == 1:
            evt = 'triple'
            _bs = 'idle'
        elif time.ticks_diff(now, _bd) >= LONG_MS:
            evt    = 'long'
            _blong = True
            _bs    = 'wait_rel'

    elif _bs == 'wait_rel':
        if v == 1:
            _bs = 'idle'

    btn_prev = v
    return evt


# ── Pixel Font Data ──────────────────────────────────
DIGITS = {
    0: [1,1,1, 1,0,1, 1,0,1, 1,0,1, 1,1,1],
    1: [0,1,0, 1,1,0, 0,1,0, 0,1,0, 1,1,1],
    2: [1,1,1, 0,0,1, 1,1,1, 1,0,0, 1,1,1],
    3: [1,1,1, 0,0,1, 1,1,1, 0,0,1, 1,1,1],
    4: [1,0,1, 1,0,1, 1,1,1, 0,0,1, 0,0,1],
    5: [1,1,1, 1,0,0, 1,1,1, 0,0,1, 1,1,1],
    6: [1,1,1, 1,0,0, 1,1,1, 1,0,1, 1,1,1],
    7: [1,1,1, 0,0,1, 0,0,1, 0,0,1, 0,0,1],
    8: [1,1,1, 1,0,1, 1,1,1, 1,0,1, 1,1,1],
    9: [1,1,1, 1,0,1, 1,1,1, 0,0,1, 1,1,1],
}

LETTERS = {
    'a': [1,1,1, 1,0,1, 1,1,1],
    'p': [1,1,0, 1,1,0, 1,0,0],
}

BW  = 4
BH  = 6
GAP = 1


# ── Drawing Primitives ──────────────────────────────
def draw_digit(d, x, y, bw=BW, bh=BH, gap=GAP):
    pat = DIGITS[d]
    for r in range(5):
        for c in range(3):
            oled.fill_rect(x + c * (bw + gap), y + r * (bh + gap),
                           bw, bh, pat[r * 3 + c])


def draw_letter(ch, x, y):
    pat = LETTERS[ch]
    bw, bh, gap = 2, 3, 1
    for r in range(3):
        for c in range(3):
            oled.fill_rect(x + c * (bw + gap), y + r * (bh + gap),
                           bw, bh, pat[r * 3 + c])


def draw_colon(x, y, on, bh=BH, gap=GAP):
    v  = 1 if on else 0
    dh = 5 * (bh + gap) - gap
    oled.fill_rect(x, y + dh // 3, 2, 2, v)
    oled.fill_rect(x, y + dh * 2 // 3, 2, 2, v)


def draw_dot(x, y, bh=BH, gap=GAP):
    dh = 5 * (bh + gap) - gap
    oled.fill_rect(x, y + dh - 3, 3, 3, 1)


# ── Icons ────────────────────────────────────────────
def draw_hourglass(x, y):
    """9 x 11 sand-clock icon"""
    oled.hline(x, y, 9, 1)
    oled.hline(x, y + 10, 9, 1)
    oled.line(x,     y + 1, x + 4, y + 5, 1)
    oled.line(x + 8, y + 1, x + 4, y + 5, 1)
    oled.line(x,     y + 9, x + 4, y + 5, 1)
    oled.line(x + 8, y + 9, x + 4, y + 5, 1)
    # sand grains
    oled.fill_rect(x + 2, y + 1, 5, 2, 1)
    oled.fill_rect(x + 2, y + 8, 5, 2, 1)


def draw_mario(cx, cy):
    """~11 x 12 Mario character"""
    # Cap
    oled.fill_rect(cx + 3, cy, 5, 1, 1)
    oled.fill_rect(cx + 2, cy + 1, 7, 2, 1)
    # Face
    oled.fill_rect(cx + 1, cy + 3, 9, 4, 1)
    oled.fill_rect(cx + 2, cy + 3, 2, 2, 0)    # L eye
    oled.fill_rect(cx + 7, cy + 3, 2, 2, 0)    # R eye
    oled.fill_rect(cx + 4, cy + 5, 3, 1, 0)    # mouth
    # Body + arms
    oled.fill_rect(cx + 2, cy + 7, 7, 3, 1)
    oled.fill_rect(cx + 4, cy + 8, 3, 1, 0)    # overall
    oled.fill_rect(cx,     cy + 7, 2, 2, 1)    # L arm
    oled.fill_rect(cx + 9, cy + 7, 2, 2, 1)    # R arm
    # Legs
    oled.fill_rect(cx + 2, cy + 10, 3, 2, 1)
    oled.fill_rect(cx + 6, cy + 10, 3, 2, 1)


# ── Original Mode Draws ─────────────────────────────
def draw_mode_clock(blink):
    dt = rtc.datetime()
    h24, m = dt[4], dt[5]
    ampm = 'a' if h24 < 12 else 'p'
    h12  = h24 % 12 or 12
    dw = 3 * (BW + GAP) - GAP
    sp = 2
    cw = 2
    tw = dw * 4 + cw + sp * 4
    sx = (128 - tw) // 2
    dh = 5 * (BH + GAP) - GAP
    y  = (64 - dh) // 2 + 10
    cx = sx
    if h12 >= 10:
        draw_digit(h12 // 10, cx, y)
    cx += dw + sp
    draw_digit(h12 % 10, cx, y)
    cx += dw + sp
    draw_colon(cx, y, blink)
    cx += cw + sp
    draw_digit(m // 10, cx, y)
    cx += dw + sp
    draw_digit(m % 10, cx, y)
    draw_letter(ampm, sx, y - 13)


def draw_mode_date():
    dt = rtc.datetime()
    mo, day = dt[1], dt[2]
    dw = 3 * (BW + GAP) - GAP
    sp = 2
    dotw = 5
    tw = dw * 4 + dotw + sp * 4
    sx = (128 - tw) // 2 - 1
    dh = 5 * (BH + GAP) - GAP
    y  = (64 - dh) // 2 + 8
    cx = sx
    draw_digit(mo // 10, cx, y);   cx += dw + sp
    draw_digit(mo % 10, cx, y);    cx += dw + sp
    draw_dot(cx, y);               cx += dotw + sp
    draw_digit(day // 10, cx, y);  cx += dw + sp
    draw_digit(day % 10, cx, y)
    oled.text('date', 0, 0, 1)


def draw_mode_year():
    yr = rtc.datetime()[0]
    dw = 3 * (BW + GAP) - GAP
    sp = 2
    tw = dw * 4 + sp * 3
    sx = (128 - tw) // 2
    dh = 5 * (BH + GAP) - GAP
    y  = (64 - dh) // 2 + 8
    draw_digit(yr // 1000,       sx,              y)
    draw_digit((yr // 100) % 10, sx + (dw + sp),    y)
    draw_digit((yr // 10) % 10,  sx + (dw + sp) * 2, y)
    draw_digit(yr % 10,          sx + (dw + sp) * 3, y)
    oled.text('year', 0, 0, 1)


def draw_mode_seconds(blink):
    s  = rtc.datetime()[6]
    dw = 3 * (BW + GAP) - GAP
    sp = 2
    tw = dw * 2 + sp
    sx = (128 - tw) // 2
    dh = 5 * (BH + GAP) - GAP
    y  = (64 - dh) // 2 + 10
    draw_digit(s // 10, sx, y)
    draw_digit(s % 10, sx + dw + sp, y)
    if blink:
        oled.fill_rect(sx + tw + 3, y + dh - 3, 2, 2, 1)
    oled.text('sec', 0, 0, 1)


# ── Timer Helpers ────────────────────────────────────
def _get_remaining():
    """Seconds left on running timer."""
    if not timer_running:
        return 0
    ms = time.ticks_diff(timer_end_t, time.ticks_ms())
    return max(0, ms // 1000)


def _draw_time_digits(secs, show_digits, colon_on=True):
    """Draw time value using pixel digits.  show_digits=False hides for blink."""
    dw = 3 * (BW + GAP) - GAP
    sp = 2
    cw = 2
    dh = 5 * (BH + GAP) - GAP
    y  = (64 - dh) // 2 + 10

    mm = secs // 60
    ss = secs % 60
    tw = dw * 4 + cw + sp * 4
    sx = (128 - tw) // 2
    if show_digits:
        cx = sx
        draw_digit(mm // 10, cx, y);  cx += dw + sp
        draw_digit(mm % 10,  cx, y);  cx += dw + sp
        draw_colon(cx, y, colon_on);  cx += cw + sp
        draw_digit(ss // 10, cx, y);  cx += dw + sp
        draw_digit(ss % 10,  cx, y)


# ── Set-Time Helpers ─────────────────────────────────
def _enter_set_time():
    global setting_time, set_field, set_vals
    dt = rtc.datetime()
    set_vals[0] = dt[4]    # hour
    set_vals[1] = dt[5]    # minute
    set_vals[2] = dt[6]    # second
    set_vals[3] = dt[1]    # month
    set_vals[4] = dt[2]    # day
    set_vals[5] = dt[0]    # year
    set_field    = 0
    setting_time = True


def _apply_set_time():
    global setting_time
    dt  = rtc.datetime()
    rtc.datetime((set_vals[5], set_vals[3], set_vals[4],
                  dt[3], set_vals[0], set_vals[1], set_vals[2], 0))


def _adjust_field(delta):
    if set_field == 0:      # hour 0-23
        set_vals[0] = (set_vals[0] + delta) % 24
    elif set_field == 1:    # minute 0-59
        set_vals[1] = (set_vals[1] + delta) % 60
    elif set_field == 2:    # second – any press resets to 0
        set_vals[2] = 0
    elif set_field == 3:    # month 1-12
        set_vals[3] = (set_vals[3] - 1 + delta) % 12 + 1
    elif set_field == 4:    # day 1-31
        set_vals[4] = (set_vals[4] - 1 + delta) % 31 + 1
    elif set_field == 5:    # year
        set_vals[5] += delta
        if set_vals[5] > 2099:
            set_vals[5] = 2020
        elif set_vals[5] < 2020:
            set_vals[5] = 2099


def draw_set_time(blink):
    """Draw time-setting screen with blinking active field."""
    dw = 3 * (BW + GAP) - GAP
    sp = 2
    cw = 2
    dh = 5 * (BH + GAP) - GAP

    if set_field <= 1:  # ---- hour / minute ----
        h24 = set_vals[0]
        m   = set_vals[1]
        ampm = 'a' if h24 < 12 else 'p'
        h12  = h24 % 12 or 12
        tw = dw * 4 + cw + sp * 4
        sx = (128 - tw) // 2
        y  = (64 - dh) // 2 + 10
        show_hr = blink or set_field != 0
        show_mn = blink or set_field != 1
        cx = sx
        if show_hr:
            if h12 >= 10:
                draw_digit(h12 // 10, cx, y)
            draw_digit(h12 % 10, cx + dw + sp, y)
        cx += (dw + sp) * 2
        draw_colon(cx, y, True)
        cx += cw + sp
        if show_mn:
            draw_digit(m // 10, cx, y)
            draw_digit(m % 10, cx + dw + sp, y)
        draw_letter(ampm, sx, y - 13)
        lbl = 'hour' if set_field == 0 else 'min'
        oled.text('set', 0, 0, 1)
        oled.text(lbl, 128 - len(lbl) * 8, 0, 1)

    elif set_field == 2:  # ---- second ----
        s = set_vals[2]
        tw = dw * 2 + sp
        sx = (128 - tw) // 2
        y  = (64 - dh) // 2 + 10
        if blink:
            draw_digit(s // 10, sx, y)
            draw_digit(s % 10, sx + dw + sp, y)
        oled.text('set', 0, 0, 1)
        oled.text('sec', 104, 0, 1)

    elif set_field <= 4:  # ---- month / day ----
        mo  = set_vals[3]
        day = set_vals[4]
        dotw = 5
        tw = dw * 4 + dotw + sp * 4
        sx = (128 - tw) // 2 - 1
        y  = (64 - dh) // 2 + 8
        show_mo  = blink or set_field != 3
        show_day = blink or set_field != 4
        cx = sx
        if show_mo:
            draw_digit(mo // 10, cx, y)
            draw_digit(mo % 10, cx + dw + sp, y)
        cx += (dw + sp) * 2
        draw_dot(cx, y)
        cx += dotw + sp
        if show_day:
            draw_digit(day // 10, cx, y)
            draw_digit(day % 10, cx + dw + sp, y)
        lbl = 'month' if set_field == 3 else 'day'
        oled.text('set', 0, 0, 1)
        oled.text(lbl, 128 - len(lbl) * 8, 0, 1)

    else:  # ---- year ----
        yr = set_vals[5]
        tw = dw * 4 + sp * 3
        sx = (128 - tw) // 2
        y  = (64 - dh) // 2 + 8
        if blink:
            draw_digit(yr // 1000,       sx,                y)
            draw_digit((yr // 100) % 10, sx + (dw + sp),    y)
            draw_digit((yr // 10) % 10,  sx + (dw + sp) * 2, y)
            draw_digit(yr % 10,          sx + (dw + sp) * 3, y)
        oled.text('set', 0, 0, 1)
        oled.text('year', 96, 0, 1)


# ── Chronograph Helpers ──────────────────────────────
def draw_stopwatch(x, y):
    """10 x 12 stopwatch icon"""
    # top button
    oled.fill_rect(x + 4, y, 3, 2, 1)
    # circle body
    oled.hline(x + 2, y + 2, 7, 1)
    oled.hline(x + 2, y + 11, 7, 1)
    oled.vline(x, y + 4, 6, 1)
    oled.vline(x + 10, y + 4, 6, 1)
    oled.pixel(x + 1, y + 3, 1)
    oled.pixel(x + 9, y + 3, 1)
    oled.pixel(x + 1, y + 10, 1)
    oled.pixel(x + 9, y + 10, 1)
    # hand
    oled.line(x + 5, y + 7, x + 5, y + 3, 1)
    oled.line(x + 5, y + 7, x + 8, y + 5, 1)


def _chrono_ms():
    """Current elapsed ms of chronograph."""
    if chrono_running:
        return chrono_elapsed + time.ticks_diff(time.ticks_ms(), chrono_start)
    return chrono_elapsed


def draw_mode_chrono():
    """Draw chronograph screen: MM:SS.cc at half size"""
    draw_stopwatch(2, 2)
    ms = _chrono_ms()
    total_s = ms // 1000
    cs = (ms % 1000) // 10   # centiseconds
    mm = total_s // 60
    ss = total_s % 60

    # Slightly larger digits: bw=2, bh=3, gap=2
    bw, bh, gap = 2, 3, 2
    dw = 3 * (bw + gap) - gap    # 10
    sp = 1
    cw = 2
    dh = 5 * (bh + gap) - gap    # 23

    # MM:SS
    tw_main = dw * 4 + cw + sp * 4 + 2  # +2 for dot gap
    # .cc
    tw_cs = 2 + dw * 2 + sp             # dot + 2 digits
    tw = tw_main + tw_cs
    sx = (128 - tw) // 2
    y  = (64 - dh) // 2 + 9

    cx = sx
    draw_digit(mm // 10, cx, y, bw, bh, gap);  cx += dw + sp
    draw_digit(mm % 10,  cx, y, bw, bh, gap);  cx += dw + sp
    draw_colon(cx, y, True, bh, gap);           cx += cw + sp
    draw_digit(ss // 10, cx, y, bw, bh, gap);  cx += dw + sp
    draw_digit(ss % 10,  cx, y, bw, bh, gap);  cx += dw + sp

    # dot separator
    oled.fill_rect(cx, y + dh - 2, 2, 2, 1);   cx += 2 + sp
    # centisecond digits
    draw_digit(cs // 10, cx, y, bw, bh, gap);  cx += dw + sp
    draw_digit(cs % 10,  cx, y, bw, bh, gap)

    # Status label
    if chrono_sub == C_IDLE:
        oled.text('chrono', 14, 2, 1)
    elif chrono_sub == C_STOPPED:
        oled.text('stop', 14, 2, 1)
    elif chrono_sub == C_RUNNING:
        oled.text('run', 14, 2, 1)


# ── Timer Mode Draw ─────────────────────────────────
def draw_mode_timer(blink):
    draw_hourglass(2, 2)
    if timer_sub == T_VIEW:
        if timer_running:
            remaining = _get_remaining()
            oled.text('timer', 14, 2, 1)
            _draw_time_digits(remaining, True, blink)
        else:
            oled.text('timer', 14, 2, 1)
            oled.text('long press', 24, 30, 1)
            oled.text('to set timer', 16, 42, 1)
    elif timer_sub == T_SET:
        oled.text('set', 14, 2, 1)
        _draw_time_digits(timer_set_s, blink)
    elif timer_sub == T_PLAY:
        if timer_paused:
            oled.text('pause', 14, 2, 1)
            _draw_time_digits(timer_pause_rem, blink)
        else:
            remaining = _get_remaining()
            oled.text('play', 14, 2, 1)
            _draw_time_digits(remaining, True, blink)


# ── Timeout Overlay (Mario) ─────────────────────────
def draw_timeout(frame):
    draw_mario(55, 16)
    b = 2 if (frame % 4) < 2 else 0
    oled.text('time', 48, 38 + b, 1)
    oled.text('out!', 48, 50 + b, 1)
    if (frame % 6) < 3:
        oled.rect(0, 0, 128, 64, 1)


# ── Event Handling ───────────────────────────────────
def handle_event(evt):
    global mode, timer_sub, timer_set_s, timer_end_t
    global timer_running, timer_paused, timer_pause_rem, timeout_show
    global setting_time, set_field, set_repeat, set_rep_next
    global chrono_sub, chrono_running, chrono_start, chrono_elapsed

    if evt is None:
        return

    # Timeout overlay – any press dismisses
    if timeout_show:
        timeout_show  = False
        timer_running = False
        timer_paused  = False
        timer_sub     = T_VIEW
        return

    # Time-setting mode
    if setting_time:
        if evt == 'triple':
            _apply_set_time()
            setting_time = False
            set_repeat   = False
        elif evt == 'single':
            _adjust_field(1)
        elif evt == 'double':
            set_field += 1
            if set_field > 5:
                _apply_set_time()
                setting_time = False
        elif evt == 'long':
            _adjust_field(1)
            set_repeat   = True
            set_rep_next = time.ticks_add(time.ticks_ms(), REPEAT_MS)
        return

    # Long press on clock → enter time-set mode
    if mode == MODE_CLOCK and evt == 'long':
        _enter_set_time()
        return

    # Timer-mode sub-state handling
    if mode == MODE_TIMER:
        if timer_sub == T_VIEW:
            if evt == 'single':
                mode = (mode + 1) % NUM_MODES
            elif evt == 'long':
                timer_sub   = T_SET
                timer_set_s = 30
            elif evt == 'triple':
                mode = MODE_CLOCK

        elif timer_sub == T_SET:
            if evt == 'single':
                timer_set_s += 30
                if timer_set_s > 5400:      # max 90:00
                    timer_set_s = 30        # wrap to 00:30
            elif evt == 'double':
                timer_set_s -= 30
                if timer_set_s < 30:        # min 00:30
                    timer_set_s = 5400      # wrap to 90:00
            elif evt == 'long':
                timer_end_t   = time.ticks_add(time.ticks_ms(),
                                               timer_set_s * 1000)
                timer_running = True
                timer_paused  = False
                timer_sub     = T_PLAY
            elif evt == 'triple':
                timer_sub = T_VIEW
                mode = MODE_CLOCK

        elif timer_sub == T_PLAY:
            if evt == 'single':
                if timer_running:
                    # Pause
                    timer_pause_rem = _get_remaining()
                    timer_running   = False
                    timer_paused    = True
                elif timer_paused:
                    # Resume from pause
                    timer_end_t   = time.ticks_add(time.ticks_ms(),
                                                   timer_pause_rem * 1000)
                    timer_running = True
                    timer_paused  = False
            elif evt == 'long':
                if timer_running:
                    # Stop + reset to original set time → paused
                    timer_running   = False
                    timer_paused    = True
                    timer_pause_rem = timer_set_s
                elif timer_paused:
                    # Paused → enter set mode with last set time
                    timer_paused = False
                    timer_sub    = T_SET
            elif evt == 'triple':
                timer_sub = T_VIEW
                mode = MODE_CLOCK
        return

    # Chronograph mode handling
    if mode == MODE_CHRONO:
        if chrono_sub == C_IDLE:
            # Preview screen — shows elapsed if bg running
            if evt == 'single':
                mode = (mode + 1) % NUM_MODES
            elif evt == 'long':
                if chrono_running:
                    # Re-enter: show running chrono
                    chrono_sub = C_RUNNING
                else:
                    # Fresh start
                    chrono_elapsed = 0
                    chrono_start   = time.ticks_ms()
                    chrono_running = True
                    chrono_sub     = C_RUNNING

        elif chrono_sub == C_RUNNING:
            if evt == 'single':
                # Stop
                chrono_elapsed += time.ticks_diff(time.ticks_ms(), chrono_start)
                chrono_running = False
                chrono_sub     = C_STOPPED
            elif evt == 'triple':
                # Exit but keep running in background
                chrono_sub = C_IDLE
                mode = MODE_CLOCK

        elif chrono_sub == C_STOPPED:
            if evt == 'single':
                # Resume
                chrono_start   = time.ticks_ms()
                chrono_running = True
                chrono_sub     = C_RUNNING
            elif evt == 'long':
                # Reset — stay in chrono, ready to start
                chrono_elapsed = 0
                chrono_running = False
            elif evt == 'triple':
                # Exit
                chrono_sub = C_IDLE
                mode = MODE_CLOCK
        return

    # Normal modes – single press cycles
    if evt == 'single':
        mode = (mode + 1) % NUM_MODES


# ── Timer Countdown Check ────────────────────────────
def check_timer():
    global timeout_show, timer_running, timer_sub
    if timer_running:
        if time.ticks_diff(timer_end_t, time.ticks_ms()) <= 0:
            timer_running = False
            timeout_show  = True
            timer_sub     = T_VIEW


# ── Auto-Repeat for Set-Time ─────────────────────────
def check_set_repeat():
    global set_repeat, set_rep_next
    if not setting_time or not set_repeat:
        return
    # stop repeat when button is released
    if btn.value() == 1:
        set_repeat = False
        return
    now = time.ticks_ms()
    if time.ticks_diff(now, set_rep_next) >= 0:
        _adjust_field(1)
        set_rep_next = time.ticks_add(now, REPEAT_MS)


# ── Main Loop ────────────────────────────────────────
def main():
    blink    = True
    frame    = 0
    last_draw = time.ticks_ms()

    while True:
        now = time.ticks_ms()

        evt = poll_button()
        handle_event(evt)
        check_timer()
        check_set_repeat()

        # Faster refresh when chrono is actively running on screen
        draw_ms = 100 if (mode == MODE_CHRONO and chrono_sub == C_RUNNING) else 500
        if time.ticks_diff(now, last_draw) >= draw_ms:
            last_draw = now
            oled.fill(0)

            if timeout_show:
                draw_timeout(frame)
            elif setting_time:
                draw_set_time(blink)
            elif mode == MODE_CLOCK:
                draw_mode_clock(blink)
            elif mode == MODE_DATE:
                draw_mode_date()
            elif mode == MODE_YEAR:
                draw_mode_year()
            elif mode == MODE_SEC:
                draw_mode_seconds(blink)
            elif mode == MODE_TIMER:
                draw_mode_timer(blink)
            elif mode == MODE_CHRONO:
                draw_mode_chrono()

            oled.show()
            blink = not blink
            frame += 1

        # Faster polling when chrono is actively displayed & running
        time.sleep_ms(10 if (mode == MODE_CHRONO and chrono_sub == C_RUNNING) else 30)


main()
