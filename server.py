from flask import Flask, redirect, render_template, request, url_for
import json
import re
from webpixels import RgbPixel
from webpixels.controller import ColorKinetics

app = Flask(__name__)

channels = {}
pixels = {}

def load_config(config_file):
   with open(config_file) as f:
      config = json.loads(f.read())

   for controllerConfig in config['controllers']:
      controllerType = controllerConfig['type']
      if controllerType == 'ColorKinetics':
         controller = ColorKinetics(host=controllerConfig['host'])
      for channel in controller.channels:
         name = '%s:%d' % (controllerConfig['name'], channel.dmx_channel)
         channels[name] = channel

   for pixelConfig in config['rgbpixels']:
      chan_set = [channels[name] for name in pixelConfig['channels']]
      pixels[pixelConfig['name']] = RgbPixel(*chan_set)

hex_triplet_pattern = re.compile(r'^#([0-9a-fA-F]{6})$')
def hex_triplet_to_rgb(hex):
   match = hex_triplet_pattern.match(hex)
   if match:
      value = int(match.group(1), 16)
      return value >> 16, value >> 8 & 0xff, value & 0xff
   else:
      raise ValueError('Invalid color')

def rgb_to_hex_triplet(r, g, b):
   return '#%02x%02x%02x' % (r, g, b)

@app.route('/')
def index():
   pixel_list = [(name, pixel.get()) for name, pixel in pixels.items()]
   pixel_list.sort(key=lambda pixel: pixel[0])
   average = tuple([sum([pixel[i] for name, pixel in pixel_list]) / len(pixel_list)
                    for i in range(3)])
   average = rgb_to_hex_triplet(*average)
   pixel_list = [(name, rgb_to_hex_triplet(*pixel)) for name, pixel in pixel_list]
   return render_template('index.html', pixels=pixel_list, average=average)

@app.route('/pixel/all', methods=['POST'])
def set_all_pixels():
   r, g, b = hex_triplet_to_rgb(request.form['color'])
   controllers = set()
   for pixel in pixels.values():
      pixel.set(r, g, b)
      controllers.update(pixel.get_controllers())
   for controller in controllers:
      controller.sync()
   return redirect(url_for('index'))

@app.route('/pixel/<pixel>', methods=['GET', 'POST'])
def pixel(pixel):
   if request.method == 'POST':
      r, g, b = hex_triplet_to_rgb(request.form['color'])
      pixels[pixel].set(r, g, b)
      pixels[pixel].sync()
      return redirect(url_for('index'))
   else:
      rgb = pixels[pixel].get()
      return rgb_to_hex_triplet(*rgb)

@app.route('/pixels', methods=['POST'])
def set_pixels():
   controllers = set()
   for name, pixel in pixels.items():
      key = 'color_%s' % name
      if key in request.form.keys():
         r, g, b = hex_triplet_to_rgb(request.form[key])
         pixels[name].set(r, g, b)
         controllers.update(pixels[name].get_controllers())
   for controller in controllers:
      controller.sync()
   return redirect(url_for('index'))

if __name__ == '__main__':
   import sys

   if len(sys.argv) != 2:
      print("Usage: python server.py config.json")

   configFile = sys.argv[1]
   load_config(configFile)

   app.debug = True
   app.run(host='0.0.0.0', port=80)
