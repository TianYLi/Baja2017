
import RPi.GPIO as GPIO
import time

sClock = 27
sLatch = 17
sData = 22
number = 0

GPIO.setmode(GPIO.BCM)
segments = (sClock, sLatch, sData)

for segment in segments:
    GPIO.setup(segment, GPIO.OUT)
    GPIO.output(segment, 0)

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

def showNumber(value):
    n = abs(value)
    for i in range(2):
        remainder = n % 10
        postNumber(remainder, 0)
        n /= 10
    GPIO.output(sLatch, 0)
    GPIO.output(sLatch, 1)


def postNumber(n, decimal):
    if decimal:
        num[str(n)] |= dp
    for x in range(8):
        GPIO.output(sClock, 0)
        GPIO.output(sData, num[str(n)] & 1 << (7-x))
        GPIO.output(sClock, 1)
i = 0
while(1):
    showNumber(i)
    i+=1
    i %= 100
    time.sleep(0.22)
