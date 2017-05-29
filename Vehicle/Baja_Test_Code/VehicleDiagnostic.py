# Vehicle software for USD Baja 2017, for use of future USD teams
# Author: Jack Li
from __future__ import print_function
import json
import subprocess
import time
import RPi.GPIO as GPIO
import XBee
import Adafruit_ADS1x15
import Adafruit_GPIO.SPI as SPI
import Adafruit_MAX31855.MAX31855 as MAX31855

#initialize Xbee
xbee = XBee.XBee("/dev/ttyUSB0")  # Your serial port name here

# Create ADS1115 ADC (16-bit) instances
adc1 = Adafruit_ADS1x15.ADS1115(address=0x48, busnum=1) #hall effects
adc2 = Adafruit_ADS1x15.ADS1115(address=0x49, busnum=1) #4x lvdts

# Choose a gain of 1 for reading voltages from 0 to 4.09V.
# Or pick a different gain to change the range of voltages that are read:
#  - 2/3 = +/-6.144V
#  -   1 = +/-4.096V
#  -   2 = +/-2.048V
#  -   4 = +/-1.024V
#  -   8 = +/-0.512V
#  -  16 = +/-0.256V
# See table 3 in the ADS1015/ADS1115 datasheet for more info on gain.
GAIN = 1

#initializing stuff for temp sensor
tClock = 25
tCS = 24
tD0 = 18
temp_sensor = MAX31855.MAX31855(tClock, tCS, tD0)

#Note: 7-segment display is two sets of two displays connected in series

# these are pin locations for the 7segment display on the Pi
sClock = [27, 19]
sLatch = [17, 13]
sData = [22, 26]

# this is global table that converts number into 7seg lightup
a = 1<<0
b = 1<<6
c = 1<<5
d = 1<<4
e = 1<<3
f = 1<<1
g = 1<<2
dp = 1<<7
num = {' ': 0,
       '0': a | b | c | d | e | f,
       '1': b | c,
       '2': a | b | d | e | g,
       '3': a | b | c | d | g,
       '4': f | g | b | c,
       '5': a | f | g | c | d,
       '6': a | f | g | e | c | d,
       '7': a | b | c,
       '8': a | b | c | d | e | f | g,
       '9': a | b | c | d | f | g}

#converts temperature in celsieus to farenheit
def c_to_f(c):
    return c* 9.0/5.0 +32.0

# initializes 7-segment display
def initsseg(setnum):
    GPIO.setmode(GPIO.BCM)
    segments = (sClock[setnum], sLatch[setnum], sData[setnum])
    print(segments)
    for segment in segments:
        GPIO.setup(segment, GPIO.OUT)
        GPIO.output(segment, 0)

#Specifies which number to be displayed on the 7-segment display
def showNumber(value, setnum):
    # print("show: {}, {}".format(value, setnum))
    n = abs(value)
    for i in range(2):
        remainder = n % 10
        postNumber(remainder, 0, setnum)
        n /= 10
    GPIO.output(sLatch[setnum], 0)
    GPIO.output(sLatch[setnum], 1)

#Called by show number, part of 7-seg display code
def postNumber(n, decimal, setnum):
    # print("post: {}, {}, {}".format(n, decimal, setnum))
    if decimal:
        num[str(n)] |= dp
    for x in range(8):
        GPIO.output(sClock[setnum], 0)
        GPIO.output(sData[setnum], num[str(n)] & 1 << (7-x))
        GPIO.output(sClock[setnum], 1)
	time.sleep(0.001)
# END OF 7-SEGMENT DISPLAY CODE

# constantly running once the program starts up
# NOTE FOR FUTURE YEARS: Consider running separate threads with loops 
# to do each sensor as opposed to having all of them in one big loop 
# like I have it here.
def startloop():
    # init GPIO for temp sensor
    GPIO.setup(12, GPIO.OUT)
    GPIO.output(12, GPIO.HIGH)
    # STARTING LOOP OF OUTPUT
    print('Reading sensory values, press Ctrl-C to quit...')
    # Print nice channel column headers.
    print('| {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6} | {5:>6} | {6:>6} | {7:>6} | {8:>6} | {9:>6} | {10:>6} | {11:>6} |'.format(*range(12)))
    print('-' * 73)

    # initial time - this is used by hall effect sensor to calculate speed/rpm
    # Note for future years: Don't use hall effects (magnet sensors) use some laser based sensor instead
    oldtime = [time.time(), time.time()]

    # stores values to be displayed/sent
    values = [0]*12

    # checks whether hall-effect values are high or low
    # used to prevent double counting
    hilo = [0]*2

    # raw/temp values from adc for hall effects
    checker = [0]*2

    #initializing led, yay more gpio
    GPIO.setup(23, GPIO.OUT)
    GPIO.setup(5, GPIO.OUT)

    # Main loop.
    while True:
        # Read all the ADC channel values in a list. 

        # first to be read is hall effect for wheel speed
        checker[0] = adc1.read_adc(0, gain=GAIN)
        if(hilo[0] == 0 and int(checker[0]) < 1000):
            hilo[0] = 1
        if(hilo[0] == 1 and int(checker[0]) > 1000):
            timechange = time.time() - oldtime[0]
            values[0] = 22/timechange
            oldtime[0] = time.time()
            hilo[0] = 0

        # display speed values to top set of 7-segment displays
        # we don't expect to go over 99 mph so 2 displays is sufficient
        showNumber(int(values[0]), 0)

        # next up is hall effect for engine rpm
        checker[1] = adc1.read_adc(1, gain=GAIN)
        if(hilo[1] == 0 and checker[1] < 1000):
            hilo[1] = 1
        if(hilo[1] == 1 and checker[1] > 1000):
            timechange = time.time() - oldtime[1]
            try:
                values[1] = 1/(timechange/60)
            except ZeroDivisionError:
                pass
            oldtime[1] = time.time()
            hilo[1] = 0

        # display rpm values x100. (i.e. 1000 rpm is displayed as 10)
	    showNumber(int(values[1])/100, 1)


        # each of the 4 lvdts
        for i in range(4):
           values[(i+1)*2] = (adc2.read_adc(i, gain=GAIN)+300)/1023*0.25
           values[(i+1)*2+1] = (adc2.read_adc(i, gain=GAIN)+150)/800*0.5
        
        # get value (in Celsieus) from temp sensor (does not use adc, directly connected to GPIO)
        temp = temp_sensor.readTempC()
        values[10] = temp
        # gotta display farenheit as well
        values[11] = c_to_f(temp)

	    #temperature LED turns on when engine temp is over 150 farenheit (hopefully we never use this)
	    if(c_to_f(temp) > 150):
            GPIO.output(23, GPIO.HIGH)
        else:
            GPIO.output(23, GPIO.LOW)

        # Print the ADC values.
        print('| {0:>6.2f} | {1:>6.2f} | {2:>6.2f} | {3:>6.2f} | {4:>6.2f} | {5:>6.2f} | {6:>6.2f} | {7:>6.2f} | {8:>6.2f} | {9:>6.2f} | {10:6.2f} | {11:6.2f} |'.format(*values))
        # construct message to be sent
        sendstr = "{0:.2f}%$%{1:.2f}%$%{2:.2f}%$%{3:.2f}%$%{4:.2f}%$%{5:.2f}%$%{6:.2f}%$%{7:.2f}%$%{8:.2f}%$%{9:.2f}%$%{10:.2f}%$%{11:.2f}".format(*values)
        # Send ADC values to pit side
        sent = xbee.SendStr(sendstr)

        # led that blinks every time we send a packet
	    if sent is not None:
	        GPIO.output(5, GPIO.HIGH)
            # Pause for 0.1 seconds
            time.sleep(0.01)
            GPIO.output(5, GPIO.LOW)

if __name__ == "__main__":
    # initialize the 7-segment displays
    initsseg(0)
    initsseg(1)
    # run start loop!
    startloop()



