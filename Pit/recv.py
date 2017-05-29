# Simple test to see if XBee is functional (sends to itself)
# Author: Jack Li
import XBee
from time import sleep

if __name__ == "__main__":
    xbee = XBee.XBee("/dev/ttyUSB0")
    while(1):
        sent = xbee.SendStr("Hi, Chachi")
        #sleep(0.5)
        Msg = xbee.Receive()
        print(Msg)
        sleep(.1)
