from abc import ABCMeta, abstractmethod

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