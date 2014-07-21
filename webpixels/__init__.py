from abc import ABCMeta, abstractmethod
from math import copysign
import re

MAX_STEP_SIZE = 10

class Channel(object):
   def __init__(self, name, controller, value=0):
      self.name = name
      self.controller = controller
      self.value = value

   def set(self, new_value):
      self.value = new_value

   def set_target(self, new_value):
      self.target_value = new_value

   def step(self):
      diff = self.target_value - self.value
      diff = copysign(max(MAX_STEP_SIZE, abs(diff)), diff)
      self.value += diff
      return self.value != self.target_value

   def get(self):
      return self.value

   def sync(self):
      self.controller.sync()

   def get_controller(self):
      return self.controller

   def get_name(self):
      return self.name

   def __str__(self):
      return "<Channel %s>" % self.name

class Pixel(object):
   __metaclass__ = ABCMeta

   def __init__(self, name):
      self.name = name

   @abstractmethod
   def set(self, red, green, blue):
      pass

   @abstractmethod
   def set_target(self, red, green, blue):
      pass

   @abstractmethod
   def step(self):
      pass

   @abstractmethod
   def get(self):
      pass

   def get_html_color(self):
      r, g, b = self.get()
      return '#%02x%02x%02x' % (r, g, b)

   @abstractmethod
   def get_controllers(self):
      pass

   def get_name(self):
      return self.name

   def sync(self):
      for controller in self.get_controllers():
         controller.sync()

   def __str__(self):
      return "<Pixel %s>" % self.name

class RgbPixel(Pixel):
   def __init__(self, name, red_chan, green_chan, blue_chan):
      super(RgbPixel, self).__init__(name)
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

   def set_target(self, red, green, blue):
      self.red.set_target(red)
      self.green.set_target(green)
      self.blue.set_target(blue)

   def step(self):
      results = (self.red.step(), self.green.step(), self.blue.step())
      return any(results)

   def get(self):
      return self.red.get(), self.green.get(), self.blue.get()

   def get_controllers(self):
      return self.controllers

   def get_channels(self):
      return (self.red, self.green, self.blue)

class PixelSet(Pixel):
   def __init__(self, name, pixels):
      super(PixelSet, self).__init__(name)
      self.pixels = pixels
      self.controllers = set()
      for pixel in pixels:
         self.controllers.update(pixel.get_controllers())

   def set(self, red, green, blue):
      for pixel in self.pixels:
         pixel.set(red, green, blue)

   def set_target(self, red, green, blue):
      for pixel in self.pixels:
         pixel.set_target(red, green, blue)

   def step(self):
      results = [pixel.step() for pixel in self.pixels]
      return any(results)

   def get(self):
      values = [pixel.get() for pixel in self.pixels]
      rgb = tuple(sum(values) for values in zip(*values))
      return tuple(value / len(self.pixels) for value in rgb)

   def get_controllers(self):
      return self.controllers

   def get_pixels(self):
      return self.pixels

class Controller(object):
   __metaclass__ = ABCMeta

   def __init__(self, name):
      self.name = name

   @abstractmethod
   def sync(self):
      pass

   def get_name(self):
      return self.name
