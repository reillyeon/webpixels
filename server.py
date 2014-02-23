from flask import Flask, redirect, render_template, request, url_for
import json
import re
from webpixels import RgbPixel
from webpixels.controller import ColorKinetics

app = Flask(__name__)

pixels = []

def load_config(config_file):
   with open(config_file) as f:
      config = json.loads(f.read())
   for controllerConfig in config['controllers']:
      controllerType = controllerConfig['type']
      if controllerType == 'ColorKinetics':
         controller = ColorKinetics(host=controllerConfig['host'])
      for pixel in controllerConfig['pixels']:
         channels = [controller.channels[channel] for channel in pixel]
         pixels.append(RgbPixel(*channels))

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
   values = [pixel.get() for pixel in pixels]
   pixel_list = []
   for i in range(len(pixels)):
      pixel_list.append((str(i), rgb_to_hex_triplet(*values[i])))
   average = tuple([sum([pixel[i] for pixel in values]) / len(values)
                    for i in range(3)])
   average = rgb_to_hex_triplet(*average)
   return render_template('index.html', pixels=pixel_list, average=average)

@app.route('/pixel/all', methods=['POST'])
def set_all_pixels():
   r, g, b = hex_triplet_to_rgb(request.form['color'])
   controllers = set()
   for pixel in pixels:
      pixel.set(r, g, b)
      controllers.update(pixel.get_controllers())
   for controller in controllers:
      controller.sync()
   return redirect(url_for('index'))

@app.route('/pixel/<int:pixel>', methods=['GET', 'POST'])
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
   for i in range(len(pixels)):
      key = 'color_%d' % i
      if key in request.form.keys():
         r, g, b = hex_triplet_to_rgb(request.form[key])
         pixels[i].set(r, g, b)
         controllers.update(pixels[i].get_controllers())
   for controller in controllers:
      controller.sync()
   return redirect(url_for('index'))

if __name__ == '__main__':
   import sys

   if len(sys.argv) != 2:
      print "Usage: python server.py config.json"

   configFile = sys.argv[1]
   load_config(configFile)

   app.debug = True
   app.run(host='0.0.0.0', port=80)
