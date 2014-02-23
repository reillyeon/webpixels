from abc import ABCMeta, abstractmethod
import re

class Channel(object):
   def __init__(self, controller, value=0):
      self.controller = controller
      self.value = value

   def set(self, new_value):
      self.value = new_value

   def get(self):
      return self.value

   def sync(self):
      controller.sync()

   def get_controller(self):
      return self.controller

   def __str__(self):
      return "<Channel %d>" % self.value

class Pixel(object):
   __metaclass__ = ABCMeta

   @abstractmethod
   def set(self, red, green, blue):
      pass

   hex_triplet_pattern = re.compile(r'^#([0-9a-fA-F]{6})$')
   def set_html_color(self, color):
      match = Pixel.hex_triplet_pattern.match(color)
      if match:
         value = int(match.group(1), 16)
         self.set(value >> 16, value >> 8 & 0xff, value & 0xff)
      else:
         raise ValueError('Invalid color')

   @abstractmethod
   def get(self):
      pass

   def get_html_color(self):
      r, g, b = self.get()
      return '#%02x%02x%02x' % (r, g, b)

   @abstractmethod
   def get_controllers(self):
      pass

   def sync(self):
      for controller in self.get_controllers():
         controller.sync()

   def __str__(self):
      r, g, b = self.get()
      return "<Pixel %d, %d, %d>" % (r, g, b)

class RgbPixel(Pixel):
   def __init__(self, red_chan, green_chan, blue_chan, value=(0, 0, 0)):
      self.controllers = set()
      self.red = red_chan
      self.controllers.add(red_chan.get_controller())
      self.green = green_chan
      self.controllers.add(green_chan.get_controller())
      self.blue = blue_chan
      self.controllers.add(blue_chan.get_controller())

   def set(self, red, green, blue):
      self.red.set(red)
      self.green.set(green)
      self.blue.set(blue)

   def get(self):
      return self.red.get(), self.green.get(), self.blue.get()

   def get_controllers(self):
      return self.controllers

class AveragePixel(Pixel):
   def __init__(self, pixels):
      self.pixels = pixels
      self.controllers = set()
      for pixel in pixels:
         self.controllers.update(pixel.get_controllers())

   def set(self, red, green, blue):
      for pixel in self.pixels:
         pixel.set(red, green, blue)

   def get(self):
      values = [pixel.get() for pixel in self.pixels]
      rgb = tuple(sum(values) for values in zip(*values))
      return tuple(value / len(self.pixels) for value in rgb)

   def get_controllers(self):
      return self.controllers

class Controller(object):
   __metaclass__ = ABCMeta

   @abstractmethod
   def sync(self):
      pass
