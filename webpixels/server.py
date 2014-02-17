from flask import Flask, redirect, render_template, request, url_for
from basic import *
from controller import ColorKinetics
import re

app = Flask(__name__)

controller = ColorKinetics(host="192.168.1.44")

pixels = []
for i in range(8):
   r, g, b = controller.channels[i*3:i*3+3]
   pixels.append(RgbPixel(r, g, b))

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
   pixel_list = []
   for i in range(len(pixels)):
      pixel_list.append((str(i), rgb_to_hex_triplet(*pixels[i].get())))
   return render_template('index.html', pixels=pixel_list)

@app.route('/pixel/all', methods=['POST'])
def all_pixels():
   r, g, b = hex_triplet_to_rgb(request.form['color'])
   for pixel in pixels:
      pixel.set(r, g, b)
   controller.sync()
   return redirect(url_for('index'))

@app.route('/pixel/<int:pixel>', methods=['GET', 'POST'])
def pixel(pixel):
   if request.method == 'POST':
      r, g, b = hex_triplet_to_rgb(request.form['color'])
      pixels[pixel].set(r, g, b)
      controller.sync()
      return redirect(url_for('index'))
   else:
      rgb = pixels[pixel].get()
      return rgb_to_hex_triplet(*rgb)

@app.route('/reset', methods=['POST'])
def pixel_reset():
   for pixel in pixels:
      pixel.set(0, 0, 0)
   controller.sync()
   return ''

if __name__ == '__main__':
   controller.sync()
   app.debug = True
   app.run(host='0.0.0.0', port=80)
