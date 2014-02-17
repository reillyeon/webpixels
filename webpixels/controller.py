from basic import Channel, Controller
import socket
import struct

class ColorKinetics(Controller):
   def __init__(self, host, port=6038):
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      self.sock.connect((host, port))

      self.channels = [Channel() for i in range(512)]

   def sync(self):
      header = struct.pack(">IHHIBBHIB",
                           0x0401dc4a, 0x0100, 0x0101, 0x00000000, 0x00, 0x00,
                           0x0000, 0xffffffff, 0x00)
      channels = [channel.get() for channel in self.channels]
      body = struct.pack("512B", *channels)
      self.sock.send(header + body)
