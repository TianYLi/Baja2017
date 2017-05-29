import serial
import struct
from collections import deque

class XBee():
    RxBuff = bytearray()
    RxMessages = deque()

    def __init__(self, serialport, baudrate=9600):
        self.serial = serial.Serial(port=serialport, baudrate=baudrate)

    def Receive(self):
        """
           Receives data from serial and checks buffer for potential messages.
           Returns the next message in the queue if available.
        """
        remaining = self.serial.inWaiting()
        while remaining:
            chunk = self.serial.read(remaining)
            print("chunk :"+ chunk)
            remaining -= len(chunk)
            self.RxBuff.extend(chunk)

        msgs = self.RxBuff.split(bytes(b'\x7E'))
        for msg in msgs[:-1]:
            self.Validate(msg)

        self.RxBuff = (bytearray() if self.Validate(msgs[-1]) else msgs[-1])

        if self.RxMessages:
            return self.RxMessages.popleft()
        else:
            return None

    def Validate(self, msg):
        """
        Parses a byte or bytearray object to verify the contents are a
          properly formatted XBee message.

        Inputs: An incoming XBee message

        Outputs: True or False, indicating message validity
        """
        # 9 bytes is Minimum length to be a valid Rx frame
        #  LSB, MSB, Type, Source Address(2), RSSI,
        #  Options, 1 byte data, checksum
        if (len(msg) - msg.count(bytes(b'0x7D'))) < 9:
            return False

        # All bytes in message must be unescaped before validating content
        frame = self.Unescape(msg)

        LSB = frame[1]
        # Frame (minus checksum) must contain at least length equal to LSB
        if LSB > (len(frame[2:]) - 1):
            return False

        # Validate checksum
        if (sum(frame[2:3+LSB]) & 0xFF) != 0xFF:
            return False

        print("Rx: " + self.format(bytearray(b'\x7E') + msg))
        self.RxMessages.append(frame)
        return True

    def SendStr(self, msg, addr=0x0013A200415AF7AF, options=0x00, frameid=0x01):
        """
        Inputs:
          msg: A message, in string format, to be sent
          addr: The 16 bit address of the destination XBee
            (default: 0xFFFF broadcast)
          options: Optional byte to specify transmission options
            (default 0x01: disable acknowledge)
          frameid: Optional frameid, only used if Tx status is desired
        Returns:
          Number of bytes sent
        """
        return self.Send(msg.encode('utf-8'), addr, options, frameid)

    def Send(self, msg, addr=0x0013A200415AF7B2, options=0x00, frameid=0x01):
        """
        Inputs:
          msg: A message, in bytes or bytearray format, to be sent to an XBee
          addr: The 16 bit address of the destination XBee
            (default broadcast)
          options: Optional byte to specify transmission options
            (default 0x01: disable ACK)
          frameod: Optional frameid, only used if transmit status is desired
        Returns:
          Number of bytes sent
        """
        if not msg:
            return 0
        print("addr: {:02X}".format(addr))
	print("addr: {:02X}\n ".format(addr))
        print("addr: {:02X}".format(addr))
 	print("addrrrrrr: {:02X}\n".format((addr&0xFF00)>>8))
        print("addr: {:02X}".format(addr))
	print("Jasmine stop telling me what to do: {:02X}\n".format(addr & 0xFF))
        print("addr: {:02X}".format(addr))
        hexs = '7E {:02X} 10 {:02X} {:02X} FF FE 00 {:02X}'.format(
            len(msg) + 0xE,           # LSB (length)
            frameid,
            addr,
            # (addr & 0xFF00) >> 8,   # Destination address high byte
            # addr & 0xFF,            # Destination address low byte
            options
        )
        print("addr: {:02X}".format(addr))        
        frame = bytearray.fromhex(hexs)
        print("Jack is a butt: "+ self.format(frame)+ "\n")
        print("addr: {:02X}".format(addr))
	#  Append message content
        frame.extend(msg)
        print("addr: {:02X}".format(addr))
	print("extend: " + self.format(frame) + "\n")
        print("addr: {:02X}".format(addr))
        # Calculate checksum byte
        #n = int(''.join(str(ord(c)) for c in msg))
        #n = msg.encode("hex")
        print(int(0x4B))
        msgsum = 0
        addrsum = 0
        i = 0
        for c in msg:
            msgsum = msgsum + int(ord(c))
        print(str(addr))
        for k in str(addr):
            if i%2 == 1:
                print(prev+k)
                addrsum = addrsum + int(prev+k)
            else:   
                prev = k
            i = i+1
        print("msg: {}, mhex: {}, addr: {:02X}".format(addr, type(addrsum), addrsum))
        
        checksum1=twoDigitHex(msgsum+int(addrsum)+int(0x01)+int(0x10))
        print(checksum1)
	print("Austin is also a butt append: " + self.format(frame) + "\n")
        # Escape any bytes containing reserved characters
        # frame = self.Escape(frame)
	
        print("Tx: " + self.format(frame))
        return self.serial.write(frame)

    def HexAppend(a, b):
        sizeof_b = 0
        while((b >> sizeof_b) >0):
            sizeof_b += 1

        sizeof_b += sizeof_b % 4
        return (a << sizeof_b) | b

    def Replacer(self, msg):
        """
        Helper function to replace special characters in the frame
        """
        for i in range(len(msg)):
            print("%d is %d", i, msg[i])

    def Unescape(self, msg):
        """
        Helper function to unescaped an XBee API message.

        Inputs:
          msg: An byte or bytearray object containing a raw XBee message
               minus the start delimeter

        Outputs:
          XBee message with original characters.
        """
        if msg[-1] == 0x7D:
            # Last byte indicates an escape, can't unescape that
            return None

        out = bytearray()
        skip = False
        for i in range(len(msg)):
            if skip:
                skip = False
                continue

            if msg[i] == 0x7D:
                out.append(msg[i+1] ^ 0x20)
                skip = True
            else:
                out.append(msg[i])

        return out

    def Escape(self, msg):
        """
        Escapes reserved characters before an XBee message is sent.

        Inputs:
          msg: A bytes or bytearray object containing an original message to
               be sent to an XBee

         Outputs:
           A bytearray object prepared to be sent to an XBee in API mode
         """
        escaped = bytearray()
        reserved = bytearray(b"\x7E\x7D\x11\x13")

        escaped.append(msg[0])
        for m in msg[1:]:
            if m in reserved:
                escaped.append(0x7D)
                escaped.append(m ^ 0x20)
            else:
                escaped.append(m)

        return escaped

    def format(self, msg):
        """
        Formats a byte or bytearray object into a more human readable string
          where each bytes is represented by two ascii characters and a space

        Input:
          msg: A bytes or bytearray object

        Output:
          A string representation
        """
        return " ".join("{:02x}".format(b) for b in msg)

    def twoDigitHex(number):
        return '%02x' %number
