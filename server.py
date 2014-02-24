from flask import Flask, redirect, render_template, request, url_for
import json
import time
from webpixels import PixelSet, RgbPixel
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

   for fixtureConfig in config['fixtures']:
      pixel_set = [pixels[name] for name in fixtureConfig['pixels']]
      pixels[fixtureConfig['name']] = PixelSet(pixel_set)

   all_pixels = [pixel for pixel in pixels.values()
                 if not isinstance(pixel, PixelSet)]
   pixels['all'] = PixelSet(all_pixels)

@app.route('/')
def index():
   all_pixels = pixels['all'].get_html_color()
   pixel_list = [(name, pixel.get_html_color())
                 for name, pixel in pixels.items()
                 if not isinstance(pixel, PixelSet)]
   pixel_list.sort(key=lambda pixel: pixel[0])
   fixture_list = [(name, pixel.get_html_color())
                   for name, pixel in pixels.items()
                   if isinstance(pixel, PixelSet) and
                      name != 'all']
   fixture_list.sort(key=lambda pixel: pixel[0])
   return render_template('index.html',
                          all=all_pixels,
                          pixels=pixel_list,
                          fixtures=fixture_list)

@app.route('/pixel/<pixel>', methods=['GET', 'POST'])
def pixel(pixel):
   pixel = pixels[pixel]
   if request.method == 'POST':
      pixel.fade_html_color(request.form['color'])
      for i in range(40):
         time.sleep(0.025)
         pixel.fade_progress(i / 39)
         pixel.sync()
      return redirect(url_for('index'))
   else:
      return pixel.get_html_color()

@app.route('/pixels', methods=['POST'])
def set_pixels():
   pixel_set = []
   controllers = set()
   for name, pixel in pixels.items():
      key = 'color_%s' % name
      if key in request.form.keys():
         pixel = pixels[name]
         pixel.fade_html_color(request.form[key])
         pixel_set.append(pixel)
         controllers.update(pixel.get_controllers())

   for i in range(40):
      time.sleep(0.025)
      for pixel in pixel_set:
         pixel.fade_progress(i / 39)
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
