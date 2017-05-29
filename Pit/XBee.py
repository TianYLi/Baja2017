import serial
import struct, time
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
        #print(remaining)
        while remaining:
            #print("remaining: {}".format(remaining))
            chunk = self.serial.read(remaining)
            #print("chunk : {}".format(chunk))
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
        if frame is None:
            return False
        LSB = frame[1]
        # Frame (minus checksum) must contain at least length equal to LSB
        if LSB > (len(frame[2:]) - 1):
            return False

        # Validate checksum
        if (sum(frame[2:3+LSB]) & 0xFF) != 0xFF:
            return False

        #print("Rx: " + self.format(bytearray(b'\x7E') + msg))
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

    def Send(self, msg, addr=0x0013A200415AF7AF, options=0x00, frameid=0x01):
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
        hexs = '7E {:04X} 00 {:02X} 00 {:02X} {:02X}'.format(
            len(msg) + 0xB,           # LSB (length)
            frameid,
            addr,
            options
        )
        
        frame = bytearray.fromhex(hexs)
        frame.extend(msg)
        hexmsg = msg.encode("hex")
        msgsum = 0
        addrsum = 0
        tdhmsg=[hexmsg[i:i+2] for i in range(0, len(hexmsg), 2)]
        for c in tdhmsg:
            msgsum = msgsum + int(c,16)
        tdhaddr= self.twoDigitHex(addr)
        n=2
        tdhaddr2 = [tdhaddr[i:i+n] for i in range(0, len(tdhaddr),n)]
        for k in tdhaddr2:
            addrsum=addrsum+int(k,16)
        checksum1=self.twoDigitHex(0xFF-(0xFF&(int(msgsum)+int(addrsum)+int(0x01))))
        frame.append(int(checksum1,16))
        #self.checksum(frame)
        frame = self.Escape(frame)
        #print(self.format(frame))
        #print(self.verify(self.Unescape(frame), int(checksum1, 16)))
        return self.serial.write(frame)
    """
    def HexAppend(a, b):
        sizeof_b = 0
        while((b >> sizeof_b) >0):
            sizeof_b += 1

        sizeof_b += sizeof_b % 4
        return (a << sizeof_b) | b
    """
    def Replacer(self, msg):
        """
        Helper function to replace special characters in the frame
        """
        for i in range(1, len(msg)):
            if(msg[i] == 17):
                msg = msg[:i] + b'\x7d' + b'\x31' + msg[i+1:]
                i = i+1
            if(msg[i] == 19):
                msg = msg[:i] + b'\x7d' + b'\x33' + msg[i+1:]
                i = i+1
            if(msg[i] == 125):
                msg = msg[:i] + b'\x7d' + b'\x5d' + msg[i+1:]
                i = i+1
            if(msg[i] == 126):
                msg = msg[:i] + b'\x7d' + b'\x5e' + msg[i+1:]
                i = i+1
        return msg
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

    def twoDigitHex(self, number):
        return '%02x' % number

    def checksum(self, frame):
        total = 0
        for byte in frame:
            total += byteToInt(byte)
        total = total & 0xFF
        return byteToInt(0xFF - total)

    def verify(self, frame, chksum):
        total = 0
        for byte in frame:
            print(type(byte))
            total += byte
        print(type(chksum))
        total += byteToInt(chksum)
        print(total)
        total &= 0xFF
        print(total)
        return total == 0xFF

def byteToInt(byte):
	"""
	byte -> int
	
	Determines whether to use ord() or not to get a byte's value.
	"""
	if hasattr(byte, 'bit_length'):
		# This is already an int
		return byte
	return ord(byte) if hasattr(byte, 'encode') else byte[0]
