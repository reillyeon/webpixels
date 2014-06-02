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
      pixels[fixture.get_name()] = fixture

   all_pixels = [pixel for pixel in pixels.values()
                 if not isinstance(pixel, PixelSet)]
   pixels['all'] = PixelSet('all', all_pixels)

   if 'presets' in config:
      presets.update(config['presets'])

def save_config(config_file):
   controller_set = set()
   saved_controllers = {}
   saved_pixels = {}
   saved_fixtures = {}

   for pixel in pixels.values():
      controller_set.update(pixel.get_controllers())
      if isinstance(pixel, RgbPixel):
         saved_pixels[pixel.get_name()] = {
            'channels': [
               pixel.red.get_name(),
               pixel.green.get_name(),
               pixel.blue.get_name()
            ]
         }
      elif isinstance(pixel, PixelSet) and pixel.get_name() != 'all':
         saved_fixtures[pixel.get_name()] = {
            'pixels': [subpixel.get_name() for subpixel in pixel.get_pixels()]
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

@app.route('/', methods=['GET'])
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

   preset_list = list(presets.keys())
   preset_list.sort()

   return render_template('index.html',
                          all=all_pixels,
                          pixels=pixel_list,
                          fixtures=fixture_list,
                          presets=preset_list,
                          last_preset=last_preset)

@app.route('/pixel/<pixel>', methods=['GET', 'POST'])
def pixel(pixel):
   pixel = pixels[pixel]
   if request.method == 'POST':
      return pixel_post(pixel)
   else:
      return pixel_get(pixel)

def pixel_post(pixel):
   immediate = 'immediate' in request.form.keys() and \
      request.form['immediate'] == 'true'
   if immediate:
      pixel.set_html_color(request.form['color'])
      pixel.sync()
   else:
      pixel.fade_html_color(request.form['color'])
      for i in range(40):
         time.sleep(0.025)
         pixel.fade_progress(i / 39)
         pixel.sync()
   return redirect_url()

def pixel_get(pixel):
   channels = None
   subpixels = None

   if isinstance(pixel, RgbPixel):
      channels = [(c.get_name(), c.get()) for c in pixel.get_channels()]
   elif isinstance(pixel, PixelSet):
      subpixels = [(p.get_name(), p.get_html_color())
                   for p in pixel.get_pixels()]

   return render_template('pixel.html',
                          pixel=pixel.get_name(),
                          color=pixel.get_html_color(),
                          channels=channels,
                          subpixels=subpixels)

@app.route('/pixels', methods=['POST'])
def pixels_post():
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

   return redirect_url()

@app.route('/channel/<channel>', methods=['GET', 'POST'])
def channel(channel):
   channel = channels[channel]
   if request.method == 'POST':
      return channel_post(channel)
   else:
      return channel_get(channel)

def channel_post(channel):
   channel.set(int(request.form['value']))
   channel.sync()

   return redirect_url()

def channel_get(channel):
   return render_template('channel.html',
                          channel=channel.get_name(),
                          value=channel.get())

@app.route('/channels', methods=['POST'])
def channels_post():
   controllers = set()
   for name, channel in channels.items():
      if name in request.form.keys():
         channel.set(int(request.form[name]))
         controllers.add(channel.get_controller())

   for controller in controllers:
      controller.sync()

   return redirect_url()

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
      if isinstance(pixel, PixelSet):
         continue

      preset[name] = pixel.get()

   presets[request.form['name']] = preset
   save_config(config_file)

   global last_preset
   last_preset = request.form['preset']

   return redirect_url()

@app.route('/preset/apply', methods=['POST'])
def preset_apply():
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

   global last_preset
   last_preset = request.form['preset']

   return redirect_url()

@app.route('/preset/delete', methods=['POST'])
def preset_delete():
   del presets[request.form['name']]
   save_config(config_file)

   return redirect_url()

if __name__ == '__main__':
   import sys

   if len(sys.argv) != 2:
      print("Usage: python server.py config.json")

   config_file = sys.argv[1]
   load_config(config_file)

   app.debug = True
   app.run(host='0.0.0.0', port=80)
