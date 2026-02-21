from machine import Pin, SoftI2C, RTC
import ssd1306
import time

i2c = SoftI2C(scl=Pin(6), sda=Pin(5))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
rtc = RTC()

# Large digit font: each digit is 3 cols x 5 rows of blocks
# 1 = filled block, 0 = empty
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

# Small block letters for AM/PM (3x3 grid, half-size blocks)
LETTERS = {
    'a': [1,1,1, 1,0,1, 1,1,1],
    'p': [1,1,0, 1,1,0, 1,0,0],
}

# Block size for each cell of the digit grid
BW = 4   # block width
BH = 6   # block height
GAP = 1  # gap between blocks

def draw_digit(d, x, y):
    pattern = DIGITS[d]
    for row in range(5):
        for col in range(3):
            px = x + col * (BW + GAP)
            py = y + row * (BH + GAP)
            c = pattern[row * 3 + col]
            oled.fill_rect(px, py, BW, BH, c)

def draw_letter(ch, x, y):
    pattern = LETTERS[ch]
    bw, bh, gap = 2, 3, 1
    for row in range(3):
        for col in range(3):
            px = x + col * (bw + gap)
            py = y + row * (bh + gap)
            c = pattern[row * 3 + col]
            oled.fill_rect(px, py, bw, bh, c)

def draw_colon(x, y, on):
    c = 1 if on else 0
    # Two square dots vertically centered within digit height (34px)
    oled.fill_rect(x, y + 10, 2, 2, c)
    oled.fill_rect(x, y + 22, 2, 2, c)

def draw_clock():
    colon_on = True
    while True:
        dt = rtc.datetime()
        h24 = dt[4]
        m = dt[5]

        # 12-hour format
        ampm = 'a' if h24 < 12 else 'p'
        h12 = h24 % 12
        if h12 == 0:
            h12 = 12

        h1 = h12 // 10
        h2 = h12 % 10
        m1 = m // 10
        m2 = m % 10

        oled.fill(0)

        # Layout: each digit=14px wide, colon=2px, spacing=2px
        dw = 3 * (BW + GAP) - GAP  # 14
        colon_w = 2
        spacing = 2
        total_w = dw * 4 + colon_w + spacing * 4
        start_x = (128 - total_w) // 2      # shift left
        dh = 5 * (BH + GAP) - GAP  # 34
        y = (64 - dh) // 2 + 10  # shift down

        cx = start_x
        # Hour tens - skip leading zero
        if h1 > 0:
            draw_digit(h1, cx, y)
        cx += dw + spacing

        # Hour ones
        draw_digit(h2, cx, y)
        cx += dw + spacing

        # Blinking colon
        draw_colon(cx, y, colon_on)
        cx += colon_w + spacing

        # Minute tens
        draw_digit(m1, cx, y)
        cx += dw + spacing

        # Minute ones
        draw_digit(m2, cx, y)

        # AM/PM indicator - block letter in top-left area
        draw_letter(ampm, start_x, y - 13)

        oled.show()
        colon_on = not colon_on
        time.sleep(1)

draw_clock()
