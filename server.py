from flask import Flask, redirect, render_template, request, url_for
import json
import time
from webpixels import PixelSet, RgbPixel
from webpixels.controller import ColorKinetics

app = Flask(__name__)

config_file = None

channels = {}
pixels = {}
presets = {}

def load_config(config_file):
   with open(config_file) as f:
      config = json.loads(f.read())

   for controllerConfig in config['controllers']:
      controllerType = controllerConfig['type']
      if controllerType == 'ColorKinetics':
         controller = ColorKinetics(controllerConfig['name'],
                                    controllerConfig['host'])
      for channel in controller.channels:
         channels[channel.get_name()] = channel

   for pixelConfig in config['pixels']:
      chan_set = [channels[name] for name in pixelConfig['channels']]
      pixel = RgbPixel(pixelConfig['name'], *chan_set)
      pixels[pixel.get_name()] = pixel

   for fixtureConfig in config['fixtures']:
      pixel_set = [pixels[name] for name in fixtureConfig['pixels']]
      fixture = PixelSet(fixtureConfig['name'], pixel_set)
      pixels[fixture.get_name()] = fixture

   all_pixels = [pixel for pixel in pixels.values()
                 if not isinstance(pixel, PixelSet)]
   pixels['all'] = PixelSet('all', all_pixels)

   if 'presets' in config:
      presets.update(config['presets'])

def save_config(config_file):
   controller_set = set()
   saved_controllers = []
   saved_pixels = []
   saved_fixtures = []

   for pixel in pixels.values():
      controller_set.update(pixel.get_controllers())
      if isinstance(pixel, RgbPixel):
         saved_pixels.append({
            'name': pixel.get_name(),
            'channels': [
               pixel.red.get_name(),
               pixel.green.get_name(),
               pixel.blue.get_name()
            ]
         })
      elif isinstance(pixel, PixelSet) and pixel.get_name() != 'all':
         saved_fixtures.append({
            'name': pixel.get_name(),
            'pixels': [subpixel.get_name() for subpixel in pixel.get_pixels()]
         })

   for controller in controller_set:
      if isinstance(controller, ColorKinetics):
         controller_type = "ColorKinetics"
      saved_controllers.append({
         'name': controller.get_name(),
         'host': controller.host,
         'type': controller_type
      })

   save_data = json.dumps({
      'controllers': saved_controllers,
      'pixels': saved_pixels,
      'fixtures': saved_fixtures,
      'presets': presets
   }, sort_keys=True, indent=2, separators=(',', ': '))

   with open(config_file, 'w') as f:
      f.write(save_data)

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

   preset_list = presets.keys()

   return render_template('index.html',
                          all=all_pixels,
                          pixels=pixel_list,
                          fixtures=fixture_list,
                          presets=preset_list)

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

@app.route('/preset/save', methods=['POST'])
def save_preset():
   preset = {}

   for name, pixel in pixels.items():
      if isinstance(pixel, PixelSet):
         continue

      preset[name] = pixel.get()

   presets[request.form['preset']] = preset
   save_config(config_file)

   return redirect(url_for('index'))

@app.route('/preset/apply', methods=['POST'])
def apply_preset():
   preset = presets[request.form['preset']]
   pixel_set = []
   controller_set = set()

   for name, value in preset.items():
      pixel = pixels[name]
      pixel.fade(*value)
      pixel_set.append(pixel)
      controller_set.update(pixel.get_controllers())

   for i in range(40):
      time.sleep(0.025)
      for pixel in pixel_set:
         pixel.fade_progress(i / 39)
      for controller in controller_set:
         controller.sync()

   return redirect(url_for('index'))

@app.route('/preset/delete', methods=['POST'])
def delete_preset():
   del presets[request.form['preset']]
   save_config(config_file)

   return redirect(url_for('index'))

if __name__ == '__main__':
   import sys

   if len(sys.argv) != 2:
      print("Usage: python server.py config.json")

   config_file = sys.argv[1]
   load_config(config_file)

   app.debug = True
   app.run(host='0.0.0.0', port=80)
