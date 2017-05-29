# Isolated test code for Hall Effect Sensors
# Author: Jack Li

from __future__ import print_function
import json
import subprocess
import time

import Adafruit_ADS1x15

adc1 = Adafruit_ADS1x15.ADS1115(address=0x48, busnum=1)
GAIN = 1

print('Reading ADS1x15 values, press Ctrl-C to quit...')
# Print nice channel column headers.
print('| {0:>7} | {1:>7} | {2:>7} | {3:>7} |'.format(*range(12)))
print('-' * 73)

values = [0]*4

try:
    if (sys.version_info > (3, 0)):
        py3 = True
except:
    pass


# Main loop.
while True:
    values[0] = adc1.read_adc(0, gain=GAIN)
    values[1] = adc1.read_adc(1, gain=GAIN)
    values[2] = adc1.read_adc(2, gain=GAIN)
    values[3] = adc1.read_adc(3, gain=GAIN)
    print('| {0:>6.2f} | {1:>6.2f} | {2:>6.2f} | {3:>6.2f} |'.format(*values))
    time.sleep(0.1)
