from abc import ABCMeta, abstractmethod

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

   @abstractmethod
   def get(self):
      pass

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

class Controller(object):
   __metaclass__ = ABCMeta

   @abstractmethod
   def sync(self):
      pass
