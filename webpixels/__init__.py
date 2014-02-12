from abc import ABCMeta, abstractmethod
import socket
import struct

class Channel(object):
   def __init__(self, value=0):
      self.value = value

   def set(self, new_value):
      self.value = new_value

   def get(self):
      return self.value

   def __str__(self):
      return "<Channel %d>" % self.value

class Pixel(object):
   __metaclass__ = ABCMeta

   @abstractmethod
   def set(self, red, green, blue):
      pass

   @abstractmethod
   def get(self):
      pass

   def __str__(self):
      r, g, b = self.get()
      return "<Pixel %d, %d, %d>" % (r, g, b)

class RgbPixel(Pixel):
   def __init__(self, red_chan, green_chan, blue_chan, value=(0, 0, 0)):
      self.red = red_chan
      self.green = green_chan
      self.blue = blue_chan

   def set(self, red, green, blue):
      self.red.set(red)
      self.green.set(green)
      self.blue.set(blue)

   def get(self):
      return self.red.get(), self.green.get(), self.blue.get()

class Controller(object):
   __metaclass__ = ABCMeta

   @abstractmethod
   def sync(self):
      pass

class ColorKinetics(Controller):
   class CKChannel(Channel):
      def __init__(self, dmx_id):
         Channel.__init__(self, value=0)
         self.dmx_id = dmx_id

   def __init__(self, host, port=6038):
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      self.sock.connect((host, port))

      self.channels = [Channel(0) for i in xrange(512)]

   def sync(self):
      header = struct.pack(">IHHIBBHIB",
                           0x0401dc4a, 0x0100, 0x0101, 0x00000000, 0x00, 0x00,
                           0x0000, 0xffffffff, 0x00)
      channels = [channel.get() for channel in self.channels]
      body = struct.pack("512B", *channels)
      self.sock.send(header + body)

