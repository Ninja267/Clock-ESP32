from machine import Pin, SoftI2C, RTC
import ssd1306
import time

i2c = SoftI2C(scl=Pin(6), sda=Pin(5))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
rtc = RTC()

btn = Pin(9, Pin.IN, Pin.PULL_UP)

mode = 0
NUM_MODES = 5
btn_prev = 1

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

BW = 4
BH = 6
GAP = 1


def draw_digit(d, x, y, bw=BW, bh=BH, gap=GAP):
    pat = DIGITS[d]
    for r in range(5):
        for c in range(3):
            oled.fill_rect(x + c * (bw + gap), y + r * (bh + gap), bw, bh, pat[r * 3 + c])


def draw_letter(ch, x, y):
    pat = LETTERS[ch]
    bw, bh, gap = 2, 3, 1
    for r in range(3):
        for c in range(3):
            oled.fill_rect(x + c * (bw + gap), y + r * (bh + gap), bw, bh, pat[r * 3 + c])


def draw_colon(x, y, on, bh=BH, gap=GAP):
    v = 1 if on else 0
    dh = 5 * (bh + gap) - gap
    oled.fill_rect(x, y + dh // 3, 2, 2, v)
    oled.fill_rect(x, y + dh * 2 // 3, 2, 2, v)


def draw_dot(x, y, bh=BH, gap=GAP):
    dh = 5 * (bh + gap) - gap
    oled.fill_rect(x, y + dh - 3, 3, 3, 1)


def check_button():
    global btn_prev, mode
    val = btn.value()
    if btn_prev == 1 and val == 0:
        mode = (mode + 1) % NUM_MODES
    btn_prev = val


def draw_mode_clock(blink):
    dt = rtc.datetime()
    h24, m = dt[4], dt[5]
    ampm = 'a' if h24 < 12 else 'p'
    h12 = h24 % 12 or 12
    dw = 3 * (BW + GAP) - GAP
    sp = 2
    cw = 2
    tw = dw * 4 + cw + sp * 4
    sx = (128 - tw) // 2
    dh = 5 * (BH + GAP) - GAP
    y = (64 - dh) // 2 + 10
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
    y = (64 - dh) // 2 + 8
    cx = sx
    draw_digit(mo // 10, cx, y)
    cx += dw + sp
    draw_digit(mo % 10, cx, y)
    cx += dw + sp
    draw_dot(cx, y)
    cx += dotw + sp
    draw_digit(day // 10, cx, y)
    cx += dw + sp
    draw_digit(day % 10, cx, y)
    oled.text('date', 0, 0, 1)


def draw_mode_year():
    yr = rtc.datetime()[0]
    dw = 3 * (BW + GAP) - GAP
    sp = 2
    tw = dw * 4 + sp * 3
    sx = (128 - tw) // 2
    dh = 5 * (BH + GAP) - GAP
    y = (64 - dh) // 2 + 8
    draw_digit(yr // 1000, sx, y)
    draw_digit((yr // 100) % 10, sx + dw + sp, y)
    draw_digit((yr // 10) % 10, sx + (dw + sp) * 2, y)
    draw_digit(yr % 10, sx + (dw + sp) * 3, y)
    oled.text('year', 0, 0, 1)


def draw_mode_seconds(blink):
    s = rtc.datetime()[6]
    dw = 3 * (BW + GAP) - GAP
    sp = 2
    tw = dw * 2 + sp
    sx = (128 - tw) // 2
    dh = 5 * (BH + GAP) - GAP
    y = (64 - dh) // 2 + 10
    draw_digit(s // 10, sx, y)
    draw_digit(s % 10, sx + dw + sp, y)
    if blink:
        oled.fill_rect(sx + tw + 3, y + dh - 3, 2, 2, 1)
    oled.text('sec', 0, 0, 1)


def draw_mode_secret(frame):
    cx, cy = 59, 22
    # Skull head (11x7)
    oled.fill_rect(cx, cy, 11, 7, 1)
    oled.fill_rect(cx - 1, cy + 1, 1, 5, 1)
    oled.fill_rect(cx + 11, cy + 1, 1, 5, 1)
    # Eyes
    oled.fill_rect(cx + 2, cy + 2, 2, 2, 0)
    oled.fill_rect(cx + 7, cy + 2, 2, 2, 0)
    # Mouth
    oled.fill_rect(cx + 3, cy + 5, 1, 1, 0)
    oled.fill_rect(cx + 5, cy + 5, 1, 1, 0)
    oled.fill_rect(cx + 7, cy + 5, 1, 1, 0)
    # Crossbones
    oled.line(cx - 2, cy + 8, cx + 13, cy + 13, 1)
    oled.line(cx + 13, cy + 8, cx - 2, cy + 13, 1)
    b = 2 if (frame % 4) < 2 else 0
    oled.text('we are', 40, 38 + b, 1)
    oled.text('pirates', 36, 50 + b, 1)
    if (frame % 6) < 3:
        oled.rect(0, 0, 128, 64, 1)


def main():
    blink = True
    frame = 0
    while True:
        check_button()
        oled.fill(0)
        if mode == 0:
            draw_mode_clock(blink)
        elif mode == 1:
            draw_mode_date()
        elif mode == 2:
            draw_mode_year()
        elif mode == 3:
            draw_mode_seconds(blink)
        elif mode == 4:
            draw_mode_secret(frame)
        oled.show()
        blink = not blink
        frame += 1
        time.sleep(0.5 if mode == 3 else 1)

main()
