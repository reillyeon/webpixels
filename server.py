from flask import Flask, redirect, render_template, request, url_for
import json
from webpixels import AveragePixel, RgbPixel
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
      pixels[fixtureConfig['name']] = AveragePixel(pixel_set)

   all_pixels = [pixel for pixel in pixels.values()
                 if not isinstance(pixel, AveragePixel)]
   pixels['all'] = AveragePixel(all_pixels)

@app.route('/')
def index():
   pixel_list = [(name, pixel.get_html_color())
                 for name, pixel in pixels.items()
                 if not isinstance(pixel, AveragePixel)]
   pixel_list.sort(key=lambda pixel: pixel[0])
   fixture_list = [(name, pixel.get_html_color())
                   for name, pixel in pixels.items()
                   if isinstance(pixel, AveragePixel)]
   fixture_list.sort(key=lambda pixel: pixel[0])
   return render_template('index.html',
                          pixels=pixel_list,
                          fixtures=fixture_list)

@app.route('/pixel/<pixel>', methods=['GET', 'POST'])
def pixel(pixel):
   if request.method == 'POST':
      pixels[pixel].set_html_color(request.form['color'])
      pixels[pixel].sync()
      return redirect(url_for('index'))
   else:
      return pixels[pixel].get_html_color()

@app.route('/pixels', methods=['POST'])
def set_pixels():
   controllers = set()
   for name, pixel in pixels.items():
      key = 'color_%s' % name
      if key in request.form.keys():
         pixels[name].set_html_color(request.form[key])
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
