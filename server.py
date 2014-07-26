from datetime import timedelta
from flask import Flask, redirect, render_template, request, url_for
import json
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.wsgi import WSGIContainer
from webpixels import PixelSet, RgbPixel
from webpixels.controller import ColorKinetics

app = Flask(__name__)
ioloop = IOLoop.instance()

config_file = None

channels = {}
pixels = {}
fixtures = {}
presets = {}
last_preset = None

def load_config(config_file):
   with open(config_file) as f:
      config = json.loads(f.read())

   for name, controllerConfig in config['controllers'].items():
      controllerType = controllerConfig['type']
      if controllerType == 'ColorKinetics':
         controller = ColorKinetics(name, controllerConfig['host'])
      for channel in controller.channels:
         channels[channel.get_name()] = channel

   for name, pixelConfig in config['pixels'].items():
      chan_set = [channels[channel] for channel in pixelConfig['channels']]
      pixel = RgbPixel(name, *chan_set)
      pixels[pixel.get_name()] = pixel

   for name, fixtureConfig in config['fixtures'].items():
      pixel_set = [pixels[pixel] for pixel in fixtureConfig['pixels']]
      fixture = PixelSet(name, pixel_set)
      fixtures[fixture.get_name()] = fixture

   global all_pixel
   all_pixel = PixelSet('all', pixels.values())

   if 'presets' in config:
      presets.update(config['presets'])

def save_config(config_file):
   controller_set = set()
   saved_controllers = {}
   saved_pixels = {}
   saved_fixtures = {}

   for pixel in pixels.values():
      controller_set.update(pixel.get_controllers())
      saved_pixels[pixel.get_name()] = {
         'channels': [
            pixel.red.get_name(),
            pixel.green.get_name(),
            pixel.blue.get_name()
         ]
      }

   for fixture in fixtures.values():
      saved_fixtures[fixture.get_name()] = {
         'pixels': [subpixel.get_name() for subpixel in fixture.get_pixels()]
      }

   for controller in controller_set:
      if isinstance(controller, ColorKinetics):
         controller_type = "ColorKinetics"
      saved_controllers[controller.get_name()] = {
         'host': controller.host,
         'type': controller_type
      }

   save_data = json.dumps({
      'controllers': saved_controllers,
      'pixels': saved_pixels,
      'fixtures': saved_fixtures,
      'presets': presets
   }, sort_keys=True, indent=2, separators=(',', ': '))

   with open(config_file, 'w') as f:
      f.write(save_data)

def redirect_url():
   return redirect(request.args.get('next') or \
                   request.referrer or \
                   url_for('index'))

fade_in_progress = False

def fade_step():
   global fade_in_progress

   need_more = False
   controller_set = set()
   for pixel in pixels.values():
      if pixel.step():
         need_more = True
      controller_set.update(pixel.get_controllers())

   for controller in controller_set:
      controller.sync()

   if need_more:
      ioloop.add_timeout(timedelta(milliseconds=25), fade_step)
   else:
      fade_in_progress = False

def start_fade():
   global fade_in_progress

   if fade_in_progress:
      return

   fade_in_progress = True
   fade_step()

@app.route('/', methods=['GET'])
def index():
   fixture_list = []
   for name, fixture in fixtures.items():
      subpixels = [(pixel.get_name(), pixel.get_html_color())
                   for pixel in fixture.get_pixels()]
      fixture_list.append((name, fixture.get_html_color(), subpixels))

   fixture_list.sort(key=lambda fixture: fixture[0])


   return render_template('index.html',
                          all=all_pixel.get_html_color(),
                          fixtures=fixture_list)

@app.route('/pixel/<name>', methods=['GET', 'POST'])
def pixel(name):
   if name == 'all':
      pixel = all_pixel
   else:
      pixel = fixtures.get(name)
      if pixel is None:
         pixel = pixels[name]

   if request.method == 'POST':
      return pixel_post(pixel)
   else:
      return pixel_get(pixel)

def pixel_post(pixel):
   r = int(request.form['r'])
   g = int(request.form['g'])
   b = int(request.form['b'])

   pixel.set_target(r, g, b)
   start_fade()

   return ""

def pixel_get(pixel):
   r, g, b = pixel.get()

   return render_template('pixel.html',
                          pixel=pixel.get_name(),
                          r=r, g=g, b=b)

@app.route('/presets', methods=['GET'])
def preset_list():
   preset_list = list(presets.keys())
   preset_list.sort()

   return render_template('presets.html',
                          presets=preset_list,
                          last_preset=last_preset)

@app.route('/preset/save', methods=['POST'])
def preset_save():
   preset = {}

   for name, pixel in pixels.items():
      preset[name] = pixel.get()

   presets[request.form['name']] = preset
   save_config(config_file)

   global last_preset
   last_preset = request.form['name']

   return ""

@app.route('/preset/apply', methods=['POST'])
def preset_apply():
   name = request.form['preset']
   preset = presets[name]

   for name, value in preset.items():
      pixel = pixels[name]
      pixel.set_target(*value)

   start_fade()

   global last_preset
   last_preset = name

   return ""

@app.route('/preset/delete', methods=['POST'])
def preset_delete():
   del presets[request.form['name']]
   save_config(config_file)

   return ""

if __name__ == '__main__':
   import sys

   if len(sys.argv) != 2:
      print("Usage: python server.py config.json")

   config_file = sys.argv[1]
   load_config(config_file)

   app.debug = True
   http_server = HTTPServer(WSGIContainer(app))
   http_server.listen(80)
   ioloop.start()
