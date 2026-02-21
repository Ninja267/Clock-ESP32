"""
Chronograph prototype — centisecond (XX) display stress test.
Press boot button to start, press again to stop, hold to reset.
"""
from machine import Pin, SoftI2C
import ssd1306
import time

i2c  = SoftI2C(scl=Pin(6), sda=Pin(5))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
btn  = Pin(9, Pin.IN, Pin.PULL_UP)

# ── States ───────────────────────────────────────────
IDLE    = 0
RUNNING = 1
STOPPED = 2

state     = IDLE
start_t   = 0       # ticks_ms when started
elapsed   = 0       # frozen elapsed ms when stopped
fps_count = 0
fps_time  = 0
fps_val   = 0

# ── Big digit font (5 rows x 3 cols) ────────────────
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

BW  = 8      # block width  (bigger for visibility)
BH  = 10     # block height
GAP = 2


def draw_digit(d, x, y):
    pat = DIGITS[d]
    for r in range(5):
        for c in range(3):
            oled.fill_rect(x + c * (BW + GAP), y + r * (BH + GAP),
                           BW, BH, pat[r * 3 + c])


# ── Button handling ──────────────────────────────────
btn_prev   = 1
down_time  = 0
LONG_MS    = 600


def check_button():
    global state, start_t, elapsed, btn_prev, down_time
    v   = btn.value()
    now = time.ticks_ms()

    # Press down
    if btn_prev == 1 and v == 0:
        down_time = now

    # Release
    if btn_prev == 0 and v == 1:
        held = time.ticks_diff(now, down_time)
        if held >= LONG_MS:
            # Long press → reset
            state   = IDLE
            elapsed = 0
        else:
            # Short press → start/stop
            if state == IDLE:
                start_t = time.ticks_ms()
                state   = RUNNING
            elif state == RUNNING:
                elapsed = time.ticks_diff(now, start_t)
                state   = STOPPED
            elif state == STOPPED:
                start_t = time.ticks_add(now, -elapsed)
                state   = RUNNING

    btn_prev = v


# ── Main loop ────────────────────────────────────────
def main():
    global fps_count, fps_time, fps_val

    fps_time = time.ticks_ms()

    while True:
        check_button()

        # Calculate centiseconds (0-99)
        if state == RUNNING:
            ms = time.ticks_diff(time.ticks_ms(), start_t)
        elif state == STOPPED:
            ms = elapsed
        else:
            ms = 0

        cs = (ms // 10) % 100    # centiseconds 00-99

        # Draw
        oled.fill(0)

        # Status label
        if state == IDLE:
            oled.text('ready', 0, 0, 1)
        elif state == RUNNING:
            oled.text('running', 0, 0, 1)
        elif state == STOPPED:
            oled.text('stopped', 0, 0, 1)

        # Big centisecond digits
        dw = 3 * (BW + GAP) - GAP
        sp = 6
        tw = dw * 2 + sp
        sx = (128 - tw) // 2
        y  = 12
        draw_digit(cs // 10, sx, y)
        draw_digit(cs % 10, sx + dw + sp, y)

        # FPS counter
        fps_count += 1
        now = time.ticks_ms()
        dt  = time.ticks_diff(now, fps_time)
        if dt >= 1000:
            fps_val   = fps_count * 1000 // dt
            fps_count = 0
            fps_time  = now

        oled.text('fps:' + str(fps_val), 88, 0, 1)

        oled.show()
        # No sleep — run as fast as possible!


main()
