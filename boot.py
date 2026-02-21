# ── Wi-Fi & Timezone Config ──────────────────────────
# Credentials are loaded from config.py (gitignored).
# Create your own config.py with:
#   WIFI_SSID     = 'your-ssid'
#   WIFI_PASSWORD = 'your-password'
#   UTC_OFFSET    = 1
# ─────────────────────────────────────────────────────
try:
    from config import WIFI_SSID, WIFI_PASSWORD, UTC_OFFSET
except ImportError:
    print('config.py not found — using fallback values')
    WIFI_SSID     = 'your-ssid'
    WIFI_PASSWORD = 'your-password'
    UTC_OFFSET    = 0

import network, ntptime, time
from machine import RTC

rtc = RTC()

# Connect to Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASSWORD)

print('Connecting to Wi-Fi...', end='')
for _ in range(20):  # wait up to 10 seconds
    if wlan.isconnected():
        break
    time.sleep(0.5)
    print('.', end='')

if wlan.isconnected():
    print(' connected!')
    try:
        ntptime.settime()  # sync UTC time from internet
        # Apply timezone offset
        import utime
        now = utime.time() + UTC_OFFSET * 3600
        tm = utime.localtime(now)
        # tm = (year, month, day, hour, minute, second, weekday, yearday)
        rtc.datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))
        print('Time synced:', rtc.datetime())
    except Exception as e:
        print('NTP sync failed:', e)
    wlan.active(False)  # turn off Wi-Fi to save power
else:
    print(' failed!')
    print('Using fallback time')
    # Fallback: static time if Wi-Fi unavailable
    rtc.datetime((2026, 2, 20, 3, 12, 0, 0, 0))
